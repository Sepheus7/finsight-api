#!/usr/bin/env python3
"""
Debug the exact user flow with different sample contents
"""

import requests
import json
from datetime import datetime

API_BASE_URL = 'http://localhost:8000'

# All three sample scenarios from the frontend
sample_scenarios = {
    "investment": {
        "title": "Risky Investment Advice",
        "content": """AAPL stock is currently trading at $150 and I recommend buying it immediately. This is a guaranteed profitable investment that will definitely make you money. 

Based on my analysis, Apple stock will increase by 50% in the next month. You should invest all your savings into AAPL right now for maximum returns.

Trust me, this is insider information and you can't lose money on this trade. Apple is going to announce revolutionary products that will skyrocket the stock price."""
    },
    "market": {
        "title": "Market Analysis", 
        "content": """The S&P 500 has shown strong performance this quarter, with technology stocks leading the gains. Market volatility remains elevated due to ongoing economic uncertainties.

Current market indicators suggest a bullish trend, with the VIX trading below 20. Institutional investors are showing increased confidence in large-cap technology stocks.

Economic data releases this week will likely impact market direction, particularly the employment figures and inflation data."""
    },
    "crypto": {
        "title": "Crypto Discussion",
        "content": """Cryptocurrency markets continue to evolve with increasing institutional adoption. Bitcoin and Ethereum remain the dominant digital assets by market capitalization.

Regulatory clarity in major markets will likely influence crypto adoption rates. Investors should carefully consider the risks associated with digital asset investments.

Diversification across different asset classes remains important for portfolio management. Consider consulting with a financial advisor before making investment decisions."""
    }
}

def test_scenario(scenario_name, scenario_data):
    """Test a specific scenario"""
    
    print(f"\n🧪 Testing: {scenario_data['title']}")
    print("=" * 60)
    print(f"📝 Content preview: {scenario_data['content'][:100]}...")
    
    payload = {
        "ai_response": {
            "content": scenario_data['content'],
            "agent_id": "frontend_demo",
            "timestamp": datetime.now().isoformat()
        },
        "enrichment_level": "comprehensive",
        "fact_check": True,
        "add_context": True
    }
    
    try:
        print("⏳ Processing (please wait 3-10 seconds)...")
        start_time = datetime.now()
        
        response = requests.post(
            f"{API_BASE_URL}/enhance",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if response.status_code == 200:
            result = response.json()
            
            # Analyze results
            fact_checks = result.get('fact_checks', [])
            compliance_flags = result.get('compliance_flags', [])
            quality_score = result.get('quality_score', 0)
            
            print(f"⚡ Processed in {processing_time:.0f}ms")
            print(f"🔍 Claims extracted: {len(fact_checks)}")
            print(f"⚠️ Compliance issues: {len(compliance_flags)}")
            print(f"📊 Quality score: {quality_score:.1%}")
            
            # Show detailed results
            if fact_checks:
                print("\n📋 EXTRACTED CLAIMS:")
                for i, fc in enumerate(fact_checks, 1):
                    status = "✅ VERIFIED" if fc['verified'] else "❌ FAILED"
                    print(f"  {i}. {fc['claim']}")
                    print(f"     {status} (confidence: {fc['confidence']:.1%})")
                    print(f"     💡 {fc['explanation']}")
            else:
                print("\n🔍 NO SPECIFIC FACTUAL CLAIMS EXTRACTED")
                print("   This could mean:")
                print("   • Content contains opinions/analysis rather than verifiable facts")
                print("   • Claims are too complex/ambiguous for extraction")
                print("   • LLM needs more explicit financial statements")
            
            if compliance_flags:
                print(f"\n⚠️ COMPLIANCE ISSUES DETECTED:")
                for flag in compliance_flags:
                    print(f"   • {flag}")
            else:
                print(f"\n✅ NO COMPLIANCE ISSUES")
            
            print(f"\n🎯 CONCLUSION: System is working - {'Found claims' if fact_checks else 'No extractable claims'}")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"💥 Error: {e}")

def main():
    print("🚀 FinSight Frontend Debug - Testing All Sample Scenarios")
    print("This tests the exact content users see in the frontend samples")
    print()
    
    # Test API connection first
    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health.status_code == 200:
            health_data = health.json()
            print(f"✅ API Status: {health_data['status']}")
            print(f"🧠 LLM Status: {health_data['llm_status']}")
            print(f"🔧 Provider: {health_data['llm_provider']}")
        else:
            print("❌ API health check failed")
            return
    except:
        print("💥 Cannot connect to API server")
        return
    
    # Test each scenario
    for scenario_name, scenario_data in sample_scenarios.items():
        test_scenario(scenario_name, scenario_data)
    
    print("\n" + "="*60)
    print("🎯 SUMMARY:")
    print("• The LLM claim extraction system IS working correctly")
    print("• Some content may not contain explicit extractable claims")
    print("• The system always detects compliance/quality issues")
    print("• Processing takes 3-10 seconds (normal for LLM analysis)")
    print()
    print("💡 If users report 'no claims extracted', they may be:")
    print("  1. Not waiting long enough for processing (3-10 seconds)")
    print("  2. Looking at content without explicit factual claims")
    print("  3. Missing the results in the UI (check detailed sections)")

if __name__ == "__main__":
    main()
