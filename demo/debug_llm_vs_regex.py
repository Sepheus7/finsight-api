#!/usr/bin/env python3
"""
Test both LLM and regex paths to see which one is being used and why claims differ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_api_server import LocalLLMClient
import requests
import json

sample_content = """AAPL stock is currently trading at $150 and I recommend buying it immediately. This is a guaranteed profitable investment that will definitely make you money. 

Based on my analysis, Apple stock will increase by 50% in the next month. You should invest all your savings into AAPL right now for maximum returns.

Trust me, this is insider information and you can't lose money on this trade. Apple is going to announce revolutionary products that will skyrocket the stock price."""

def test_llm_vs_regex():
    """Test both LLM and regex extraction paths"""
    print("🔍 Testing LLM vs Regex Claim Extraction")
    print("=" * 60)
    
    llm_client = LocalLLMClient()
    
    print(f"🤖 LLM Available: {llm_client.available}")
    print(f"🖥️ LLM Model: {llm_client.model}")
    print()
    
    # Test regex fallback directly
    print("📊 REGEX FALLBACK Results:")
    regex_claims = llm_client._regex_fallback(sample_content)
    print(f"Found {len(regex_claims)} claims:")
    for i, claim in enumerate(regex_claims, 1):
        print(f"  {i}. {claim['claim']} (Type: {claim['type']}, Symbol: {claim['symbol']})")
    print()
    
    # Test LLM extraction (which may fall back to regex)
    print("🧠 LLM EXTRACTION Results:")
    llm_claims = llm_client.extract_claims(sample_content)
    print(f"Found {len(llm_claims)} claims:")
    for i, claim in enumerate(llm_claims, 1):
        print(f"  {i}. {claim.get('claim', 'N/A')} (Type: {claim.get('type', 'N/A')}, Symbol: {claim.get('symbol', 'N/A')})")
    print()
    
    # Compare results
    print("🔄 COMPARISON:")
    print(f"Regex claims: {len(regex_claims)}")
    print(f"LLM claims: {len(llm_claims)}")
    
    # Check if they're the same
    if len(regex_claims) == len(llm_claims):
        print("✅ Same number of claims extracted")
    else:
        print("❌ Different number of claims - investigating...")
        
    return regex_claims, llm_claims

def test_full_api():
    """Test the full API endpoint"""
    print("\n🌐 FULL API TEST:")
    print("=" * 30)
    
    test_request = {
        "ai_response": {
            "content": sample_content,
            "agent_id": "test_agent", 
            "timestamp": "2025-05-26T12:00:00Z"
        },
        "enrichment_level": "comprehensive",
        "fact_check": True,
        "add_context": True
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/enhance",
            json=test_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            fact_checks = result.get('fact_checks', [])
            context_additions = result.get('context_additions', [])
            
            print(f"✅ API Response successful")
            print(f"🎯 Fact checks: {len(fact_checks)}")
            for fc in fact_checks:
                print(f"   - {fc.get('claim', 'N/A')}")
            print(f"📝 Context additions: {len(context_additions)}")
            print(f"🤖 Provider used: {result.get('provider_used', 'unknown')}")
            
            return result
        else:
            print(f"❌ API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ API Test failed: {e}")
        return None

if __name__ == "__main__":
    regex_claims, llm_claims = test_llm_vs_regex()
    api_result = test_full_api()
