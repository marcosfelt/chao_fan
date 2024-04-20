import logging
import sqlite3
from argparse import ArgumentParser

import pandas as pd
from sqlmodel import Session

from chao_fan.db import engine
from chao_fan.models import IngredientNutrition

logger = logging.getLogger(__name__)


def read_sqlite_table(table_name: str, db: sqlite3.Connection) -> pd.DataFrame:
    """Read a table from a SQLite database"""
    return pd.read_sql_query(f"SELECT * FROM {table_name}", db)


def rename_columns_grams(s: str) -> str:
    """Rename columns"""
    if s in ["fdc_id", "description"]:
        return s
    else:
        return f"{s}_grams"


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    parser = ArgumentParser()
    parser.add_argument(
        "sqlite_db",
        type=str,
        help="Path to the Comprehensive food SQLite database file",
    )
    parser.add_argument(
        "--table_name",
        type=str,
        default="usda_branded_column",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=10000,
        help="Number of rows to insert into the database at a time",
    )
    args = parser.parse_args()

    logger.info("Connecting to SQLite database")
    db = sqlite3.connect(args.sqlite_db)

    # Count the number of rows in the table
    num_rows = db.execute(f"SELECT COUNT(*) FROM {args.table_name}").fetchone()[0]
    logger.info(f"Number of rows in {args.table_name}: {num_rows}")
    n_batches = num_rows // args.batch_size + 1

    # Read the ingredient nutrition data in batches and insert into IngredientNutrition table
    batch = 1
    for df in pd.read_sql_query(
        f"SELECT * FROM {args.table_name}", db, chunksize=args.batch_size
    ):
        logger.info(f"Processing batch {batch}/{n_batches}")

        # Rename columns
        # df = df.rename(rename_columns_grams)

        # Connect to Postgres
        with Session(engine) as session:
            session.bulk_insert_mappings(
                IngredientNutrition, df.to_dict(orient="records")
            )
            session.commit()
        batch += 1


if __name__ == "__main__":
    main()
