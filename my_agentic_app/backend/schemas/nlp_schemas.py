"""
Pydantic schemas for the Core NLP & Entity Extraction Engine.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

IntentType = Literal[
    "inquiry_general",
    "check_stock",
    "place_order",
    "upload_slip",
    "other"
]

class ClassifiedIntent(BaseModel):
    """ผลลัพธ์จากการจำแนกจุดประสงค์ของข้อความ"""
    intent: IntentType = Field(..., description="หมวดหมู่หลักของข้อความ")
    confidence: float = Field(..., description="ระดับความมั่นใจของ AI (0.0 ถึง 1.0)")
    reasoning: str = Field(..., description="เหตุผลสั้นๆ ว่าทำไมถึงจัดอยู่ในหมวดหมู่นี้")

class OrderItemEntity(BaseModel):
    """ข้อมูลสินค้าแต่ละชิ้นที่สกัดได้จากคำพูด"""
    item_name: str = Field(..., description="ชื่อสินค้าที่ลูกค้าเรียก (ยังไม่ใช่ SKU)")
    quantity: int = Field(..., description="จำนวนที่เป็นตัวเลขเท่านั้น")
    unit: Optional[str] = Field(None, description="หน่วยนับ เช่น แผง, กล่อง, กิโล, ชิ้น, ถุง")
    special_request: Optional[str] = Field(None, description="คำขอพิเศษ เช่น ไม่หวาน, ขอใบกำกับภาษี")

class ExtractedOrder(BaseModel):
    """ก้อนออเดอร์รวมที่สกัดได้จาก 1 ประโยค"""
    items: List[OrderItemEntity] = Field(..., description="รายการสินค้าทั้งหมดที่สกัดได้")
    delivery_address: Optional[str] = Field(None, description="ที่อยู่จัดส่ง (ถ้าลูกค้าพิมพ์มาในประโยค)")
