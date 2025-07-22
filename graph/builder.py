from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import agent_node, state_updater_node, tool_node
from tools.driver_tools import tools

def should_continue(state: GraphState) -> str:
    """Conditional edge to decide whether to continue or end the conversation."""
    last_message = state['agent_state'].messages[-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "call_tools"
    return END

def create_graph():
    """Builds and compiles the LangGraph agent."""
    workflow = StateGraph(GraphState)

    # Define the nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("call_tools", tool_node)
    workflow.add_node("update_state", state_updater_node)

    # Define the edges
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "call_tools": "call_tools",
            END: END,
        },
    )
    workflow.add_edge("call_tools", "update_state")
    workflow.add_edge("update_state", "agent")

    # Compile the graph
    app = workflow.compile()
    return app

# Create a single instance of the app to be imported elsewhere
app = create_graph()