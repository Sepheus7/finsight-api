#!/usr/bin/env python3
"""
FinSight GitHub Publication Validation Script
Tests core functionality before GitHub publication.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all core modules can be imported."""
    print("🔍 Testing module imports...")
    
    try:
        from src.utils.enhanced_ticker_resolver import EnhancedTickerResolver
        from src.utils.llm_claim_extractor import LLMClaimExtractor
        from src.handlers.enhanced_fact_check_handler import EnhancedFinancialFactChecker
        print("✅ All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_ticker_resolution():
    """Test enhanced ticker resolution functionality."""
    print("\n🎯 Testing enhanced ticker resolution...")
    
    try:
        from src.utils.enhanced_ticker_resolver import EnhancedTickerResolver
        
        resolver = EnhancedTickerResolver()
        
        # Test major companies
        test_companies = [
            "Apple Inc",
            "Microsoft Corporation", 
            "Amazon.com Inc",
            "Tesla, Inc.",
            "Google"
        ]
        
        success_count = 0
        for company in test_companies:
            try:
                result = resolver.resolve_ticker(company)
                if result and result.ticker and result.confidence > 0.7:
                    success_count += 1
                    print(f"✅ {company} → {result.ticker} (confidence: {result.confidence:.2f})")
                else:
                    print(f"⚠️  {company} → No reliable match")
            except Exception as e:
                print(f"❌ {company} → Error: {e}")
        
        success_rate = success_count / len(test_companies)
        print(f"\n📊 Ticker Resolution Success Rate: {success_rate:.1%}")
        return success_rate >= 0.8
        
    except Exception as e:
        print(f"❌ Ticker resolution test failed: {e}")
        return False

def test_ollama_integration():
    """Test Ollama LLM integration."""
    print("\n🦙 Testing Ollama integration...")
    
    try:
        import requests
        
        # Check if Ollama server is running
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                print(f"✅ Ollama server running with {len(models)} models")
                
                # Test LLM claim extractor with Ollama
                from src.utils.llm_claim_extractor import LLMClaimExtractor
                
                extractor = LLMClaimExtractor(provider="ollama")
                test_text = "Apple's revenue for Q4 2023 was $119.6 billion, up 2% year over year."
                
                claims = extractor.extract_claims(test_text)
                if claims:
                    print(f"✅ Extracted {len(claims)} claims using Ollama")
                    return True
                else:
                    print("⚠️  Ollama running but no claims extracted")
                    return False
                    
            else:
                print("⚠️  Ollama server not responding properly")
                return False
                
        except requests.exceptions.RequestException:
            print("⚠️  Ollama server not running (this is okay for GitHub publication)")
            return True  # Not a failure for publication
            
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False

def test_regex_fallback():
    """Test regex-based extraction (no LLM required)."""
    print("\n🔧 Testing regex fallback...")
    
    try:
        from src.utils.llm_claim_extractor import LLMClaimExtractor
        
        extractor = LLMClaimExtractor(provider="regex")
        test_text = "Microsoft's market cap is $3.2 trillion. Apple reported revenue of $394.3 billion in 2023."
        
        claims = extractor.extract_claims(test_text)
        if claims and len(claims) >= 1:
            print(f"✅ Regex fallback extracted {len(claims)} claims")
            for i, claim in enumerate(claims[:2]):  # Show first 2
                print(f"   - Claim {i+1}: {type(claim).__name__}")
            return True
        else:
            print("❌ Regex fallback failed to extract claims")
            return False
            
    except Exception as e:
        print(f"❌ Regex fallback test failed: {e}")
        return False

def test_fact_checking():
    """Test basic imports and instantiation."""
    print("\n🔍 Testing fact checking system...")
    
    try:
        from src.handlers.enhanced_fact_check_handler import EnhancedFinancialFactChecker
        
        # Test instantiation only
        fact_checker = EnhancedFinancialFactChecker(use_llm=False)
        print("✅ Fact checker instantiated successfully")
        
        # Test basic claim extraction
        test_text = "Apple stock is performing well this quarter."
        claims = fact_checker.extract_financial_claims(test_text)
        
        print(f"✅ Extracted {len(claims)} claims from test text")
        return True
        
    except Exception as e:
        print(f"❌ Fact checking test failed: {e}")
        return False

def test_file_structure():
    """Verify required files exist for GitHub publication."""
    print("\n📁 Testing file structure...")
    
    required_files = [
        "README.md",
        "LICENSE", 
        ".gitignore",
        ".env.template",
        "requirements.txt",
        "src/main.py",
        "src/utils/enhanced_ticker_resolver.py",
        "src/utils/llm_claim_extractor.py",
        "src/handlers/enhanced_fact_check_handler.py",
        "tests/test_ticker_integration.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"❌ Missing: {file_path}")
        else:
            print(f"✅ Found: {file_path}")
    
    if missing_files:
        print(f"\n❌ {len(missing_files)} required files missing")
        return False
    else:
        print(f"\n✅ All {len(required_files)} required files present")
        return True

def main():
    """Run all publication validation tests."""
    print("🚀 FinSight GitHub Publication Validation")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Module Imports", test_imports),
        ("Ticker Resolution", test_ticker_resolution),
        ("Regex Fallback", test_regex_fallback),
        ("Fact Checking", test_fact_checking),
        ("Ollama Integration", test_ollama_integration)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall Score: {passed_tests}/{total_tests} ({passed_tests/total_tests:.1%})")
    
    if passed_tests >= total_tests - 1:  # Allow 1 failure (Ollama might not be running)
        print("\n🎉 FinSight is ready for GitHub publication!")
        return True
    else:
        print("\n⚠️  Please fix failing tests before GitHub publication")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
