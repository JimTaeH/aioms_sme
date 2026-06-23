# Flow controller / Orchestrator using graph-based agent flow (e.g., LangGraph)
"""
Core orchestrator for the AI Agent using LangGraph.
Updated to support Gemma model series from Google AI API.
"""
import os
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from backend.agent_core.state import AgentState
# from langgraph.checkpoint.memory import MemorySaver

from backend.agent_core.tools.db_tools import (
    check_inventory_stock, 
    update_inventory_quantity, 
    add_new_product, 
    check_user_profile)

from backend.agent_core.tools.parser_tools import extract_slip_data
from backend.core.llm_factory import LLMFactory

from langchain_core.messages import trim_messages
from backend.agent_core.prompts.system_prompts import get_main_agent_prompt

import logging
logger = logging.getLogger(__name__)

## 1. Initialize the LLM via Factory Pattern
# You can easily switch providers here (e.g., provider="typhoon", model_name="typhoon-v1.5x-70b-instruct")
llm = LLMFactory.create_llm(
    provider="typhoon", 
    model_name="typhoon-v2.5-30b-a3b-instruct",
    # model_name="pathumma-thaillm-qwen3-8b-think-3.0.0",
    temperature=0.1
)

# 2. Define and Bind Tools
# Gemma models (especially 27B+ versions) have strong reasoning for tool calling
agent_tools = [
    check_inventory_stock,
    update_inventory_quantity,
    add_new_product,
    extract_slip_data,
    check_user_profile
]
llm_with_tools = llm.bind_tools(agent_tools)

SENSITIVE_TOOLS = ["check_inventory_stock", "update_inventory_quantity", "add_new_product"]

# 3. Define Graph Nodes with Async Support
async def chatbot_node(state: AgentState):
    """
    Primary agent node that processes messages using the Gemma model.
    """
    # 1. Get the full conversation history from the state
    full_messages = state.get("messages", [])
    user_role = state.get("user_role", "customer")
    current_user_id = state.get("user_id", "unknown_id")
    is_registered = state.get("is_registered", False)

    # system_instruction = SystemMessage(content=MAIN_AGENT_PROMPT)
    system_instruction = get_main_agent_prompt(user_role, current_user_id, is_registered)

    filtered_messages = [msg for msg in full_messages if not isinstance(msg, SystemMessage)]
    context_messages = [system_instruction] + filtered_messages
    
    # 2. Trim the messages to keep only the most recent ones
    # For example, max_tokens=10 means keeping the last 10 messages (approx 5 turns).
    # token_counter=len means we are counting the number of messages, not actual text tokens.
    trimmed_messages = trim_messages(
        context_messages,
        max_tokens=6, 
        strategy="last",
        token_counter=len,
        include_system=True, # Set to True if you have a SystemMessage at index 0 that must be kept
        allow_partial=False  # Ensures we don't break tool-call message pairs
    )

    logger.info(f"\n========== 🧠 DEBUG: LLM INPUT (User: {current_user_id}) ==========")
    for idx, msg in enumerate(trimmed_messages):
        content_preview = msg.content if isinstance(msg, SystemMessage) else (msg.content[:200] + "..." if len(msg.content) > 200 else msg.content)
        logger.info(f"[{idx}] {msg.type.upper()}: {content_preview}")
    logger.info("====================================================================\n")
    
    # 3. Invoke the LLM with the short-term window
    response = await llm_with_tools.ainvoke(trimmed_messages)

    logger.info(f"\n========== 🤖 DEBUG: LLM OUTPUT ==========")
    logger.info(f"CONTENT: {response.content}")
    if getattr(response, 'tool_calls', None):
        logger.info(f"TOOLS CALLED: {response.tool_calls}")
    logger.info("==========================================\n")
    
    # 4. Return ONLY the new response. 
    # LangGraph's operator.add will append this to the full state in the database.
    return {"messages": [response]}
# Standard ToolNode for executing function calls
tools_node = ToolNode(tools=agent_tools)

