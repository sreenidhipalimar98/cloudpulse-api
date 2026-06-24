from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import json
import os

Base = declarative_base()


def _get_db_url():
    """Build database URL from settings or DATABASE_CREDENTIALS secret."""
    # In ECS, credentials come from Secrets Manager as a JSON string
    creds_json = os.environ.get("DATABASE_CREDENTIALS")
    if creds_json:
        try:
            creds = json.loads(creds_json)
            return f"postgresql://{creds['username']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['dbname']}"
        except (json.JSONDecodeError, KeyError):
            pass

    # Fallback to individual env vars (local dev)
    return f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"


def get_engine():
    return create_engine(_get_db_url(), pool_pre_ping=True, pool_size=5)


def get_session_factory():
    engine = get_engine()
    return sessionmaker(bind=engine)


def get_db():
    """FastAPI dependency for database sessions."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
