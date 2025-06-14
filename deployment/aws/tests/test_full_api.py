#!/usr/bin/env python3

"""
Complete FinSight Bedrock API Test with Proper Request Bodies
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

def test_fact_check_with_proper_data():
    """Test fact-check endpoint with proper financial content"""
    api_url = "https://jfho5me3zi.execute-api.us-east-1.amazonaws.com/dev"
    
    print("🧪 FinSight Bedrock API - Comprehensive Test")
    print("=============================================")
    print(f"🔗 API Endpoint: {api_url}")
    print()
    
    # Test data with financial claims
    test_payload = {
        "advice": "Apple stock (AAPL) has risen 15% this quarter and is expected to continue growing due to strong iPhone sales. Tesla (TSLA) is also performing well with a 20% increase in delivery numbers.",
        "context": "Financial market analysis for Q1 2025",
        "enable_llm": True,
        "enable_context_enrichment": True
    }
    
    print("📊 Test: Enhanced Fact Check with Financial Claims")
    print("-" * 50)
    print(f"📋 Test Payload: {json.dumps(test_payload, indent=2)}")
    print()
    
    try:
        headers, body = sign_request('POST', f'{api_url}/fact-check', test_payload)
        print("🔒 Request signed with AWS credentials")
        
        response = requests.post(f'{api_url}/fact-check', headers=headers, data=body)
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Response:")
            print(json.dumps(result, indent=2))
            
            # Check for expected fields
            expected_fields = ['claims', 'verification_results', 'enriched_context', 'quality_score']
            for field in expected_fields:
                if field in result:
                    print(f"  ✅ {field}: Found")
                else:
                    print(f"  ❌ {field}: Missing")
                    
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        
    print()
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_fact_check_with_proper_data()
