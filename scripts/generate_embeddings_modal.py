import logging
import os

import modal
import torch
from dotenv import load_dotenv

from chao_fan.pipelines.generate_embedings import update_embeddings

load_dotenv()
timeout = os.environ.get("INGREDIENT_EMBEDDING_GENERATION_TIMEOUT_SECONDS")
modal_timeout = int(timeout) + 20

stub = modal.Stub("chao-fan-generate-embeddings")

image = modal.Image.debian_slim(python_version="3.11").poetry_install_from_file(
    "pyproject.toml"
)


@stub.function(
    image=image, gpu="any", secrets=[modal.Secret.from_dotenv()], timeout=modal_timeout
)
def modal_update_embeddings():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    print("CUDA available: ", torch.cuda.is_available())
    update_embeddings()
