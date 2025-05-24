"""
Test the Enhanced FinSight System
Tests the new LLM-powered fact-checking system
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_basic_functionality():
    """Test basic functionality without LLM dependencies"""
    
    print("🧪 Testing Enhanced FinSight System")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from models.financial_models import FinancialClaim, FactCheckResult, ClaimType, RiskLevel
        from utils.llm_claim_extractor import LLMClaimExtractor
        from handlers.enhanced_fact_check_handler import EnhancedFinancialFactChecker
        from config import config
        print("✅ All imports successful")
        
        # Test configuration
        print("⚙️ Testing configuration...")
        print(f"   LLM Provider: {config.llm.provider}")
        print(f"   Debug Mode: {config.debug}")
        print(f"   Cache Enabled: {config.data.cache_enabled}")
        print("✅ Configuration loaded")
        
        # Test model creation
        print("🔧 Testing model creation...")
        claim = FinancialClaim(
            claim_text="Apple's market cap is $3 trillion",
            entity="Apple",
            claim_type=ClaimType.MARKET_CAP,
            value="3000000000000",
            confidence=0.9
        )
        print(f"✅ Created claim: {claim.claim_text}")
        
        # Test LLM extractor with regex fallback
        print("🤖 Testing LLM Extractor (regex mode)...")
        extractor = LLMClaimExtractor(provider="regex")
        test_text = "Microsoft's market cap reached $3 trillion. Apple's revenue grew by 15% last quarter."
        claims = extractor.extract_claims(test_text)
        print(f"✅ Extracted {len(claims)} claims from test text")
        
        for i, claim in enumerate(claims, 1):
            print(f"   Claim {i}: {claim.claim_text}")
            print(f"   Entity: {claim.entity}, Type: {claim.claim_type.value}")
        
        # Test enhanced fact checker
        print("🔍 Testing Enhanced Fact Checker...")
        fact_checker = EnhancedFinancialFactChecker(use_llm=False)  # Use regex mode
        
        if claims:
            result = fact_checker.verify_claim(claims[0])
            print(f"✅ Verified claim with confidence: {result.confidence_score:.1%}")
            print(f"   Result: {'Accurate' if result.is_accurate else 'Inaccurate'}")
            print(f"   Explanation: {result.explanation}")
        
        print("\n🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_cli_interface():
    """Test the CLI interface"""
    
    print("\n🖥️ Testing CLI Interface...")
    
    try:
        from main import FinSightCLI
        
        cli = FinSightCLI()
        test_text = "Tesla's market cap is approximately $800 billion"
        
        print(f"   Testing with: {test_text}")
        results = cli.fact_check_text(test_text, use_llm=False)
        
        print(f"✅ CLI test completed")
        print(f"   Total claims: {results['total_claims']}")
        print(f"   Accurate claims: {results['accurate_claims']}")
        print(f"   Overall accuracy: {results['overall_accuracy']:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        test_cli_interface()
    
    print("\n" + "=" * 50)
    print("🚀 To use the system:")
    print("   python src/main.py -t 'Your financial claim here'")
    print("   python src/main.py --interactive")
    print("   python src/main.py -f your_file.txt")
