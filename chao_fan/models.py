from typing import List, Optional
from pydantic import HttpUrl
from sqlmodel import Field, SQLModel, Session, create_engine, AutoString, select


class Recipe(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    spoonacular_enriched: bool = False
    title: Optional[str] = None
    vegetarian: Optional[bool] = None
    vegan: Optional[bool] = None
    gluten_free: Optional[bool] = None
    dairy_free: Optional[bool] = None
    very_healthy: Optional[bool] = None
    cheap: Optional[bool] = None
    very_popular: Optional[bool] = None
    sustainable: Optional[bool] = None
    low_fodmap: Optional[bool] = None
    weight_watcher_smart_points: Optional[int] = None
    gaps: Optional[str] = None
    preparation_minutes: Optional[int] = None
    cooking_minutes: Optional[int] = None
    aggregate_likes: Optional[int] = None
    health_score: Optional[int] = None
    credits_text: Optional[str] = None
    source_name: Optional[str] = None
    price_per_serving: Optional[float] = None
    # extended_ingredients: Optional[List[dict]] = None
    ready_in_minutes: Optional[int] = None
    servings: Optional[int] = None
    source_url: HttpUrl = Field(sa_type=AutoString, nullable=True)
    image: HttpUrl = Field(sa_type=AutoString, nullable=True)
    image_type: Optional[str] = None
    summary: Optional[str] = None
    # cuisines: Optional[List[str]] = None
    # dish_types: Optional[List[str]] = None
    # diets: Optional[List[str]] = None
    # occasions: Optional[List[str]] = None
    instructions: Optional[str] = None
    # analyzed_instructions: Optional[List[dict]] = None
    spoonacular_score: Optional[int] = None


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


def add_recipes(engine):
    import json

    with open("data/recipes.json", "r") as file:
        recipe_dicts = json.load(file)
    session = Session(engine)
    for recipe_dict in recipe_dicts:
        recipe_camel_case = {camel_to_snake(k): v for k, v in recipe_dict.items()}
        del recipe_camel_case["id"]
        recipe = Recipe(**recipe_camel_case)
        session.add(recipe)
    session.commit()
    session.close()


def get_recipe(engine, url: str):
    with Session(engine) as session:
        statement = select(Recipe).where(Recipe.source_url == url)
        results = session.exec(statement)
        for recipe in results:
            print(recipe)
