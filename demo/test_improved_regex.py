#!/usr/bin/env python3
"""
Test the improved regex patterns directly
"""

import re

# Sample content
sample_content = """AAPL stock is currently trading at $150 and I recommend buying it immediately. This is a guaranteed profitable investment that will definitely make you money. 

Based on my analysis, Apple stock will increase by 50% in the next month. You should invest all your savings into AAPL right now for maximum returns.

Trust me, this is insider information and you can't lose money on this trade. Apple is going to announce revolutionary products that will skyrocket the stock price."""

def test_improved_regex_fallback(text):
    """Test the improved regex fallback function"""
    claims = []
    
    # Enhanced stock price patterns - more comprehensive
    stock_patterns = [
        # Original patterns (keep for backward compatibility)
        r'(?:[A-Za-z]+\s+)?\(([A-Z]{2,5})\)\s+(?:is|are)?\s*(?:currently\s+)?(?:trading|priced)\s+(?:at|around|near)\s+\$?(\d+(?:\.\d{2})?)',
        
        # NEW: Direct ticker patterns (most important for our sample)
        r'\b([A-Z]{2,5})\s+stock\s+is\s+currently\s+trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
        r'\b([A-Z]{2,5})\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
        
        # Company name to ticker mappings
        r'\b(Apple|AAPL)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
        r'\b(Microsoft|MSFT)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
        r'\b(Tesla|TSLA)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
        r'\b(Amazon|AMZN)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
        r'\b(Google|GOOGL)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
        r'\b(Meta|META)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
    ]
    
    # Company name to ticker mapping
    name_to_ticker = {
        'Apple': 'AAPL', 'Microsoft': 'MSFT', 'Tesla': 'TSLA',
        'Amazon': 'AMZN', 'Google': 'GOOGL', 'Meta': 'META'
    }
    
    for pattern in stock_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) >= 2:
                symbol = match.group(1).upper()
                value = match.group(2)
                
                # Convert company names to tickers
                if symbol in name_to_ticker:
                    symbol = name_to_ticker[symbol]
                
                # Skip invalid symbols like "STOCK"
                if symbol in ['STOCK', 'IS', 'AT', 'THE']:
                    continue
                
                claims.append({
                    "claim": f"{symbol} is currently trading at ${value}",
                    "type": "stock_price",
                    "symbol": symbol,
                    "value": value,
                    "timeframe": "current"
                })
    
    # Add prediction/growth patterns
    prediction_patterns = [
        r'\b(Apple|AAPL|Microsoft|MSFT|Tesla|TSLA|Amazon|AMZN|Google|GOOGL|Meta|META)\s+stock\s+will\s+increase\s+by\s+(\d+(?:\.\d+)?%)',
        r'\b([A-Z]{2,5})\s+will\s+(?:increase|rise|grow)\s+(?:by\s+)?(\d+(?:\.\d+)?%)',
    ]
    
    for pattern in prediction_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) >= 2:
                symbol = match.group(1).upper()
                percentage = match.group(2)
                
                # Convert company names to tickers
                if symbol in name_to_ticker:
                    symbol = name_to_ticker[symbol]
                
                claims.append({
                    "claim": f"{symbol} stock will increase by {percentage}",
                    "type": "prediction",
                    "symbol": symbol,
                    "value": percentage,
                    "timeframe": "future"
                })
    
    return claims

def main():
    print("🧪 Testing Improved Regex Fallback")
    print("=" * 50)
    print(f"📝 Sample: {sample_content[:100]}...")
    print()
    
    claims = test_improved_regex_fallback(sample_content)
    
    print(f"🎯 Found {len(claims)} claims:")
    for i, claim in enumerate(claims, 1):
        print(f"  {i}. {claim['claim']}")
        print(f"     Type: {claim['type']}, Symbol: {claim['symbol']}, Value: {claim['value']}")
    
    if claims:
        print(f"\n✅ SUCCESS! Regex patterns now catch the claims!")
    else:
        print(f"\n❌ Still no claims found - need more pattern work")

if __name__ == "__main__":
    main()
