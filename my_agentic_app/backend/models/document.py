"""
Document model representing uploaded files, slips, or receipts.
"""
from typing import Optional, Any, Dict
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base
from backend.models.user import User

class Document(Base):
    """
    Document entity mapping to the 'documents' table.
    Tracks files uploaded via LINE and parsed data from Typhoon-OCR.
    """
    __tablename__ = "documents"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    doc_type: Mapped[str] = mapped_column(String(50), default="slip") # 'slip', 'invoice', 'other'
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending") # 'pending', 'processing', 'completed', 'failed'
    
    # Store the extracted OCR data directly as a JSON object
    extracted_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Relationship to the User model
    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, doc_type='{self.doc_type}', status='{self.status}')>"
