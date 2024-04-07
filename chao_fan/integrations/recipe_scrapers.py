import logging
from datetime import datetime
from typing import List, Optional

import nltk
from ingredient_parser import parse_ingredient
from recipe_scrapers import WebsiteNotImplementedError, scrape_me
from recipe_scrapers._exceptions import NoSchemaFoundInWildMode, SchemaOrgException
from requests.exceptions import ConnectionError
from urllib3.exceptions import HTTPError

from chao_fan.models import IngredientNutrition, Instruction, Recipe, RecipeIngredient

logger = logging.getLogger(__name__)


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


def estimate_ingredient_price(ingredient: RecipeIngredient) -> float:
    return 0.5


def estimate_ingredient_nutrition(
    ingredient: RecipeIngredient,
) -> IngredientNutrition | None:
    return {}


def create_ingredients(ingredients_txt: List[str]) -> List[RecipeIngredient]:
    """Create ingredients from a list of strings"""
    parsed_ingredients = []
    for ingredient_txt in ingredients_txt:
        if ingredient_txt is None:
            continue
        # Create ingredient
        ingredient = RecipeIngredient(
            full_description=ingredient_txt,
        )

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
            ingredient.amount = parsed_ingredient.amount[0].quantity
            ingredient.unit = parsed_ingredient.amount[0].unit

        # Estimate ingredient price
        ingredient.estimated_price_100grams = estimate_ingredient_price(ingredient)

        # Estimate ingredient nutrition
        # ingredient_nutrition = estimate_ingredient_nutrition(ingredient)
        # if ingredient_nutrition:
        #     ingredient.ingredient_nutrition = ingredient_nutrition

        parsed_ingredients.append(ingredient)
    return parsed_ingredients


def scrape_recipe(url: str) -> Recipe | None:
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
    recipe = Recipe(source_url=url)
    while not scraper and tries < 3:
        try:
            scraper = scrape_me(url, wild_mode=wild_mode)
            tries += 1
        except WebsiteNotImplementedError:
            wild_mode = True
        except NoSchemaFoundInWildMode as e:
            recipe.enrichment_failed_at = datetime.now()
            logger.error(e)
            return recipe
        except HTTPError as e:
            recipe.enrichment_failed_at = datetime.now()
            logger.error(e)
            return recipe
        except ConnectionError as e:
            recipe.enrichment_failed_at = datetime.now()
            logger.error(e)
            return recipe
    if scraper is None:
        recipe.enrichment_failed_at = datetime.now()
        return recipe

    try:
        recipe.title = scraper.title()
        instructions_text = scraper.instructions()
        instructions_list = scraper.instructions_list()
    except SchemaOrgException as e:
        logger.error(e)
        recipe.enrichment_failed_at = datetime.now()
        return recipe
    except TypeError as e:
        recipe.enrichment_failed_at = datetime.now()
        logger.error(e)
        return recipe

    # Instructions
    if instructions_text:
        instructions = create_instructions(instructions_text, instructions_list)
        if len(instructions) > 0:
            recipe.instructions = instructions

    # Ingredients
    ingredients = create_ingredients(scraper.ingredients())
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
    return recipe
