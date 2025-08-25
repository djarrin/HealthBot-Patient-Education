import uuid
from langchain_core.messages import HumanMessage, AIMessage
from ..types import HealthBotState


def node_handle_restart(state: HealthBotState) -> HealthBotState:
    print("🔄 Node: handle_restart")
    messages = state["messages"]
    user_message = (state.get("user_message") or "").strip().lower()
    current_status = state.get("status", "ask_restart")
    
    # Check if we have a user message (continuing from previous state)
    if user_message:
        print(f"🔄 Processing user restart response: '{user_message}'")
        
        # Create human message with user's restart decision
        human_message = HumanMessage(
            content=user_message,
            name="patient",
            id=str(uuid.uuid4())
        )
        messages.append(human_message)
        
        # Handle user response
        if user_message in {"yes", "y", "restart", "again", "another", "new topic"}:
            print("🔄 User wants to learn about another topic, resetting state")
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
            print("🔄 User wants to end session")
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
            # Invalid response, ask again
            print("🔄 Invalid restart response, asking again")
            ai_message = AIMessage(
                content="I didn't understand. Would you like to learn about another health topic?",
                name="healthbot",
                id=str(uuid.uuid4())
            )
            messages.append(ai_message)
            
            return {
                **state,
                "status": "ask_restart",
                "bot_message": "I didn't understand. Would you like to learn about another health topic?",
                "response_type": "confirmation",
                "confirmation_prompt": True
            }
    
    # First time asking for restart - create AI message with the restart question
    print("🔄 First time asking for restart")
    ai_message = AIMessage(
        content="Would you like to learn about another health topic? Reply 'yes' or 'no'.",
        name="healthbot",
        id=str(uuid.uuid4())
    )
    messages.append(ai_message)
    
    print("🔄 Setting status to 'ask_restart' and ending execution")
    return {
        **state,
        "status": "ask_restart",
        "bot_message": "Would you like to learn about another health topic?",
        "response_type": "confirmation",
        "confirmation_prompt": True
    }
