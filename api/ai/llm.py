import os
from langchain_openai import ChatOpenAI
from django.conf import settings


def get_llm(streaming: bool = False):
    """Initialize and return LangChain ChatOpenAI LLM instance"""
    api_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OpenAI API key is not configured. Set OPENAI_API_KEY.")
    
    model = os.getenv("LANGCHAIN_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("LANGCHAIN_TEMPERATURE", 0.25))
    max_tokens = int(os.getenv("LANGCHAIN_MAX_TOKENS", 800))
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
        streaming=streaming,
    )


llm = get_llm()