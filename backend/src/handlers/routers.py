from langgraph.graph import END
from .types import HealthBotState


def router(state: HealthBotState) -> str:
    """Main router for user interaction points - routes based on message_type"""
    status = state.get("status", "collecting_topic")
    user_message = (state.get("user_message") or "").strip().lower()
    message_type = state.get("message_type", "topic")
    
    print(f"🔀 Router called with status: {status}, user_message: '{user_message}', message_type: '{message_type}'")
    
    # Route based on message_type, not status
    if message_type == "confirmation":
        if status == "presenting_summary":
            if user_message in {"ready", "r", "ok", "go", "yes", "y", "i'm ready", "ready for quiz"}:
                print("✅ User ready for quiz, routing to generate_question")
                return "generate_question"
            elif user_message in {"no", "n", "not ready", "not yet", "skip"}:
                print("❌ User not ready for quiz, ending session")
                return END
            else:
                # Invalid confirmation response, wait for user
                print("⏸️  Invalid confirmation response, waiting for user")
                return END
        else:
            # Confirmation message in wrong state, wait for user
            print("⏸️  Confirmation message in wrong state, waiting for user")
            return END
    
    elif message_type == "answer":
        if status == "present_question":
            if user_message.upper() in {"A", "B", "C", "D"}:
                print("✅ User provided quiz answer, routing to evaluate")
                return "evaluate"
            else:
                # Invalid answer format, wait for user response
                print("⏸️  Invalid answer format, waiting for user response")
                return END
        else:
            # Answer message in wrong state, wait for user
            print("⏸️  Answer message in wrong state, waiting for user")
            return END
    
    elif message_type == "restart":
        if status == "ask_restart":
            print("✅ User provided restart response, routing to handle_restart")
            return "handle_restart"
        else:
            # Restart message in wrong state, wait for user
            print("⏸️  Restart message in wrong state, waiting for user")
            return END
    
    elif message_type == "topic":
        # New topic request - always route to collect_topic
        print("🆕 User sent new topic, routing to collect_topic")
        return "collect_topic"
    
    # Default: wait for user input
    print("⏸️  No valid message type, waiting for user input")
    return END


def entry_router(state: HealthBotState) -> str:
    """Router to determine which node to start from based on current status and message type"""
    status = state.get("status", "collecting_topic")
    user_message = (state.get("user_message") or "").strip()
    message_type = state.get("message_type", "topic")
    
    print(f"🚪 Entry router called with status: {status}, user_message: '{user_message}', message_type: '{message_type}'")
    
    # If we have a user message, route based on message_type
    if user_message:
        if message_type == "topic":
            # New topic request - always start fresh
            print("🆕 User sent new topic, starting fresh from collect_topic")
            return "collect_topic"
        elif message_type == "confirmation" and status == "presenting_summary":
            print("✅ User sent confirmation, continuing from present_summary")
            return "present_summary"
        elif message_type == "answer" and status == "present_question":
            print("✅ User sent answer, continuing from present_question")
            return "present_question"
        elif message_type == "restart" and status == "ask_restart":
            print("✅ User sent restart response, continuing from ask_restart")
            return "ask_restart"
    
    # If no user message, continue from current status
    if status in ["presenting_summary", "present_question", "ask_restart", "generate_question", "searching", "summarizing"]:
        print(f"🔄 Continuing from {status}")
        return status
    
    # Default: start new workflow
    print("🆕 Starting new workflow from collect_topic")
    return "collect_topic"


def present_summary_router(state: HealthBotState) -> str:
    """Router for present_summary node - can end execution when presenting summary for first time"""
    status = state.get("status", "collecting_topic")
    user_message = (state.get("user_message") or "").strip()
    message_type = state.get("message_type", "topic")
    confirmation_prompt = state.get("confirmation_prompt")
    
    print(f"📄 Present summary router called with status: {status}, user_message: '{user_message}', message_type: '{message_type}'")
    
    # If we have a user message, route based on message_type
    if user_message:
        if message_type == "confirmation":
            # Check if user wants to take the quiz (true) or decline (false)
            if user_message.lower() in {"true", "yes", "y", "ready", "r", "ok", "go", "i'm ready", "ready for quiz"}:
                print("✅ User ready for quiz, routing to generate_question")
                return "generate_question"
            elif user_message.lower() in {"false", "no", "n", "not ready", "not yet", "skip"}:
                print("❌ User declined quiz, routing to handle_restart")
                return "handle_restart"
            else:
                # Invalid confirmation response, wait for user
                print("⏸️  Invalid confirmation response, waiting for user")
                return END
        elif message_type == "topic":
            # New topic request - always route to collect_topic
            print("🆕 User sent new topic, routing to collect_topic")
            return "collect_topic"
    
    # If no user message and we have a confirmation prompt, end execution
    # This means we just presented the summary for the first time
    if not user_message and confirmation_prompt:
        print("📄 Summary presented for first time, ending execution")
        return END
    
    # If no user message and no confirmation prompt, wait for user input
    print("⏸️  No user message, waiting for user input")
    return END


def tool_router(state: HealthBotState) -> str:
    """Router specifically for handling tool execution flow"""
    messages = state.get("messages", [])
    
    print(f"🔧 Tool router called with {len(messages)} messages")
    
    # Check if the last message has tool calls that need to be executed
    if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
        print("🔧 Found tool calls, routing to tools")
        return "tools"  # Execute the tool
    
    # If no tool calls, proceed directly to summarize
    print("📝 No tool calls found, proceeding to summarize")
    return "summarize"
