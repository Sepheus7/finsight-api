#!/usr/bin/env python3
"""
Quick test of a single AI-enhanced evaluation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from test_ai_evaluation_local import enhance_claim_locally, test_claim

def main():
    print("🚀 Quick AI Enhancement Test")
    print("="*60)
    
    # Test a single claim
    test_claim(
        "Apple Inc. (AAPL) stock price is $185.50",
        "Stock Price Test with AI Enhancement"
    )

if __name__ == "__main__":
    main()
