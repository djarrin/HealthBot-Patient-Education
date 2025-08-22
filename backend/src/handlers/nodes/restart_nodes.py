import uuid
from langchain_core.messages import HumanMessage, AIMessage
from ..types import HealthBotState


def node_handle_restart(state: HealthBotState) -> HealthBotState:
    print("🔄 Node: handle_restart")
    messages = state["messages"]
    user_message = (state.get("user_message") or "").strip().lower()
    
    # Create human message with user's restart decision
    human_message = HumanMessage(
        content=user_message,
        name="patient",
        id=str(uuid.uuid4())
    )
    messages.append(human_message)
    
    if user_message in {"yes", "y", "restart", "again", "another", "new topic"}:
        # Create AI message for restart
        ai_message = AIMessage(
            content="Great! What health topic or medical condition would you like to learn about?",
            name="healthbot",
            id=str(uuid.uuid4())
        )
        messages.append(ai_message)
        
        # Reset sensitive state for privacy and accuracy
        return {
            **state,
            "status": "collecting_topic",
            "bot_message": "Great! What health topic or medical condition would you like to learn about?",
            "response_type": "text",
            # Clear all sensitive data
            "user_message": "",
            "topic": "",
            "search_results": [],
            "summary": "",
            "citations": [],
            "question": "",
            "correct_answer": "",
            "multiple_choice": None,
            "user_answer": "",
            "grade": "",
            "explanation": "",
            "confirmation_prompt": None
        }
    elif user_message in {"no", "n", "end", "exit", "quit", "stop"}:
        # Create AI message for session end
        ai_message = AIMessage(
            content="Thanks for learning with HealthBot! Take care and stay healthy! 👋",
            name="healthbot",
            id=str(uuid.uuid4())
        )
        messages.append(ai_message)
        
        return {
            **state,
            "status": "ended",
            "bot_message": "Thanks for learning with HealthBot! Take care and stay healthy! 👋",
            "response_type": "text"
        }
    else:
        # Wait for user response
        return {
            **state,
            "status": "ask_restart",
            "bot_message": "I didn't understand. Would you like to learn about another health topic? Reply 'yes' or 'no'.",
            "response_type": "text"
        }
