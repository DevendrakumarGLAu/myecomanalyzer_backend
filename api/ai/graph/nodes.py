import logging
from api.intent_classifier import IntentClassifier
from api.analytics_service import AnalyticsService
from api.prompt_builder import PromptBuilder
from api.ai.llm import llm
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

logger = logging.getLogger("langchain_graph")


def detect_intent_node(state):
    """Detect user intent from message"""
    try:
        intent = IntentClassifier.classify(
            state["user_message"]
        )
        state["intent"] = intent
        logger.debug(f"Intent detected: {intent}")
    except Exception as e:
        logger.exception(f"Error detecting intent: {e}")
        state["intent"] = "general"
    
    return state


def fetch_analytics_node(state):
    """Fetch analytics data for the user"""
    try:
        analytics = AnalyticsService.fetch_analytics(
            current_user=state["user"],
            platform_code=state.get("platform")
        )
        state["analytics"] = analytics
        logger.debug(f"Analytics fetched for user: {state['user']}")
    except Exception as e:
        logger.exception(f"Error fetching analytics: {e}")
        state["analytics"] = {"summary": {}}
    
    return state


def ai_response_node(state):
    """Generate AI response using LangChain LLM"""
    try:
        messages = PromptBuilder.build_messages(
            user_message=state["user_message"],
            intent=state.get("intent", "general"),
            analytics_summary=state.get("analytics", {}).get("summary", {}),
            platform_code=state.get("platform"),
        )
        
        # Convert messages to LangChain format
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                langchain_messages.append(HumanMessage(content=content))
        
        # Invoke LLM
        response = llm.invoke(langchain_messages)
        state["ai_reply"] = response.content
        logger.debug("AI response generated successfully")
    
    except Exception as e:
        logger.exception(f"Error generating AI response: {e}")
        state["ai_reply"] = "I'm unable to process your request at the moment. Please try again later."
    
    return state
