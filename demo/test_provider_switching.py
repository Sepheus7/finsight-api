#!/usr/bin/env python3
"""
Test script for LLM provider switching in the FinSight API
Tests switching between Ollama and Bedrock providers
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 30  # seconds

# Financial test cases with stock price claims
TEST_CONTENT = {
    "basic": "Apple (AAPL) is currently trading at $180 per share. Tesla (TSLA) stock is at $750.",
    "prediction": "I believe AAPL will increase by 15% next quarter based on their new product lineup.",
    "mixed": "MSFT is trading at $350, while AMZN is at $3200. I expect META to grow by 20% this year."
}

def test_provider(provider_name="auto", test_case="basic"):
    """
    Test a specific LLM provider with a test case
    
    Args:
        provider_name: 'ollama', 'bedrock', or 'auto'
        test_case: The test case to use from TEST_CONTENT
    
    Returns:
        Dict containing test results
    """
    content = TEST_CONTENT[test_case]
    
    request_data = {
        "ai_response": {
            "content": content,
            "agent_id": "provider-test-agent",
            "timestamp": datetime.now().isoformat()
        },
        "enrichment_level": "comprehensive",
        "fact_check": True,
        "add_context": True,
        "llm_provider": provider_name
    }
    
    print(f"\nTesting {provider_name.upper()} provider with case: {test_case}")
    print(f"Input: {content[:60]}...")
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{API_BASE_URL}/enhance", 
            json=request_data,
            timeout=DEFAULT_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            elapsed = time.time() - start_time
            
            print(f"✓ Success ({elapsed:.2f}s) - Using: {result['provider_used']}")
            print(f"✓ Facts checked: {len(result['fact_checks'])}")
            print(f"✓ Quality score: {result['quality_score'] * 100:.1f}%")
            
            # Verify provider was actually used as requested
            if provider_name != "auto" and not result['provider_used'].startswith(provider_name):
                print(f"⚠️ Warning: Requested {provider_name} but got {result['provider_used']}")
            
            return {
                "success": True,
                "provider_requested": provider_name,
                "provider_used": result['provider_used'],
                "facts_checked": len(result['fact_checks']),
                "quality_score": result['quality_score'],
                "elapsed_seconds": elapsed
            }
        else:
            print(f"✗ Error: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        return {
            "success": False,
            "error": "Exception",
            "details": str(e)
        }

def run_all_tests():
    """Run tests for all providers and test cases"""
    results = {}
    
    for provider in ["auto", "ollama", "bedrock"]:
        provider_results = {}
        for case in TEST_CONTENT.keys():
            provider_results[case] = test_provider(provider, case)
        results[provider] = provider_results
    
    print("\n==== SUMMARY ====")
    for provider, provider_results in results.items():
        success_count = sum(1 for r in provider_results.values() if r["success"])
        print(f"{provider.upper()}: {success_count}/{len(provider_results)} tests passed")
    
    return results

if __name__ == "__main__":
    print("FinSight LLM Provider Switch Test")
    print("=================================")
    
    # First check API health to confirm both providers
    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=5).json()
        print(f"API Status: {health['status']}")
        print(f"Available Providers:")
        for name, info in health['providers'].items():
            print(f"- {name}: {info['status']}")
        print(f"Current Provider: {health['current_provider']}")
    except Exception as e:
        print(f"Error checking API health: {e}")
        exit(1)
    
    # Run the tests
    print("\nRunning provider switch tests...")
    results = run_all_tests()
