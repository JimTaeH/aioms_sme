"""
Service module for managing document tracking and OCR records.
"""
import logging
from sqlalchemy import select
from backend.core.database import AsyncSessionLocal
from backend.models.document import Document
from backend.models.user import User

logger = logging.getLogger(__name__)

class DocumentService:
    """
    Handles database operations related to tracking user documents and slips.
    """
    
    @staticmethod
    async def save_ocr_document(line_user_id: str, message_id: str, extracted_data: dict, status: str = "completed") -> bool:
        """
        Saves the parsed OCR document to the database, linked to the specific user.
        
        Args:
            line_user_id (str): The LINE User ID to link the document to.
            message_id (str): The original LINE message ID (used as pseudo file_path).
            extracted_data (dict): The raw JSON data extracted from Typhoon-OCR.
            status (str): The processing status ('completed' or 'failed').
            
        Returns:
            bool: True if successful, False otherwise.
        """
        async with AsyncSessionLocal() as db:
            try:
                # 1. Fetch the internal user ID using the LINE User ID
                query = select(User).where(User.line_user_id == line_user_id)
                result = await db.execute(query)
                user = result.scalars().first()
                
                if not user:
                    logger.error(f"Cannot save document: User {line_user_id} not found in database.")
                    return False

                # 2. Create a new Document record
                new_doc = Document(
                    user_id=user.id,
                    doc_type="slip",
                    file_path=f"line_msg_{message_id}", # Temporarily use message_id as reference
                    status=status,
                    extracted_data=extracted_data
                )
                
                # 3. Save to database
                db.add(new_doc)
                await db.commit()
                logger.info(f"Successfully saved OCR document record for user {user.id}")
                return True
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Database error while saving document: {str(e)}")
                return False