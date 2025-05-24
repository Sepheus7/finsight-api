#!/usr/bin/env python3
"""
Local Test Script for AI-Enhanced Financial Fact Checking
Tests the integrated AI evaluation system with sample financial claims
Uses local modules directly instead of Lambda functions
"""

import json
import time
from datetime import datetime
import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from fact_check_handler import FinancialFactChecker
from ai_evaluator_handler import lambda_handler as ai_evaluator_lambda

def simulate_ai_evaluation(claim: str, fact_check_result: dict) -> dict:
    """Simulate AI evaluation when LLM service is not available"""
    import random
    
    # Analyze claim characteristics
    claim_lower = claim.lower()
    confidence = fact_check_result.get('confidence', 0.3)
    
    # Simulate different evaluation scenarios based on claim content
    if any(word in claim_lower for word in ['stock', 'price', 'market cap', 'revenue']):
        # Verifiable financial data - adjust confidence based on verification success
        if fact_check_result.get('verified', False):
            confidence_multiplier = random.uniform(1.1, 1.3)  # Boost verified claims
            quality_score = random.uniform(0.7, 0.9)
            risk_level = "low"
        else:
            confidence_multiplier = random.uniform(0.7, 0.9)  # Reduce unverified claims
            quality_score = random.uniform(0.4, 0.6)
            risk_level = "medium"
            
    elif any(word in claim_lower for word in ['believes', 'thinks', 'opinion']):
        # Opinion-based claims - generally lower confidence
        confidence_multiplier = random.uniform(0.6, 0.8)
        quality_score = random.uniform(0.3, 0.5)
        risk_level = "medium"
        
    elif any(word in claim_lower for word in ['will', 'predict', 'forecast', 'next']):
        # Future predictions - variable confidence
        confidence_multiplier = random.uniform(1.0, 1.2)  # Sometimes boost for detailed predictions
        quality_score = random.uniform(0.5, 0.7)
        risk_level = "high"
        
    elif any(word in claim_lower for word in ['historically', 'past', 'trend']):
        # Historical claims - moderate adjustment
        confidence_multiplier = random.uniform(0.8, 1.0)
        quality_score = random.uniform(0.5, 0.8)
        risk_level = "low"
        
    else:
        # General claims
        confidence_multiplier = random.uniform(0.9, 1.1)
        quality_score = random.uniform(0.4, 0.7)
        risk_level = "medium"
    
    return {
        'overall_score': quality_score,
        'quality_assessment': f'Simulated AI evaluation of {len(claim.split())} word claim with {risk_level} risk',
        'improvement_suggestions': [
            'Add specific data sources for verification',
            'Include time context for claims',
            'Specify confidence intervals where applicable'
        ],
        'confidence_adjustments': {
            'fact_check_confidence': confidence_multiplier,
            'context_relevance': random.uniform(0.6, 1.0),
            'compliance_severity': random.uniform(0.8, 1.0)
        },
        'strengths': ['Clear statement', 'Specific claim'],
        'weaknesses': ['Limited verification', 'Needs more context'],
        'risk_assessment': {
            'financial_risk': risk_level,
            'regulatory_risk': 'low',
            'misinformation_risk': risk_level
        },
        'explanation': f'Simulated evaluation: Applied {confidence_multiplier:.2f}x confidence multiplier based on claim type and verification status'
    }

def print_separator(title=""):
    """Print a nice separator"""
    print("\n" + "="*80)
    if title:
        print(f" {title} ".center(80, "="))
        print("="*80)

def enhance_claim_locally(claim: str) -> dict:
    """Enhanced claim processing using local modules"""
    
    # Initialize handlers
    fact_checker = FinancialFactChecker()
    
    # Step 1: Extract and verify claims
    claims = fact_checker.extract_financial_claims(claim)
    fact_checks = []
    
    for extracted_claim in claims:
        fact_check = fact_checker.verify_claim(extracted_claim)
        fact_checks.append(fact_check)
    
    # If no claims extracted, treat the input as a single claim
    if not claims:
        fact_check = fact_checker.verify_claim(claim)
        fact_checks = [fact_check]
    
    # Step 2: Calculate original confidence
    original_confidence = None
    if fact_checks:
        confidences = [fc.get('confidence', 0.3) for fc in fact_checks]
        original_confidence = sum(confidences) / len(confidences)
    
    # Step 3: AI evaluation
    ai_evaluation = None
    enhanced_confidence = original_confidence
    
    try:
        class MockContext:
            aws_request_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        ai_event = {
            'content': claim,
            'fact_checks': fact_checks,
            'context_additions': [],  # No context for simple test
            'compliance_flags': [],   # No compliance flags for test
            'request_id': MockContext.aws_request_id
        }
        
        ai_response = ai_evaluator_lambda(ai_event, MockContext())
        
        # Check if AI evaluation succeeded or failed
        if 'error' in ai_response:
            print(f"⚠️  AI evaluation failed: {ai_response.get('error', 'Unknown error')}")
            print("🔄 Using simulated AI evaluation for demonstration...")
            # Use simulated AI evaluation for demonstration
            ai_evaluation = simulate_ai_evaluation(claim, fact_checks[0] if fact_checks else {'confidence': 0.3, 'verified': False})
        else:
            ai_evaluation = ai_response.get('ai_evaluation', {})
        
        # Apply confidence adjustment if provided
        if ai_evaluation and 'confidence_adjustments' in ai_evaluation:
            adjustments = ai_evaluation['confidence_adjustments']
            fact_check_multiplier = adjustments.get('fact_check_confidence', 1.0)
            if original_confidence is not None:
                enhanced_confidence = min(0.99, max(0.01, original_confidence * fact_check_multiplier))
            
    except Exception as e:
        print(f"⚠️  AI evaluation failed: {str(e)}")
        print("🔄 Using simulated AI evaluation for demonstration...")
        # Use simulated AI evaluation for demonstration
        ai_evaluation = simulate_ai_evaluation(claim, fact_checks[0] if fact_checks else {'confidence': 0.3, 'verified': False})
        
        # Apply simulated confidence adjustment
        if ai_evaluation and 'confidence_adjustments' in ai_evaluation:
            adjustments = ai_evaluation['confidence_adjustments']
            fact_check_multiplier = adjustments.get('fact_check_confidence', 1.0)
            if original_confidence is not None:
                enhanced_confidence = min(0.99, max(0.01, original_confidence * fact_check_multiplier))
    
    # Determine verification status
    verification_status = 'verified' if all(fc.get('verified', False) for fc in fact_checks) else 'unverified'
    if not fact_checks:
        verification_status = 'no_claims_found'
    
    return {
        'original_confidence': original_confidence,
        'enhanced_confidence': enhanced_confidence,
        'verification_status': verification_status,
        'ai_evaluation': ai_evaluation,
        'evidence': [
            {
                'description': fc.get('explanation', ''),
                'source': fc.get('source', ''),
                'confidence': fc.get('confidence', 0.3),
                'claim': fc.get('claim', '')
            }
            for fc in fact_checks
        ],
        'fact_checks_count': len(fact_checks),
        'claims_extracted': len(claims)
    }

