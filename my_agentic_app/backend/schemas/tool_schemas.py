"""
Centralized Pydantic schemas for data validation across all AI Agent tools.
Keeping schemas here ensures separation of concerns and reusability.
"""
from pydantic import BaseModel, Field

# ==========================================
# Database Tool Schemas
# ==========================================

class CheckInventoryInput(BaseModel):
    """Schema for checking inventory stock."""
    sku: str = Field(
        ..., 
        description="The strictly formatted Stock Keeping Unit identifier to search for (e.g., 'SKU-001'). You can also correct the format of incoming SKU ID."
    )

class UpdateInventoryInput(BaseModel):
    """Schema for updating inventory quantity."""
    sku: str = Field(
        ..., 
        description="The specific SKU to update."
    )
    quantity_change: int = Field(
        ..., 
        description="The integer amount to add or subtract. Use positive numbers to add stock, and negative numbers to reduce stock."
    )

class AddProductInput(BaseModel):
    """Schema for registering a completely new product."""
    sku: str = Field(..., description="The new unique identifier for the product.")
    product_name: str = Field(..., description="The descriptive name of the product.")
    price: float = Field(..., description="The unit price of the product in THB.")
    initial_quantity: int = Field(default=0, description="The starting stock quantity. Defaults to 0 if not specified.")

# ==========================================
# Parser Tool Schemas
# ==========================================

class ExtractSlipDataInput(BaseModel):
    """Schema for extracting text from a LINE image message."""
    message_id: str = Field(
        ..., 
        description="The strictly required LINE message ID referencing the uploaded image."
    )
    line_user_id: str = Field(
        ..., 
        description="The strictly required LINE user ID of the sender for database tracking."
    )