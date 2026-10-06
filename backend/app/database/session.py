from sqlalchemy.orm import Session

from backend.app.database.connection import engine


def get_db() -> Session:
    return Session(engine)