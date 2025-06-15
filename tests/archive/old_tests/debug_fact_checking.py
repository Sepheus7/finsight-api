#!/usr/bin/env python3
"""Debug claim extraction from the API server"""

import json
import requests

# Test the current API server's claim extraction
test_content = "Apple Inc (AAPL) stock is currently trading at $150 and will definitely increase by 50% next month. Tesla stock (TSLA) is also guaranteed to double in value."

# Make request to the enhance endpoint with detailed logging
response = requests.post('http://localhost:8000/enhance', 
    json={
        "ai_response": {
            "content": test_content,
            "agent_id": "debug_test",
            "timestamp": "2025-05-29T18:00:00Z"
        },
        "enrichment_level": "comprehensive",
        "fact_check": True,
        "add_context": True
    }
)

print("Status Code:", response.status_code)
print("\nResponse JSON:")
print(json.dumps(response.json(), indent=2))

# Check specifically for fact checks
result = response.json()
print(f"\nFact Checks Found: {len(result.get('fact_checks', []))}")
print(f"Provider Used: {result.get('provider_used', 'Unknown')}")
print(f"Processing Time: {result.get('processing_time_ms', 0)}ms")

if result.get('fact_checks'):
    for i, fact in enumerate(result['fact_checks']):
        print(f"\nFact Check {i+1}:")
        print(f"  Claim: {fact.get('claim', 'N/A')}")
        print(f"  Verified: {fact.get('verified', 'N/A')}")
        print(f"  Confidence: {fact.get('confidence', 0)}")
        print(f"  Source: {fact.get('source', 'N/A')}")
