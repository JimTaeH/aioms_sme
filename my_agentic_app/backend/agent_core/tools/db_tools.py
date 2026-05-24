"""
Database interaction tools for the AI agent.
These tools are exposed to the LLM via function calling.
"""
from langchain_core.tools import tool
from sqlalchemy import select
from backend.core.database import AsyncSessionLocal
from backend.models.inventory import InventoryItem

@tool
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