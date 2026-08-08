import sys
import os
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 1. Add the project root to the Python path to allow importing the 'backend' module.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 2. Import the Base which contains all registered models from __init__.py
from backend.models import Base
from dotenv import load_dotenv

load_dotenv()

# This is the Alembic Config object, providing access to values within the .ini file.
config = context.config

# 3. Hardcode or dynamically load the async database URL (Ensure it matches your database.py)
# Note: For production, you should load this from a .env file instead of hardcoding.
DATABASE_URL = os.getenv("DATABASE_URL")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 4. Set the target metadata for 'autogenerate' support
target_metadata = Base.metadata

# --- The rest of the file remains standard for the async template ---

# เพิ่มฟังก์ชันนี้ไว้ด้านบนๆ ของไฟล์ (ก่อนถึงฟังก์ชัน run_migrations_online)
def include_object(object, name, type_, reflected, compare_to):
    # ให้ Alembic เมินตารางที่ชื่อขึ้นต้นด้วย checkpoint 
    if type_ == "table" and name and name.startswith("checkpoint"):
        return False
    return True

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    """
    Run the actual migration processing.
    """
    context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """
    In this scenario we need to create an Engine and associate a
    connection with the context.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode using the async loop.
    """
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()