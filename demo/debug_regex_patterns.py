#!/usr/bin/env python3
"""
Test the regex patterns vs LLM extraction to understand the inconsistency
"""

import re

# Sample content from frontend
sample_content = """AAPL stock is currently trading at $150 and I recommend buying it immediately. This is a guaranteed profitable investment that will definitely make you money. 

Based on my analysis, Apple stock will increase by 50% in the next month. You should invest all your savings into AAPL right now for maximum returns.

Trust me, this is insider information and you can't lose money on this trade. Apple is going to announce revolutionary products that will skyrocket the stock price."""

def test_regex_patterns(text):
    """Test the current regex patterns"""
    print("🔍 Testing Current Regex Patterns")
    print("=" * 50)
    
    # These are the actual patterns from llm_api_server.py
    stock_patterns = [
        r'(?:[A-Za-z]+\s+)?\(([A-Z]{2,5})\)\s+(?:is|are)?\s*(?:currently\s+)?(?:trading|priced)\s+(?:at|around|near)\s+\$?(\d+(?:\.\d{2})?)',
        r'(?:^|\s)([A-Z]{2,5})\s+(?:is|are)?\s*(?:currently\s+)?(?:trading|priced)\s+(?:at|around|near)\s+\$?(\d+(?:\.\d{2})?)',
    ]
    
    claims_found = []
    
    for i, pattern in enumerate(stock_patterns, 1):
        print(f"\nPattern {i}: {pattern}")
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        pattern_claims = []
        for match in matches:
            claim = {
                "claim": f"{match.group(1)} is priced at ${match.group(2)}",
                "type": "stock_price", 
                "symbol": match.group(1).upper(),
                "value": match.group(2),
                "matched_text": match.group(0)
            }
            pattern_claims.append(claim)
            claims_found.append(claim)
        
        if pattern_claims:
            print(f"  ✅ Found {len(pattern_claims)} matches:")
            for claim in pattern_claims:
                print(f"    • Matched: '{claim['matched_text']}'")
                print(f"    • Symbol: {claim['symbol']}, Value: ${claim['value']}")
        else:
            print(f"  ❌ No matches")
    
    return claims_found

def test_improved_patterns(text):
    """Test improved regex patterns that should catch more cases"""
    print("\n🚀 Testing Improved Regex Patterns")
    print("=" * 50)
    
    # More comprehensive patterns
    improved_patterns = [
        # Current patterns (keep existing)
        r'(?:[A-Za-z]+\s+)?\(([A-Z]{2,5})\)\s+(?:is|are)?\s*(?:currently\s+)?(?:trading|priced)\s+(?:at|around|near)\s+\$?(\d+(?:\.\d{2})?)',
        r'(?:^|\s)([A-Z]{2,5})\s+(?:is|are)?\s*(?:currently\s+)?(?:trading|priced)\s+(?:at|around|near)\s+\$?(\d+(?:\.\d{2})?)',
        
        # NEW: Handle "AAPL stock is currently trading at $150"
        r'\b([A-Z]{2,5})\s+stock\s+is\s+currently\s+trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
        
        # NEW: Handle "Apple stock will increase by 50%"  
        r'\b(Apple|Microsoft|Google|Tesla|Amazon|Meta)\s+stock\s+will\s+increase\s+by\s+(\d+(?:\.\d+)?%)',
        
        # NEW: More flexible trading patterns
        r'\b([A-Z]{2,5})\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
        
        # NEW: Company name patterns
        r'\b(Apple|AAPL)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
    ]
    
    claims_found = []
    
    for i, pattern in enumerate(improved_patterns, 1):
        print(f"\nPattern {i}: {pattern}")
        matches = re.finditer(pattern, text, re.IGNORECASE) 
        
        pattern_claims = []
        for match in matches:
            # Handle different group structures
            if len(match.groups()) >= 2:
                symbol = match.group(1).upper()
                value = match.group(2)
                
                # Convert company names to tickers
                if symbol in ['APPLE']:
                    symbol = 'AAPL'
                elif symbol in ['MICROSOFT']:
                    symbol = 'MSFT'
                
                claim = {
                    "claim": f"{symbol} trading claim",
                    "type": "stock_price",
                    "symbol": symbol,
                    "value": value,
                    "matched_text": match.group(0)
                }
                pattern_claims.append(claim)
                claims_found.append(claim)
        
        if pattern_claims:
            print(f"  ✅ Found {len(pattern_claims)} matches:")
            for claim in pattern_claims:
                print(f"    • Matched: '{claim['matched_text']}'")
                print(f"    • Symbol: {claim['symbol']}, Value: {claim['value']}")
        else:
            print(f"  ❌ No matches")
    
    return claims_found

def main():
    print("🧪 Diagnosing Why Regex Fails on 'Risky Investment Advice' Sample")
    print("=" * 70)
    print(f"📝 Sample text:")
    print(f"'{sample_content[:100]}...'")
    print()
    
    # Test current patterns
    current_claims = test_regex_patterns(sample_content)
    
    # Test improved patterns  
    improved_claims = test_improved_patterns(sample_content)
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY:")
    print(f"• Current patterns found: {len(current_claims)} claims")
    print(f"• Improved patterns found: {len(improved_claims)} claims")
    
    if len(improved_claims) > len(current_claims):
        print("\n🎯 SOLUTION: Improve regex patterns in llm_api_server.py")
        print("   The current patterns are too restrictive for this content!")
    else:
        print("\n🤔 Issue might be in LLM processing, not regex patterns")

if __name__ == "__main__":
    main()
