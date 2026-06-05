# backend/alembic/env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# Make sure alembic can find your app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.session import Base
from app.models import user 
from app.models import application      # import all models so Alembic can see them

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata    # tells Alembic which tables to track


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()