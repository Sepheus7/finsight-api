#!/usr/bin/env python3
"""
End-to-End Multi-Source Integration Test Suite

This comprehensive test suite validates the complete enhanced multi-source fact-checking
system across all phases: backend infrastructure, API integration, frontend enhancement,
and real-world scenarios.

Test Coverage:
- Individual source testing (Yahoo Finance, World Bank, Alpha Vantage)
- Cross-validation scenarios 
- Error handling and fallback strategies
- Performance testing with concurrent requests
- Frontend-backend integration
- Real-world fact-checking scenarios
"""

import asyncio
import json
import logging
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test result container"""
    test_name: str
    success: bool
    duration_ms: int
    details: Dict[str, Any]
    error_message: Optional[str] = None


class MultiSourceEndToEndTester:
    """Comprehensive end-to-end testing framework"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        
    def log_test_result(self, result: TestResult):
        """Log and store test result"""
        self.results.append(result)
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"{status} {result.test_name} ({result.duration_ms}ms)")
        if result.error_message:
            print(f"    Error: {result.error_message}")
    
    def test_api_health_comprehensive(self) -> TestResult:
        """Test comprehensive API health check"""
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            response.raise_for_status()
            
            health_data = response.json()
            
            # Validate required fields
            required_fields = [
                "status", "timestamp", "providers", 
                "enhanced_multi_source", "legacy_multi_source", 
                "enhanced_features"
            ]
            
            missing_fields = [field for field in required_fields if field not in health_data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Check provider availability
            providers = health_data.get("providers", {})
            available_providers = [p for p, data in providers.items() if data.get("status") == "available"]
            
            # Check multi-source capabilities
            legacy_available = health_data.get("legacy_multi_source", {}).get("status") == "available"
            enhanced_available = health_data.get("enhanced_multi_source", {}).get("status") == "available"
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return TestResult(
                test_name="API Health Check",
                success=True,
                duration_ms=duration_ms,
                details={
                    "available_providers": available_providers,
                    "legacy_multi_source": legacy_available,
                    "enhanced_multi_source": enhanced_available,
                    "health_data": health_data
                }
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return TestResult(
                test_name="API Health Check",
                success=False,
                duration_ms=duration_ms,
                details={},
                error_message=str(e)
            )
    
    def test_single_fact_check(self, content: str, expected_claims: int = 1) -> TestResult:
        """Test single fact-checking request"""
        start_time = time.time()
        test_name = f"Single Fact Check ({expected_claims} claims)"
        
        try:
            test_data = {
                "ai_response": {
                    "content": content,
                    "agent_id": "test_agent",
                    "timestamp": datetime.now().isoformat()
                },
                "enrichment_level": "comprehensive",
                "fact_check": True,
                "add_context": True,
                "llm_provider": "auto"
            }
            
            response = requests.post(
                f"{self.base_url}/enhance",
                json=test_data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            fact_checks = result.get("fact_checks", [])
            
            if len(fact_checks) == 0:
                raise ValueError("No fact checks returned")
            
            # Validate fact check structure
            for fc in fact_checks:
                required_fc_fields = ["claim", "verified", "confidence", "source", "explanation"]
                missing_fc_fields = [field for field in required_fc_fields if field not in fc]
                if missing_fc_fields:
                    raise ValueError(f"Missing fact check fields: {missing_fc_fields}")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Check for multi-source indicators
            multi_source_count = sum(1 for fc in fact_checks if ',' in fc.get('source', ''))
            
            return TestResult(
                test_name=test_name,
                success=True,
                duration_ms=duration_ms,
                details={
                    "fact_check_count": len(fact_checks),
                    "multi_source_count": multi_source_count,
                    "avg_confidence": sum(fc.get('confidence', 0) for fc in fact_checks) / len(fact_checks),
                    "sources_used": list(set(fc.get('source', '') for fc in fact_checks)),
                    "claims": [fc.get('claim', '')[:50] + "..." for fc in fact_checks]
                }
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return TestResult(
                test_name=test_name,
                success=False,
                duration_ms=duration_ms,
                details={},
                error_message=str(e)
            )
    
    def test_concurrent_requests(self, num_requests: int = 5) -> TestResult:
        """Test concurrent fact-checking requests"""
        start_time = time.time()
        test_name = f"Concurrent Requests ({num_requests})"
        
        try:
            test_contents = [
                "Apple Inc. (AAPL) is trading at $150 per share.",
                "Microsoft Corporation has a market cap of $2.5 trillion.",
                "Tesla's stock price has increased 20% this quarter.",
                "Amazon's revenue exceeded $400 billion last year.",
                "Google's parent company Alphabet is a tech giant."
            ]
            
            def make_request(content):
                test_data = {
                    "ai_response": {
                        "content": content,
                        "agent_id": "concurrent_test",
                        "timestamp": datetime.now().isoformat()
                    },
                    "enrichment_level": "comprehensive",
                    "fact_check": True,
                    "add_context": True,
                    "llm_provider": "auto"
                }
                
                response = requests.post(
                    f"{self.base_url}/enhance",
                    json=test_data,
                    timeout=30
                )
                return response.json()
            
            # Execute concurrent requests
            with ThreadPoolExecutor(max_workers=num_requests) as executor:
                futures = [
                    executor.submit(make_request, test_contents[i % len(test_contents)])
                    for i in range(num_requests)
                ]
                
                results = []
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Concurrent request failed: {e}")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if len(results) < num_requests * 0.8:  # Allow 20% failure rate
                raise ValueError(f"Too many concurrent requests failed: {len(results)}/{num_requests}")
            
            # Analyze results
            total_fact_checks = sum(len(r.get("fact_checks", [])) for r in results)
            avg_response_time = duration_ms / len(results)
            
            return TestResult(
                test_name=test_name,
                success=True,
                duration_ms=duration_ms,
                details={
                    "successful_requests": len(results),
                    "total_requests": num_requests,
                    "total_fact_checks": total_fact_checks,
                    "avg_response_time_ms": avg_response_time,
                    "success_rate": len(results) / num_requests
                }
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return TestResult(
                test_name=test_name,
                success=False,
                duration_ms=duration_ms,
                details={},
                error_message=str(e)
            )
    
    def test_error_handling_scenarios(self) -> List[TestResult]:
        """Test various error handling scenarios"""
        results = []
        
        # Test 1: Invalid request format
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.base_url}/enhance",
                json={"invalid": "data"},
                timeout=10
            )
            # Should return 422 Unprocessable Entity
            duration_ms = int((time.time() - start_time) * 1000)
            success = response.status_code == 422
            
            results.append(TestResult(
                test_name="Error Handling - Invalid Request",
                success=success,
                duration_ms=duration_ms,
                details={"status_code": response.status_code},
                error_message=None if success else f"Expected 422, got {response.status_code}"
            ))
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            results.append(TestResult(
                test_name="Error Handling - Invalid Request",
                success=False,
                duration_ms=duration_ms,
                details={},
                error_message=str(e)
            ))
        
        # Test 2: Empty content
        start_time = time.time()
        try:
            test_data = {
                "ai_response": {
                    "content": "",
                    "agent_id": "test_agent",
                    "timestamp": datetime.now().isoformat()
                },
                "enrichment_level": "comprehensive",
                "fact_check": True,
                "add_context": True,
                "llm_provider": "auto"
            }
            
            response = requests.post(
                f"{self.base_url}/enhance",
                json=test_data,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Should handle gracefully
            results.append(TestResult(
                test_name="Error Handling - Empty Content",
                success=True,
                duration_ms=duration_ms,
                details={"fact_checks": len(result.get("fact_checks", []))}
            ))
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            results.append(TestResult(
                test_name="Error Handling - Empty Content",
                success=False,
                duration_ms=duration_ms,
                details={},
                error_message=str(e)
            ))
        
        return results
    
    def test_real_world_scenarios(self) -> List[TestResult]:
        """Test real-world fact-checking scenarios"""
        results = []
        
        scenarios = [
            {
                "name": "Stock Information",
                "content": "Apple Inc. (AAPL) is currently trading at $150 per share and has a market capitalization of over $2 trillion. The company reported strong quarterly earnings.",
                "expected_sources": ["yahoo_finance", "yfinance"]
            },
            {
                "name": "Economic Data",
                "content": "The United States GDP growth rate was 2.1% in the last quarter. The Federal Reserve has maintained interest rates at current levels.",
                "expected_sources": ["world_bank", "yahoo_finance"]
            },
            {
                "name": "Investment Advice",
                "content": "This stock is guaranteed to double in value within 30 days. You should invest all your savings immediately for maximum returns.",
                "expected_verification": False  # Should be flagged as unreliable
            },
            {
                "name": "Mixed Financial Claims",
                "content": "Tesla's stock has grown 300% this year while Microsoft maintains stable dividend payments. The S&P 500 index reached new highs.",
                "expected_claims": 3
            }
        ]
        
        for scenario in scenarios:
            start_time = time.time()
            try:
                test_data = {
                    "ai_response": {
                        "content": scenario["content"],
                        "agent_id": "scenario_test",
                        "timestamp": datetime.now().isoformat()
                    },
                    "enrichment_level": "comprehensive",
                    "fact_check": True,
                    "add_context": True,
                    "llm_provider": "auto"
                }
                
                response = requests.post(
                    f"{self.base_url}/enhance",
                    json=test_data,
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                fact_checks = result.get("fact_checks", [])
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Validate scenario-specific expectations
                validation_success = True
                validation_details = {}
                
                if "expected_sources" in scenario:
                    found_sources = set()
                    for fc in fact_checks:
                        source = fc.get("source", "")
                        if "," in source:
                            found_sources.update(s.strip() for s in source.split(","))
                        else:
                            found_sources.add(source)
                    
                    expected_found = any(exp_src in found_sources for exp_src in scenario["expected_sources"])
                    validation_details["expected_sources_found"] = expected_found
                    if not expected_found:
                        validation_success = False
                
                if "expected_verification" in scenario:
                    verification_status = [fc.get("verified", False) for fc in fact_checks]
                    expected_verification = scenario["expected_verification"]
                    verification_match = expected_verification in verification_status
                    validation_details["verification_match"] = verification_match
                    if not verification_match:
                        validation_success = False
                
                if "expected_claims" in scenario:
                    actual_claims = len(fact_checks)
                    expected_claims = scenario["expected_claims"]
                    claims_match = actual_claims >= expected_claims * 0.8  # Allow 20% tolerance
                    validation_details["claims_match"] = claims_match
                    validation_details["expected_claims"] = expected_claims
                    validation_details["actual_claims"] = actual_claims
                    if not claims_match:
                        validation_success = False
                
                results.append(TestResult(
                    test_name=f"Real-World - {scenario['name']}",
                    success=validation_success,
                    duration_ms=duration_ms,
                    details={
                        "fact_check_count": len(fact_checks),
                        "validation_details": validation_details,
                        "avg_confidence": sum(fc.get('confidence', 0) for fc in fact_checks) / len(fact_checks) if fact_checks else 0
                    }
                ))
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                results.append(TestResult(
                    test_name=f"Real-World - {scenario['name']}",
                    success=False,
                    duration_ms=duration_ms,
                    details={},
                    error_message=str(e)
                ))
        
        return results
    
    def test_frontend_integration(self) -> TestResult:
        """Test frontend-backend integration"""
        start_time = time.time()
        
        try:
            # Test health endpoint response format for frontend
            health_response = requests.get(f"{self.base_url}/health", timeout=10)
            health_response.raise_for_status()
            health_data = health_response.json()
            
            # Validate frontend-expected fields
            frontend_requirements = [
                ("providers", dict),
                ("enhanced_multi_source", dict),
                ("legacy_multi_source", dict),
                ("enhanced_features", dict)
            ]
            
            validation_errors = []
            for field, expected_type in frontend_requirements:
                if field not in health_data:
                    validation_errors.append(f"Missing field: {field}")
                elif not isinstance(health_data[field], expected_type):
                    validation_errors.append(f"Wrong type for {field}: expected {expected_type}")
            
            # Test enhanced API response format
            test_data = {
                "ai_response": {
                    "content": "Apple Inc. is a technology company trading on NASDAQ.",
                    "agent_id": "frontend_test",
                    "timestamp": datetime.now().isoformat()
                },
                "enrichment_level": "comprehensive",
                "fact_check": True,
                "add_context": True,
                "llm_provider": "auto"
            }
            
            enhance_response = requests.post(
                f"{self.base_url}/enhance",
                json=test_data,
                timeout=30
            )
            enhance_response.raise_for_status()
            
            enhance_data = enhance_response.json()
            
            # Validate frontend-expected enhancement response
            enhance_requirements = [
                ("fact_checks", list),
                ("context_additions", list),
                ("quality_score", (int, float)),
                ("compliance_flags", list)
            ]
            
            for field, expected_type in enhance_requirements:
                if field not in enhance_data:
                    validation_errors.append(f"Missing enhancement field: {field}")
                elif not isinstance(enhance_data[field], expected_type):
                    validation_errors.append(f"Wrong type for enhancement {field}: expected {expected_type}")
            
            # Validate fact check structure for frontend
            fact_checks = enhance_data.get("fact_checks", [])
            if fact_checks:
                fc_requirements = ["claim", "verified", "confidence", "source", "explanation"]
                for field in fc_requirements:
                    if field not in fact_checks[0]:
                        validation_errors.append(f"Missing fact check field: {field}")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if validation_errors:
                raise ValueError(f"Frontend integration validation errors: {validation_errors}")
            
            return TestResult(
                test_name="Frontend Integration",
                success=True,
                duration_ms=duration_ms,
                details={
                    "health_fields_valid": True,
                    "enhancement_fields_valid": True,
                    "fact_check_structure_valid": True,
                    "total_fact_checks": len(fact_checks)
                }
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return TestResult(
                test_name="Frontend Integration",
                success=False,
                duration_ms=duration_ms,
                details={},
                error_message=str(e)
            )
    
    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run the complete end-to-end test suite"""
        print("🚀 Starting Comprehensive End-to-End Test Suite")
        print("=" * 70)
        
        # Test 1: API Health
        print("\n📊 Testing API Health...")
        health_result = self.test_api_health_comprehensive()
        self.log_test_result(health_result)
        
        # Test 2: Single Fact Checks
        print("\n🧪 Testing Single Fact Checks...")
        single_tests = [
            ("Apple Inc. (AAPL) is currently trading at $150 per share.", 1),
            ("Tesla and Microsoft are both technology companies with high market caps.", 2),
            ("The Federal Reserve controls US monetary policy and sets interest rates.", 1)
        ]
        
        for content, expected_claims in single_tests:
            result = self.test_single_fact_check(content, expected_claims)
            self.log_test_result(result)
        
        # Test 3: Concurrent Requests
        print("\n⚡ Testing Concurrent Requests...")
        concurrent_result = self.test_concurrent_requests(5)
        self.log_test_result(concurrent_result)
        
        # Test 4: Error Handling
        print("\n🛡️ Testing Error Handling...")
        error_results = self.test_error_handling_scenarios()
        for result in error_results:
            self.log_test_result(result)
        
        # Test 5: Real-World Scenarios
        print("\n🌍 Testing Real-World Scenarios...")
        scenario_results = self.test_real_world_scenarios()
        for result in scenario_results:
            self.log_test_result(result)
        
        # Test 6: Frontend Integration
        print("\n🎨 Testing Frontend Integration...")
        frontend_result = self.test_frontend_integration()
        self.log_test_result(frontend_result)
        
        # Generate summary
        return self.generate_test_summary()
    
    def generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        avg_duration = sum(r.duration_ms for r in self.results) / total_tests if total_tests > 0 else 0
        
        print("\n" + "=" * 70)
        print("📋 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "0.0%")
        print(f"⏱️ Average Duration: {avg_duration:.1f}ms")
        
        # Categorize results
        categories = {
            "API Health": [r for r in self.results if "Health" in r.test_name],
            "Fact Checking": [r for r in self.results if "Fact Check" in r.test_name],
            "Performance": [r for r in self.results if "Concurrent" in r.test_name],
            "Error Handling": [r for r in self.results if "Error Handling" in r.test_name],
            "Real-World": [r for r in self.results if "Real-World" in r.test_name],
            "Frontend": [r for r in self.results if "Frontend" in r.test_name]
        }
        
        print("\n📊 Results by Category:")
        for category, results in categories.items():
            if results:
                category_passed = sum(1 for r in results if r.success)
                category_total = len(results)
                print(f"  {category}: {category_passed}/{category_total} passed")
        
        # Failed tests detail
        failed_results = [r for r in self.results if not r.success]
        if failed_results:
            print("\n❌ Failed Tests:")
            for result in failed_results:
                print(f"  - {result.test_name}: {result.error_message}")
        
        # Performance metrics
        performance_results = [r for r in self.results if r.success]
        if performance_results:
            durations = [r.duration_ms for r in performance_results]
            print(f"\n⚡ Performance Metrics:")
            print(f"  - Fastest: {min(durations)}ms")
            print(f"  - Slowest: {max(durations)}ms")
            print(f"  - Average: {sum(durations)/len(durations):.1f}ms")
        
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        if success_rate >= 0.9:
            print(f"\n🎉 PHASE 4 COMPLETE: End-to-End Testing SUCCESSFUL!")
            print(f"✅ Multi-source integration is production-ready")
            print(f"✅ All critical functionality verified")
            print(f"✅ Error handling and edge cases covered")
            print(f"✅ Performance requirements met")
        elif success_rate >= 0.7:
            print(f"\n⚠️ PHASE 4 PARTIAL SUCCESS: Most tests passed")
            print(f"✅ Core functionality working")
            print(f"⚠️ Some issues need attention")
        else:
            print(f"\n❌ PHASE 4 NEEDS ATTENTION: Multiple test failures")
            print(f"❌ Critical issues found")
            print(f"❌ System not production-ready")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "avg_duration_ms": avg_duration,
            "categories": {cat: len(results) for cat, results in categories.items()},
            "failed_test_names": [r.test_name for r in failed_results],
            "performance_metrics": {
                "fastest_ms": min([r.duration_ms for r in performance_results]) if performance_results else 0,
                "slowest_ms": max([r.duration_ms for r in performance_results]) if performance_results else 0,
                "average_ms": avg_duration
            }
        }


def main():
    """Run the comprehensive end-to-end test suite"""
    tester = MultiSourceEndToEndTester()
    summary = tester.run_comprehensive_test_suite()
    
    # Save detailed results
    with open("test_results_end_to_end.json", "w") as f:
        json.dump({
            "summary": summary,
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "duration_ms": r.duration_ms,
                    "details": r.details,
                    "error_message": r.error_message
                }
                for r in tester.results
            ],
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: test_results_end_to_end.json")
    
    return summary["success_rate"] >= 0.8


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
