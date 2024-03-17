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


class RecipeMealPlanMealLink(SQLModel, table=True):
    recipe_id: Optional[int] = Field(
        default=None, foreign_key="recipe.id", primary_key=True
    )
    meal_plan_meal_id: Optional[int] = Field(
        default=None, foreign_key="mealplanmeal.id", primary_key=True
    )


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
    source_url: HttpUrl = Field(sa_type=AutoString, nullable=True)
    image: HttpUrl = Field(sa_type=AutoString, nullable=True)
    image_type: Optional[str] = None
    summary: Optional[str] = None
    spoonacular_score: Optional[int] = None

    instructions: List["Instruction"] = Relationship(back_populates="Recipe")
    cuisines: List["Cuisine"] = Relationship(back_populates="Recipe")
    ingredients: List["Ingredient"] = Relationship(back_populates="Recipe")
    meal_plan_meals: List["MealPlanMeal"] = Relationship(
        back_populates="Recipe", link_model=RecipeMealPlanMealLink
    )


class Instruction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    recipe_id: Optional[int] = Field(default=None, foreign_key="recipe.id")
    step_number: int
    step: str


class RecipeIngredientLink(SQLModel, table=True):
    recipe_id: Optional[int] = Field(
        default=None, foreign_key="recipe.id", primary_key=True
    )
    ingredient_id: Optional[int] = Field(
        default=None, foreign_key="ingredient.id", primary_key=True
    )


class Ingredient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    recipes: List[Recipe] = Relationship(back_populates="Ingredient")


class RecipeCuisineLink(SQLModel, table=True):
    recipe_id: Optional[int] = Field(
        default=None, foreign_key="recipe.id", primary_key=True
    )
    cuisine_id: Optional[int] = Field(
        default=None, foreign_key="cuisine.id", primary_key=True
    )


class Cuisine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    recipes: List[Recipe] = Relationship(back_populates="Cuisine")


class MealPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    start_date: AwareDatetime = Field(default=None, sa_type=DateTime(timezone=True))
    end_date: AwareDatetime = Field(default=None, sa_type=DateTime(timezone=True))
    theme: Optional[str] = None
    active: bool = False
    meals: List["MealPlanMeal"] = Relationship(back_populates="MealPlan")


class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"


class MealPlanMeal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meal_time: AwareDatetime = Field(default=None, sa_type=DateTime(timezone=True))
    meal_type: Optional[MealType] = None
    recipes: List[Recipe] = Relationship(
        back_populates="MealPlanMeal", link_model=RecipeMealPlanMealLink
    )
    meal_plan_id: Optional[int] = Field(default=None, foreign_key="mealplan.id")
    meal_plan: Optional[MealPlan] = Relationship(back_populates="MealPlanMeal")
