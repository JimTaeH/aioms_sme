"""
Script to seed the database with initial mockup data (Owner, Admin, Customers, and Inventory).
Run this script directly from the root directory: python -m backend.seed
"""
import asyncio
import logging
from backend.core.database import AsyncSessionLocal
from backend.models.user import User
from backend.models.inventory import InventoryItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_database():
    """Inserts predefined mockup data into the database if it does not already exist."""
    async with AsyncSessionLocal() as db:
        try:
            # ==========================================
            # 1. Seed Users (RBAC Simulation)
            # ==========================================
            mock_users = [
                User(
                    line_user_id="U_OWNER_MOCKUP", # คุณสามารถเปลี่ยนเป็น LINE ID จริงของคุณได้ทีหลัง
                    role="owner",
                    is_registered=True,
                    full_name="Sahatsawat Sriphol",
                    company_name="AIOMS Tech",
                    phone_number="080-000-0000"
                ),
                User(
                    line_user_id="U_ADMIN_MOCKUP",
                    role="admin",
                    is_registered=True,
                    full_name="คุณแมว แอดมิน",
                ),
                User(
                    line_user_id="U_CUSTOMER_MOCKUP",
                    role="customer",
                    customer_grade="vip",
                    is_registered=True,
                    full_name="Cafe Ama",
                    company_name="บริษัท อาม่า คอฟฟี่ จำกัด",
                    tax_id="0105555555555",
                    address="123 ถ.สุขุมวิท กทม."
                )
            ]
            
            for user in mock_users:
                db.add(user)

            # ==========================================
            # 2. Seed Inventory Items
            # ==========================================
            mock_inventory = [
                InventoryItem(sku="SKU-015", product_name="เมล็ดกาแฟ House Blend 1kg", price=550.0, quantity=100),
                InventoryItem(sku="SKU-016", product_name="ไซรัปวานิลลา 750ml", price=250.0, quantity=50),
                InventoryItem(sku="SKU-017", product_name="แก้วพลาสติก 16oz (100ใบ)", price=120.0, quantity=200),
            ]
            
            for item in mock_inventory:
                db.add(item)

            await db.commit()
            logger.info("Successfully seeded the database with mockup Users and Inventory!")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Data seeding failed (Data might already exist): {str(e)}")

if __name__ == "__main__":
    asyncio.run(seed_database())