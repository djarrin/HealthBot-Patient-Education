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
        
        # For local development, bypass authentication if running offline
        is_local = os.getenv('IS_OFFLINE') == 'true'
        
        # For non-health endpoints, check if we have authentication (unless running locally)
        if not is_local and ('requestContext' not in event or 'authorizer' not in event['requestContext']):
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

        # Get user info - use mock data for local development
        if is_local:
            user_id = body.get('userId', 'test-user-123')
            user_email = body.get('userEmail', 'test@example.com')
        else:
            user_claims = event['requestContext']['authorizer']['claims']
            user_id = user_claims['sub']
            user_email = user_claims.get('email', '')

        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            print(f"Generated new session ID: {session_id}")

        now_iso = datetime.now(timezone.utc).isoformat()
        ttl_30d = int(datetime.now(timezone.utc).timestamp()) + (30 * 24 * 60 * 60)

        # Skip DynamoDB operations for local development
        if not is_local:
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
        else:
            # For local development, just generate a message ID
            message_id = str(uuid.uuid4())
            print(f"Local development: Skipping DynamoDB operations for session {session_id}")

        # Set up checkpointing configuration
        checkpoint_config = {
            'configurable': {
                'thread_id': session_id,
                'user_id': user_id
            }
        }

        # Run the LangGraph workflow
        print(f"Running LangGraph workflow for session: {session_id}")
        result = GRAPH.invoke(
            {
                'user_message': message_content,
                'session_id': session_id,
                'user_id': user_id
            },
            checkpoint_config
        )

        # Extract the response from the result
        print(f"LangGraph result keys: {list(result.keys())}")
        print(f"LangGraph result: {result}")
        
        # The response should be in bot_message based on our workflow
        if 'bot_message' in result:
            response_content = result['bot_message']
        elif 'messages' in result and result['messages']:
            # Fallback to messages format
            assistant_messages = [msg for msg in result['messages'] if msg.get('role') == 'assistant']
            if assistant_messages:
                response_content = assistant_messages[-1].get('content', '')
            else:
                response_content = "I'm sorry, I couldn't generate a response at this time."
        else:
            response_content = "I'm sorry, I couldn't generate a response at this time."

        # Persist assistant response (skip for local development)
        assistant_message_id = str(uuid.uuid4())
        if not is_local:
            user_messages_table.put_item(Item={
                'sessionId': session_id,
                'timestamp': now_iso,
                'messageId': assistant_message_id,
                'userId': user_id,
                'content': response_content,
                'type': 'assistant',
                'ttl': ttl_30d
            })
        else:
            print(f"Local development: Skipping assistant message persistence for session {session_id}")

        return _response(200, {
            'message': response_content,
            'sessionId': session_id,
            'messageId': assistant_message_id
        })

    except Exception as e:
        print(f"Error in handler: {str(e)}")
        import traceback
        traceback.print_exc()
        return _response(500, {'error': 'Internal server error', 'message': str(e)})

def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to create API Gateway response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }
