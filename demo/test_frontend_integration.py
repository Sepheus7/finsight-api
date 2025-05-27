#!/usr/bin/env python3
"""
FinSight Frontend Integration Test
Tests that the frontend can successfully communicate with the LLM server
"""

import requests
import json
import time
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test health endpoint"""
    print("🔍 Testing Health Endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health endpoint working")
            print(f"   Status: {health_data.get('status')}")
            print(f"   LLM Status: {health_data.get('llm_status')}")
            print(f"   Fallback: {health_data.get('fallback', 'None')}")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_enhance_endpoint():
    """Test enhance endpoint with sample financial content"""
    print("\n🔍 Testing Enhance Endpoint...")
    
    test_content = """
    Apple (AAPL) is currently trading at $150.00 and represents a guaranteed investment opportunity. 
    The stock will definitely increase by 30% next quarter based on strong fundamentals.
    Tesla (TSLA) is priced at $200.00 and is showing excellent growth potential.
    """
    
    payload = {
        "ai_response": {
            "content": test_content.strip(),
            "agent_id": "integration_test",
            "timestamp": datetime.now().isoformat()
        },
        "enrichment_level": "comprehensive",
        "fact_check": True,
        "add_context": True
    }
    
    try:
        print("📤 Sending request...")
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE_URL}/enhance", 
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Enhance endpoint working")
            print(f"   Processing time: {processing_time:.2f}s")
            print(f"   Server processing: {result.get('processing_time_ms', 0)}ms")
            print(f"   Provider used: {result.get('provider_used', 'unknown')}")
            print(f"   Quality score: {result.get('quality_score', 0):.2f}")
            print(f"   Fact checks: {len(result.get('fact_checks', []))}")
            print(f"   Compliance flags: {len(result.get('compliance_flags', []))}")
            
            # Show fact check results
            if result.get('fact_checks'):
                print("\n📊 Fact Check Results:")
                for i, fact in enumerate(result['fact_checks'], 1):
                    status = "✅" if fact['verified'] else "❌"
                    print(f"   {i}. {status} {fact['claim']}")
                    print(f"      Confidence: {fact['confidence']:.1%}")
                    print(f"      Explanation: {fact['explanation']}")
            
            # Show compliance issues
            if result.get('compliance_flags'):
                print("\n⚠️  Compliance Issues:")
                for flag in result['compliance_flags']:
                    print(f"   • {flag}")
            
            return True
        else:
            print(f"❌ Enhance endpoint failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Enhance endpoint error: {e}")
        return False

def test_cors_headers():
    """Test CORS headers for frontend compatibility"""
    print("\n🔍 Testing CORS Headers...")
    try:
        response = requests.options(f"{API_BASE_URL}/enhance")
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
        }
        
        print("✅ CORS headers present:")
        for header, value in cors_headers.items():
            if value:
                print(f"   {header}: {value}")
        
        return True
    except Exception as e:
        print(f"❌ CORS test error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 FinSight Frontend Integration Test")
    print("=" * 50)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run tests
    tests = [
        test_health_endpoint,
        test_enhance_endpoint,
        test_cors_headers
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print(f"🎯 Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ Frontend integration ready!")
        print("\n📝 Next Steps:")
        print("1. Open the frontend in a browser: frontend/enhanced-demo-clean.html")
        print("2. Try enhancing some financial content")
        print("3. Verify fact-checking and compliance features work")
    else:
        print("❌ Some tests failed. Check the server and try again.")
    
    return passed == total

if __name__ == "__main__":
    main()
