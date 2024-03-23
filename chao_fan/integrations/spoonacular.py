from typing import Any, Dict, List, Optional
import requests
import os
from dotenv import load_dotenv
from chao_fan.models import Cuisine, Recipe, Instruction, Ingredient, RecipeIngredient
from pydantic import HttpUrl


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


def deserialize_instructions(
    instructions: List[Dict[str, int | str]]
) -> List[Instruction]:
    return [
        Instruction(
            step_number=instruction_dict["number"], step=instruction_dict["step"]
        )
        for instruction_dict in instructions
    ]


def deserialize_ingredients(
    ingredient_dicts: List[Dict[str, Any]]
) -> List[RecipeIngredient]:
    ingredients = []
    for ingredient_dict in ingredient_dicts:
        amount, unit = None, None
        if ingredient_dict.get("measures") and ingredient_dict["measures"].get(
            "metric"
        ):
            amount = ingredient_dict["measures"]["metric"]["amount"]
            unit = ingredient_dict["measures"]["metric"]["unitShort"]

        ingredients.append(
            RecipeIngredient(
                amount=amount,
                unit=unit,
                ingredient=Ingredient(
                    name=ingredient_dict["name"],
                    spoonacular_id=ingredient_dict["id"],
                    aisle=ingredient_dict.get("aisle"),
                ),
            )
        )
    return ingredients


def deserialize_cuisines(cuisine_list: List[str]) -> List[Cuisine]:
    return [Cuisine(name=cuisine) for cuisine in cuisine_list]


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
    del response_converted["id"]
    if "instructions" in response_converted:
        del response_converted["instructions"]
    cuisines_list = response_converted.get("cuisines")
    if "cuisines" in response_converted:
        del response_converted["cuisines"]
    recipe = Recipe(spoonacular_enriched=True, **response_converted)
    if cuisines_list:
        cuisines = deserialize_cuisines(cuisines_list)
        if len(cuisines) > 0:
            recipe.cuisines = cuisines
    if response_converted.get("analyzed_instructions"):
        instructions = deserialize_instructions(
            response_converted["analyzed_instructions"][0]["steps"]
        )
        if len(instructions) > 0:
            recipe.instructions = instructions
    if response_converted.get("extended_ingredients"):
        ingredients = deserialize_ingredients(
            response_converted["extended_ingredients"]
        )
        if len(ingredients) > 0:
            recipe.recipe_ingredients = ingredients
    return recipe


if __name__ == "__main__":
    recipe = extract_recipe(
        "https://evseats.com/cuban-chicken-black-bean-rice-bowls/",
    )
    print(recipe)
