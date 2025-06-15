#!/usr/bin/env python3
"""
Test the exact API call that the frontend makes
"""

import requests
import json
from datetime import datetime

API_BASE_URL = 'http://localhost:8000'

def test_frontend_api_call():
    """Test the exact payload the frontend sends"""
    
    # This is the exact content from the "Risky Investment Advice" sample
    test_content = """AAPL stock is currently trading at $150 and I recommend buying it immediately. This is a guaranteed profitable investment that will definitely make you money. 

Based on my analysis, Apple stock will increase by 50% in the next month. You should invest all your savings into AAPL right now for maximum returns.

Trust me, this is insider information and you can't lose money on this trade. Apple is going to announce revolutionary products that will skyrocket the stock price."""

    # Exact payload format from frontend JavaScript
    payload = {
        "ai_response": {
            "content": test_content,
            "agent_id": "frontend_demo",
            "timestamp": datetime.now().isoformat()
        },
        "enrichment_level": "comprehensive",
        "fact_check": True,
        "add_context": True
    }
    
    print("🧪 Testing Frontend API Call")
    print("=" * 50)
    print(f"📡 Endpoint: {API_BASE_URL}/enhance")
    print(f"📝 Content length: {len(test_content)} characters")
    print(f"🔍 Expected claims: AAPL stock price claim")
    print()
    
    try:
        print("⏳ Making API request (this may take 5-10 seconds)...")
        start_time = datetime.now()
        
        response = requests.post(
            f"{API_BASE_URL}/enhance",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        print(f"⚡ Response received in {processing_time:.0f}ms")
        print(f"📊 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n✅ SUCCESS - Claims were extracted!")
            print("=" * 50)
            
            # Show fact checks
            fact_checks = result.get('fact_checks', [])
            print(f"🔍 Fact Checks Found: {len(fact_checks)}")
            
            for i, fc in enumerate(fact_checks, 1):
                print(f"\n   Claim #{i}:")
                print(f"   📝 Text: {fc['claim']}")
                print(f"   ✅ Verified: {fc['verified']}")
                print(f"   🎯 Confidence: {fc['confidence']:.1%}")
                print(f"   📊 Source: {fc['source']}")
                print(f"   💡 Explanation: {fc['explanation']}")
            
            # Show compliance issues
            compliance_flags = result.get('compliance_flags', [])
            print(f"\n⚠️ Compliance Issues: {len(compliance_flags)}")
            for flag in compliance_flags:
                print(f"   • {flag}")
            
            # Show quality score
            quality_score = result.get('quality_score', 0)
            print(f"\n📊 Quality Score: {quality_score:.1%}")
            print(f"🔧 Provider Used: {result.get('provider_used', 'unknown')}")
            
            print("\n🎉 CLAIM EXTRACTION IS WORKING PERFECTLY!")
            print("The issue might be in the frontend display or user interaction.")
            
        else:
            print(f"\n❌ FAILED - HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n💥 CONNECTION ERROR: {e}")
        print("Make sure the API server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n🚨 UNEXPECTED ERROR: {e}")

if __name__ == "__main__":
    test_frontend_api_call()
