#!/usr/bin/env python3
"""
Local Test Script for AI-Enhanced Financial Fact Checking
Tests the integrated AI evaluation system with sample financial claims
"""

import json
import time
from datetime import datetime
import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhance_handler import enhance_financial_claim

def print_separator(title=""):
    """Print a nice separator"""
    print("\n" + "="*80)
    if title:
        print(f" {title} ".center(80, "="))
        print("="*80)

def test_claim(claim: str, description: str):
    """Test a single financial claim"""
    print(f"\n🔍 Testing: {description}")
    print(f"📝 Claim: {claim}")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Test the enhanced claim function
        result = enhance_financial_claim(claim)
        
        elapsed = time.time() - start_time
        
        print(f"⏱️  Processing time: {elapsed:.2f}s")
        print(f"✅ Enhanced successfully!")
        
        # Display results
        print(f"\n📊 Results:")
        print(f"   Original Confidence: {result.get('original_confidence', 'N/A')}")
        print(f"   Enhanced Confidence: {result.get('enhanced_confidence', 'N/A')}")
        print(f"   Verification Status: {result.get('verification_status', 'N/A')}")
        
        # AI Evaluation details
        ai_eval = result.get('ai_evaluation', {})
        if ai_eval:
            print(f"\n🤖 AI Evaluation:")
            print(f"   Reasoning: {ai_eval.get('reasoning', 'N/A')}")
            print(f"   Contextual Factors: {ai_eval.get('contextual_factors', [])}")
            print(f"   Confidence Adjustment: {ai_eval.get('confidence_adjustment', 'N/A')}")
        
        # Evidence
        evidence = result.get('evidence', [])
        if evidence:
            print(f"\n📋 Evidence ({len(evidence)} items):")
            for i, item in enumerate(evidence[:3], 1):  # Show first 3
                print(f"   {i}. {item.get('description', 'No description')}")
                print(f"      Source: {item.get('source', 'Unknown')}")
                print(f"      Confidence: {item.get('confidence', 'N/A')}")
                
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error after {elapsed:.2f}s: {str(e)}")
        return {"error": str(e)}

def main():
    """Run comprehensive tests of the AI evaluation system"""
    
    print_separator("AI-Enhanced Financial Fact Checking Test Suite")
    print(f"🚀 Starting tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test cases with different types of financial claims
    test_cases = [
        {
            "claim": "Apple Inc. (AAPL) stock price is $185.50",
            "description": "Current Stock Price Claim (Verifiable)"
        },
        {
            "claim": "Microsoft has a market capitalization of $2.8 trillion",
            "description": "Market Cap Claim (Verifiable)"
        },
        {
            "claim": "Tesla's revenue increased by 25% last quarter",
            "description": "Percentage Growth Claim (Contextual)"
        },
        {
            "claim": "Warren Buffett believes tech stocks are overvalued in 2024",
            "description": "Opinion/Belief Claim (Subjective)"
        },
        {
            "claim": "The Federal Reserve will raise interest rates by 0.75% next month",
            "description": "Future Prediction Claim (Unverifiable)"
        },
        {
            "claim": "Gold prices have historically performed well during economic uncertainty",
            "description": "Historical Trend Claim (Complex)"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print_separator(f"Test Case {i}/{len(test_cases)}")
        
        result = test_claim(test_case["claim"], test_case["description"])
        results.append({
            "test_case": test_case,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        # Add a small delay between tests
        if i < len(test_cases):
            time.sleep(2)
    
    # Summary
    print_separator("Test Summary")
    
    successful_tests = [r for r in results if "error" not in r["result"]]
    failed_tests = [r for r in results if "error" in r["result"]]
    
    print(f"📈 Overall Results:")
    print(f"   ✅ Successful: {len(successful_tests)}/{len(results)}")
    print(f"   ❌ Failed: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        print(f"\n🎯 Confidence Score Analysis:")
        for result in successful_tests:
            test_desc = result["test_case"]["description"]
            original = result["result"].get("original_confidence", "N/A")
            enhanced = result["result"].get("enhanced_confidence", "N/A")
            
            if original != "N/A" and enhanced != "N/A":
                change = enhanced - original
                change_str = f"{change:+.2f}" if change != 0 else "0.00"
                print(f"   • {test_desc[:40]:<40} | {original:.2f} → {enhanced:.2f} ({change_str})")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for result in failed_tests:
            test_desc = result["test_case"]["description"]
            error = result["result"]["error"]
            print(f"   • {test_desc}: {error}")
    
    # Save detailed results
    output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    print_separator("Test Complete")

if __name__ == "__main__":
    main()
