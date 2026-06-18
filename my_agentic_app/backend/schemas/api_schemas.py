"""
Pydantic schemas for REST API endpoints (e.g., LIFF App integration).
"""
from pydantic import BaseModel, Field
from typing import Optional

class UserRegistrationRequest(BaseModel):
    """Schema for receiving user registration data from the LIFF App."""
    line_user_id: str = Field(..., description="The unique LINE User ID.")
    full_name: str = Field(..., description="Customer's full name.")
    phone_number: str = Field(..., description="Customer's contact number.")
    
    # ข้อมูลสำหรับออกใบเสนอราคา/ใบกำกับภาษี (อาจจะกรอกหรือไม่กรอกก็ได้)
    company_name: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None