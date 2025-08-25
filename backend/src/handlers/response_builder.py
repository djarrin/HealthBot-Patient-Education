import json
from typing import Dict, Any

from .response_types import (
    create_text_response,
    create_confirmation_response,
    create_multiple_choice_response
)

def extract_response_data(new_state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract response data from the workflow state."""
    return {
        'bot_response': new_state.get('bot_message') or "",
        'response_type': new_state.get('response_type', 'text'),
        'multiple_choice': new_state.get('multiple_choice'),
        'confirmation_prompt': new_state.get('confirmation_prompt'),
        'status': new_state.get('status')
    }

def build_response_data(response_data: Dict[str, Any], bot_metadata: Dict[str, str]) -> Dict[str, Any]:
    """Build the response data based on the response type."""
    bot_response = response_data['bot_response']
    response_type = response_data['response_type']
    multiple_choice = response_data['multiple_choice']
    confirmation_prompt = response_data['confirmation_prompt']
    status = response_data['status']
    
    bot_message_id = bot_metadata.get('message_id', '')
    bot_timestamp = bot_metadata.get('timestamp', '')
    
    print(f"🔍 Bot response: {bot_response[:100]}...")
    print(f"🔍 Response type: {response_type}")
    print(f"🔍 Multiple choice: {multiple_choice is not None}")
    print(f"🔍 Confirmation prompt: {confirmation_prompt is not None}")
    
    if response_type == 'multiple_choice' and multiple_choice:
        return create_multiple_choice_response(
            bot_response, bot_message_id, bot_timestamp, 
            status, multiple_choice
        )
    elif response_type == 'confirmation' and confirmation_prompt:
        return create_confirmation_response(
            bot_response, bot_message_id, bot_timestamp,
            status, confirmation_prompt
        )
    else:
        return create_text_response(
            bot_response, bot_message_id, bot_timestamp,
            status
        )

def create_api_response(session_id: str, message_id: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create the final API response."""
    return {
        'sessionId': session_id,
        'messageId': message_id,
        'response': response_data
    }

def create_error_response(status: int, error: str, message: str) -> Dict[str, Any]:
    """Create an error response."""
    return {
        'error': error,
        'message': message
    }

def create_health_response() -> Dict[str, Any]:
    """Create a health check response."""
    return {
        'status': 'healthy',
        'message': 'HealthBot API is running'
    }