def test_claim(claim: str, description: str):
    """Test a single financial claim"""
    print(f"\n🔍 Testing: {description}")
    print(f"📝 Claim: {claim}")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Test the enhanced claim function
        result = enhance_claim_locally(claim)
        
        elapsed = time.time() - start_time
        
        print(f"⏱️  Processing time: {elapsed:.2f}s")
        print(f"✅ Enhanced successfully!")
        
        # Display results
        print(f"\n📊 Results:")
        original_conf = result.get('original_confidence')
        enhanced_conf = result.get('enhanced_confidence')
        
        if original_conf is not None:
            print(f"   Original Confidence: {original_conf:.3f}")
        else:
            print(f"   Original Confidence: N/A (no verifiable claims)")
            
        if enhanced_conf is not None:
            print(f"   Enhanced Confidence: {enhanced_conf:.3f}")
        else:
            print(f"   Enhanced Confidence: N/A")
            
        print(f"   Verification Status: {result.get('verification_status', 'N/A')}")
        print(f"   Claims Extracted: {result.get('claims_extracted', 0)}")
        print(f"   Fact Checks: {result.get('fact_checks_count', 0)}")
        
        # AI Evaluation details
        ai_eval = result.get('ai_evaluation', {})
        if ai_eval:
            print(f"\n🤖 AI Evaluation:")
            reasoning = ai_eval.get('explanation', ai_eval.get('reasoning', 'N/A'))
            # Truncate long reasoning for display
            if len(reasoning) > 200:
                reasoning = reasoning[:200] + "..."
            print(f"   Explanation: {reasoning}")
            
            # Show quality assessment
            quality = ai_eval.get('quality_assessment', '')
            if quality:
                print(f"   Quality Assessment: {quality}")
            
            # Show confidence adjustments
            adjustments = ai_eval.get('confidence_adjustments', {})
            if adjustments:
                fact_check_mult = adjustments.get('fact_check_confidence', 1.0)
                print(f"   Confidence Multiplier: {fact_check_mult:.2f}x")
            
            # Show risk assessment
            risk_assess = ai_eval.get('risk_assessment', {})
            if risk_assess:
                financial_risk = risk_assess.get('financial_risk', 'unknown')
                misinfo_risk = risk_assess.get('misinformation_risk', 'unknown')
                print(f"   Financial Risk: {financial_risk}, Misinfo Risk: {misinfo_risk}")
            
            factors = ai_eval.get('contextual_factors', [])
            if factors:
                print(f"   Contextual Factors: {factors}")
            
            adjustment = ai_eval.get('confidence_adjustment', 0)
            if adjustment != 0:
                print(f"   Confidence Adjustment: {adjustment:+.3f}")
        
        # Evidence
        evidence = result.get('evidence', [])
        if evidence:
            print(f"\n📋 Evidence ({len(evidence)} items):")
            for i, item in enumerate(evidence[:3], 1):  # Show first 3
                print(f"   {i}. Claim: {item.get('claim', 'N/A')}")
                print(f"      Explanation: {item.get('description', 'No description')}")
                print(f"      Source: {item.get('source', 'Unknown')}")
                print(f"      Confidence: {item.get('confidence', 'N/A'):.3f}")
                print()
                
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error after {elapsed:.2f}s: {str(e)}")
        import traceback
        traceback.print_exc()
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
            time.sleep(1)
    
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
            original = result["result"].get("original_confidence")
            enhanced = result["result"].get("enhanced_confidence")
            
            if original is not None and enhanced is not None:
                change = enhanced - original
                change_str = f"{change:+.3f}" if change != 0 else " 0.000"
                print(f"   • {test_desc[:40]:<40} | {original:.3f} → {enhanced:.3f} ({change_str})")
            else:
                print(f"   • {test_desc[:40]:<40} | No verifiable claims found")
    
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
