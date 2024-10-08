import logging
import os
from datetime import datetime
from typing import List, Optional

import nltk
from ingredient_parser import parse_ingredient
from recipe_scrapers import WebsiteNotImplementedError, scrape_me
from recipe_scrapers._exceptions import NoSchemaFoundInWildMode, SchemaOrgException
from requests.exceptions import ConnectionError
from sqlmodel import Session, select
from urllib3.exceptions import HTTPError

from chao_fan.integrations.sentence_transformer import generate_embeddings
from chao_fan.models import (
    IngredientNutrition,
    IngredientPrice,
    Instruction,
    Recipe,
    RecipeIngredient,
)

logger = logging.getLogger(__name__)

INGREDIENT_PRICE_COSINE_DISTANCE_CUTOFF = float(
    os.environ.get("INGREDIENT_PRICE_COSINE_DISTANCE_CUTOFF", 0.6)
)
INGREDIENT_NUTRITION_COSINE_DISTANCE_CUTOFF = float(
    os.environ.get("INGREDIENT_NUTRITION_COSINE_DISTANCE_CUTOFF", 0.8)
)


def create_instructions(
    instructions: str,
    instructions_list: Optional[List[str]] = None,
) -> List[Instruction]:
    """Create instructions from a string"""
    if instructions_list is None:
        instructions_list = instructions.split("\n")
    return [
        Instruction(step_number=i, step=step)
        for i, step in enumerate(instructions_list)
    ]


def download_nltk_model():
    nltk.download("averaged_perceptron_tagger")


def estimate_ingredient_price(
    ingredient: RecipeIngredient,
    session: Session,
    cosine_distance_cutoff: float = 0.6,
    number_to_average: int = 5,
) -> float | None:
    """

    Estimate the price of an ingredient

    Parameters
    ----------
    ingredient : RecipeIngredient
        The ingredient to estimate the price of
    session : Session
        The database session
    cosine_distance_cutoff : float, optional
        The cosine distance cutoff below which we return None, by default 0.6
    number_to_average : int, optional
        The number of ingredients to average, by default 5

    Returns
    -------
    float
        The estimated price of the ingredient

    Notes
    -----
    This function estimates the price of an ingredient by finding the top 5 ingredients with the closest embeddings
    and returning the average price. If the cosine distance is less than the cutoff, return None.

    """
    if ingredient.embedding is None:
        return None
    statement = (
        select(IngredientPrice)
        .where(
            IngredientPrice.embedding.cosine_distance(ingredient.embedding)
            > cosine_distance_cutoff
        )
        .order_by(IngredientPrice.embedding.cosine_distance(ingredient.embedding))
        .limit(number_to_average)
    )
    results: List[IngredientPrice] = session.exec(statement).all()
    if len(results) == 0:
        return None
    return sum([result.price_100grams for result in results]) / 5


def estimate_ingredient_nutrition(
    ingredient: RecipeIngredient,
    session: Session,
    cosine_distance_cutoff: float = 0.6,
) -> IngredientNutrition | None:
    if ingredient.embedding is None:
        return None
    statement = (
        select(IngredientNutrition)
        .where(
            IngredientNutrition.embedding.cosine_distance(ingredient.embedding)
            > cosine_distance_cutoff
        )
        .order_by(IngredientNutrition.embedding.cosine_distance(ingredient.embedding))
        .limit(1)
    )
    results: List[IngredientNutrition] = session.exec(statement).all()
    if len(results) == 0:
        return None
    return results[0]


def create_ingredients(
    ingredients_txt: List[str], embedding_model=None, session: Session | None = None
) -> List[RecipeIngredient]:
    """Create ingredients from a list of strings"""
    parsed_ingredients = []
    for ingredient_txt in ingredients_txt:
        if ingredient_txt is None:
            continue
        # Create ingredient
        ingredient = RecipeIngredient(full_description=ingredient_txt)

        # Try to parse using ingredient parser
        parsed_ingredient = parse_ingredient(ingredient_txt)
        if parsed_ingredient is None:
            ingredient.name = ingredient_txt
            parsed_ingredients.append(ingredient)
            logger.debug("Could not parse: {}")
            continue

        # Parse name
        ingredient.description = (
            parsed_ingredient.name.text if parsed_ingredient.name is not None else None
        )
        if ingredient.description is None:
            ingredient.description = ingredient_txt
        if len(parsed_ingredient.amount) > 0:
            try:
                ingredient.amount = float(parsed_ingredient.amount[0].quantity)
                ingredient.unit = str(parsed_ingredient.amount[0].unit)
            except ValueError:
                pass

        # Embedding
        if embedding_model is not None:
            ingredient.embedding = generate_embeddings(
                ingredient.description,
                model=embedding_model,
                show_progress_bar=False,
            )

        if session is not None and ingredient.embedding is not None:
            # Estimate ingredient price
            ingredient.estimated_price_100grams = estimate_ingredient_price(
                ingredient,
                session,
                cosine_distance_cutoff=INGREDIENT_PRICE_COSINE_DISTANCE_CUTOFF,
            )

            # Estimate ingredient nutrition
            ingredient_nutrition = estimate_ingredient_nutrition(
                ingredient,
                session,
                cosine_distance_cutoff=INGREDIENT_NUTRITION_COSINE_DISTANCE_CUTOFF,
            )
            if ingredient_nutrition:
                ingredient.ingredient_nutrition = ingredient_nutrition

        parsed_ingredients.append(ingredient)
    return parsed_ingredients


def scrape_recipe(
    recipe: Recipe,
    session: Session | None = None,
    embedding_model=None,
) -> Recipe:
    """
    Scrape a recipe from a URL

    Parameters
    ----------
    url : str
        The URL of the recipe


    Returns
    -------
    Recipe
        The scraped recipe

    """
    scraper = None
    wild_mode = False
    tries = 0
    recipe.enrichment_failed_at = datetime.now()
    while not scraper and tries < 3:
        try:
            scraper = scrape_me(recipe.source_url, wild_mode=wild_mode)
            tries += 1
        except WebsiteNotImplementedError:
            wild_mode = True
        except NoSchemaFoundInWildMode as e:
            logger.error(e)
            return recipe
        except HTTPError as e:
            logger.error(e)
            return recipe
        except ConnectionError as e:
            logger.error(e)
            return recipe
    if scraper is None:
        return recipe

    try:
        recipe.title = scraper.title()
        instructions_text = scraper.instructions()
        instructions_list = scraper.instructions_list()
    except SchemaOrgException as e:
        logger.error(e)
        return recipe
    except TypeError as e:
        logger.error(e)
        return recipe

    # Instructions
    if instructions_text:
        instructions = create_instructions(instructions_text, instructions_list)
        if len(instructions) > 0:
            recipe.instructions = instructions

    # Ingredients
    ingredients = create_ingredients(
        scraper.ingredients(), embedding_model=embedding_model, session=session
    )
    if len(ingredients) > 0:
        recipe.recipe_ingredients = ingredients

    # Total time
    try:
        total_time = scraper.total_time()
        if total_time:
            recipe.ready_in_minutes = total_time
    except SchemaOrgException as e:
        logger.error(e)

    # Image
    try:
        image = scraper.image()
    except SchemaOrgException as e:
        logger.error(e)
        image = None
    if image:
        recipe.image = image

    recipe.enriched_at = datetime.now()
    recipe.enrichment_failed_at = None
    return recipe
