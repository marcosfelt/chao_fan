import logging
import os
from typing import List

from sqlalchemy.engine import Engine
from sqlmodel import Session, select, text

from chao_fan.db import engine
from chao_fan.integrations.sentence_transformer import generate_embeddings, get_model
from chao_fan.models import Ingredient, IngredientNutrition, IngredientPrice
from chao_fan.utils import Timeout

logger = logging.getLogger(__name__)


def generate_ingredient_embeddings(
    engine: Engine,
    ingredient_model: Ingredient,
    batch_size: int,
    device: str | None = None,
):
    """
    Generate embeddings for ingredients tables that don't have them

    Parameters
    ----------
    engine : Engine
        The sqlalchemy engine
    ingredient_model : Ingredient
        The ingredient table for which to generate embeddings
    batch_size : int
        The batch size for encoding embeddings
    """
    transformer_model = get_model(device=device)
    with Session(engine) as session:
        table_name = ingredient_model.__tablename__
        n_rows = session.exec(
            text(f"SELECT count(*) FROM {table_name} WHERE embedding IS NULL")
        ).fetchone()[0]
        logger.info(f"Number of rows in {table_name} without embeddings: {n_rows}")
    n_batches = n_rows // batch_size + 1
    batch = 1
    while True:
        with Session(engine) as session:
            logger.info(f"Generating embeddings for batch {batch}/{n_batches}")
            # Query for ingredients that don't have embeddings
            ingredients = session.exec(
                select(ingredient_model)
                .where(ingredient_model.embedding == None)  # noqa
                .limit(batch_size)
            )
            ingredients: List[Ingredient] = ingredients.fetchall()
            if len(ingredients) == 0:
                break
            ingredient_descriptions = [
                ingredient.description for ingredient in ingredients
            ]

            # Generate embeddings
            ingredient_embeddings = generate_embeddings(
                ingredient_descriptions,
                model=transformer_model,
                show_progress_bar=False,
            )

            # Update ingredients with embeddings
            for ingredient, embedding in zip(ingredients, ingredient_embeddings):
                ingredient.embedding = embedding
            session.commit()
        batch += 1


def update_embeddings():
    # Generate IngredientNutrition and IngredientPrice embeddings
    device = os.environ.get("INGREDIENT_EMBEDDING_DEVICE", None)
    batch_size = int(os.environ.get("INGREDIENT_EMBEDDING_GENERATION_BATCH_SIZE", 1000))
    timeout = os.environ.get("INGREDIENT_EMBEDDING_GENERATION_TIMEOUT_SECONDS", 600)
    try:
        with Timeout(int(timeout)):
            for ingredient in [IngredientNutrition, IngredientPrice]:
                logger.info(f"Generating embeddings for {ingredient.__name__}")
                generate_ingredient_embeddings(
                    engine, ingredient, batch_size=batch_size, device=device
                )
    except TimeoutError:
        logger.error(
            f"Timed out after {timeout} seconds while generating embeddings for IngredientNutrition and IngredientPrice"
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    update_embeddings()
