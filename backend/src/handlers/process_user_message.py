import json
from typing import Dict, Any

# Import our modular components
from .request_validator import validate_request, validate_message_body, validate_environment
from .session_manager import generate_session_id, upsert_chat_session, save_user_message, save_bot_message
from .workflow_engine import execute_workflow
from .response_builder import (
    extract_response_data, 
    build_response_data, 
    create_api_response, 
    create_error_response, 
    create_health_response
)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        print(f"🚀 Handler started")
        print(f"📝 Received event: {json.dumps(event, default=str)}")
        
        # Validate request and extract user info
        is_valid, user_info, error_msg = validate_request(event)
        if not is_valid:
            return _response(401, create_error_response(401, 'Unauthorized', error_msg))
        
        # Handle health check
        if user_info.get('is_health_check'):
            return _response(200, create_health_response())
        
        # Validate environment
        env_valid, env_error = validate_environment()
        if not env_valid:
            return _response(500, create_error_response(500, 'Configuration error', env_error))
        
        # Validate message body
        body_valid, message_data, body_error = validate_message_body(event)
        if not body_valid:
            return _response(400, create_error_response(400, 'Bad Request', body_error))
        
        message_content = message_data['message_content']
        session_id = message_data['session_id']
        user_id = user_info['user_id']
        user_email = user_info['user_email']
        
        print(f"📨 Message content: '{message_content}'")
        print(f"🆔 Session ID: '{session_id}'")
        
        # Generate session ID if not provided
        if not session_id:
            session_id = generate_session_id()
            print(f"Generated new session ID: {session_id}")
        
        # Manage session and save user message
        upsert_chat_session(session_id, user_id, user_email)
        message_id = save_user_message(session_id, user_id, message_content)
        
        # Execute workflow
        try:
            new_state = execute_workflow(session_id, message_content)
        except Exception as workflow_error:
            return _response(500, create_error_response(500, 'Workflow execution failed', str(workflow_error)))
        
        # Extract and build response
        response_data = extract_response_data(new_state)
        bot_metadata = save_bot_message(session_id, user_id, response_data['bot_response'])
        final_response_data = build_response_data(response_data, bot_metadata)
        
        # Create API response
        api_response = create_api_response(session_id, message_id, final_response_data)
        
        print(f"🔍 Response data keys: {list(api_response.keys())}")
        print(f"🔍 About to return response...")
        
        return _response(200, api_response)
        
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        import traceback
        traceback.print_exc()
        return _response(500, create_error_response(500, 'Internal server error', str(e)))


def _response(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }
