from .db import SQLModel, engine


def setup_db():
    SQLModel.metadata.create_all(engine)


def reset_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
