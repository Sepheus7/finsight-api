#!/usr/bin/env python3
"""
Multi-Source Integration Test Suite
Tests the integrated multi-source fact checking capabilities and fallback behavior
"""

import json
import requests
import time
from typing import Dict, Any, List
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiSourceIntegrationTester:
    """Comprehensive tester for multi-source integration capabilities"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.test_results = []
    
    def test_health_endpoint(self) -> Dict[str, Any]:
        """Test health endpoint and multi-source status"""
        logger.info("Testing health endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                
                result = {
                    "test": "health_endpoint",
                    "status": "PASS",
                    "data": health_data,
                    "multi_source_available": health_data.get("enhanced_features", {}).get("multi_source_fact_checking", False),
                    "bedrock_available": health_data.get("providers", {}).get("bedrock", {}).get("status") == "available",
                    "current_provider": health_data.get("current_provider")
                }
                
                logger.info(f"Health check PASSED - Multi-source: {result['multi_source_available']}, Bedrock: {result['bedrock_available']}")
                return result
            else:
                result = {
                    "test": "health_endpoint",
                    "status": "FAIL",
                    "error": f"HTTP {response.status_code}",
                    "data": None
                }
                logger.error(f"Health check FAILED: {result['error']}")
                return result
                
        except Exception as e:
            result = {
                "test": "health_endpoint",
                "status": "ERROR",
                "error": str(e),
                "data": None
            }
            logger.error(f"Health check ERROR: {result['error']}")
            return result
    
    def test_enhance_endpoint_basic(self) -> Dict[str, Any]:
        """Test basic enhance endpoint functionality"""
        logger.info("Testing basic enhance endpoint...")
        
        test_content = "Apple stock is currently trading at $150 and Tesla stock is at $200."
        
        payload = {
            "ai_response": {
                "content": test_content,
                "agent_id": "test-agent",
                "timestamp": "2025-05-27T22:30:00Z"
            },
            "enrichment_level": "comprehensive",
            "fact_check": True,
            "add_context": True,
            "llm_provider": "bedrock"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/enhance",
                json=payload,
                timeout=30
            )
            processing_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                enhance_data = response.json()
                
                result = {
                    "test": "enhance_endpoint_basic",
                    "status": "PASS",
                    "processing_time_ms": processing_time,
                    "api_processing_time_ms": enhance_data.get("processing_time_ms", 0),
                    "fact_checks_count": len(enhance_data.get("fact_checks", [])),
                    "context_additions_count": len(enhance_data.get("context_additions", [])),
                    "quality_score": enhance_data.get("quality_score", 0),
                    "provider_used": enhance_data.get("provider_used"),
                    "compliance_flags": enhance_data.get("compliance_flags", []),
                    "enhanced_content_length": len(enhance_data.get("enhanced_content", "")),
                    "original_content_length": len(enhance_data.get("original_content", "")),
                    "enhancement_ratio": len(enhance_data.get("enhanced_content", "")) / max(1, len(enhance_data.get("original_content", ""))),
                    "data": enhance_data
                }
                
                logger.info(f"Basic enhance test PASSED - {result['fact_checks_count']} fact checks, {result['context_additions_count']} context additions")
                return result
            else:
                result = {
                    "test": "enhance_endpoint_basic",
                    "status": "FAIL",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "data": None
                }
                logger.error(f"Basic enhance test FAILED: {result['error']}")
                return result
                
        except Exception as e:
            result = {
                "test": "enhance_endpoint_basic",
                "status": "ERROR",
                "error": str(e),
                "data": None
            }
            logger.error(f"Basic enhance test ERROR: {result['error']}")
            return result
    
    def test_provider_switching(self) -> Dict[str, Any]:
        """Test provider switching functionality"""
        logger.info("Testing provider switching...")
        
        test_content = "AAPL is trading at $175 per share."
        providers_to_test = ["auto", "bedrock", "ollama"]
        provider_results = {}
        
        for provider in providers_to_test:
            logger.info(f"Testing provider: {provider}")
            
            payload = {
                "ai_response": {
                    "content": test_content,
                    "agent_id": "test-agent",
                    "timestamp": "2025-05-27T22:30:00Z"
                },
                "enrichment_level": "comprehensive",
                "fact_check": True,
                "add_context": True,
                "llm_provider": provider
            }
            
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/enhance",
                    json=payload,
                    timeout=30
                )
                processing_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    enhance_data = response.json()
                    provider_results[provider] = {
                        "status": "PASS",
                        "processing_time_ms": processing_time,
                        "provider_used": enhance_data.get("provider_used"),
                        "fact_checks_count": len(enhance_data.get("fact_checks", [])),
                        "quality_score": enhance_data.get("quality_score", 0)
                    }
                    logger.info(f"Provider {provider} PASSED - used {provider_results[provider]['provider_used']}")
                else:
                    provider_results[provider] = {
                        "status": "FAIL",
                        "error": f"HTTP {response.status_code}",
                        "processing_time_ms": processing_time
                    }
                    logger.warning(f"Provider {provider} FAILED: {provider_results[provider]['error']}")
                    
            except Exception as e:
                provider_results[provider] = {
                    "status": "ERROR",
                    "error": str(e),
                    "processing_time_ms": 0
                }
                logger.error(f"Provider {provider} ERROR: {provider_results[provider]['error']}")
        
        # Analyze results
        passed_providers = [p for p, r in provider_results.items() if r["status"] == "PASS"]
        result = {
            "test": "provider_switching",
            "status": "PASS" if len(passed_providers) > 0 else "FAIL",
            "providers_tested": providers_to_test,
            "providers_passed": passed_providers,
            "provider_results": provider_results,
            "primary_provider_working": "bedrock" in passed_providers or "auto" in passed_providers
        }
        
        logger.info(f"Provider switching test {'PASSED' if result['status'] == 'PASS' else 'FAILED'} - {len(passed_providers)}/{len(providers_to_test)} providers working")
        return result
    
    def test_complex_financial_content(self) -> Dict[str, Any]:
        """Test complex financial content with multiple claims"""
        logger.info("Testing complex financial content...")
        
        test_content = """
        Market Update: Apple (AAPL) is currently trading at $175.50, up 2.3% from yesterday. 
        Microsoft (MSFT) closed at $420.75, while Tesla (TSLA) reached $180.25. 
        Analysts predict AAPL will increase by 15% over the next quarter due to strong iPhone sales.
        The overall market cap of Apple is approximately $2.8 trillion.
        Investment recommendation: Consider buying tech stocks for long-term growth.
        """
        
        payload = {
            "ai_response": {
                "content": test_content,
                "agent_id": "test-agent",
                "timestamp": "2025-05-27T22:30:00Z"
            },
            "enrichment_level": "comprehensive",
            "fact_check": True,
            "add_context": True,
            "llm_provider": "bedrock"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/enhance",
                json=payload,
                timeout=45
            )
            processing_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                enhance_data = response.json()
                
                # Analyze the response
                fact_checks = enhance_data.get("fact_checks", [])
                context_additions = enhance_data.get("context_additions", [])
                compliance_flags = enhance_data.get("compliance_flags", [])
                
                # Count different types of claims
                stock_price_claims = len([fc for fc in fact_checks if "trading" in fc.get("claim", "").lower() or "price" in fc.get("claim", "").lower()])
                prediction_claims = len([fc for fc in fact_checks if "predict" in fc.get("claim", "").lower() or "increase" in fc.get("claim", "").lower()])
                
                result = {
                    "test": "complex_financial_content",
                    "status": "PASS",
                    "processing_time_ms": processing_time,
                    "total_fact_checks": len(fact_checks),
                    "stock_price_claims": stock_price_claims,
                    "prediction_claims": prediction_claims,
                    "context_additions": len(context_additions),
                    "compliance_flags": len(compliance_flags),
                    "quality_score": enhance_data.get("quality_score", 0),
                    "enhanced_content_contains_disclaimers": "disclaimer" in enhance_data.get("enhanced_content", "").lower(),
                    "enhanced_content_contains_risk_warning": "risk" in enhance_data.get("enhanced_content", "").lower(),
                    "fact_checks_details": fact_checks,
                    "compliance_flags_details": compliance_flags,
                    "data": enhance_data
                }
                
                logger.info(f"Complex content test PASSED - {result['total_fact_checks']} fact checks, quality score: {result['quality_score']}")
                return result
            else:
                result = {
                    "test": "complex_financial_content",
                    "status": "FAIL",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "data": None
                }
                logger.error(f"Complex content test FAILED: {result['error']}")
                return result
                
        except Exception as e:
            result = {
                "test": "complex_financial_content",
                "status": "ERROR",
                "error": str(e),
                "data": None
            }
            logger.error(f"Complex content test ERROR: {result['error']}")
            return result
    
    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run all tests and generate comprehensive report"""
        logger.info("🚀 Starting comprehensive multi-source integration test suite...")
        
        test_start_time = time.time()
        
        # Run all tests
        test_methods = [
            self.test_health_endpoint,
            self.test_enhance_endpoint_basic,
            self.test_provider_switching,
            self.test_complex_financial_content
        ]
        
        all_results = []
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for test_method in test_methods:
            try:
                result = test_method()
                all_results.append(result)
                
                if result["status"] == "PASS":
                    passed_tests += 1
                elif result["status"] == "FAIL":
                    failed_tests += 1
                else:
                    error_tests += 1
                    
            except Exception as e:
                logger.error(f"Test method {test_method.__name__} crashed: {e}")
                all_results.append({
                    "test": test_method.__name__,
                    "status": "ERROR",
                    "error": f"Test method crashed: {str(e)}",
                    "data": None
                })
                error_tests += 1
        
        total_test_time = (time.time() - test_start_time) * 1000
        
        # Generate summary
        summary = {
            "test_suite": "multi_source_integration",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": len(test_methods),
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "success_rate": passed_tests / len(test_methods) * 100,
            "total_test_time_ms": total_test_time,
            "all_results": all_results
        }
        
        # Extract key insights
        health_result = next((r for r in all_results if r["test"] == "health_endpoint"), {})
        provider_result = next((r for r in all_results if r["test"] == "provider_switching"), {})
        
        summary["system_status"] = {
            "multi_source_available": health_result.get("multi_source_available", False),
            "bedrock_available": health_result.get("bedrock_available", False),
            "current_provider": health_result.get("current_provider", "unknown"),
            "working_providers": provider_result.get("providers_passed", [])
        }
        
        # Overall assessment
        if passed_tests == len(test_methods):
            summary["overall_status"] = "ALL_TESTS_PASSED"
        elif passed_tests > 0:
            summary["overall_status"] = "PARTIAL_SUCCESS"
        else:
            summary["overall_status"] = "ALL_TESTS_FAILED"
        
        logger.info(f"✅ Test suite completed: {passed_tests}/{len(test_methods)} tests passed ({summary['success_rate']:.1f}%)")
        logger.info(f"📊 Overall status: {summary['overall_status']}")
        
        return summary

