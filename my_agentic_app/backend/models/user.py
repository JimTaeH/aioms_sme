"""
User model representing system users or LINE application users.
"""
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
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

    # -----------------------------------------------------
    # RBAC & System Access
    # -----------------------------------------------------
    role = Column(String, default="customer", nullable=False) # Options: 'owner', 'admin', 'customer'
    is_registered = Column(Boolean, default=False) # True if user completed the LIFF registration

    # -----------------------------------------------------
    # Customer Profiling (Populated via LIFF App later)
    # -----------------------------------------------------
    full_name = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    customer_grade = Column(String, default="standard") # Options: 'standard', 'vip', 'wholesale'

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<User(id={self.id}, display_name='{self.display_name}')>"
