# backend/app/db/session.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


# Engine — the actual connection to PostgreSQL
# pool_pre_ping=True means it checks if connection is alive before using it
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)

# SessionLocal — a factory for DB sessions
# autocommit=False → you manually commit changes (safer)
# autoflush=False  → changes aren't sent to DB until you explicitly flush/commit
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base — all models will inherit from this
# SQLAlchemy uses this to track which classes are DB tables
Base = declarative_base()

