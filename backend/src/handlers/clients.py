import os
from langchain_openai import ChatOpenAI
from tavily import TavilyClient


def get_llm() -> ChatOpenAI:
    """Get configured OpenAI LLM client"""
    # Debug API key loading
    api_key = os.environ.get("OPENAI_API_KEY", "")
    print(f"OpenAI API Key (first 10 chars): {api_key[:10]}...")
    print(f"OpenAI API Key length: {len(api_key)}")
    
    # For Volcengine relay, we need to configure the base URL
    # Volcengine typically uses a different endpoint
    base_url = os.environ.get("OPENAI_BASE_URL", "https://openai.vocareum.com/v1")
    print(f"Using base URL: {base_url}")
    
    # Keep a small, fast model for lambda latency
    return ChatOpenAI(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), 
        temperature=0,
        api_key=api_key,
        base_url=base_url,
        max_retries=0  # Disable retries to get immediate error feedback
    )


def get_tavily_client() -> TavilyClient:
    """Get Tavily client for direct API access"""
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable is required")
    return TavilyClient(api_key=api_key)
