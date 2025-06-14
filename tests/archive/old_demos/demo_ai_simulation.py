#!/usr/bin/env python3
"""
Direct test of simulated AI evaluation to demonstrate the concept
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from test_ai_evaluation_local import simulate_ai_evaluation
import json

def main():
    print("🤖 Testing Simulated AI Evaluation")
    print("="*60)
    
    # Sample fact check result
    sample_fact_check = {
        'claim': 'Apple Inc. (AAPL) stock price is $185.50',
        'confidence': 0.3,
        'verified': False,
        'explanation': 'Could not verify with available data sources'
    }
    
    # Test different claim types
    test_cases = [
        {
            'claim': 'Apple Inc. (AAPL) stock price is $185.50',
            'type': 'Stock Price (Verifiable)'
        },
        {
            'claim': 'Warren Buffett believes tech stocks are overvalued',
            'type': 'Opinion/Belief'
        },
        {
            'claim': 'The Federal Reserve will raise rates next month',
            'type': 'Future Prediction'
        },
        {
            'claim': 'Gold has historically performed well during uncertainty',
            'type': 'Historical Trend'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['type']}")
        print(f"Claim: {test_case['claim']}")
        print("-" * 40)
        
        # Get simulated AI evaluation
        ai_eval = simulate_ai_evaluation(test_case['claim'], sample_fact_check)
        
        # Display results
        print(f"🎯 Overall Score: {ai_eval['overall_score']:.2f}")
        print(f"📊 Quality Assessment: {ai_eval['quality_assessment']}")
        
        conf_adj = ai_eval['confidence_adjustments']['fact_check_confidence']
        print(f"🔧 Confidence Multiplier: {conf_adj:.2f}x")
        
        original_conf = 0.3
        enhanced_conf = original_conf * conf_adj
        change = enhanced_conf - original_conf
        print(f"📈 Confidence Change: {original_conf:.3f} → {enhanced_conf:.3f} ({change:+.3f})")
        
        risk = ai_eval['risk_assessment']
        print(f"⚠️  Risk Assessment: Financial={risk['financial_risk']}, Misinfo={risk['misinformation_risk']}")
        
        print(f"💡 Explanation: {ai_eval['explanation']}")

if __name__ == "__main__":
    main()
