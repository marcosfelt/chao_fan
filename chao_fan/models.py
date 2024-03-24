import os
from enum import Enum
from typing import List, Optional

from pgvector.sqlalchemy import Vector
from pydantic import AwareDatetime
from sqlalchemy import Column, DateTime
from sqlmodel import Field, LargeBinary, Relationship, SQLModel

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

vector_column = lambda: Column(
    Vector(float(os.environ.get("EMBEDDING_DIMENSION", 384)))
)


class Recipe(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    enriched_at: Optional[AwareDatetime] = Field(
        default=None, sa_type=DateTime(timezone=True)
    )
    enrichment_failed_at: Optional[AwareDatetime] = Field(
        default=None, sa_type=DateTime(timezone=True)
    )
    title: Optional[str] = None
    source_name: Optional[str] = None
    price_per_serving: Optional[float] = None
    ready_in_minutes: Optional[int] = None
    servings: Optional[int] = None
    source_url: Optional[str] = None
    image: Optional[str] = None
    image_type: Optional[str] = None
    summary: Optional[str] = None
    instructions: List["Instruction"] = Relationship(back_populates="recipe")
    cuisines: List["Cuisine"] = Relationship(
        back_populates="recipes", link_model=RecipeCuisineLink
    )
    recipe_ingredients: List["RecipeIngredient"] = Relationship(back_populates="recipe")
    meals: List["Meal"] = Relationship(
        back_populates="recipes", link_model=RecipeMealLink
    )
    embedding: List[float] = Field(sa_column=vector_column())


class Instruction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    step_number: Optional[int] = None
    step: Optional[str] = None
    recipe_id: Optional[int] = Field(default=None, foreign_key="recipe.id")
    recipe: Optional[Recipe] = Relationship(back_populates="instructions")


class Ingredient(SQLModel):
    description: str
    embedding: List[float] = Field(sa_column=vector_column())


class IngredientNutrition(Ingredient, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fdc_id: Optional[int] = None
    serving_size: Optional[str] = None
    food_category: Optional[str] = None
    sugarstotalincludingnlea_grams: Optional[float] = None
    fattyacidstotalsaturated_grams: Optional[float] = None
    cholesterol_grams: Optional[float] = None
    vitaminctotalascorbicacid_grams: Optional[float] = None
    vitaminaiu_grams: Optional[float] = None
    sodiumna_grams: Optional[float] = None
    potassium_grams: Optional[float] = None
    ironfe_grams: Optional[float] = None
    calciumca_grams: Optional[float] = None
    fiber_grams: Optional[float] = None
    energy_grams: Optional[float] = None
    carb_grams: Optional[float] = None
    fat_grams: Optional[float] = None
    protein_grams: Optional[float] = None
    recipe_ingredients: List["RecipeIngredient"] = Relationship(
        back_populates="ingredient_nutrition"
    )
    embedding: List[float] = Field(sa_column=vector_column())


class IngredientPrice(Ingredient, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    price_100grams: float
    embedding: List[float] = Field(sa_column=vector_column())


class RecipeIngredient(Ingredient, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: Optional[str] = None
    unit: Optional[str] = None
    full_description: Optional[str] = None
    estimated_price_100grams: Optional[float] = None
    ingredient_nutrition_id: Optional[int] = Field(
        default=None, foreign_key="ingredientnutrition.id"
    )
    ingredient_nutrition: Optional[IngredientNutrition] = Relationship(
        back_populates="recipe_ingredients"
    )
    recipe_id: Optional[int] = Field(default=None, foreign_key="recipe.id")
    recipe: Optional[Recipe] = Relationship(back_populates="recipe_ingredients")
    embedding: List[float] = Field(sa_column=vector_column())


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
