from sqlalchemy import create_engine

from backend.app.core.config import settings



engine = create_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://"),
    pool_pre_ping = True,
) 