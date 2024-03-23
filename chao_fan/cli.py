from .db import engine, SQLModel


def setup_db():
    SQLModel.metadata.create_all(engine)
