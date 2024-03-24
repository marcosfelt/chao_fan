import os

from sqlmodel import Session, SQLModel, create_engine, text

from . import models  # Needed to make sure the tables are created

postgres_url = os.environ.get("POSTGRES_URL")
engine = create_engine(postgres_url)
