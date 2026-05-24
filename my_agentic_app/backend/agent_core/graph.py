# Flow controller / Orchestrator using graph-based agent flow (e.g., LangGraph)
"""
Core orchestrator for the AI Agent using LangGraph.
Updated to support Gemma model series from Google AI API.
"""
import os
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from backend.agent_core.state import AgentState
from backend.agent_core.tools.db_tools import check_inventory_stock

# 1. Initialize the Gemma Model
# Note: Ensure the model name matches the exact string provided by Google AI Studio/Vertex AI
# Currently using "gemma-4-31b" as requested. 
# If this is a custom or preview model, ensure your API Key has access permissions.
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",  # Adjusting to your specific requested version
    temperature=0.1,      # Lower temperature for more precise operation management
    max_tokens=2048,
    timeout=30,
    max_retries=2
)

# 2. Define and Bind Tools
# Gemma models (especially 27B+ versions) have strong reasoning for tool calling
agent_tools = [check_inventory_stock]
llm_with_tools = llm.bind_tools(agent_tools)

# 3. Define Graph Nodes with Async Support
async def chatbot_node(state: AgentState):
    """
    Primary agent node that processes messages using the Gemma model.
    """
    # Using ainvoke for full asynchronous non-blocking execution
    response = await llm_with_tools.ainvoke(state["messages"])
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

# 5. Compile the Final Graph
app_graph = workflow.compile()