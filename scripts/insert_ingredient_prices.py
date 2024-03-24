import logging

import pandas as pd
import requests
from sqlalchemy import Engine
from sqlmodel import select

from chao_fan.db import Session, engine
from chao_fan.models import IngredientPrice

logger = logging.getLogger(__name__)


def download_ingredient_price_data(
    version="3036.9", sheet="PP-NAP1718"
) -> pd.DataFrame:
    """
    Download ingredient price data from USDA website

    Parameters
    ----------
    version : str
        USDA data version
    sheet : str
        Excel sheet name, corresponds to the year of the data


    Notes
    -----
    Data comes from https://www.ers.usda.gov/data-products/purchase-to-plate/

    Returns
    -------
    pd.DataFrame
        The ingredient price data
    """
    params = {"v": version}
    url = f"https://www.ers.usda.gov/webdocs/DataFiles/105537/pp_national_average_prices.xlsx"
    r = requests.get(url, params=params, allow_redirects=True)
    if r.status_code != 200:
        raise ValueError(
            f"Failed to download ingredient price data. Status code: {r.status_code}"
        )
    prices_df = pd.read_excel(r.content, sheet_name=sheet)
    return prices_df


def reformat_ingredient_price_data(df: pd.DataFrame) -> pd.DataFrame:
    """Reformat the ingredient price data"""
    df = df.rename(
        columns={"food_description": "description", "price_100gm": "price_100grams"}
    )
    df = df[["description", "price_100grams"]]
    df = df.drop_duplicates().dropna()
    return df


def upsert_ingredient_price_data(df: pd.DataFrame, engine: Engine):
    """Upsert the ingredient price data into the database"""
    with Session(engine) as session:
        for index, row in df.iterrows():
            ingredient = session.exec(
                select(IngredientPrice).where(
                    IngredientPrice.description == row["description"]
                )
            ).first()
            if ingredient is None:
                ingredient = IngredientPrice(description=row["description"])
            ingredient.price_100grams = row["price_100grams"]
            session.add(ingredient)
        session.commit()


def update_ingredient_price_data():
    """Update the ingredient price data in the database"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Download ingredient price data
    logger.info("Downloading ingredient price data")
    df = download_ingredient_price_data()

    # Reformat data
    df = reformat_ingredient_price_data(df)

    # Insert into database
    logger.info(f"Upserting ingredient price data ({len(df)} rows)")
    upsert_ingredient_price_data(df, engine)


if __name__ == "__main__":
    upsert_ingredient_price_data()
