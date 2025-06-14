#!/usr/bin/env python3

"""
FinSight Bedrock API Test Script
Tests the deployed AWS API with proper IAM authentication using boto3
"""

import boto3
import json
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import time

def sign_request(method, url, data=None, headers=None):
    """Sign AWS API Gateway request with SigV4"""
    session = boto3.Session()
    credentials = session.get_credentials()
    region = 'us-east-1'
    service = 'execute-api'
    
    if headers is None:
        headers = {}
    
    if data:
        headers['Content-Type'] = 'application/json'
        body = json.dumps(data)
    else:
        body = ''
    
    request = AWSRequest(method=method, url=url, data=body, headers=headers)
    SigV4Auth(credentials, service, region).add_auth(request)
    
    return dict(request.headers), body

def test_api():
    """Test the FinSight Bedrock API"""
    api_url = "https://jfho5me3zi.execute-api.us-east-1.amazonaws.com/dev"
    
    print("🧪 FinSight Bedrock API Test Suite")
    print("==================================")
    print(f"🔗 API Endpoint: {api_url}")
    print()
    
    # Test 1: Health Check
    print("📊 Test 1: Health Check")
    print("----------------------")
    try:
        headers, body = sign_request('GET', f'{api_url}/health')
        response = requests.get(f'{api_url}/health', headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # Test 2: Root endpoint
    print("📊 Test 2: API Information")
    print("--------------------------")
    try:
        headers, body = sign_request('GET', f'{api_url}/')
        response = requests.get(f'{api_url}/', headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Service: {data.get('message', 'N/A')}")
            print(f"Version: {data.get('version', 'N/A')}")
            print(f"Endpoints: {len(data.get('endpoints', {}))}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # Test 3: Enhanced Fact Check with Bedrock
    print("📊 Test 3: Enhanced Fact Check (Bedrock)")
    print("---------------------------------------")
    try:
        test_data = {
            "text": "Apple Inc. reported record quarterly revenue of $123.9 billion in Q4 2024, representing a 15% increase year-over-year.",
            "enhanced": True
        }
        headers, body = sign_request('POST', f'{api_url}/fact-check', test_data)
        response = requests.post(f'{api_url}/fact-check', headers=headers, data=body)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Enhanced: {result.get('enhanced', False)}")
            print(f"Claims Found: {len(result.get('claims', []))}")
            print(f"LLM Provider: {result.get('llm_provider', 'N/A')}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    print("✅ Bedrock API testing complete!")

if __name__ == "__main__":
    test_api()
