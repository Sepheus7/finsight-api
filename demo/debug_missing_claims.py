#!/usr/bin/env python3
"""
Debug why the prediction claim "Apple stock will increase by 50%" is not being extracted
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_api_server import LocalLLMClient
import re

# Full sample content
sample_content = """AAPL stock is currently trading at $150 and I recommend buying it immediately. This is a guaranteed profitable investment that will definitely make you money. 

Based on my analysis, Apple stock will increase by 50% in the next month. You should invest all your savings into AAPL right now for maximum returns.

Trust me, this is insider information and you can't lose money on this trade. Apple is going to announce revolutionary products that will skyrocket the stock price."""

def debug_prediction_patterns():
    """Debug why prediction claims are not being extracted"""
    print("🔍 Debugging Prediction Claim Extraction")
    print("=" * 60)
    print(f"📝 Target claim: 'Apple stock will increase by 50%'")
    print()
    
    # Test individual prediction patterns
    prediction_patterns = [
        r'\b(Apple|AAPL|Microsoft|MSFT|Tesla|TSLA|Amazon|AMZN|Google|GOOGL|Meta|META)\s+stock\s+will\s+increase\s+by\s+(\d+(?:\.\d+)?%)',
        r'\b([A-Z]{2,5})\s+will\s+(?:increase|rise|grow)\s+(?:by\s+)?(\d+(?:\.\d+)?%)',
        r'\b(Apple|AAPL)\s+stock\s+will\s+increase\s+by\s+(\d+(?:\.\d+)?%)',
        r'(Apple|AAPL)\s+stock\s+will\s+increase\s+by\s+(\d+(?:\.\d+)?%)',
    ]
    
    print("🧪 Testing Individual Patterns:")
    for i, pattern in enumerate(prediction_patterns, 1):
        print(f"  {i}. Pattern: {pattern}")
        matches = list(re.finditer(pattern, sample_content, re.IGNORECASE))
        if matches:
            for match in matches:
                print(f"     ✅ Match: {match.group()} -> Symbol: {match.group(1)}, Value: {match.group(2)}")
        else:
            print(f"     ❌ No matches")
        print()
    
    # Test the actual server method
    print("🖥️ Testing Server Method:")
    llm_client = LocalLLMClient()
    claims = llm_client._regex_fallback(sample_content)
    
    print(f"Total claims found: {len(claims)}")
    for i, claim in enumerate(claims, 1):
        print(f"  {i}. {claim['claim']}")
        print(f"     Type: {claim['type']}, Symbol: {claim['symbol']}, Value: {claim['value']}")
    
    # Check if prediction claims are in the results
    prediction_claims = [c for c in claims if c['type'] == 'prediction']
    print(f"\n📊 Prediction claims found: {len(prediction_claims)}")
    
    return claims

def debug_exact_text_match():
    """Check what the exact text looks like around the prediction"""
    print("\n🔍 Exact Text Analysis:")
    print("=" * 40)
    
    # Find the exact position of the prediction text
    prediction_text = "Apple stock will increase by 50%"
    index = sample_content.find(prediction_text)
    
    if index != -1:
        print(f"✅ Found prediction text at position {index}")
        print(f"Context: ...{sample_content[max(0, index-20):index+len(prediction_text)+20]}...")
        print(f"Exact match: '{sample_content[index:index+len(prediction_text)]}'")
    else:
        print("❌ Prediction text not found exactly")
        # Check for variations
        variations = [
            "Apple stock will increase",
            "stock will increase by 50%",
            "increase by 50%"
        ]
        for var in variations:
            if var in sample_content:
                print(f"✅ Found variation: '{var}'")

if __name__ == "__main__":
    debug_exact_text_match()
    debug_prediction_patterns()
