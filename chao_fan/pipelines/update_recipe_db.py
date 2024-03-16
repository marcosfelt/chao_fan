from typing import Dict, List
from chao_fan.integrations.pinterest import (
    setup_pinterest,
    get_pinterest_board_id,
    get_pin_links,
    Pin,
)
from chao_fan.integrations.spoonacular import extract_recipe
from dotenv import load_dotenv
import os
from chao_fan.models import Recipe
from chao_fan.db import engine
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
                spoonacular_enriched=False,
            )
            session.add(recipe)
        session.commit()


def enrich_recipes_spoonacular(engine: Engine, max_api_calls: int = 150):
    with Session(engine) as session:
        statement = (
            select(Recipe)
            .where(Recipe.spoonacular_enriched == False)
            .limit(max_api_calls)
        )
        results = session.exec(statement)
        for recipe in tqdm(results, total=max_api_calls):
            enriched_recipe = extract_recipe(recipe.source_url)
            recipe.sqlmodel_update(enriched_recipe)
            session.add(recipe)
        session.commit()


def update_recipe_db():
    """Update recipe database with new pins from pinterest board"""
    logger = logging.getLogger(__name__)
    load_dotenv()

    # Get pinterest links

    logger.info("Getting pinterest links")
    pins = get_pinterest_links(BOARD_NAME)
    new_pins = find_pins_not_in_db(pins, engine)
    logger.info(f"Found {len(new_pins)} new pins. Inserting into recipe table.")
    insert_pins_into_db(new_pins, engine)

    # Enrich recipes
    logger.info("Enriching recipes with Spoonacular")
    try:
        enrich_recipes_spoonacular(engine, max_api_calls=MAX_SPOONACULAR_API_CALLS)
    except ValueError as e:
        logger.error(e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    update_recipe_db()
    print("Recipe database updated.")
