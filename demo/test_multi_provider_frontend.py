#!/usr/bin/env python3
"""
Test script to verify multi-provider functionality from frontend perspective
"""
import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

def test_provider(provider_name, content):
    """Test a specific provider with given content"""
    print(f"\n🧪 Testing {provider_name} provider...")
    print("-" * 50)
    
    payload = {
        "ai_response": {
            "content": content,
            "agent_id": "test_frontend",
            "timestamp": datetime.now().isoformat()
        },
        "enrichment_level": "comprehensive",
        "fact_check": True,
        "add_context": True,
        "llm_provider": provider_name
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(f"{API_BASE_URL}/enhance", json=payload, timeout=60)
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Provider: {result.get('provider_used', 'unknown')}")
            print(f"⚡ Processing Time: {processing_time:.2f}s")
            print(f"📊 Quality Score: {result.get('quality_score', 0):.2f}")
            print(f"🔍 Fact Checks: {len(result.get('fact_checks', []))}")
            print(f"📝 Enhanced Length: {len(result.get('enhanced_content', ''))}")
            
            # Show a snippet of enhanced content
            enhanced = result.get('enhanced_content', '')[:200]
            print(f"📄 Enhanced Preview: {enhanced}...")
            
            return True, result
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

def test_health_endpoint():
    """Test the health endpoint"""
    print("🏥 Testing health endpoint...")
    print("-" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print("✅ Health endpoint working")
            print(f"📡 Providers available:")
            
            for provider, info in health.get('providers', {}).items():
                status = info.get('status', 'unknown')
                model = info.get('model', 'N/A')
                print(f"  - {provider}: {status} ({model})")
                
            return True, health
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False, None

def main():
    """Run all tests"""
    print("🚀 FinSight Multi-Provider Frontend Test Suite")
    print("=" * 60)
    
    # Test health endpoint first
    health_ok, health_data = test_health_endpoint()
    if not health_ok:
        print("❌ Cannot proceed - health endpoint failed")
        return
    
    # Test content for different scenarios
    test_content = {
        "auto": "Bitcoin will definitely reach $100k by next week. Guaranteed profits!",
        "ollama": "Apple stock shows promising growth potential based on recent earnings.",
        "bedrock": "Microsoft Azure cloud services are expanding market share significantly."
    }
    
    results = {}
    
    # Test each provider
    for provider in ["auto", "ollama", "bedrock"]:
        success, result = test_provider(provider, test_content[provider])
        results[provider] = (success, result)
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n📋 TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = sum(1 for success, _ in results.values() if success)
    total_tests = len(results)
    
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    
    for provider, (success, result) in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        provider_used = result.get('provider_used', 'N/A') if result else 'N/A'
        print(f"  {provider.upper()}: {status} (used: {provider_used})")
    
    if successful_tests == total_tests:
        print("\n🎉 All tests passed! Multi-provider system is working correctly.")
        print("🌐 Frontend can now switch between Ollama, Bedrock, and auto mode.")
    else:
        print(f"\n⚠️  {total_tests - successful_tests} test(s) failed. Check the logs above.")

if __name__ == "__main__":
    main()