async def unauthorized_node(state: AgentState):
    """
    A fallback node triggered when a user tries to access a restricted tool.
    Returns an error message pretending to be the tool's output.
    """
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", [])
    
    messages = []
    for tc in tool_calls:
        # ตอบกลับไปหา LLM ว่าระบบปฏิเสธการเข้าถึง
        error_msg = f"System Error: Permission Denied. Role '{state.get('user_role')}' cannot use '{tc['name']}'. Please apologize to the user."
        messages.append(ToolMessage(content=error_msg, name=tc["name"], tool_call_id=tc["id"]))
        
    logger.warning(f"Blocked unauthorized tool access by user role: {state.get('user_role')}")
    return {"messages": messages}

async def require_registration_node(state: AgentState):
    """Node สำหรับแจ้งเตือนให้ผู้ใช้ไปลงทะเบียนผ่าน LIFF"""
    # คุณสามารถเปลี่ยนเป็น JSON แบบ Flex Message ได้ในอนาคต แต่ตอนนี้ใช้ Text + URL ไปก่อนครับ
    # สังเกต: ต้องเปลี่ยน YOUR_LIFF_ID เป็นไอดีจริงจาก LINE Developer Console
    liff_url = "https://liff.line.me/2010442914-ppUIL7TE"
    msg = f"สวัสดีครับ! 🙏 เพื่อการให้บริการที่ถูกต้องและออกเอกสารใบเสนอราคาได้ กรุณาลงทะเบียนข้อมูลลูกค้าที่ลิงก์นี้ก่อนนะครับ: {liff_url}"
    
    return {"messages": [AIMessage(content=msg)]}

def route_initial(state: AgentState) -> str:
    """ตรวจสอบตอนเริ่มต้นกราฟว่าผู้ใช้ลงทะเบียนหรือยัง"""
    if not state.get("is_registered", False):
        return "require_registration" # ยังไม่ลงทะเบียน เตะไป Node แจ้งเตือน
    return "agent" # ลงทะเบียนแล้ว ให้ AI ทำงานตามปกติ

# ==========================================
# RBAC Routing Logic
# ==========================================

def route_based_on_rbac(state: AgentState) -> str:
    """
    Inspects the AI's intended tool calls and routes them based on user permissions.
    """
    last_message = state["messages"][-1]
    
    # ถ้าไม่มีการเรียก Tool ให้จบการทำงาน
    if not getattr(last_message, "tool_calls", None):
        return END
        
    user_role = state.get("user_role", "customer")
    
    # เช็คว่ามี Tool ไหนเป็น Sensitive Tool ไหม
    for tc in last_message.tool_calls:
        if tc["name"] in SENSITIVE_TOOLS and user_role not in ["admin", "owner"]:
            return "unauthorized" # สกัดกั้นทันที!
            
    return "tools"

def should_continue(state: AgentState) -> str:
    """
    Determines the next step in the workflow based on the model's decision.
    """
    last_message = state["messages"][-1]
    
    # Check if Gemma decided to trigger a tool call
    if last_message.tool_calls:
        return "tools"
    return END

# 4. Construct the Workflow
workflow = StateGraph(AgentState)

# Register nodes
workflow.add_node("agent", chatbot_node)
workflow.add_node("tools", tools_node)
workflow.add_node("unauthorized", unauthorized_node)
workflow.add_node("require_registration", require_registration_node)

# Set execution flow
workflow.set_conditional_entry_point(
    route_initial,
    {
        "require_registration": "require_registration",
        "agent": "agent"
    }
)

# workflow.add_conditional_edges(
#     "agent",
#     should_continue,
#     {
#         "tools": "tools",
#         END: END
#     }
# )

workflow.add_conditional_edges(
    "agent",
    route_based_on_rbac,
    {
        "tools": "tools",
        "unauthorized": "unauthorized",
        END: END
    }
)

# Circular edge: always return to agent after tool execution to parse results
workflow.add_edge("tools", "agent")
workflow.add_edge("unauthorized", "agent")
workflow.add_edge("require_registration", END)

# memory = MemorySaver()

# # 5. Compile the Final Graph
# app_graph = workflow.compile(checkpointer=memory)