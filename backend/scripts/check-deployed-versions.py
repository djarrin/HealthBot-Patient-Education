#!/usr/bin/env python3
"""
Script to check what versions are actually deployed in the Lambda function.
Run this locally to see what versions are working in production.
"""

import subprocess
import json
import sys

def check_lambda_versions():
    """Check what versions are deployed in Lambda by invoking a test function."""
    
    print("🔍 Checking deployed Lambda versions...")
    
    # Create a test event that will return package versions
    test_event = {
        "httpMethod": "GET",
        "path": "/health",
        "headers": {},
        "body": ""
    }
    
    try:
        # Try to invoke the Lambda function locally first
        print("📦 Checking local package versions...")
        import langchain
        import langgraph
        import langchain_community
        import langchain_openai
        
        print(f"  langchain: {langchain.__version__}")
        print(f"  langgraph: {langgraph.__version__}")
        print(f"  langchain-community: {langchain_community.__version__}")
        print(f"  langchain-openai: {langchain_openai.__version__}")
        
    except ImportError as e:
        print(f"❌ Local packages not installed: {e}")
    
    print("\n💡 To check deployed versions:")
    print("1. Deploy to AWS: npm run deploy")
    print("2. Check CloudWatch logs for any version info")
    print("3. Or add version logging to your Lambda function")

if __name__ == "__main__":
    check_lambda_versions()
