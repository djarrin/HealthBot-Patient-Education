import uuid
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ..types import HealthBotState


def node_collect_topic(state: HealthBotState) -> HealthBotState:
    print("📝 Node: collect_topic")
    messages = state["messages"]
    user_message = (state.get("user_message") or "").strip()
    
    # Validate that we have a user message
    if not user_message:
        print("❌ No user message provided, cannot proceed")
        return {
            **state,
            "status": "collecting_topic",
            "bot_message": "I didn't catch that. What health topic would you like to learn about?",
            "response_type": "text"
        }
    
    # Create system message if this is the first interaction
    if not messages:
        system_prompt = (
            "You are a medical education assistant helping patients learn about health topics. "
            "Your role is to:\n"
            "1. Search for up-to-date medical information from trusted sources\n"
            "2. Create patient-friendly summaries with citations\n"
            "3. Generate comprehension questions to test understanding\n"
            "4. Provide educational feedback with explanations\n"
            "5. Guide patients through the learning process\n\n"
            "Always be accurate, educational, and encouraging. Never give medical advice."
        )
        sys_message = SystemMessage(
            content=system_prompt,
            name="system"
        )
        messages.append(sys_message)
    
    # Create human message from user input
    human_message = HumanMessage(
        content=user_message,
        name="patient",
        id=str(uuid.uuid4())
    )
    messages.append(human_message)
    
    print(f"📝 Setting status to 'searching' for topic: {user_message}")
    return {
        **state,
        "topic": user_message,
        "status": "searching",
        "bot_message": f"Got it! I'll search for trusted, up-to-date medical information on: {user_message}. This may take a moment...",
        "response_type": "text",
        "user_message": ""  # Clear consumed input
    }


def node_search(state: HealthBotState) -> HealthBotState:
    print("🔍 Node: search")
    messages = state["messages"]
    topic = state.get("topic", "").strip()
    
    # Validate topic before proceeding
    if not topic:
        print("❌ No topic provided for search")
        return {
            **state,
            "status": "collecting_topic",
            "bot_message": "I need a health topic to search for. What would you like to learn about?",
            "response_type": "text"
        }
    
    # Create AI message that will call the search tool
    search_prompt = f"Search for up-to-date medical information about: {topic}"
    ai_message = AIMessage(
        content=search_prompt,
        name="healthbot",
        id=str(uuid.uuid4()),
        tool_calls=[{
            "id": str(uuid.uuid4()),
            "type": "tool_call",
            "name": "web_search",
            "args": {"question": topic}
        }]
    )
    messages.append(ai_message)
    
    print(f"🔍 Created tool call for topic: '{topic}'")
    return {
        **state,
        "status": "searching",  # This will trigger router to check for tool calls
        "bot_message": f"Searching for information about {topic}...",
        "response_type": "text"
    }
