"""
Demo script to showcase the FinSight interactive capabilities
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from main import FinSightCLI
import json

def demo_enhanced_finsight():
    """Demonstrate the enhanced FinSight system"""
    
    print("🚀 FinSight Enhanced Demo")
    print("=" * 60)
    
    cli = FinSightCLI()
    
    # Test cases with different types of claims
    test_cases = [
        {
            "name": "Market Cap Claims",
            "text": "Microsoft's market cap is $3 trillion and Apple's market cap reached $3.5 trillion",
            "use_llm": False
        },
        {
            "name": "Mixed Financial Claims", 
            "text": "Tesla stock is trading at $200 per share. The company reported $25 billion in revenue last quarter, representing a 15% growth.",
            "use_llm": False
        },
        {
            "name": "Revenue Growth",
            "text": "Apple's revenue grew by 8% year-over-year while Microsoft saw a 12% increase in quarterly revenue.",
            "use_llm": False
        },
        {
            "name": "Interest Rate Claims",
            "text": "The Federal Reserve will raise interest rates by 0.25% next month.",
            "use_llm": False
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['name']}")
        print(f"Input: {test_case['text']}")
        print("-" * 50)
        
        try:
            results = cli.fact_check_text(test_case['text'], test_case['use_llm'])
            
            print(f"✅ Results: {results['accurate_claims']}/{results['total_claims']} accurate claims")
            print(f"📊 Overall Confidence: {results['overall_accuracy']:.1%}")
            print(f"⚠️ High Risk Claims: {results['high_risk_claims']}")
            
            for j, result in enumerate(results['results'], 1):
                status = "✅" if result['is_accurate'] else "❌"
                print(f"   {status} Claim {j}: {result['claim']}")
                print(f"      Entity: {result['entity']}")
                print(f"      Type: {result['claim_type']}")
                print(f"      Confidence: {result['confidence_score']:.1%}")
                print(f"      Explanation: {result['explanation']}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print(f"\n🎉 Demo completed! FinSight processed {sum(len(tc['text'].split()) for tc in test_cases)} words across {len(test_cases)} test cases.")
    
    # Usage instructions
    print("\n" + "=" * 60)
    print("📚 How to Use FinSight:")
    print("=" * 60)
    print("1. Interactive Mode:")
    print("   python src/main.py --interactive")
    print("")
    print("2. Single Claim Analysis:")
    print("   python src/main.py -t 'Your financial claim here'")
    print("")
    print("3. File Processing:")
    print("   python src/main.py -f earnings_report.txt")
    print("")
    print("4. With LLM Enhancement (requires API key):")
    print("   export OPENAI_API_KEY=your_key")
    print("   python src/main.py -t 'Complex financial statement'")
    print("")
    print("5. Regex-only Mode (no API required):")
    print("   python src/main.py -t 'Financial claim' --no-llm")
    print("")
    print("🔧 Configuration:")
    print("   Set environment variables in .env file or export them:")
    print("   - OPENAI_API_KEY (for OpenAI)")
    print("   - ANTHROPIC_API_KEY (for Claude)")
    print("   - FINSIGHT_LLM_PROVIDER (openai|anthropic|regex)")
    print("   - FINSIGHT_DEBUG (true|false)")

if __name__ == "__main__":
    demo_enhanced_finsight()
