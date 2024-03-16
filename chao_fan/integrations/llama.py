"""Generate meal plan themes for different cuisines using llama"""

from typing import List, Optional
import outlines
from outlines import models, generate
from pydantic import BaseModel, ValidationError
from tqdm import trange, tqdm
import json
import logging
from huggingface_hub import hf_hub_download

CUISINES_NAMES = [
    "Japanese",
    "Chinese",
    "Korean",
    "Soul food",
    "Italian",
    "Mexican",
    "West African",
    "Cuban",
]
logger = logging.getLogger(__name__)


def get_model(model_name: str = "phi-2.Q4_K_M.gguf"):
    """Get a phi-2 model from Hugging Face Hub

    Parameters
    ----------
    model_name : str, optional
        The name of the model to download, by default "phi-2.Q4_K_M.gguf"

    Notes
    -----
    Model is cached after first download

    """
    model_path = hf_hub_download(repo_id="TheBloke/phi-2-GGUF", filename=model_name)
    return models.llamacpp(model_path, verbose=False)


class Example(BaseModel):
    question: str
    answer: str


class Cuisine(BaseModel):
    name: str
    ingredients: str


class MealPlanTheme(BaseModel):
    name: str
    cuisine: Cuisine


@outlines.prompt
def json_prompt(adjective: str = "friendly"):
    """
    "You are a {{ adjective }} assistant that outputs answers in JSON."
    """


@outlines.prompt
def cuisine_ingredients_prompt(cuisine: str):
    """
    List ingredients commonly used in {{ cuisine }} cuisine.
    """


def create_ingredients_example(cuisine: str, ingredients: List[str]):
    question = cuisine_ingredients_prompt(cuisine)
    answer = json.dumps({"ingredients": ", ".join(ingredients)})
    return Example(question=question, answer=answer)


@outlines.prompt
def meal_plan_theme_prompt(cuisine: Cuisine, adjective: str = "fun"):
    """
    {{ cuisine.name }} food uses the following ingredients: {{ cuisine.ingredients }}. Create a theme for a {{ adjective }} {{ cuisine.name }} meal plan.
    """


def create_theme_example(theme: str, cuisine: Cuisine):
    question = meal_plan_theme_prompt(cuisine)
    answer = json.dumps({"theme": theme})
    return Example(question=question, answer=answer)


@outlines.prompt
def few_shots(instructions: str, examples: List[Example], question: str):
    """{{ instructions }}

    Examples
    --------

    {% for example in examples %}
    Q: {{ example.question }}
    A: {{ example.answer }}

    {% endfor %}
    Question
    --------

    Q: {{ question }}
    A:
    """


def generate_cuisine_ingredients(model, cuisines: List[str]) -> List[Cuisine]:
    """
    Generate ingredients for a list of cuisines.

    Parameters
    ----------
    model : outlines.models.
        The model to use for generation.
    """
    examples = [
        create_ingredients_example(
            "Japanese", ["rice", "soy sauce", "seaweed", "salmon"]
        ),
        create_ingredients_example("Chinese", ["soy sauce", "rice", "ginger"]),
        create_ingredients_example("Mediterannean", ["olive oil", "tomatoes", "feta"]),
    ]
    generator = generate.json(model, Cuisine)
    cuisine_ingredients = []
    for cuisine in tqdm(cuisines):
        prompt = few_shots(
            json_prompt(adjective="friendly"),
            examples,
            cuisine_ingredients_prompt(cuisine),
        )
        logger.debug(prompt)
        try:
            c: Cuisine = generator(prompt)
            cuisine_ingredients.append(c)
        except ValidationError as e:
            logger.error(e)

    return cuisine_ingredients


class SimpleTheme(BaseModel):
    theme: str


def generate_themes(model, cuisines: List[Cuisine]) -> List[MealPlanTheme]:
    """
    Generate ingredients for a list of cuisines.

    Parameters
    ----------
    model : outlines.models.
        The model to use for generation.
    """
    examples = [
        create_theme_example(
            "Total Tacos",
            Cuisine(name="Mexican", ingredients="tortillas, beef, cheese"),
        ),
        create_theme_example(
            "Fried rice rules",
            Cuisine(name="Chinese", ingredients="soy sauce, rice, ginger"),
        ),
        create_theme_example(
            "Fresh Mediterannean salads",
            Cuisine(name="Mediterannean", ingredients="olive oil, tomatoes, feta"),
        ),
    ]

    generator = generate.json(model, SimpleTheme)
    themes = []
    for cuisine in tqdm(cuisines):
        prompt = few_shots(
            json_prompt(adjective="friendly"),
            examples,
            meal_plan_theme_prompt(cuisine),
        )
        logger.debug(prompt)
        try:
            theme_name: SimpleTheme = generator(prompt)
            theme = MealPlanTheme(name=theme_name.theme, cuisine=cuisine)
            themes.append(theme)
        except ValidationError as e:
            logger.error(e)
    return themes


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    get_model()
