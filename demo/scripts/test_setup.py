#!/usr/bin/env python3
"""
Quick test to verify demo setup is working
"""

import requests
import time
import json

def test_api_server():
    """Test if local API server is responding"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Server: Running")
            return True
        else:
            print(f"❌ API Server: Returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API Server: Not responding - {e}")
        return False

def test_frontend_server():
    """Test if frontend server is responding"""
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend Server: Running")
            return True
        else:
            print(f"❌ Frontend Server: Returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend Server: Not responding - {e}")
        return False

def test_enhance_endpoint():
    """Test the main enhance endpoint"""
    try:
        test_payload = {
            "ai_response": {
                "content": "Apple stock is trading at $150 per share. This is a guaranteed profitable investment.",
                "agent_id": "test_agent"
            },
            "enrichment_level": "standard",
            "fact_check": True,
            "add_context": True
        }
        
        print("🔄 Testing enhance endpoint...")
        response = requests.post(
            "http://localhost:8000/enhance", 
            json=test_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Enhance Endpoint: Working")
            print(f"   📊 Quality Score: {result.get('quality_score', 'N/A')}")
            print(f"   🔍 Fact Checks: {len(result.get('fact_checks', []))}")
            print(f"   ⚡ Processing Time: {result.get('processing_time_ms', 'N/A')}ms")
            return True
        else:
            print(f"❌ Enhance Endpoint: Failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Enhance Endpoint: Error - {e}")
        return False

def main():
    print("🧪 FinSight Demo Health Check")
    print("=" * 40)
    
    # Test API server
    api_ok = test_api_server()
    time.sleep(1)
    
    # Test frontend server  
    frontend_ok = test_frontend_server()
    time.sleep(1)
    
    # Test enhance endpoint if API is running
    enhance_ok = False
    if api_ok:
        enhance_ok = test_enhance_endpoint()
    
    print("\n" + "=" * 40)
    print("📋 Summary:")
    print(f"   API Server: {'✅' if api_ok else '❌'}")
    print(f"   Frontend: {'✅' if frontend_ok else '❌'}")
    print(f"   Enhancement: {'✅' if enhance_ok else '❌'}")
    
    if api_ok and frontend_ok and enhance_ok:
        print("\n🎉 All systems ready for demo!")
        print("🌐 Open: http://localhost:8080/enhanced-demo.html")
    else:
        print("\n⚠️  Some issues detected. Check server startup.")
        if not api_ok:
            print("   • Start API: python api_server.py")
        if not frontend_ok:
            print("   • Start frontend: cd frontend && python -m http.server 8080")

if __name__ == "__main__":
    main()
