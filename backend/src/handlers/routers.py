from langgraph.graph import END
from .types import HealthBotState


def router(state: HealthBotState) -> str:
    """Main router for user interaction points"""
    status = state.get("status", "collecting_topic")
    user_message = (state.get("user_message") or "").strip().lower()
    message_type = state.get("message_type", "topic")
    
    print(f"🔀 Router called with status: {status}, user_message: '{user_message}', message_type: '{message_type}'")
    
    if status == "presenting_summary":
        # If message type is confirmation, check if user is ready
        if message_type == "confirmation":
            if user_message in {"ready", "r", "ok", "go", "yes", "y", "i'm ready", "ready for quiz"}:
                print("✅ User ready for quiz, routing to generate_question")
                return "generate_question"
            elif user_message in {"no", "n", "not ready", "not yet", "skip"}:
                print("❌ User not ready for quiz, ending session")
                return END
            else:
                # User sent something else, treat as new topic
                print("🔄 User sent new topic, routing to collect_topic")
                return "collect_topic"
        else:
            # If not a confirmation message, treat as new topic
            print("🔄 User sent new topic, routing to collect_topic")
            return "collect_topic"
    
    elif status == "present_question":
        # If message type is answer, check if it's a valid quiz answer
        if message_type == "answer":
            if user_message.upper() in {"A", "B", "C", "D"}:
                print("✅ User provided quiz answer, routing to evaluate")
                return "evaluate"
            else:
                # Invalid answer format, wait for user response
                print("⏸️  Invalid answer format, waiting for user response")
                return END
        else:
            # If not an answer message, treat as new topic
            print("🔄 User sent new topic, routing to collect_topic")
            return "collect_topic"
    
    elif status == "ask_restart":
        # Proceed once user responds yes/no
        if message_type == "restart":
            if user_message in {"yes", "y", "restart", "again", "another", "new topic"}:
                print("✅ User wants to restart, routing to handle_restart")
                return "handle_restart"
            elif user_message in {"no", "n", "end", "exit", "quit", "stop"}:
                print("❌ User wants to end, routing to handle_restart")
                return "handle_restart"
            else:
                # Wait for user response
                print("⏸️  Waiting for user response at ask_restart")
                return END
        else:
            # If not a restart message, treat as new topic
            print("🔄 User sent new topic, routing to collect_topic")
            return "collect_topic"
    elif status == "ended":
        print("✅ Session ended")
        return END
    
    print(f"⚠️  No matching status, ending")
    return END


def entry_router(state: HealthBotState) -> str:
    """Router to determine which node to start from based on current status and message type"""
    status = state.get("status", "collecting_topic")
    user_message = (state.get("user_message") or "").strip()
    message_type = state.get("message_type", "topic")
    
    print(f"🚪 Entry router called with status: {status}, user_message: '{user_message}', message_type: '{message_type}'")
    print(f"🚪 State keys: {list(state.keys())}")
    
    # If we have a user message with a specific message type, route accordingly
    if user_message:
        if message_type == "confirmation" and status == "presenting_summary":
            print("✅ User sent confirmation, continuing from present_summary")
            return "present_summary"
        elif message_type == "answer" and status == "present_question":
            print("✅ User sent answer, continuing from present_question")
            return "present_question"
        elif message_type == "restart" and status == "ask_restart":
            print("✅ User sent restart response, continuing from ask_restart")
            return "ask_restart"
        elif message_type == "topic":
            print("🆕 User sent new topic, starting fresh from collect_topic")
            return "collect_topic"
    
    # If we're in presenting_summary with no user message, continue from present_summary
    if status == "presenting_summary":
        print("🔄 Continuing from presenting_summary")
        return "present_summary"
    
    # If we're in other states with no user message, continue from that state
    if status in ["generate_question", "present_question", "ask_restart", "ended", "awaiting_answer", "searching", "summarizing"]:
        print(f"🔄 Continuing from {status}")
        return status
    
    # Default: start new workflow
    print("🆕 Starting new workflow from collect_topic")
    return "collect_topic"


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
