from langchain_core.tools import tool
from .clients import get_tavily_client


@tool
def web_search(question: str) -> dict:
    """
    Search for up-to-date medical information on a given health topic.
    Returns relevant, evidence-based information from trusted medical sources.
    """
    # Validate the question parameter
    if not question or not question.strip():
        print("❌ Empty search question provided")
        return {
            "results": [],
            "error": "Search question cannot be empty"
        }
    
    try:
        tavily_client = get_tavily_client()
        print(f"🔍 Searching for: '{question}'")
        response = tavily_client.search(
            question,
            search_depth="advanced",
            max_results=8,
            include_domains=["mayoclinic.org", "healthline.com", "webmd.com", "medlineplus.gov", "cdc.gov", "nih.gov"]
        )
        print(f"✅ Search completed successfully")
        return response
    except Exception as e:
        print(f"❌ Error in web_search: {e}")
        return {
            "results": [],
            "error": str(e)
        }
