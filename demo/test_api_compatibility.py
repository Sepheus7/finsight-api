#!/usr/bin/env python3
"""
API Compatibility Checker for FinSight Frontend Integration
"""

import requests
import json
import sys
from datetime import datetime

def test_api_endpoint(base_url="http://localhost:8000"):
    """Test the FinSight API endpoints"""
    
    print("🔍 Testing FinSight API Compatibility")
    print("=" * 40)
    
    # Test health endpoint
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Health endpoint: OK")
        else:
            print(f"❌ Health endpoint: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint: Connection failed - {e}")
        return False
    
    # Test enhance endpoint with sample data
    sample_request = {
        "ai_response": {
            "content": "Apple stock is guaranteed to double in the next month! This is insider information from reliable sources. You should invest all your savings immediately.",
            "agent_id": "test_agent",
            "timestamp": datetime.now().isoformat()
        },
        "enrichment_level": "comprehensive",
        "fact_check": True,
        "add_context": True
    }
    
    try:
        enhance_response = requests.post(
            f"{base_url}/enhance", 
            json=sample_request,
            timeout=30
        )
        
        if enhance_response.status_code == 200:
            result = enhance_response.json()
            print("✅ Enhance endpoint: OK")
            print(f"   - Quality Score: {result.get('quality_score', 'N/A')}")
            print(f"   - Fact Checks: {len(result.get('fact_checks', []))}")
            print(f"   - Compliance Flags: {len(result.get('compliance_flags', []))}")
            print(f"   - Processing Time: {result.get('processing_time_ms', 'N/A')}ms")
            
            # Check if LLM enhancement was used
            if result.get('enhanced_content') != result.get('original_content'):
                print("✅ LLM Enhancement: Active")
            else:
                print("⚠️  LLM Enhancement: May not be active")
                
            return True
        else:
            print(f"❌ Enhance endpoint: {enhance_response.status_code}")
            print(f"   Error: {enhance_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Enhance endpoint: Request failed - {e}")
        return False

def check_server_type(base_url="http://localhost:8000"):
    """Determine which server is running"""
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if "LLM-Enhanced" in response.text:
            return "LLM-Enhanced Server"
        else:
            return "Basic Demo Server"
    except:
        return "Unknown"

def main():
    print("🚀 FinSight API Compatibility Check")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Check which server is running
    server_type = check_server_type()
    print(f"🖥️  Server Type: {server_type}")
    print()
    
    if server_type == "Basic Demo Server":
        print("⚠️  WARNING: You're running the basic demo server!")
        print("   For LLM features, use: python demo/llm_api_server.py")
        print()
    
    # Run API tests
    success = test_api_endpoint()
    
    print()
    print("=" * 40)
    if success:
        print("✅ API is ready for frontend integration!")
        print()
        print("🔗 Frontend Integration Tips:")
        print("1. API Base URL: http://localhost:8000")
        print("2. Main endpoint: POST /enhance")
        print("3. CORS enabled for all origins")
        print("4. Check API docs: http://localhost:8000/docs")
    else:
        print("❌ API not ready. Please start the server first:")
        print("   python demo/llm_api_server.py")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
