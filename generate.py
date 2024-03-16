from typing import List, Optional
import outlines
from outlines import models, generate
from dotenv import load_dotenv
from pydantic import BaseModel
from tqdm import trange, tqdm
import json

CUISINES_NAMES = ["Japanese", "Chinese", "Korean", "Soul food", "Italian", "Mexican"]


class Example(BaseModel):
    question: str
    answer: str


class MealPlanTheme(BaseModel):
    name: str
    cuisine: Optional[str] = None


class Cuisine(BaseModel):
    name: str
    ingredients: str


@outlines.prompt
def meal_plan_theme_prompt(cuisine: str):
    """
    Create a theme for a {{ cuisine }} meal plan.
    """


def create_theme_example(theme: str, cuisine: str):
    question = meal_plan_theme_prompt(cuisine)
    answer = json.dumps({"theme": theme})
    return Example(question=question, answer=answer)


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
            "You are a friendly assistant that outputs answers in JSON.",
            examples,
            cuisine_ingredients_prompt(cuisine),
        )
        c: Cuisine = generator(prompt)
        cuisine_ingredients.append(c)

    return cuisine_ingredients


def generate_themes():
    model = models.llamacpp("./phi-2.Q4_K_M.gguf", verbose=False)

    cuisines = generate_cuisine_ingredients(model, CUISINES_NAMES)
    with open("cuisines.json", "w") as f:
        json.dump([cuisine.model_dump() for cuisine in cuisines], f, indent=2)


if __name__ == "__main__":
    generate_themes()
