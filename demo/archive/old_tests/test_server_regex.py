#!/usr/bin/env python3
"""
Test the improved regex patterns using the actual server code
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_api_server import LocalLLMClient

# Sample content from the "Risky Investment Advice" scenario
sample_content = """AAPL stock is currently trading at $150 and I recommend buying it immediately. This is a guaranteed profitable investment that will definitely make you money. 

Based on my analysis, Apple stock will increase by 50% in the next month. You should invest all your savings into AAPL right now for maximum returns.

Trust me, this is insider information and you can't lose money on this trade. Apple is going to announce revolutionary products that will skyrocket the stock price."""

def test_server_regex():
    """Test the regex fallback method from the actual server"""
    print("🧪 Testing Server Regex Fallback")
    print("=" * 50)
    print(f"📝 Sample: {sample_content[:80]}...")
    print()
    
    # Create LLM client and test regex fallback directly
    llm_client = LocalLLMClient()
    claims = llm_client._regex_fallback(sample_content)
    
    print(f"🎯 Found {len(claims)} claims:")
    for i, claim in enumerate(claims, 1):
        print(f"  {i}. {claim['claim']}")
        print(f"     Type: {claim['type']}, Symbol: {claim['symbol']}, Value: {claim['value']}")
    
    if len(claims) > 0:
        print("\n✅ SUCCESS! Server regex patterns catch the claims!")
        print(f"📊 Breakdown: {len([c for c in claims if c['type'] == 'stock_price'])} stock prices, "
              f"{len([c for c in claims if c['type'] == 'prediction'])} predictions")
    else:
        print("\n❌ FAILED! No claims extracted.")
    
    return claims

if __name__ == "__main__":
    test_server_regex()
