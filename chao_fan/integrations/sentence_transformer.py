"""
Integration with SQLite vector search
"""

import numpy as np
from sentence_transformers import SentenceTransformer


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
