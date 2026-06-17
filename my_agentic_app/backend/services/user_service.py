"""
Service module for managing user data and automated registrations.
"""
import logging
from sqlalchemy import select
from backend.core.database import AsyncSessionLocal
from backend.models.user import User
from typing import Optional

logger = logging.getLogger(__name__)

class UserService:
    """
    Handles database operations related to system users and LINE clients.
    """
    
    @staticmethod
    async def get_user_profile(line_user_id: str) -> Optional[User]:
        """
        Retrieves the complete user profile from the database using their LINE ID.
        Useful for checking user roles (RBAC) and customer grades before executing agent tools.
        
        Args:
            line_user_id (str): The unique identifier provided by LINE.
            
        Returns:
            Optional[User]: The user model instance if found, None otherwise.
        """
        async with AsyncSessionLocal() as db:
            try:
                query = select(User).where(User.line_user_id == line_user_id)
                result = await db.execute(query)
                return result.scalars().first()
            except Exception as e:
                logger.error(f"Failed to fetch user profile for {line_user_id}: {str(e)}")
                return None

    @staticmethod
    async def register_user_if_not_exists(line_user_id: str) -> None:
        """
        Checks if a user with the given LINE ID exists in the database.
        If not, automatically creates and saves a new user record.
        
        Args:
            line_user_id (str): The unique identifier provided by the LINE platform.
        """
        async with AsyncSessionLocal() as db:
            try:
                # Query the database to check for existing user
                query = select(User).where(User.line_user_id == line_user_id)
                result = await db.execute(query)
                existing_user = result.scalars().first()
                
                if not existing_user:
                    # Instantiate and save a new user
                    new_user = User(line_user_id=line_user_id, role="customer", is_active=True)
                    db.add(new_user)
                    await db.commit()
                    logger.info(f"Successfully auto-registered new user: {line_user_id}")
                else:
                    logger.debug(f"User {line_user_id} already exists. Skipping registration.")
                    
            except Exception as e:
                await db.rollback()
                logger.error(f"Database error during user auto-registration: {str(e)}")