import json
import boto3
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

# Import secrets manager utility
from ..utils.secrets_manager import set_secrets_as_env_vars

# LangGraph workflow
from .healthbot_graph import build_graph
from .response_types import (
    create_text_response,
    create_confirmation_response,
    create_multiple_choice_response
)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
chat_sessions_table = dynamodb.Table(os.environ['CHAT_SESSIONS_TABLE'])
user_messages_table = dynamodb.Table(os.environ['USER_MESSAGES_TABLE'])

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        print(f"🚀 Handler started")
        print(f"📝 Received event: {json.dumps(event, default=str)}")
        
        # Handle health check endpoint
        path = event.get('path', '')
        http_method = event.get('httpMethod', '')
        print(f"🔍 Request path: {path}, method: {http_method}")
        
        if http_method == 'GET' and ('/health' in path or path.endswith('/health')):
            return _response(200, {'status': 'healthy', 'message': 'HealthBot API is running'})
        
        # For non-health endpoints, check if we have authentication
        if 'requestContext' not in event or 'authorizer' not in event['requestContext']:
            return _response(401, {'error': 'Unauthorized', 'message': 'Authentication required'})
        
        # Load secrets from AWS Secrets Manager and set as environment variables
        print("🔐 Loading secrets...")
        secrets = set_secrets_as_env_vars()
        print(f"✅ Loaded secrets keys: {list(secrets.keys())}")
        
        # Debug API key loading
        openai_key = os.environ.get('OPENAI_API_KEY', '')
        print(f"🔑 OpenAI API Key loaded: {openai_key[:10] if openai_key else 'NOT_FOUND'}...")
        print(f"🔑 OpenAI API Key length: {len(openai_key) if openai_key else 0}")
        
        # Check if required environment variables are set
        required_env_vars = ['OPENAI_API_KEY', 'TAVILY_API_KEY']
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars:
            print(f"❌ Missing required environment variables: {missing_vars}")
            return _response(500, {'error': 'Configuration error', 'message': f'Missing environment variables: {missing_vars}'})
        
        body = json.loads(event.get('body', '{}'))
        message_content = body.get('message', '').strip()
        session_id = body.get('sessionId')
        
        print(f"📨 Message content: '{message_content}'")
        print(f"🆔 Session ID: '{session_id}'")

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
        
        # Create the graph once for this request
        try:
            graph = build_graph()
            print("✅ Graph created successfully")
        except Exception as e:
            print(f"❌ Error creating graph: {e}")
            import traceback
            traceback.print_exc()
            return _response(500, {'error': 'Graph creation failed', 'message': str(e)})
        
        # Try to get existing state
        print(f"🔍 Attempting to get existing state for session: {session_id}")
        print(f"🔍 Config: {config}")
        
        try:
            existing_state = graph.get_state(config=config)
            print(f"✅ Found existing state for session {session_id}")
            print(f"🔍 Existing state type: {type(existing_state)}")
            print(f"🔍 Existing state keys: {list(existing_state.keys()) if hasattr(existing_state, 'keys') else 'No keys'}")
            
            # Convert state snapshot to dict if needed
            if hasattr(existing_state, 'get'):
                state_dict = existing_state
            else:
                print(f"🔍 Converting state to dict...")
                print(f"🔍 Existing state type: {type(existing_state)}")
                print(f"🔍 Existing state repr: {repr(existing_state)}")
                
                # Handle different state object types
                if hasattr(existing_state, '__dict__'):
                    state_dict = existing_state.__dict__
                elif hasattr(existing_state, 'dict'):
                    state_dict = existing_state.dict()
                elif hasattr(existing_state, 'model_dump'):
                    state_dict = existing_state.model_dump()
                else:
                    # Try to convert to dict, but handle the error gracefully
                    try:
                        state_dict = dict(existing_state)
                    except (ValueError, TypeError) as conv_error:
                        print(f"❌ Error converting state to dict: {conv_error}")
                        print(f"🔍 Trying alternative conversion methods...")
                        
                        # If it's a sequence, try to convert it differently
                        if hasattr(existing_state, '__iter__'):
                            try:
                                state_dict = {k: v for k, v in existing_state}
                            except Exception:
                                # Last resort: create a new state
                                print(f"❌ Could not convert state, creating new state")
                                state_dict = {"user_message": message_content, "status": "collecting_topic"}
                        else:
                            # Last resort: create a new state
                            print(f"❌ Could not convert state, creating new state")
                            state_dict = {"user_message": message_content, "status": "collecting_topic"}
            
            print(f"🔍 State dict keys: {list(state_dict.keys())}")
            print(f"🔍 Current status: {state_dict.get('status', 'unknown')}")
            
            # Update the state with new user message
            state_dict["user_message"] = message_content
            
            # Continue the workflow from existing state
            print("🔄 Invoking graph with existing state...")
            new_state = graph.invoke(state_dict, config=config)
            print(f"✅ Continued workflow, new state status: {new_state.get('status', 'unknown')}")
            
        except Exception as state_error:
            print(f"❌ Error getting existing state: {state_error}")
            print(f"🔍 State error type: {type(state_error)}")
            import traceback
            traceback.print_exc()
            raise state_error
            
    except Exception as e:
        print(f"❌ No existing state found for session {session_id}, starting new workflow: {str(e)}")
        print(f"🔍 Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        
        # Create initial state for new session
        initial_state = {
            "user_message": message_content,
            "status": "collecting_topic"
        }
        
        # Run the workflow with new state
        print("🔄 Invoking graph with new state...")
        print(f"🔍 Initial state: {initial_state}")
        try:
            new_state = graph.invoke(initial_state, config=config)
            print(f"✅ Started new workflow, new state status: {new_state.get('status', 'unknown')}")
            print(f"🔍 New state keys: {list(new_state.keys()) if hasattr(new_state, 'keys') else 'No keys'}")
        except Exception as invoke_error:
            print(f"❌ Error invoking graph: {invoke_error}")
            import traceback
            traceback.print_exc()
            return _response(500, {'error': 'Workflow execution failed', 'message': str(invoke_error)})

        # Extract bot response from the state
        bot_response = new_state.get('bot_message') or ""
        response_type = new_state.get('response_type', 'text')
        multiple_choice = new_state.get('multiple_choice')
        confirmation_prompt = new_state.get('confirmation_prompt')

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

        # Build response object based on type
        if response_type == 'multiple_choice' and multiple_choice:
            response_data = create_multiple_choice_response(
                bot_response, bot_message_id, bot_timestamp, 
                new_state.get('status'), multiple_choice
            )
        elif response_type == 'confirmation' and confirmation_prompt:
            response_data = create_confirmation_response(
                bot_response, bot_message_id, bot_timestamp,
                new_state.get('status'), confirmation_prompt
            )
        else:
            response_data = create_text_response(
                bot_response, bot_message_id, bot_timestamp,
                new_state.get('status')
            )

        return _response(200, {
            'sessionId': session_id,
            'messageId': message_id,
            'response': response_data
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
