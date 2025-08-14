import json
import boto3
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
chat_sessions_table = dynamodb.Table(os.environ['CHAT_SESSIONS_TABLE'])
user_messages_table = dynamodb.Table(os.environ['USER_MESSAGES_TABLE'])
session_state_table = dynamodb.Table(os.environ['SESSION_STATE_TABLE'])

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
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

        # Load current session state (if any)
        state_resp = session_state_table.get_item(Key={'sessionId': session_id})
        state = state_resp.get('Item') or {
            'sessionId': session_id,
            'version': 0,
            'status': 'collecting_topic',
            'ttl': ttl_30d
        }

        # Placeholder logic advancing state; LangGraph will update these fields
        if state.get('status') == 'collecting_topic':
            state.update({'topic': message_content, 'status': 'summarizing'})
        else:
            state.update({'lastUserMessage': message_content})

        state['version'] = state.get('version', 0) + 1
        state['updatedAt'] = now_iso

        session_state_table.put_item(Item=state)

        bot_response = f"I received your message: '{message_content}'. This is a placeholder response. AI integration coming soon!"

        bot_message_id = str(uuid.uuid4())
        bot_timestamp = datetime.now(timezone.utc).isoformat()
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
                'timestamp': bot_timestamp
            }
        })

    except Exception as e:
        print(f"Error processing message: {str(e)}")
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
