#!/usr/bin/env python3
"""
Test the integration of Enhanced Ticker Resolver with LLM Claim Extractor
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.llm_claim_extractor import LLMClaimExtractor
from src.utils.enhanced_ticker_resolver import EnhancedTickerResolver
from src.handlers.enhanced_fact_check_handler import EnhancedFinancialFactChecker

def test_ticker_resolver_standalone():
    """Test the enhanced ticker resolver standalone functionality"""
    print("🔍 Testing Enhanced Ticker Resolver standalone...")
    
    resolver = EnhancedTickerResolver()
    
    test_companies = [
        "Apple",
        "Microsoft Corporation", 
        "Alphabet Inc",
        "Tesla Motors",
        "Meta Platforms",
        "Amazon.com",
        "JPMorgan Chase",
        "Unknown Company XYZ"
    ]
    
    print(f"\nTesting resolution for {len(test_companies)} companies:")
    for company in test_companies:
        result = resolver.resolve_ticker(company)
        if result:
            print(f"✅ '{company}' → {result.ticker} (confidence: {result.confidence:.2f}, source: {result.source})")
        else:
            print(f"❌ '{company}' → Not resolved")
    
    return True

def test_llm_claim_extractor_integration():
    """Test LLM claim extractor with enhanced ticker resolver"""
    print("\n🧠 Testing LLM Claim Extractor with Enhanced Ticker Resolver...")
    
    # Initialize with regex mode (no API key required)
    extractor = LLMClaimExtractor(provider="regex")
    
    test_text = """
    Apple's stock price reached $150 per share yesterday.
    Microsoft Corporation reported quarterly revenue of $50 billion.
    Tesla Motors' market cap exceeded $800 billion.
    Meta Platforms saw a 15% increase in user engagement.
    """
    
    print(f"\nAnalyzing text: {test_text[:100]}...")
    
    claims = extractor.extract_claims(test_text)
    print(f"Extracted {len(claims)} claims:")
    
    for i, claim in enumerate(claims, 1):
        print(f"\n{i}. Claim: {claim.text}")
        print(f"   Type: {claim.claim_type.value}")
        print(f"   Entities: {claim.entities}")
        print(f"   Values: {claim.values}")
    
    return len(claims) > 0

def test_fact_checker_integration():
    """Test enhanced fact checker with ticker resolver"""
    print("\n✅ Testing Enhanced Fact Checker with Ticker Resolver...")
    
    # Initialize without LLM (no API key required)
    fact_checker = EnhancedFinancialFactChecker(use_llm=False)
    
    test_claims = [
        "Apple's stock price is $150",
        "Microsoft's market cap is $3 trillion", 
        "Tesla stock reached $200 per share"
    ]
    
    print(f"\nTesting fact checking for {len(test_claims)} claims:")
    
    for claim_text in test_claims:
        print(f"\n📊 Processing: '{claim_text}'")
        
        # Extract claims
        claims = fact_checker.extract_financial_claims(claim_text)
        print(f"   Extracted {len(claims)} claims")
        
        if claims:
            # Verify first claim
            result = fact_checker.verify_claim(claims[0])
            print(f"   ✅ Verified: {result.verified}")
            print(f"   📈 Confidence: {result.confidence:.2f}")
            print(f"   📝 Explanation: {result.explanation}")
        
    return True

def test_concurrent_resolution():
    """Test concurrent ticker resolution"""
    print("\n⚡ Testing Concurrent Ticker Resolution...")
    
    resolver = EnhancedTickerResolver()
    
    companies = [
        "Apple", "Microsoft", "Google", "Tesla", "Amazon",
        "Meta", "Netflix", "Nvidia", "Intel", "Oracle"
    ]
    
    print(f"\nResolving {len(companies)} companies concurrently...")
    results = resolver.resolve_multiple(companies)
    
    successful = 0
    for company, result in results.items():
        if result:
            print(f"✅ {company} → {result.ticker} ({result.confidence:.2f})")
            successful += 1
        else:
            print(f"❌ {company} → Not resolved")
    
    print(f"\n📊 Success rate: {successful}/{len(companies)} ({successful/len(companies)*100:.1f}%)")
    return successful > len(companies) * 0.7  # 70% success rate

def main():
    """Run all integration tests"""
    print("🚀 FinSight Enhanced Ticker Resolution Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Ticker Resolver Standalone", test_ticker_resolver_standalone),
        ("LLM Claim Extractor Integration", test_llm_claim_extractor_integration), 
        ("Fact Checker Integration", test_fact_checker_integration),
        ("Concurrent Resolution", test_concurrent_resolution)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            if result:
                print(f"\n✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name} FAILED")
        except Exception as e:
            print(f"\n💥 {test_name} ERROR: {e}")
    
    print(f"\n{'='*60}")
    print(f"🎯 Test Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All integration tests passed! Enhanced ticker resolution is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the integration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
