"""
State definition for the LangGraph agent workflow.
Defines the structure of the data passed between nodes during execution.
"""
from typing import Annotated, TypedDict, List, Dict, Any, Optional
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    Represents the state of the agentic workflow.
    
    Attributes:
        messages: List of conversation messages (user input, AI responses, tool outputs).
                  The `operator.add` reducer ensures new messages are appended, not overwritten.
        user_id: The LINE User ID of the person interacting with the bot.
        user_role: The role of user such as 'owner', 'admin', or 'customer'.
        extracted_data: Temporary storage for parsed OCR data or intermediate variables.
        requires_human_approval: Flag indicating if the current flow pauses for human-in-the-loop.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    user_role: str # 'owner', 'admin', or 'customer'
    is_registered: bool
    nlp_intent: Optional[str]
    nlp_extracted_entities: Optional[dict]
    extracted_data: Optional[Dict[str, Any]]
    requires_human_approval: bool