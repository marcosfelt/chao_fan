"""
Integration with SQLite vector search
"""

from sqlite3 import Connection
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer, util

from chao_fan.models import IngredientNutrition, IngredientPrice


def get_model(device: str = "cpu"):
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device=device)
    return model


def generate_embeddings(
    sentences,
    model,
    **kwargs,
) -> np.ndarray:
    """Generate embeddings for a list of ingredients

    Parameters
    ----------
    sentences : List[str]
        The sentences to embed


    """

    embeddings = model.encode(sentences, **kwargs)
    return embeddings
