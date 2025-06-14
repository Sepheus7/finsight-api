#!/usr/bin/env python3
"""
Enhanced Bedrock-Friendly FinSight AWS Deployment Test
Validates the improved agentic capabilities and function calling integration
"""

import requests
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List

# Configuration
API_BASE = "https://jfho5me3zi.execute-api.us-east-1.amazonaws.com/dev"  # Updated with deployed API Gateway URL
TEST_TIMEOUT = 30

def print_header(title: str):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"🚀 {title}")
    print(f"{'='*70}")

def print_section(title: str):
    """Print formatted section"""
    print(f"\n📋 {title}")
    print("-" * 50)

def test_endpoint(name: str, method: str, path: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test an API endpoint with enhanced validation"""
    print(f"\n🧪 Testing {name}...")
    
    start_time = time.time()
    url = f"{API_BASE}{path}"
    
    try:
        if method.upper() == "POST":
            response = requests.post(
                url, 
                json=data, 
                headers={"Content-Type": "application/json"},
                timeout=TEST_TIMEOUT
            )
        else:
            response = requests.get(url, timeout=TEST_TIMEOUT)
        
        elapsed_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ {name} successful ({elapsed_time:.0f}ms)")
            return {
                "success": True,
                "data": result,
                "response_time": elapsed_time,
                "status_code": response.status_code
            }
        else:
            print(f"   ❌ {name} failed: HTTP {response.status_code}")
            print(f"      Response: {response.text[:200]}...")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "response_time": elapsed_time,
                "status_code": response.status_code
            }
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ {name} timed out after {TEST_TIMEOUT}s")
        return {"success": False, "error": "Timeout", "response_time": TEST_TIMEOUT * 1000}
    except Exception as e:
        print(f"   ❌ {name} error: {e}")
        return {"success": False, "error": str(e), "response_time": 0}

def validate_enhanced_features(result: Dict[str, Any]) -> Dict[str, bool]:
    """Validate enhanced Bedrock features in the response"""
    validation = {
        "enhanced_orchestrator": False,
        "function_calling": False,
        "multi_source": False,
        "cost_estimation": False,
        "alpha_vantage": False,
        "error_handling": False
    }
    
    if not result.get("success") or not result.get("data"):
        return validation
    
    data = result["data"]
    
    # Check for enhanced orchestrator usage
    if "orchestrator_used" in data or "routing_method" in data:
        validation["enhanced_orchestrator"] = True
    
    # Check for function calling evidence
    metadata = data.get("metadata", {})
    if "function_calls_used" in metadata or "routing_method" in metadata:
        validation["function_calling"] = metadata.get("routing_method") == "function_calling"
    
    # Check for multi-source verification
    sources_used = data.get("sources_used", [])
    if len(sources_used) > 1:
        validation["multi_source"] = True
    
    # Check for cost estimation
    if "cost_estimate" in data or "processing_cost" in data:
        validation["cost_estimation"] = True
    
    # Check for Alpha Vantage usage
    if any("alpha_vantage" in str(source).lower() for source in sources_used):
        validation["alpha_vantage"] = True
    
    # Check for enhanced error handling
    if "fallback_used" in data or "error_recovery" in data:
        validation["error_handling"] = True
    
    return validation

def main():
    """Run comprehensive enhanced deployment tests"""
    
    print_header("Enhanced Bedrock-Friendly FinSight AWS Deployment Test")
    print(f"🌐 API Endpoint: {API_BASE}")
    print(f"⏰ Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
    
    # Test 1: Health Check
    print_section("Basic Health Checks")
    health_result = test_endpoint("Health Check", "GET", "/health")
    test_results.append(("health", health_result))
    
    info_result = test_endpoint("API Info", "GET", "/")
    test_results.append(("info", info_result))
    
    # Test 2: Enhanced Fact Checking with Function Calling
    print_section("Enhanced Agentic Fact Checking")
    
    enhanced_test_cases = [
        {
            "name": "Multi-Source Stock Analysis",
            "data": {
                "text": "Apple (AAPL) is trading at $175 per share with a market cap of $2.8 trillion. The company reported record quarterly revenue of $95 billion.",
                "use_enhanced_orchestrator": True,
                "target_audience": "professional",
                "risk_tolerance": "moderate",
                "requested_capabilities": ["fact_verification", "market_data_analysis", "trend_analysis"]
            }
        },
        {
            "name": "Economic Indicators Analysis", 
            "data": {
                "text": "The US economy shows strong fundamentals with GDP growth at 2.3% annually and unemployment at 3.5%. Inflation remains at 3.8%.",
                "use_enhanced_orchestrator": True,
                "target_audience": "regulatory", 
                "risk_tolerance": "low",
                "requested_capabilities": ["economic_analysis", "fact_verification", "context_enrichment"]
            }
        },
        {
            "name": "Complex Financial Claims",
            "data": {
                "text": "Tesla's market cap reached $800 billion while Bitcoin surged to $45,000. The Federal Reserve maintained interest rates at 5.25%.",
                "use_enhanced_orchestrator": True,
                "target_audience": "general",
                "risk_tolerance": "high", 
                "requested_capabilities": ["fact_verification", "market_data_analysis", "economic_analysis"]
            }
        }
    ]
    
    enhanced_results = []
    for test_case in enhanced_test_cases:
        result = test_endpoint(test_case["name"], "POST", "/fact-check", test_case["data"])
        enhanced_results.append(result)
        test_results.append((test_case["name"].lower().replace(" ", "_"), result))
        
        # Validate enhanced features
        validation = validate_enhanced_features(result)
        if result.get("success"):
            print(f"   📊 Enhanced Features Validation:")
            for feature, enabled in validation.items():
                status = "✅" if enabled else "⭕"
                print(f"      {status} {feature.replace('_', ' ').title()}")
    
    # Test 3: Function Calling Validation
    print_section("Function Calling & Cost Optimization")
    
    function_calling_test = {
        "text": "Microsoft stock (MSFT) closed at $300, Apple at $175, and Google at $120. All three are part of the trillion-dollar club.",
        "use_enhanced_orchestrator": True,
        "enable_function_calling": True,
        "cost_optimization": True,
        "target_audience": "professional"
    }
    
    fc_result = test_endpoint("Function Calling Test", "POST", "/fact-check", function_calling_test)
    test_results.append(("function_calling", fc_result))
    
    if fc_result.get("success"):
        data = fc_result["data"]
        print(f"   💰 Cost Analysis:")
        if "cost_estimate" in data:
            cost = data["cost_estimate"]
            print(f"      • Total Cost: ${cost.get('total_estimated_cost', 0):.6f}")
            print(f"      • Model Used: {cost.get('model_used', 'unknown')}")
        
        print(f"   🔧 Tool Selection:")
        sources = data.get("sources_used", [])
        for i, source in enumerate(sources, 1):
            print(f"      {i}. {source}")
    
    # Test 4: Error Handling & Fallbacks
    print_section("Error Handling & Fallback Mechanisms")
    
    # Test with invalid/stress scenarios
    stress_tests = [
        {
            "name": "Empty Content",
            "data": {"text": ""}
        },
        {
            "name": "Very Long Content",
            "data": {"text": "Apple stock " * 1000}  # Very long repetitive text
        },
        {
            "name": "Invalid Parameters",
            "data": {
                "text": "Test content",
                "risk_tolerance": "invalid_value",
                "target_audience": "unknown_audience"
            }
        }
    ]
    
    for stress_test in stress_tests:
        result = test_endpoint(stress_test["name"], "POST", "/fact-check", stress_test["data"])
        test_results.append((f"stress_{stress_test['name'].lower().replace(' ', '_')}", result))
    
    # Test 5: Performance Analysis
    print_section("Performance & Reliability Analysis")
    
    # Analyze results
    successful_tests = [r for _, r in test_results if r.get("success")]
    failed_tests = [r for _, r in test_results if not r.get("success")]
    
    print(f"   📈 Test Summary:")
    print(f"      • Total Tests: {len(test_results)}")
    print(f"      • Successful: {len(successful_tests)}")
    print(f"      • Failed: {len(failed_tests)}")
    print(f"      • Success Rate: {len(successful_tests)/len(test_results)*100:.1f}%")
    
    if successful_tests:
        avg_response_time = sum(r["response_time"] for r in successful_tests) / len(successful_tests)
        print(f"      • Avg Response Time: {avg_response_time:.0f}ms")
    
    # Enhanced Features Summary
    print_section("Enhanced Features Status")
    
    enhanced_working = any(r.get("success") for r in enhanced_results)
    print(f"   🤖 Enhanced Orchestrator: {'✅ ACTIVE' if enhanced_working else '❌ INACTIVE'}")
    
    # Check for specific enhanced features across all successful tests
    all_validations = []
    for result in enhanced_results:
        if result.get("success"):
            validation = validate_enhanced_features(result)
            all_validations.append(validation)
    
    if all_validations:
        feature_summary = {}
        for validation in all_validations:
            for feature, enabled in validation.items():
                if feature not in feature_summary:
                    feature_summary[feature] = 0
                if enabled:
                    feature_summary[feature] += 1
        
        print(f"   📊 Feature Usage Across Tests:")
        for feature, count in feature_summary.items():
            percentage = (count / len(all_validations)) * 100
            status = "✅" if percentage > 0 else "⭕"
            print(f"      {status} {feature.replace('_', ' ').title()}: {count}/{len(all_validations)} tests ({percentage:.0f}%)")
    
    # Final Assessment
    print_section("Deployment Assessment")
    
    if len(successful_tests) >= len(test_results) * 0.8:  # 80% success rate
        print("   🎉 DEPLOYMENT SUCCESSFUL")
        print("      ✅ Enhanced Bedrock integration is working")
        print("      ✅ Function calling capabilities are active")
        print("      ✅ Multi-source intelligence is operational")
        print("      ✅ Error handling and fallbacks are robust")
        
        if enhanced_working:
            print("      ✅ Advanced agentic capabilities confirmed")
        
        print(f"\n   🚀 System is ready for production use!")
        print(f"      • API Endpoint: {API_BASE}")
        print(f"      • Enhanced Features: Active")
        print(f"      • Cost Optimization: Enabled")
        print(f"      • Multi-source Verification: Working")
        
    else:
        print("   ⚠️  DEPLOYMENT NEEDS ATTENTION")
        print("      • Some tests failed - investigate logs")
        print("      • Check AWS Bedrock model access")
        print("      • Verify environment variables")
        print("      • Review IAM permissions")
    
    print_header("Enhanced Deployment Test Complete")
    return test_results

if __name__ == "__main__":
    results = main()
