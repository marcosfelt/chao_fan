import json

# from chao_fan.integrations.llama import (
#     get_model,
#     generate_cuisine_ingredients,
#     generate_themes,
#     MealPlanTheme,
# )
import logging
from typing import List

logger = logging.getLogger(__name__)

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


# def generate_meal_plan_themes() -> List[MealPlanTheme]:
#     """Generate meal themes for different cuisines using llama"""
#     # Get Phi-2 model
#     logger.info("Downloading Phi-2 model")
# model = get_model()

# logger.info("Generating cuisine ingredients")
# cuisines = generate_cuisine_ingredients(model, CUISINES_NAMES)

# logger.info("Generating themes")
# themes = generate_themes(model=model, cuisines=cuisines)
# return themes


# def prepare_meal_plan():
#     generate_meal_plan_themes()


# if __name__ == "__main__":
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     )
#     prepare_meal_plan()
