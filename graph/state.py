from typing import TypedDict
from schemas.driver_schema import AgentState

# We use TypedDict for LangGraph's state management
class GraphState(TypedDict):
    agent_state: AgentState