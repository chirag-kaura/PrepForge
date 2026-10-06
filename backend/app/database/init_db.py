from backend.app.database.connection import engine
from backend.app.models.question_log import Base

Base.metadata.create_all(bind=engine)