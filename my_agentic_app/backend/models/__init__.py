"""
Expose all models for SQLAlchemy and Alembic metadata.
"""
from backend.models.base import Base
from backend.models.user import User
from backend.models.inventory import InventoryItem
from backend.models.document import Document

# This allows Alembic to import `Base.metadata` from a single source
__all__ = ["Base", "User", "InventoryItem", "Document"]
