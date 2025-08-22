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
    return {"configurable": {"thread_id": session_id}}

def create_initial_state(message_content: str) -> Dict[str, Any]:
    """Create the initial state for the workflow."""
    return {
        "user_message": message_content,
        "status": "collecting_topic"
    }

def execute_workflow(session_id: str, message_content: str) -> Dict[str, Any]:
    """
    Execute the LangGraph workflow.
    
    Returns:
        The final state from the workflow execution
    """
    # Set up environment
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
    
    # Create initial state
    print(f"🔍 Starting workflow for session: {session_id}")
    initial_state = create_initial_state(message_content)
    
    # Execute workflow
    print("🔄 Invoking graph...")
    try:
        new_state = graph.invoke(initial_state, config=config)
        print(f"✅ Workflow completed, final status: {new_state.get('status', 'unknown')}")
        return new_state
    except Exception as invoke_error:
        print(f"❌ Error invoking graph: {invoke_error}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Workflow execution failed: {str(invoke_error)}")
