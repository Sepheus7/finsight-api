#!/usr/bin/env python3

import boto3
import json
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import sys

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

def make_request(method, endpoint, data=None):
    """Make an authenticated request to the API"""
    base_url = "https://jfho5me3zi.execute-api.us-east-1.amazonaws.com/dev"
    url = f"{base_url}{endpoint}"
    
    try:
        headers, body = sign_request(method, url, data)
        response = requests.request(method, url, headers=headers, data=body)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        sys.exit(1)

def main():
    """Main function to test API endpoints"""
    print("🧪 FinSight API Test Client")
    print("===========================")
    
    # Test health endpoint
    print("\n📊 Testing health endpoint...")
    health = make_request('GET', '/health')
    print(json.dumps(health, indent=2))
    
    # Test root endpoint
    print("\n📊 Testing root endpoint...")
    root = make_request('GET', '/')
    print(json.dumps(root, indent=2))
    
    # Test fact check endpoint
    print("\n📊 Testing fact check endpoint...")
    fact_check_data = {
        "text": "Apple Inc. reported record quarterly revenue of $123.9 billion in Q4 2024, representing a 15% increase year-over-year.",
        "enhanced": True
    }
    fact_check = make_request('POST', '/fact-check', fact_check_data)
    print(json.dumps(fact_check, indent=2))

if __name__ == "__main__":
    main() 