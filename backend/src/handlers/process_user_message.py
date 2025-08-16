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

def get_thread_state(thread_id: str) -> Dict[str, Any]:
    """
    Get the current state of a thread using LangGraph's checkpointing system.
    Similar to the demo's graph.get_state() but for our DynamoDB-backed graph.
    """
    try:
        # Get the current state from the graph's checkpointing system
        config = {"configurable": {"thread_id": thread_id}}
        state = GRAPH.get_state(config=config)
        return state
    except Exception as e:
        print(f"Error getting thread state: {str(e)}")
        return {}

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        # Load secrets from AWS Secrets Manager and set as environment variables
        set_secrets_as_env_vars()
        
        body = json.loads(event.get('body', '{}'))
        message_content = body.get('message', '').strip()
        session_id = body.get('sessionId')

        if not message_content:
            return _response(400, {'error': 'Message content is required'})

        user_claims = event['requestContext']['authorizer']['claims']
        user_id = user_claims['sub']
        user_email = user_claims.get('email', '')

        if not session_id:
            session_id = str(uuid.uuid4())

        now_iso = datetime.now(timezone.utc).isoformat()
        ttl_30d = int(datetime.now(timezone.utc).timestamp()) + (30 * 24 * 60 * 60)

        # Upsert chat session
        chat_sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression='SET userId=:uid, userEmail=:uem, lastActivity=:la, messageCount=if_not_exists(messageCount,:z)+:one, ttl=:ttl',
            ExpressionAttributeValues={
                ':uid': user_id,
                ':uem': user_email,
                ':la': now_iso,
                ':z': 0,
                ':one': 1,
                ':ttl': ttl_30d
            }
        )

        # Persist user message with PK(sessionId), SK(timestamp)
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

        # Use thread-based checkpointing instead of manual state management
        # The session_id becomes the thread_id for checkpointing
        config = {"configurable": {"thread_id": session_id}}
        
        # Create initial state with the user message
        initial_state = {
            "user_message": message_content,
            "status": "collecting_topic"
        }
        
        # Run the graph with thread-based checkpointing
        new_state = GRAPH.invoke(initial_state, config=config)

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

        # Optional: Get the full thread state for debugging/logging
        # This shows how to query the checkpointed state, similar to the demo
        thread_state = get_thread_state(session_id)
        print(f"Thread state for {session_id}: {thread_state}")

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
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        },
        'body': json.dumps(body)
    }
