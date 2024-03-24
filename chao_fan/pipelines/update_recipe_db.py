from datetime import datetime, timedelta
from typing import Dict, List, Optional
from chao_fan.integrations.pinterest import (
    setup_pinterest,
    get_pinterest_board_id,
    get_pin_links,
    Pin,
)
from chao_fan.integrations.recipe_scrapers import scrape_recipe
from dotenv import load_dotenv
import os
from chao_fan.models import Recipe
from chao_fan.db import engine, SQLModel
from sqlmodel import Session, text, bindparam, select
from sqlalchemy.engine import Engine
import logging
from tqdm import tqdm

BOARD_NAME = "Cookin'"
MAX_SPOONACULAR_API_CALLS = 60


def get_pinterest_links(board_name: str) -> List[Pin]:
    """Get pinterest links

    Parameters
    ----------
    board_name : str
        The name of the board to get links from

    Returns
    -------
    List[Pin]
        Pins from the board

    """
    pinterest = setup_pinterest(
        email=os.environ.get("PINTEREST_EMAIL"),
        password=os.environ.get("PINTEREST_PASSWORD"),
        username=os.environ.get("PINTEREST_USERNAME"),
    )
    board_id = get_pinterest_board_id(pinterest, board_name)
    return get_pin_links(pinterest, board_id)


def find_pins_not_in_db(pins: List[Pin], engine: Engine) -> List[Pin]:
    """Find pins not in database

    Parameters
    ----------
    pins : List[Pin]
        The pins to check
    engine : Engine
        The sqlalchemy engine

    Returns
    -------
    List[Pin]
        Pins not in the database

    """
    with engine.connect() as conn:
        t = text(
            """
            SELECT DISTINCT source_url FROM recipe
            WHERE source_url in :source_urls
            """
        )
        t = t.bindparams(bindparam("source_urls", expanding=True))
        result = conn.execute(
            t,
            dict(source_urls=[pin.url for pin in pins]),
        )
        existing_urls = [row[0] for row in result]
    return [pin for pin in pins if pin.url not in existing_urls]


def insert_pins_into_db(pins: List[Pin], engine: Engine):
    """Insert pins into database

    Parameters
    ----------
    pins : List[Pin]
        The pins to insert
    engine : Engine
        The sqlalchemy engine
    """
    with Session(engine) as session:
        for pin in pins:
            recipe = Recipe(
                source_name=pin.site_name,
                source_url=pin.url,
                enriched=False,
            )
            session.add(recipe)
        session.commit()


def _enrich_recipes_batch(session: Session, recipes: List[Recipe], n: int):
    """
    1. Use recipe_scrapers to scrape recipe (title, instructions and ingredients)
    2. Extract ingredients using ingredient_parser
    3. Estimate each ingredient nutrition via semantic search in nutrition table
    4. Estimate each ingredient price via semantic search in prices table
    5. Generate recipe embedding
    6. Estimate recipe preference score using KNN on recipe embeddings
    """
    for recipe in tqdm(recipes, desc="Enriching", total=n):
        enriched_recipe = scrape_recipe(recipe.source_url)
        if enriched_recipe is None:
            continue
        # recipe_data = recipe.model_dump(exclude_unset=True)
        # enriched_recipe.sqlmodel_update(recipe_data)
        session.add(enriched_recipe)
        session.delete(recipe)


# def _enrich_recipes_spoonacular_batch(session: Session, recipes: List[Recipe], n: int):
#     for recipe in tqdm(recipes, desc="Enriching", total=n):
#         enriched_recipe = extract_recipe(recipe.source_url)
#         recipe_data = recipe.model_dump(exclude_unset=True)
#         enriched_recipe.sqlmodel_update(recipe_data)
#         session.add(enriched_recipe)


def enrich_recipes_spoonacular(
    engine: Engine,
    max_api_calls: int = 150,
    batch_size: int = 10,
    retry_enrichment_after: Optional[timedelta] = None,
):
    """
    Retrieve recipes from the database and enrich them

    Parameters
    ----------
    engine : Engine
        The sqlalchemy engine
    max_api_calls : int
        The maximum number of API calls to make
    batch_size : int
        The number of recipes to enrich at a time
    retry_enrichment_after : timedelta, optional
        The time after which to retry enrichment, if None is passed, defaults to 1 day
    """
    # Query for recipes that need to be enriched
    if retry_enrichment_after is None:
        retry_enrichment_after = timedelta(days=1)
    i = 0
    batch_size = batch_size if batch_size < max_api_calls else max_api_calls
    while i < max_api_calls:
        with Session(engine) as session:
            now = datetime.now()
            statement = (
                select(Recipe)
                .where(
                    (Recipe.enriched_at == None)
                    | (Recipe.enrichment_failed_at < now - retry_enrichment_after)
                )
                .limit(batch_size)
            )
            recipes = session.exec(statement)
            _enrich_recipes_batch(session, recipes, batch_size)
            session.commit()
            i += batch_size


def update_recipe_db():
    """Update recipe database with new pins from pinterest board"""
    logger = logging.getLogger(__name__)
    load_dotenv()

    # Get pinterest links
    logger.info("Getting pinterest links")
    # pins = get_pinterest_links(BOARD_NAME)
    # new_pins = find_pins_not_in_db(pins, engine)
    # logger.info(f"Found {len(new_pins)} new pins. Inserting into recipe table.")
    # insert_pins_into_db(new_pins, engine)

    # Enrich recipes
    logger.info("Enriching recipes")
    try:
        enrich_recipes_spoonacular(engine, max_api_calls=MAX_SPOONACULAR_API_CALLS)
    except ValueError as e:
        logger.error(e)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    update_recipe_db()
