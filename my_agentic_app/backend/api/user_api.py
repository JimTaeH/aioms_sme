"""
API Router for handling user-related operations from front-end applications.
"""
from fastapi import APIRouter, HTTPException, status
from backend.schemas.api_schemas import UserRegistrationRequest
from backend.services.user_service import UserService

router = APIRouter()

@router.post("/register", status_code=status.HTTP_200_OK)
async def register_user(request: UserRegistrationRequest):
    """
    Endpoint for the LIFF App to submit user registration data.
    """
    # model_dump() จะแปลง Pydantic Model กลับเป็น Dictionary ธรรมดาเพื่อส่งให้ Service
    success = await UserService.register_liff_user(request.model_dump())
    
    if success:
        return {
            "status": "success", 
            "message": "User registered successfully.",
            "data": {"line_user_id": request.line_user_id}
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to register user. Please try again later."
        )