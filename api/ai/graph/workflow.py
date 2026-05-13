import logging
from langgraph.graph import StateGraph, END
from api.ai.graph.state import EcommerceAgentState
from api.ai.graph.nodes import (
    detect_intent_node,
    fetch_analytics_node,
    ai_response_node,
)

logger = logging.getLogger("langchain_workflow")

# Create the state graph
workflow = StateGraph(EcommerceAgentState)

# Add nodes
workflow.add_node(
    "detect_intent",
    detect_intent_node
)

workflow.add_node(
    "fetch_analytics",
    fetch_analytics_node
)

workflow.add_node(
    "ai_response",
    ai_response_node
)

# Set entry point
workflow.set_entry_point("detect_intent")

# Add edges (workflow sequence)
workflow.add_edge(
    "detect_intent",
    "fetch_analytics"
)

workflow.add_edge(
    "fetch_analytics",
    "ai_response"
)

workflow.add_edge(
    "ai_response",
    END
)

# Compile the graph
graph = workflow.compile()


def run_graph(user, user_message: str, platform_code: str = None):
    """
    Execute the ecommerce LangChain graph workflow
    
    Args:
        user: Django User object
        user_message: User's chat message
        platform_code: Optional platform code (meesho, flipkart, etc.)
    
    Returns:
        Dictionary with ai_reply and other state
    """
    try:
        initial_state = {
            "user": user,
            "user_message": user_message,
            "intent": "",
            "analytics": {},
            "platform": platform_code,
            "ai_reply": "",
        }
        
        logger.debug(f"Starting graph execution for user: {user.id}")
        result = graph.invoke(initial_state)
        logger.debug("Graph execution completed successfully")
        return result
    
    except Exception as e:
        logger.exception(f"Error executing graph: {e}")
        return {
            "user": user,
            "user_message": user_message,
            "intent": "error",
            "analytics": {},
            "platform": platform_code,
            "ai_reply": "I encountered an error processing your request. Please try again.",
        }
