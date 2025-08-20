import json
import boto3
import os
from typing import Dict, Any

def get_secrets() -> Dict[str, str]:
    """
    Retrieve secrets from AWS Secrets Manager and return them as a dictionary.
    This function should be called at the beginning of Lambda function execution.
    """
    try:
        # Get the secret name from environment variable or use default
        secret_name = os.environ.get('SECRETS_NAME', 'healthbot-backend-secrets-dev')
        
        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        # Get the secret value
        response = client.get_secret_value(SecretId=secret_name)
        
        # Parse the secret string
        if 'SecretString' in response:
            secret_string = response['SecretString']
            secrets = json.loads(secret_string)
            return secrets
        else:
            raise Exception("Secret not found in SecretString")
            
    except Exception as e:
        print(f"Error retrieving secrets: {str(e)}")
        # Return empty dict if secrets can't be retrieved
        return {}

def set_secrets_as_env_vars():
    """
    Retrieve secrets from AWS Secrets Manager and set them as environment variables.
    This function should be called at the beginning of Lambda function execution.
    """
    # Check if running locally (serverless-offline sets this)
    if os.getenv('IS_OFFLINE') == 'true':
        # For local development, use environment variables directly
        print("Running locally - using environment variables for secrets")
        secrets = {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
        }
        
        # Set any missing secrets as environment variables
        for key, value in secrets.items():
            if value:
                os.environ[key] = value
                print(f"Set environment variable: {key}")
        
        return secrets
    else:
        # In production, load from AWS Secrets Manager
        secrets = get_secrets()
        
        for key, value in secrets.items():
            if value:  # Only set if value is not empty
                os.environ[key] = value
                print(f"Set environment variable: {key}")
        
        return secrets
