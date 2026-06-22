"""
Database interaction tools for the AI agent.
These tools are exposed to the LLM via function calling to perform CRUD operations.
"""
from langchain_core.tools import tool
from sqlalchemy import select
from backend.core.database import AsyncSessionLocal
from backend.models.inventory import InventoryItem

from backend.schemas.tool_schemas import (
    CheckInventoryInput,
    UpdateInventoryInput,
    AddProductInput,
    CheckUserProfileInput
)

from backend.models.user import User

import logging

logger = logging.getLogger(__name__)

@tool(args_schema=CheckInventoryInput)
async def check_inventory_stock(sku: str) -> str:
    """
    Queries the database to check the current stock level and price of a specific product using its SKU.
    
    Args:
        sku (str): The unique Stock Keeping Unit identifier for the product.
        
    Returns:
        str: A formatted string containing the product details, or an error message if not found.
    """
    # Use the async session factory to create an isolated session for this tool call
    async with AsyncSessionLocal() as db:
        try:
            # Query the database asynchronously
            query = select(InventoryItem).where(InventoryItem.sku == sku)
            result = await db.execute(query)
            item = result.scalars().first()
            
            if item:
                status = "Available" if item.is_available else "Out of Stock"
                return f"Product: {item.product_name} | Stock: {item.quantity} units | Price: ฿{item.price:,.2f} | Status: {status}"
            else:
                return f"Item with SKU '{sku}' not found in the inventory system."
        except Exception as e:
            return f"Error accessing database: {str(e)}"

@tool(args_schema=UpdateInventoryInput)
async def update_inventory_quantity(sku: str, quantity_change: int) -> str:
    """
    Updates the stock quantity of a product in the inventory.
    
    Args:
        sku (str): The unique Stock Keeping Unit identifier.
        quantity_change (int): The amount to change. Use positive integers to add stock (e.g., 10) 
                               and negative integers to reduce stock (e.g., -5).
                               
    Returns:
        str: A status message indicating success or failure.
    """
    async with AsyncSessionLocal() as db:
        try:
            query = select(InventoryItem).where(InventoryItem.sku == sku)
            result = await db.execute(query)
            item = result.scalars().first()
            
            if not item:
                return f"Error: SKU '{sku}' not found. Cannot update stock."
            
            # Update the quantity
            item.quantity += quantity_change
            
            # Automatically update availability status based on new quantity
            item.is_available = item.quantity > 0
            
            await db.commit()
            logger.info(f"Successful Update Inventory Quantity")
            return f"Success: Stock for '{item.product_name}' (SKU: {sku}) updated by {quantity_change}. New total quantity is {item.quantity}."
        except Exception as e:
            await db.rollback()
            return f"Error updating database: {str(e)}"

@tool(args_schema=AddProductInput)
async def add_new_product(sku: str, product_name: str, price: float, initial_quantity: int = 0) -> str:
    """
    Registers a new product into the inventory system.
    
    Args:
        sku (str): The new unique Stock Keeping Unit identifier.
        product_name (str): The name of the product.
        price (float): The price of the product.
        initial_quantity (int): The starting stock quantity (defaults to 0).
        
    Returns:
        str: A status message indicating success or failure.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Check if SKU already exists
            query = select(InventoryItem).where(InventoryItem.sku == sku)
            result = await db.execute(query)
            if result.scalars().first():
                return f"Error: Product with SKU '{sku}' already exists."

            # Create new item
            new_item = InventoryItem(
                sku=sku,
                product_name=product_name,
                price=price,
                quantity=initial_quantity,
                is_available=initial_quantity > 0
            )
            db.add(new_item)
            await db.commit()
            logger.info(f"Successful Add New Product")
            return f"Success: Product '{product_name}' (SKU: {sku}) added with initial stock of {initial_quantity}."
        except Exception as e:
            await db.rollback()
            return f"Error adding new product: {str(e)}"

@tool(args_schema=CheckUserProfileInput)
async def check_user_profile(line_user_id: str) -> str:
    """
    Queries the database to retrieve the full profile, role, and registration status of a specific user.
    """
    async with AsyncSessionLocal() as db:
        try:
            query = select(User).where(User.line_user_id == line_user_id)
            result = await db.execute(query)
            user = result.scalars().first()
            
            if user:
                return (
                    f"User Profile Found:\n"
                    f"- LINE ID: {user.line_user_id}\n"
                    f"- Role: {user.role}\n"
                    f"- Registered: {'Yes' if user.is_registered else 'No'}\n"
                    f"- Full Name: {user.full_name or 'N/A'}\n"
                    f"- Company: {user.company_name or 'N/A'}\n"
                    f"- Customer Grade: {user.customer_grade}\n"
                    f"- Phone: {user.phone_number or 'N/A'}\n"
                    f"- Address: {user.address or 'N/A'}"
                )
            else:
                return f"No profile found in the database for LINE ID: {line_user_id}."
        except Exception as e:
            logger.error(f"Database error during user profile check: {str(e)}")
            return f"Error: Unable to query database for user profile."
