import boto3
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
chat_sessions_table = dynamodb.Table(os.environ['CHAT_SESSIONS_TABLE'])
user_messages_table = dynamodb.Table(os.environ['USER_MESSAGES_TABLE'])

def generate_session_id() -> str:
    """Generate a new session ID."""
    return str(uuid.uuid4())

def get_ttl_timestamp() -> int:
    """Get TTL timestamp for 30 days from now."""
    return int(datetime.now(timezone.utc).timestamp()) + (30 * 24 * 60 * 60)

def get_current_timestamp() -> str:
    """Get current ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()

def upsert_chat_session(session_id: str, user_id: str, user_email: str) -> None:
    """Upsert chat session in DynamoDB."""
    now_iso = get_current_timestamp()
    ttl_30d = get_ttl_timestamp()
    
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

def save_user_message(session_id: str, user_id: str, message_content: str) -> str:
    """Save user message to DynamoDB and return message ID."""
    message_id = str(uuid.uuid4())
    now_iso = get_current_timestamp()
    ttl_30d = get_ttl_timestamp()
    
    user_messages_table.put_item(Item={
        'sessionId': session_id,
        'timestamp': now_iso,
        'messageId': message_id,
        'userId': user_id,
        'content': message_content,
        'type': 'user',
        'ttl': ttl_30d
    })
    
    return message_id

def save_bot_message(session_id: str, user_id: str, bot_response: str) -> Dict[str, str]:
    """Save bot message to DynamoDB and return message metadata."""
    if not bot_response:
        return {}
    
    bot_message_id = str(uuid.uuid4())
    bot_timestamp = get_current_timestamp()
    ttl_30d = get_ttl_timestamp()
    
    user_messages_table.put_item(Item={
        'sessionId': session_id,
        'timestamp': bot_timestamp,
        'messageId': bot_message_id,
        'userId': user_id,
        'content': bot_response,
        'type': 'bot',
        'ttl': ttl_30d
    })
    
    return {
        'message_id': bot_message_id,
        'timestamp': bot_timestamp
    }
