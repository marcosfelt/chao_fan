import os

from sqlmodel import create_engine

# Needed to make sure the tables are created
from . import models  # noqa: F401

postgres_url = os.environ.get("POSTGRES_URL")
engine = create_engine(postgres_url)
