"""
NLP Engine Service for Intent Classification and Entity Extraction.
"""
import logging

from backend.core.llm_factory import LLMFactory
from backend.schemas.nlp_schemas import ClassifiedIntent, ExtractedOrder

# 1. เพิ่มการ Import PydanticOutputParser
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class NLPEngineService:
    _llm = LLMFactory.create_llm(
        provider="typhoon", 
        model_name="typhoon-v2.5-30b-a3b-instruct", 
        temperature=0.0
    )

    @classmethod
    async def classify_intent(cls, user_text: str) -> ClassifiedIntent:
        """แยกแยะจุดประสงค์ของข้อความ"""
        
        # 2. สร้าง Parser เพื่อบังคับและตรวจสอบ JSON
        parser = PydanticOutputParser(pydantic_object=ClassifiedIntent)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """คุณคือ AI คัดกรองจุดประสงค์ (Intent Classifier) ประจำระบบจัดการธุรกิจ SME
            จงอ่านข้อความของลูกค้าและระบุ Intent ให้ถูกต้องที่สุดตามเงื่อนไขนี้:
            
            - 'check_stock' : ถามว่ามีของไหม, เหลือเท่าไหร่, ราคาเท่าไหร่
            - 'place_order' : ระบุชัดเจนว่าต้องการ "เอา/สั่ง/ซื้อ/รับ" สินค้าพร้อมบอกจำนวน
            - 'inquiry_general' : คำถามทั่วไปเกี่ยวกับร้าน เช่น เปิดกี่โมง, อยู่ที่ไหน
            - 'upload_slip' : มีการพูดถึงการโอนเงินหรือส่งหลักฐาน
            - 'other' : คุยเล่นนอกเรื่อง, คำทักทาย, หรือบ่นว่าใช้งานไม่ได้
            
            🚨 คำสั่งบังคับ: คุณต้องตอบกลับมาเป็นรูปแบบ JSON เท่านั้น ห้ามมีข้อความอื่นปน
            {format_instructions}
            """),
            ("human", "{text}")
        ])
        
        # 3. ต่อ Chain โดยใช้ prompt | llm | parser แทน
        chain = prompt | cls._llm | parser
        
        # 4. โยน format_instructions เข้าไปตอนรัน
        return await chain.ainvoke({
            "text": user_text, 
            "format_instructions": parser.get_format_instructions()
        })

    @classmethod
    async def extract_order_entities(cls, user_text: str) -> ExtractedOrder:
        """สกัดชื่อสินค้า จำนวน และหน่วย ออกมาจากประโยคพูดคุย"""
        
        parser = PydanticOutputParser(pydantic_object=ExtractedOrder)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """คุณคือ AI สกัดข้อมูลคำสั่งซื้อ (Order Entity Extractor)
            จงอ่านประโยคของลูกค้า แล้วดึง 'ชื่อสินค้า', 'จำนวน', และ 'หน่วยนับ' ออกมาให้ครบถ้วน
            ห้ามเดาชื่อสินค้าเองเด็ดขาด ถ้าประโยคไม่มีการสั่งของให้ตอบ items เป็น list ว่าง []
            
            🚨 คำสั่งบังคับ: คุณต้องตอบกลับมาเป็นรูปแบบ JSON เท่านั้น ห้ามมีข้อความอื่นปน
            {format_instructions}
            """),
            ("human", "{text}")
        ])
        
        chain = prompt | cls._llm | parser
        
        return await chain.ainvoke({
            "text": user_text,
            "format_instructions": parser.get_format_instructions()
        })