"""
Simple test runner for FinSight
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def test_system():
    """Test the FinSight system with proper imports"""
    
    print("🧪 Testing FinSight Enhanced System")
    print("=" * 50)
    
    try:
        # Test configuration
        print("⚙️ Loading configuration...")
        import config
        conf = config.config
        print(f"✅ Config loaded - LLM Provider: {conf.llm.provider}")
        
        # Test models
        print("📦 Loading data models...")
        from models.financial_models import FinancialClaim, FactCheckResult, ClaimType, RiskLevel
        
        claim = FinancialClaim(
            text="Apple's market cap is $3 trillion",
            claim_type=ClaimType.MARKET_CAP,
            entities=["Apple"],
            values=["3000000000000"],
            confidence=0.9,
            source_text="Apple's market cap is $3 trillion",
            start_pos=0,
            end_pos=33
        )
        print(f"✅ Created test claim: {claim.text}")
        
        # Test LLM extractor in regex mode
        print("🤖 Testing claim extraction...")
        from utils.llm_claim_extractor import LLMClaimExtractor
        
        extractor = LLMClaimExtractor(provider="regex")
        test_text = "Microsoft's market cap reached $3 trillion. Apple's revenue grew by 15%."
        claims = extractor.extract_claims(test_text)
        print(f"✅ Extracted {len(claims)} claims")
        
        for i, claim in enumerate(claims, 1):
            print(f"   Claim {i}: {claim.claim_text}")
            print(f"   Entity: {claim.entity}, Type: {claim.claim_type.value}")
        
        # Test fact checker
        print("🔍 Testing fact verification...")
        from handlers.enhanced_fact_check_handler import EnhancedFinancialFactChecker
        
        fact_checker = EnhancedFinancialFactChecker(use_llm=False)
        
        if claims:
            result = fact_checker.verify_claim(claims[0])
            print(f"✅ Verification completed")
            print(f"   Accuracy: {'✅ Accurate' if result.is_accurate else '❌ Inaccurate'}")
            print(f"   Confidence: {result.confidence_score:.1%}")
            print(f"   Explanation: {result.explanation[:100]}...")
        
        print(f"\n🎉 All tests passed! System is ready.")
        
        # Show usage examples
        print("\n📋 Usage Examples:")
        print("   # Interactive mode:")
        print("   python src/main.py --interactive")
        print("   ")
        print("   # Single claim:")
        print("   python src/main.py -t 'Tesla market cap is $800 billion'")
        print("   ")
        print("   # File processing:")
        print("   python src/main.py -f earnings_report.txt")
        print("   ")
        print("   # With LLM (requires API key):")
        print("   export OPENAI_API_KEY=your_key")
        print("   python src/main.py -t 'Your claim' # Uses LLM by default")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_system()
