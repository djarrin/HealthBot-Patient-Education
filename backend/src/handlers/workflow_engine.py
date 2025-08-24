import os
from typing import Dict, Any

from .healthbot_graph import build_graph
from ..utils.secrets_manager import set_secrets_as_env_vars

def setup_environment() -> None:
    """Set up environment variables and secrets."""
    print("🔐 Loading secrets...")
    secrets = set_secrets_as_env_vars()
    print(f"✅ Loaded secrets keys: {list(secrets.keys())}")
    
    # Debug API key loading
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    print(f"🔑 OpenAI API Key loaded: {openai_key[:10] if openai_key else 'NOT_FOUND'}...")
    print(f"🔑 OpenAI API Key length: {len(openai_key) if openai_key else 0}")

def create_workflow_config(session_id: str) -> Dict[str, Any]:
    """Create the workflow configuration for LangGraph."""
    config = {
        "configurable": {"thread_id": session_id},
        "recursion_limit": 50  # Increase recursion limit to handle complex workflows
    }
    print(f"🔍 Created workflow config with thread_id: {session_id}, recursion_limit: 50")
    return config

def create_initial_state(message_content: str, message_type: str = 'topic') -> Dict[str, Any]:
    """Create the initial state for the workflow."""
    initial_state = {
        "user_message": message_content,
        "message_type": message_type,
        "status": "collecting_topic",
        "messages": [],
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
        "bot_message": "",
        "response_type": "text",
        "confirmation_prompt": None
    }
    print(f"🔍 Created initial state with user_message: '{message_content}', message_type: '{message_type}'")
    return initial_state

def execute_workflow(session_id: str, message_content: str, message_type: str = 'topic', skip_environment_setup: bool = False) -> Dict[str, Any]:
    """
    Execute the LangGraph workflow.
    
    Args:
        session_id: The session ID for the workflow
        message_content: The user's message content
        message_type: The type of message ('topic', 'confirmation', 'answer', 'restart')
        skip_environment_setup: If True, skip setting up environment (useful when already done)
    
    Returns:
        The final state from the workflow execution
    """
    # Set up environment (unless skipped)
    if not skip_environment_setup:
        setup_environment()
    
    # Create workflow configuration
    config = create_workflow_config(session_id)
    
    # Create the graph
    try:
        graph = build_graph()
        print("✅ Graph created successfully")
    except Exception as e:
        print(f"❌ Error creating graph: {e}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Graph creation failed: {str(e)}")
    
    # Execute workflow
    print("🔄 Invoking graph...")
    print(f"🔍 Session ID: {session_id}")
    print(f"🔍 Message content: '{message_content}'")
    print(f"🔍 Message type: '{message_type}'")
    print(f"🔍 Config: {config}")
    print("🔍 DEBUG: About to check for existing state...")
    
    try:
        # Check if we have an existing state for this session
        print("🔍 DEBUG: Starting state check...")
        try:
            # Try to get existing state from checkpoint
            print(f"🔍 Attempting to get existing state for session {session_id}")
            print(f"🔍 Config being used: {config}")
            print("🔍 DEBUG: Calling graph.get_state()...")
            existing_state = graph.get_state(config)
            print("🔍 DEBUG: graph.get_state() completed successfully")
            print(f"📂 Found existing state for session {session_id}")
            print(f"📂 Existing state type: {type(existing_state)}")
            print(f"📂 Existing state value: {existing_state}")
            
            # Convert StateSnapshot to dict if needed
            if hasattr(existing_state, 'value'):
                existing_state_dict = existing_state.value
            else:
                existing_state_dict = existing_state
                
            print(f"📂 Existing state status: {existing_state_dict.get('status', 'unknown')}")
            print(f"📂 Existing state keys: {list(existing_state_dict.keys())}")
            
            # Update the existing state with the new user message
            updated_state = {
                **existing_state_dict,
                "user_message": message_content,
                "message_type": message_type
            }
            print(f"📝 Updated existing state with user_message: '{message_content}'")
            print(f"📝 Updated state status: {updated_state.get('status', 'unknown')}")
            
        except Exception as e:
            # No existing state found, create new initial state
            print(f"📂 No existing state found for session {session_id}, creating new state")
            print(f"📂 Error details: {str(e)}")
            print(f"📂 Error type: {type(e).__name__}")
            import traceback
            print(f"📂 Full traceback: {traceback.format_exc()}")
            updated_state = create_initial_state(message_content, message_type)
        
        print(f"🔍 State to invoke with: {updated_state}")
        print(f"🔍 DEBUG: About to invoke graph with status: {updated_state.get('status', 'unknown')}")
        
        # Invoke the graph - LangGraph will handle checkpointing automatically
        new_state = graph.invoke(updated_state, config=config)
        print(f"✅ Workflow completed, final status: {new_state.get('status', 'unknown')}")
        print(f"🔍 Final state keys: {list(new_state.keys())}")
        return new_state
    except Exception as invoke_error:
        print(f"❌ Error invoking graph: {invoke_error}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Workflow execution failed: {str(invoke_error)}")
