from typing import Optional
import requests
import os
from dotenv import load_dotenv
from chao_fan.models import Recipe
import json


def camel_to_snake(camel_case_str):
    snake_case_str = ""
    for i, char in enumerate(camel_case_str):
        if char.isupper():
            if i != 0:
                snake_case_str += "_"
            snake_case_str += char.lower()
        else:
            snake_case_str += char
    return snake_case_str


def extract_recipe(
    url: str, api_key: Optional[str] = None, analyze_recipe: bool = True
) -> Recipe:
    """Extract recipe from url using spoonacular

    Parameters
    ----------
    url : str
        The url of the recipe
    api_key : Optional[str], optional
        The spoonacular api key, by default None
        If None, the function will look for SPOONACULAR_API_KEY in the environment
    analyze_recipe : bool, optional
        Whether to analyze the recipe, by default True
        Note that this requires an extra Spoonacular credit

    Raises
    ------
    ValueError
        If api_key is None or not in the environment

    Returns
    -------
    Recipe
        The recipe
    """
    # Make request
    if api_key is None:
        load_dotenv()
        api_key = os.environ.get("SPOONACULAR_API_KEY")
    if api_key is None:
        raise ValueError("api_key cannot be None")
    querystring = {
        "apiKey": api_key,
        "url": url,
        "analyze": analyze_recipe,
    }
    response = requests.get(
        "https://api.spoonacular.com/recipes/extract", params=querystring
    )

    if response.status_code != 200:
        raise ValueError(
            f"Request failed with status code {response.status_code}: {response.text}"
        )

    # Convert to recipe
    response_converted = {camel_to_snake(k): v for k, v in response.json().items()}
    recipe = Recipe(spoonacular_enriched=True, **response_converted)
    return recipe


if __name__ == "__main__":
    recipe = extract_recipe(
        "https://evseats.com/cuban-chicken-black-bean-rice-bowls/",
    )
    print(recipe)
