from langchain_core.tools import tool
from .clients import get_tavily_client


@tool
def web_search(question: str) -> dict:
    """
    Search for up-to-date medical information on a given health topic.
    Returns relevant, evidence-based information from trusted medical sources.
    """
    try:
        tavily_client = get_tavily_client()
        response = tavily_client.search(
            question,
            search_depth="advanced",
            max_results=8,
            include_domains=["mayoclinic.org", "healthline.com", "webmd.com", "medlineplus.gov", "cdc.gov", "nih.gov"]
        )
        return response
    except Exception as e:
        print(f"Error in web_search: {e}")
        return {
            "results": [],
            "error": str(e)
        }
