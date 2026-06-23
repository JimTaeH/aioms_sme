"""
Asynchronous worker service that connects incoming events to the LangGraph instance.
Processes the state, invokes the model, and dispatches the final response.
"""
import logging
from langchain_core.messages import HumanMessage

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from backend.agent_core.graph import workflow

# from backend.agent_core.graph import app_graph
from backend.services.line_messenger import LineMessengerService

from backend.services.user_service import UserService
from backend.core.database import DATABASE_URL

logger = logging.getLogger(__name__)

# The PostgresSaver uses psycopg3, which requires the standard postgresql:// URL format
# We remove '+asyncpg' from our SQLAlchemy URL if it exists
PG_CHECKPOINT_URL = DATABASE_URL.replace("+asyncpg", "")

class AgentWorkerService:
    """
    Handles the execution of the AI Agent graph from background tasks.
    """
    
    @staticmethod
    async def process_line_event(event: dict) -> None:
        """
        Parses the LINE event, builds the initial AgentState, runs LangGraph,
        and sends the generated output back to LINE.
        
        Args:
            event (dict): The dictionary containing the LINE webhook event.
        """
        event_type = event.get("type")
        
        # We only handle message events of type text in this foundation phase
        if event_type != "message":
            logger.info(f"Skipping unhandled event type: {event_type}")
            return
            
        message_data = event.get("message", {})
        msg_type = message_data.get("type")
        user_id = event.get("source", {}).get("userId", "")
        reply_token = event.get("replyToken", "")
        user_text = message_data.get("text", "")

        if msg_type == "text":
            logger.info(f"Processing TEXT from user {user_id}: {user_text}")
            
        elif msg_type == "image":
            msg_id = message_data.get("id")
            # Construct a system prompt disguised as user input to trigger the OCR tool
            user_text = f"[System Context: The user just uploaded an image. The LINE message_id for this image is '{msg_id}' and the line_user_id is '{user_id}' . Please use the 'extract_slip_data' tool to read this image and tell the user what you found.]"
            logger.info(f"Processing IMAGE from user {user_id}. Message ID: {msg_id}")
            
        else:
            logger.info(f"Skipping unhandled message type: {msg_type}")
            return
        
        if not reply_token:
            logger.warning("Missing replyToken in event. Cannot respond.")
            return

        logger.info(f"Processing message from user {user_id}: {user_text}")

        # Auto-register the user asynchronously before processing the agent logic
        await UserService.register_user_if_not_exists(user_id)

        user_profile = await UserService.get_user_profile(user_id)
        current_user_role = user_profile.role if user_profile else "customer"
        is_registered = user_profile.is_registered if user_profile else False
        logger.info(f"User {user_id} executing as role: {current_user_role} Registered: {is_registered}")

        config = {"configurable": {"thread_id": user_id}}

        # Initialize the LangGraph state
        initial_state = {
            "messages": [HumanMessage(content=user_text)],
            "user_id": user_id,
            "user_role": current_user_role,
            "is_registered": is_registered,
            "extracted_data": None,
            "requires_human_approval": False
        }

        try:
            async with AsyncPostgresSaver.from_conn_string(PG_CHECKPOINT_URL) as checkpointer:
                # Automatically creates 'checkpoints' and 'checkpoint_writes' tables if they don't exist
                await checkpointer.setup()
                # Compile the workflow dynamically with the persistent checkpointer
                app_graph = workflow.compile(checkpointer=checkpointer)
                # Invoke the graph asynchronously (ainvoke)
                # This triggers LLM and any database tools automatically
                final_state = await app_graph.ainvoke(initial_state, config=config)
            
            # Extract the last AI message from the conversation state
            messages = final_state.get("messages", [])
            # logger.info(f"LLM Messages: {messages}")
            
            if messages:
                last_message_content = messages[-1].content
                final_ai_message = ""
                
                # กรณีที่ 1: โมเดลตอบกลับมาเป็น String ธรรมดา
                if isinstance(last_message_content, str):
                    final_ai_message = last_message_content
                    
                # กรณีที่ 2: โมเดลตอบกลับมาเป็น List (เช่น หลังเรียก Tool หรือมีโครงสร้างซับซ้อน)
                elif isinstance(last_message_content, list):
                    extracted_texts = []
                    for item in last_message_content:
                        # ถ้าข้างใน List เป็น String
                        if isinstance(item, str):
                            extracted_texts.append(item)
                        # ถ้าข้างใน List เป็น Dictionary แบบที่คุณเจอ
                        elif isinstance(item, dict) and "text" in item:
                            extracted_texts.append(item["text"])
                    
                    # นำข้อความที่แกะได้มารวมกัน
                    final_ai_message = " ".join(extracted_texts).strip()
                    
                # กรณีที่ 3: Fallback กันเหนียวสำหรับ Type อื่นๆ ที่ไม่คาดคิด
                else:
                    final_ai_message = str(last_message_content)
                
                # ป้องกันกรณีแกะข้อความแล้วได้ค่าว่างเปล่า
                if not final_ai_message:
                    logger.warning("Agent returned an empty message structure.")
                    final_ai_message = "ทำรายการเรียบร้อยแล้วครับ"

                # Send the answer back to the user on LINE asynchronously
                await LineMessengerService.send_reply(reply_token, final_ai_message)
            else:
                logger.error("No response messages generated by the agent graph.")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error executing agent graph workflow: {error_msg}")
            # เช็คว่าเป็น Error จากฝั่ง Google Server (500) หรือไม่
            if "500 INTERNAL" in error_msg or "google.genai" in error_msg:
                fallback_message = "ขออภัยครับ ตอนนี้เซิร์ฟเวอร์สมองกล (Google AI) มีผู้ใช้งานหนาแน่น หรือกำลังขัดข้องชั่วคราว รบกวนพิมพ์ถามใหม่อีกครั้งในอีกสักครู่นะครับ 🤖"
            else:
                fallback_message = "ขออภัยครับ ระบบประมวลผลภายในเกิดความผิดพลาด กรุณาลองใหม่อีกครั้ง"
                
            try:
                await LineMessengerService.send_reply(reply_token, fallback_message)
            except Exception as reply_err:
                logger.error(f"Failed to send fallback message: {str(reply_err)}")