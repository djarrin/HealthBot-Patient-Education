import json
import os
from typing import Dict, Any, Tuple, Optional

def validate_request(event: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate the incoming request and extract user information.
    
    Returns:
        Tuple of (is_valid, user_info, error_message)
    """
    # Handle health check endpoint
    path = event.get('path', '')
    http_method = event.get('httpMethod', '')
    
    if http_method == 'GET' and ('/health' in path or path.endswith('/health')):
        return True, {'is_health_check': True}, None
    
    # Check authentication
    if 'requestContext' not in event or 'authorizer' not in event['requestContext']:
        return False, None, 'Authentication required'
    
    # Extract user claims
    user_claims = event['requestContext']['authorizer']['claims']
    user_info = {
        'user_id': user_claims['sub'],
        'user_email': user_claims.get('email', ''),
        'is_health_check': False
    }
    
    return True, user_info, None

def validate_message_body(event: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate and extract message body data.
    
    Returns:
        Tuple of (is_valid, message_data, error_message)
    """
    try:
        body = json.loads(event.get('body', '{}'))
        message_content = body.get('message', '').strip()
        session_id = body.get('sessionId')
        message_type = body.get('messageType', 'topic')  # Default to 'topic' for backward compatibility
        
        if not message_content:
            return False, None, 'Message content is required'
        
        # Validate message type
        valid_message_types = ['topic', 'confirmation', 'answer', 'restart']
        if message_type not in valid_message_types:
            return False, None, f'Invalid messageType. Must be one of: {valid_message_types}'
        
        return True, {
            'message_content': message_content,
            'session_id': session_id,
            'message_type': message_type
        }, None
        
    except json.JSONDecodeError:
        return False, None, 'Invalid JSON in request body'

def validate_environment() -> Tuple[bool, Optional[str]]:
    """
    Validate that required environment variables are set.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_env_vars = ['OPENAI_API_KEY', 'TAVILY_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        return False, f'Missing environment variables: {missing_vars}'
    
    return True, None
