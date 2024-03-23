from typing import List, Literal, Optional
from pydantic import HttpUrl, AwareDatetime
from sqlmodel import (
    Field,
    Relationship,
    SQLModel,
    AutoString,
)
from sqlalchemy import DateTime
from datetime import datetime
from enum import Enum

### Link Models ###
# These have to be first so they can be referenced by the other models


class RecipeMealLink(SQLModel, table=True):
    recipe_id: Optional[int] = Field(
        default=None, foreign_key="recipe.id", primary_key=True
    )
    meal_id: Optional[int] = Field(
        default=None, foreign_key="meal.id", primary_key=True
    )


class RecipeCuisineLink(SQLModel, table=True):
    recipe_id: Optional[int] = Field(
        default=None, foreign_key="recipe.id", primary_key=True
    )
    cuisine_id: Optional[int] = Field(
        default=None, foreign_key="cuisine.id", primary_key=True
    )


### Main Models ###
# These are the main models that will be used in the application


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
    ready_in_minutes: Optional[int] = None
    servings: Optional[int] = None
    source_url: Optional[str] = None
    image: Optional[str] = None
    image_type: Optional[str] = None
    summary: Optional[str] = None
    spoonacular_score: Optional[float] = None

    instructions: List["Instruction"] = Relationship(back_populates="recipe")
    cuisines: List["Cuisine"] = Relationship(
        back_populates="recipes", link_model=RecipeCuisineLink
    )
    recipe_ingredients: List["RecipeIngredient"] = Relationship(back_populates="recipe")
    meals: List["Meal"] = Relationship(
        back_populates="recipes", link_model=RecipeMealLink
    )


class Instruction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    step_number: Optional[int] = None
    step: Optional[str] = None
    recipe_id: Optional[int] = Field(default=None, foreign_key="recipe.id")
    recipe: Optional[Recipe] = Relationship(back_populates="instructions")


class Ingredient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    spoonacular_id: Optional[str] = None
    aisle: Optional[str] = None
    recipe_ingredients: List["RecipeIngredient"] = Relationship(
        back_populates="ingredient"
    )


class RecipeIngredient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: Optional[str] = None
    unit: Optional[str] = None
    ingredient_id: Optional[int] = Field(default=None, foreign_key="ingredient.id")
    ingredient: Optional[Ingredient] = Relationship(back_populates="recipe_ingredients")
    recipe_id: Optional[int] = Field(default=None, foreign_key="recipe.id")
    recipe: Optional[Recipe] = Relationship(back_populates="recipe_ingredients")


class Cuisine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    recipes: List[Recipe] = Relationship(
        back_populates="cuisines", link_model=RecipeCuisineLink
    )


class MealPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    start_date: AwareDatetime = Field(default=None, sa_type=DateTime(timezone=True))
    end_date: AwareDatetime = Field(default=None, sa_type=DateTime(timezone=True))
    theme: Optional[str] = None
    active: bool = False
    meals: List["Meal"] = Relationship(back_populates="meal_plan")


class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"


class Meal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meal_time: AwareDatetime = Field(default=None, sa_type=DateTime(timezone=True))
    meal_type: Optional[MealType] = None
    recipes: List[Recipe] = Relationship(
        back_populates="meals", link_model=RecipeMealLink
    )
    meal_plan_id: Optional[int] = Field(default=None, foreign_key="mealplan.id")
    meal_plan: Optional[MealPlan] = Relationship(back_populates="meals")
