#!/usr/bin/env python3
"""
Direct API endpoint test to debug fact checking issue
"""

import asyncio
import sys
import os

# Add the demo directory to the path
sys.path.insert(0, '/Users/romainboluda/Documents/PersonalProjects/FinSight/demo')

from llm_api_server import enhance_ai_response, EnrichmentRequest, AIResponse

async def test_api_endpoint_directly():
    """Test the enhance API endpoint directly"""
    
    # Create the request object
    request = EnrichmentRequest(
        ai_response=AIResponse(
            content="Apple Inc (AAPL) stock is currently trading at $150 and will definitely increase by 50% next month.",
            agent_id="test_agent",
            timestamp="2025-05-29T10:00:00Z"
        ),
        llm_provider="ollama"
    )
    
    print("Testing API endpoint directly...")
    
    try:
        # Call the API endpoint function directly
        response = await enhance_ai_response(request)
        
        print(f"Response type: {type(response)}")
        print(f"Original content: {response.original_content[:100]}...")
        print(f"Fact checks count: {len(response.fact_checks)}")
        print(f"Provider used: {response.provider_used}")
        
        if response.fact_checks:
            for i, fact_check in enumerate(response.fact_checks):
                print(f"  Fact check {i+1}: {fact_check.claim}")
                print(f"    Verified: {fact_check.verified}")
                print(f"    Confidence: {fact_check.confidence}")
        else:
            print("  No fact checks found!")
        
        return response
        
    except Exception as e:
        print(f"Error calling API endpoint: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_api_endpoint_directly())
