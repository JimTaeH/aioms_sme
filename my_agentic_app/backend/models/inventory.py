"""
Inventory model representing products and stock levels.
"""
from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from backend.models.base import Base

class InventoryItem(Base):
    """
    Inventory entity mapping to the 'inventoryitems' table.
    Used by the Inventory Agent to manage stock.
    """
    __tablename__ = "inventory_items"

    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    product_name: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    is_available: Mapped[bool] = mapped_column(default=True)

    def __repr__(self) -> str:
        return f"<InventoryItem(sku='{self.sku}', product_name='{self.product_name}', qty={self.quantity})>"
