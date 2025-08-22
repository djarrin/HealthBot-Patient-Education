import json
import uuid
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from ..types import HealthBotState, ConfirmationPrompt
from ..clients import get_llm


def node_summarize(state: HealthBotState) -> HealthBotState:
    print("📋 Node: summarize")
    messages = state["messages"]
    topic = state.get("topic", "")
    
    # Extract search results from tool messages
    search_results = []
    for message in messages:
        if isinstance(message, ToolMessage) and message.name == "web_search":
            try:
                result_data = json.loads(message.content)
                results = result_data.get("results", [])
                
                # Normalize results
                for r in results:
                    url = r.get("url") or r.get("source", "")
                    title = r.get("title") or ""
                    content = r.get("content") or r.get("snippet") or ""
                    
                    if content and len(content.strip()) > 50:
                        search_results.append({
                            "url": url,
                            "title": title,
                            "content": content
                        })
            except Exception as e:
                print(f"Error parsing search results: {e}")
    
    print(f"📋 Found {len(search_results)} search results")
    
    # If no results, provide fallback
    if not search_results:
        search_results = [{
            "url": "https://www.healthline.com",
            "title": "Health Information",
            "content": "General health information and resources. Please try rephrasing your question for more specific results."
        }]
    
    # Create summary using LLM
    llm = get_llm()
    sources_block = "\n\n".join(
        [f"Source {i+1}: {r.get('title','').strip()} — {r.get('url','').strip()}\n{(r.get('content','') or '')[:1500]}" 
         for i, r in enumerate(search_results)]
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a careful medical educator. Write at a 7th–9th grade reading level. Include citations as [1], [2], etc. referencing the sources list order."),
        ("human", (
            "Summarize the most relevant, evidence-based information for a patient about the topic: '{topic}'.\n"
            "- Be accurate and neutral; avoid giving medical advice.\n"
            "- Use short paragraphs and clear language.\n"
            "- Add a 'Key Points' section at the end.\n"
            "- Include in-text citation markers like [1], [2] that map to the sources list order.\n"
            "- Keep the summary comprehensive but readable (aim for 300-500 words).\n\n"
            "Sources (ordered):\n{sources}\n"
        ))
    ])
    
    try:
        response = llm.invoke(prompt.format_messages(topic=topic, sources=sources_block))
        summary = response.content
        print("📋 Summary generated successfully")
    except Exception as e:
        print(f"Error calling LLM: {e}")
        summary = f"Unable to generate summary due to technical issues. Please try again later. Error: {str(e)}"
    
    # Build citations
    citations = [r.get("url", "") for r in search_results if r.get("url")]
    
    # Create AI message with summary
    ai_message = AIMessage(
        content=summary,
        name="healthbot",
        id=str(uuid.uuid4())
    )
    messages.append(ai_message)
    
    print("📋 Setting status to 'presenting_summary'")
    return {
        **state,
        "search_results": search_results,
        "summary": summary,
        "citations": citations,
        "status": "presenting_summary",
        "bot_message": summary,
        "response_type": "text"
    }


def node_present_summary(state: HealthBotState) -> HealthBotState:
    print("📄 Node: present_summary")
    messages = state["messages"]
    summary = state.get("summary", "")
    user_message = (state.get("user_message") or "").strip()
    
    # Check if we have a user message (continuing from previous state)
    if user_message:
        print(f"📄 Continuing from presenting_summary with user message: '{user_message}'")
        # Create human message with user's response
        human_message = HumanMessage(
            content=user_message,
            name="patient",
            id=str(uuid.uuid4())
        )
        messages.append(human_message)
        
        # Route to generate_question since user is ready
        print("📄 User is ready for quiz, routing to generate_question")
        return {
            **state,
            "status": "generate_question"
            # Don't clear user_message yet - it will be cleared after question generation
        }
    
    # Original logic for first time presenting summary
    # Create confirmation prompt for the frontend
    confirmation_prompt: ConfirmationPrompt = {
        "message": "When you're ready for a quick comprehension check, click the button below.",
        "requires_confirmation": True
    }
    
    # Create the full message including summary and confirmation prompt
    full_message = f"{summary}\n\n---\n\nI've provided you with comprehensive information about your health topic. When you're ready for a quick comprehension check, click the button below."
    
    # Create AI message with the full content
    ai_message = AIMessage(
        content=full_message,
        name="healthbot",
        id=str(uuid.uuid4())
    )
    messages.append(ai_message)
    
    print("📄 Setting status to 'presenting_summary' to pause for user interaction")
    return {
        **state, 
        "status": "presenting_summary",
        "bot_message": full_message,
        "response_type": "confirmation",
        "confirmation_prompt": confirmation_prompt
    }
