from sqlmodel import SQLModel

from .db import engine


def setup_db():
    SQLModel.metadata.create_all(engine)


def reset_db():
    check = input(
        "This will delete all data in the database. Are you sure you want to continue? (yes/no)"
    )
    if check != "yes":
        print("Aborting")
        return
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
