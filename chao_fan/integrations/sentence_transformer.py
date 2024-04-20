"""
Integration with SQLite vector search
"""

import logging
from typing import List

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


def get_model(device: str | None = None):
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device=device)
    return model


def generate_embeddings(
    sentences,
    model,
    **kwargs,
) -> List[List[float]]:
    """Generate embeddings for a list of ingredients

    Parameters
    ----------
    sentences : List[str]
        The sentences to embed


    """
    embeddings: np.ndarray = model.encode(sentences, **kwargs)
    embeddings = embeddings.astype(np.float32).tolist()
    return embeddings
