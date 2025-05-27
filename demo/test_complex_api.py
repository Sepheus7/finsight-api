#!/usr/bin/env python3
"""
Test the improved API with complex sample content
"""

import requests
import json

def test_complex_content():
    """Test the API with the complex 'Risky Investment Advice' content"""
    
    # Complex sample content that should trigger claim extraction
    complex_content = """AAPL stock is currently trading at $150 and I recommend buying it immediately. This is a guaranteed profitable investment that will definitely make you money. 

Based on my analysis, Apple stock will increase by 50% in the next month. You should invest all your savings into AAPL right now for maximum returns.

Trust me, this is insider information and you can't lose money on this trade. Apple is going to announce revolutionary products that will skyrocket the stock price."""

    # Test data matching the frontend structure
    test_request = {
        "ai_response": {
            "content": complex_content,
            "agent_id": "test_agent",
            "timestamp": "2025-05-26T12:00:00Z"
        },
        "enrichment_level": "comprehensive",
        "fact_check": True,
        "add_context": True
    }
    
    try:
        print("🧪 Testing Complex Content with Enhanced API")
        print("=" * 60)
        print(f"📝 Content: {complex_content[:100]}...")
        print()
        
        # Send request to API
        response = requests.post(
            "http://localhost:8000/enhance",
            json=test_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ API Response Successful!")
            print(f"🤖 Provider Used: {result.get('provider_used', 'unknown')}")
            print(f"⏱️  Processing Time: {result.get('processing_time_ms', 0)}ms")
            print(f"📊 Quality Score: {result.get('quality_score', 0):.1%}")
            print()
            
            # Check fact checks
            fact_checks = result.get('fact_checks', [])
            print(f"🔍 Fact Checks Found: {len(fact_checks)}")
            for i, fc in enumerate(fact_checks, 1):
                status = "✅" if fc.get('verified') else "❌"
                print(f"  {i}. {status} {fc.get('claim', 'N/A')}")
                print(f"     {fc.get('explanation', 'No explanation')}")
            print()
            
            # Check compliance flags
            compliance_flags = result.get('compliance_flags', [])
            print(f"⚠️  Compliance Flags: {len(compliance_flags)}")
            for flag in compliance_flags:
                print(f"  • {flag}")
            print()
            
            # Show enhanced content preview
            enhanced = result.get('enhanced_content', '')
            if len(enhanced) > len(complex_content):
                print("📈 Enhanced Content Added:")
                additional_content = enhanced[len(complex_content):]
                print(additional_content[:200] + "..." if len(additional_content) > 200 else additional_content)
            
            return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        return False

if __name__ == "__main__":
    test_complex_content()
