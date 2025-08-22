from langgraph.graph import END
from .types import HealthBotState


def router(state: HealthBotState) -> str:
    """Main router for user interaction points"""
    status = state.get("status", "collecting_topic")
    user_message = (state.get("user_message") or "").strip().lower()
    
    print(f"🔀 Router called with status: {status}, user_message: '{user_message}'")
    
    if status == "presenting_summary":
        # If user has responded with ready/confirmation, transition to generate_question
        if user_message in {"ready", "r", "ok", "go", "yes", "y", "i'm ready", "ready for quiz"}:
            print("✅ User ready for quiz, routing to generate_question")
            return "generate_question"
        elif user_message in {"no", "n", "not ready", "not yet", "skip"}:
            print("❌ User not ready for quiz, ending session")
            return END
        else:
            # Wait for user response
            print("⏸️  Waiting for user response at presenting_summary")
            return END
    
    elif status == "present_question":
        # If user has provided a quiz answer, transition to evaluate
        if user_message in {"a", "b", "c", "d"}:
            print("✅ User provided quiz answer, routing to evaluate")
            return "evaluate"
        else:
            # Wait for user response
            print("⏸️  Waiting for user response at present_question")
            return END
    
    elif status == "ask_restart":
        # Proceed once user responds yes/no
        if user_message in {"yes", "y", "restart", "again", "another", "new topic"}:
            print("✅ User wants to restart, routing to collect_topic")
            return "collect_topic"
        elif user_message in {"no", "n", "end", "exit", "quit", "stop"}:
            print("❌ User wants to end, ending session")
            return END
        else:
            # Wait for user response
            print("⏸️  Waiting for user response at ask_restart")
            return END
    
    print(f"⚠️  No matching status, ending")
    return END


def entry_router(state: HealthBotState) -> str:
    """Router to determine which node to start from based on current status"""
    status = state.get("status", "collecting_topic")
    user_message = (state.get("user_message") or "").strip()
    
    print(f"🚪 Entry router called with status: {status}, user_message: '{user_message}'")
    
    # If we have a status and user message, route based on status
    if status == "presenting_summary" and user_message:
        print("🔄 Continuing from presenting_summary")
        return "present_summary"
    elif status == "generate_question" and user_message:
        print("🔄 Continuing from generate_question")
        return "generate_question"
    elif status == "present_question" and user_message:
        print("🔄 Continuing from present_question")
        return "present_question"
    elif status == "ask_restart" and user_message:
        print("🔄 Continuing from ask_restart")
        return "handle_restart"
    elif status == "awaiting_answer" and user_message:
        print("🔄 Continuing from awaiting_answer")
        return "evaluate"
    else:
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
