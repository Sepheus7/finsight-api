#!/usr/bin/env python3
"""
Test script to verify frontend demo functionality
Tests all the key components that should work in the demo
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health endpoint"""
    print("🔍 Testing Health Endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health endpoint working: {health_data}")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_enhance_endpoint():
    """Test the enhance endpoint with sample scenarios"""
    scenarios = {
        "investment": {
            "content": "AAPL stock is currently trading at $150 and I recommend buying it immediately. This is a guaranteed profitable investment that will definitely make you money.",
            "expected_issues": ["guaranteed", "investment"]
        },
        "market": {
            "content": "The S&P 500 has shown strong performance this quarter, with technology stocks leading the gains. Market volatility remains elevated due to ongoing economic uncertainties.",
            "expected_issues": []
        },
        "crypto": {
            "content": "Cryptocurrency markets continue to evolve with increasing institutional adoption. Bitcoin and Ethereum remain the dominant digital assets by market capitalization.",
            "expected_issues": []
        }
    }
    
    print("\n🔍 Testing Enhance Endpoint...")
    
    for scenario_name, scenario_data in scenarios.items():
        print(f"\n  Testing {scenario_name} scenario...")
        
        payload = {
            "ai_response": {
                "content": scenario_data["content"],
                "agent_id": "frontend_test",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            "enrichment_level": "comprehensive",
            "fact_check": True,
            "add_context": True
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_BASE_URL}/enhance",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                processing_time = (end_time - start_time) * 1000
                
                print(f"    ✅ Status: {response.status_code}")
                print(f"    ⏱️  Processing time: {processing_time:.0f}ms")
                print(f"    📊 Quality score: {result.get('quality_score', 0):.2f}")
                print(f"    🚨 Compliance flags: {len(result.get('compliance_flags', []))}")
                print(f"    🔍 Fact checks: {len(result.get('fact_checks', []))}")
                print(f"    📖 Context additions: {len(result.get('context_additions', []))}")
                
                # Check for expected issues in investment scenario
                if scenario_name == "investment":
                    compliance_flags = result.get('compliance_flags', [])
                    if len(compliance_flags) > 0:
                        print(f"    ✅ Detected compliance issues: {compliance_flags}")
                    else:
                        print(f"    ⚠️  Expected compliance issues but found none")
                
            else:
                print(f"    ❌ Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")

def test_cors_headers():
    """Test CORS headers for frontend compatibility"""
    print("\n🔍 Testing CORS Headers...")
    try:
        response = requests.options(f"{API_BASE_URL}/enhance")
        headers = response.headers
        
        cors_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers'
        ]
        
        for header in cors_headers:
            if header in headers:
                print(f"    ✅ {header}: {headers[header]}")
            else:
                print(f"    ⚠️  Missing {header}")
                
    except Exception as e:
        print(f"    ❌ CORS test error: {e}")

def main():
    """Run all tests"""
    print("🚀 FinSight Frontend Functionality Test")
    print("=" * 50)
    
    # Test API endpoints
    health_ok = test_health_endpoint()
    if health_ok:
        test_enhance_endpoint()
        test_cors_headers()
    else:
        print("❌ Cannot proceed with other tests - health endpoint failed")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
    print("\nTo test the frontend manually:")
    print(f"   1. Open http://localhost:8080/demo-fixed.html")
    print(f"   2. Click on sample scenarios to load content")
    print(f"   3. Click 'Enhance Content with FinSight' button")
    print(f"   4. Verify results display correctly")

if __name__ == "__main__":
    main()