def main():
    """Main test execution"""
    print("=" * 80)
    print("🔍 MULTI-SOURCE INTEGRATION TEST SUITE")
    print("=" * 80)
    
    # Check if server is running
    tester = MultiSourceIntegrationTester()
    
    try:
        # Quick connectivity test
        response = requests.get(f"{tester.base_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not responding at {tester.base_url}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server at {tester.base_url}: {e}")
        print("💡 Make sure the server is running: python demo/llm_api_server.py")
        return
    
    # Run comprehensive test suite
    results = tester.run_comprehensive_test_suite()
    
    # Print detailed results
    print("\n" + "=" * 80)
    print("📋 DETAILED TEST RESULTS")
    print("=" * 80)
    
    for result in results["all_results"]:
        status_emoji = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
        print(f"\n{status_emoji} {result['test'].upper().replace('_', ' ')}")
        print(f"   Status: {result['status']}")
        
        if result["status"] == "PASS":
            # Print relevant metrics
            if "processing_time_ms" in result:
                print(f"   Processing Time: {result['processing_time_ms']:.1f}ms")
            if "fact_checks_count" in result:
                print(f"   Fact Checks: {result['fact_checks_count']}")
            if "quality_score" in result:
                print(f"   Quality Score: {result['quality_score']:.2f}")
            if "provider_used" in result:
                print(f"   Provider Used: {result['provider_used']}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"🎯 Overall Status: {results['overall_status']}")
    print(f"📈 Success Rate: {results['success_rate']:.1f}% ({results['passed_tests']}/{results['total_tests']} tests passed)")
    print(f"⏱️  Total Test Time: {results['total_test_time_ms']:.1f}ms")
    
    print(f"\n🔧 System Status:")
    system_status = results["system_status"]
    print(f"   Multi-Source Available: {'✅' if system_status['multi_source_available'] else '❌'}")
    print(f"   Bedrock Available: {'✅' if system_status['bedrock_available'] else '❌'}")
    print(f"   Current Provider: {system_status['current_provider']}")
    print(f"   Working Providers: {', '.join(system_status['working_providers']) if system_status['working_providers'] else 'None'}")
    
    # Save results to file
    results_file = f"/Users/romainboluda/Documents/PersonalProjects/FinSight/demo/test_results_multi_source_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()
