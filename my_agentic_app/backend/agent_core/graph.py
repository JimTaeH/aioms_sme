# Flow controller / Orchestrator using graph-based agent flow (e.g., LangGraph)
"""
Core orchestrator for the AI Agent using LangGraph.
Updated to support Gemma model series from Google AI API.
"""
import os
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from backend.agent_core.state import AgentState
# from langgraph.checkpoint.memory import MemorySaver

from backend.agent_core.tools.db_tools import check_inventory_stock, update_inventory_quantity, add_new_product
from backend.agent_core.tools.parser_tools import extract_slip_data
from backend.core.llm_factory import LLMFactory

from langchain_core.messages import trim_messages
from backend.agent_core.prompts.system_prompts import MAIN_AGENT_PROMPT

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
    extract_slip_data
]
llm_with_tools = llm.bind_tools(agent_tools)

# 3. Define Graph Nodes with Async Support
async def chatbot_node(state: AgentState):
    """
    Primary agent node that processes messages using the Gemma model.
    """
    system_instruction = SystemMessage(content=MAIN_AGENT_PROMPT)
    # 1. Get the full conversation history from the state
    full_messages = state.get("messages", [])

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
    
    # 3. Invoke the LLM with the short-term window
    response = await llm_with_tools.ainvoke(trimmed_messages)
    
    # 4. Return ONLY the new response. 
    # LangGraph's operator.add will append this to the full state in the database.
    return {"messages": [response]}
# Standard ToolNode for executing function calls
tools_node = ToolNode(tools=agent_tools)

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

# Set execution flow
workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

# Circular edge: always return to agent after tool execution to parse results
workflow.add_edge("tools", "agent")

# memory = MemorySaver()

# # 5. Compile the Final Graph
# app_graph = workflow.compile(checkpointer=memory)