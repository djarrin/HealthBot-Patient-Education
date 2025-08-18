import json
import boto3
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

# Import secrets manager utility
from ..utils.secrets_manager import set_secrets_as_env_vars

# LangGraph workflow
from .healthbot_graph import GRAPH

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
chat_sessions_table = dynamodb.Table(os.environ['CHAT_SESSIONS_TABLE'])
user_messages_table = dynamodb.Table(os.environ['USER_MESSAGES_TABLE'])

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        print(f"Received event: {json.dumps(event, default=str)}")
        
        # Handle health check endpoint
        path = event.get('path', '')
        http_method = event.get('httpMethod', '')
        print(f"Request path: {path}, method: {http_method}")
        
        if http_method == 'GET' and ('/health' in path or path.endswith('/health')):
            return _response(200, {'status': 'healthy', 'message': 'HealthBot API is running'})
        
        # For non-health endpoints, check if we have authentication
        if 'requestContext' not in event or 'authorizer' not in event['requestContext']:
            return _response(401, {'error': 'Unauthorized', 'message': 'Authentication required'})
        
        # Load secrets from AWS Secrets Manager and set as environment variables
        print("Loading secrets...")
        secrets = set_secrets_as_env_vars()
        print(f"Loaded secrets keys: {list(secrets.keys())}")
        
        # Debug API key loading
        openai_key = os.environ.get('OPENAI_API_KEY', '')
        print(f"OpenAI API Key loaded: {openai_key[:10] if openai_key else 'NOT_FOUND'}...")
        print(f"OpenAI API Key length: {len(openai_key) if openai_key else 0}")
        
        # Check if required environment variables are set
        required_env_vars = ['OPENAI_API_KEY', 'TAVILY_API_KEY']
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars:
            print(f"Missing required environment variables: {missing_vars}")
            return _response(500, {'error': 'Configuration error', 'message': f'Missing environment variables: {missing_vars}'})
        
        body = json.loads(event.get('body', '{}'))
        message_content = body.get('message', '').strip()
        session_id = body.get('sessionId')

        if not message_content:
            return _response(400, {'error': 'Message content is required'})

        user_claims = event['requestContext']['authorizer']['claims']
        user_id = user_claims['sub']
        user_email = user_claims.get('email', '')

        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            print(f"Generated new session ID: {session_id}")

        now_iso = datetime.now(timezone.utc).isoformat()
        ttl_30d = int(datetime.now(timezone.utc).timestamp()) + (30 * 24 * 60 * 60)

        # Upsert chat session
        chat_sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression='SET userId=:uid, userEmail=:uem, lastActivity=:la, messageCount=if_not_exists(messageCount,:z)+:one, #ttl=:ttl',
            ExpressionAttributeValues={
                ':uid': user_id,
                ':uem': user_email,
                ':la': now_iso,
                ':z': 0,
                ':one': 1,
                ':ttl': ttl_30d
            },
            ExpressionAttributeNames={
                '#ttl': 'ttl'
            }
        )

        # Persist user message
        message_id = str(uuid.uuid4())
        user_messages_table.put_item(Item={
            'sessionId': session_id,
            'timestamp': now_iso,
            'messageId': message_id,
            'userId': user_id,
            'content': message_content,
            'type': 'user',
            'ttl': ttl_30d
        })

        # Set up checkpointing configuration
        config = {"configurable": {"thread_id": session_id}}
        
        # Check if this is a new session or continuing existing session
        try:
            # Try to get existing state
            existing_state = GRAPH.get_state(config=config)
            print(f"Found existing state for session {session_id}")
            
            # Update the state with new user message
            existing_state["user_message"] = message_content
            
            # Continue the workflow from existing state
            new_state = GRAPH.invoke(existing_state, config=config)
            print(f"Continued workflow, new state: {new_state}")
            
        except Exception as e:
            print(f"No existing state found for session {session_id}, starting new workflow: {str(e)}")
            
            # Create initial state for new session
            initial_state = {
                "user_message": message_content,
                "status": "collecting_topic"
            }
            
            # Run the workflow with new state
            new_state = GRAPH.invoke(initial_state, config=config)
            print(f"Started new workflow, new state: {new_state}")

        # Extract bot response from the state
        bot_response = new_state.get('bot_message') or ""

        # Save bot message
        bot_message_id = str(uuid.uuid4())
        bot_timestamp = datetime.now(timezone.utc).isoformat()
        if bot_response:
            user_messages_table.put_item(Item={
                'sessionId': session_id,
                'timestamp': bot_timestamp,
                'messageId': bot_message_id,
                'userId': user_id,
                'content': bot_response,
                'type': 'bot',
                'ttl': ttl_30d
            })

        return _response(200, {
            'sessionId': session_id,
            'messageId': message_id,
            'response': {
                'content': bot_response,
                'messageId': bot_message_id,
                'timestamp': bot_timestamp,
                'status': new_state.get('status')
            }
        })

    except Exception as e:
        print(f"Error processing message: {str(e)}")
        import traceback
        traceback.print_exc()
        return _response(500, {'error': 'Internal server error', 'message': str(e)})


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
