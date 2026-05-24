"""
User model representing system users or LINE application users.
"""
from typing import Optional
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from backend.models.base import Base

class User(Base):
    """
    User entity mapping to the 'users' table.
    Stores LINE ID and basic profile information.
    """
    __tablename__ = "users"

    line_user_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="customer") # e.g., 'admin', 'customer'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, display_name='{self.display_name}')>"
