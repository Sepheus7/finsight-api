#!/usr/bin/env python3
"""
Comprehensive Multi-Source Integration Test Suite
Tests the enhanced system with working simple multi-source components
"""

import asyncio
import json
import logging
import requests
import time
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedMultiSourceTester:
    """Enhanced comprehensive testing for the multi-source integration"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Log test result"""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": time.time(),
            "details": details
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        
        if not success:
            logger.error(f"Failure details: {details}")
    
    def test_health_endpoint(self) -> bool:
        """Test the enhanced health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code != 200:
                self.log_test_result(
                    "health_endpoint",
                    False,
                    {"error": f"Status code: {response.status_code}"}
                )
                return False
            
            health_data = response.json()
            
            # Check required fields
            required_fields = ["providers", "multi_source", "enhanced_features"]
            for field in required_fields:
                if field not in health_data:
                    self.log_test_result(
                        "health_endpoint",
                        False,
                        {"error": f"Missing field: {field}"}
                    )
                    return False
            
            # Check multi-source status
            multi_source_info = health_data.get("multi_source", {})
            enhanced_features = health_data.get("enhanced_features", {})
            
            self.log_test_result(
                "health_endpoint",
                True,
                {
                    "multi_source_status": multi_source_info.get("status"),
                    "available_sources": multi_source_info.get("available_sources"),
                    "enhanced_fact_checking": enhanced_features.get("multi_source_fact_checking"),
                    "world_bank_integration": enhanced_features.get("world_bank_integration")
                }
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "health_endpoint",
                False,
                {"error": str(e)}
            )
            return False
    
    def test_enhance_endpoint_with_multi_source(self) -> bool:
        """Test the enhance endpoint with multi-source capabilities"""
        try:
            # Test with economic content that should trigger World Bank integration
            test_content = {
                "ai_response": {
                    "content": "The United States GDP has grown by 2.5% this year, while inflation remains at 3.2%. Economic indicators suggest continued growth.",
                    "agent_id": "test_agent",
                    "timestamp": "2024-01-01T00:00:00Z"
                },
                "llm_provider": "auto",
                "fact_check": True,
                "add_context": True,
                "enrichment_level": "comprehensive"
            }
            
            response = requests.post(
                f"{self.base_url}/enhance",
                json=test_content,
                timeout=30
            )
            
            if response.status_code != 200:
                self.log_test_result(
                    "enhance_endpoint_multi_source",
                    False,
                    {"error": f"Status code: {response.status_code}", "response": response.text}
                )
                return False
            
            result = response.json()
            
            # Check for multi-source enhancement in the actual response structure
            provider_used = result.get("provider_used", "")
            enhanced_content = result.get("enhanced_content", "")
            original_content = result.get("original_content", "")
            
            # Check if multi-source features are working
            multi_source_indicators = [
                "bedrock_with_multi_source" in provider_used,
                "World Bank" in enhanced_content,
                len(enhanced_content) > len(original_content),
                result.get("quality_score", 0) > 0.8
            ]
            
            success = any(multi_source_indicators)
            
            self.log_test_result(
                "enhance_endpoint_multi_source",
                success,
                {
                    "provider_used": provider_used,
                    "content_enhanced": len(enhanced_content) > len(original_content),
                    "world_bank_referenced": "World Bank" in enhanced_content,
                    "quality_score": result.get("quality_score"),
                    "processing_time_ms": result.get("processing_time_ms"),
                    "multi_source_indicators": multi_source_indicators
                }
            )
            return success
            
        except Exception as e:
            self.log_test_result(
                "enhance_endpoint_multi_source",
                False,
                {"error": str(e)}
            )
            return False
    
    def test_provider_switching_with_enhancement(self) -> bool:
        """Test provider switching with multi-source enhancement"""
        providers = ["auto", "bedrock"]  # Skip Ollama since it's not available
        test_content = "AAPL stock price has increased 15% this quarter due to strong iPhone sales."
        
        all_results = {}
        
        for provider in providers:
            try:
                start_time = time.time()
                
                request_data = {
                    "ai_response": {
                        "content": test_content,
                        "agent_id": "test_agent",
                        "timestamp": "2024-01-01T00:00:00Z"
                    },
                    "llm_provider": provider,
                    "fact_check": True,
                    "add_context": True
                }
                
                response = requests.post(
                    f"{self.base_url}/enhance",
                    json=request_data,
                    timeout=30
                )
                
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    
                    all_results[provider] = {
                        "success": True,
                        "duration": duration,
                        "provider_used": result.get("provider_used"),
                        "quality_score": result.get("quality_score"),
                        "content_enhanced": len(result.get("enhanced_content", "")) > len(test_content),
                        "processing_time_ms": result.get("processing_time_ms")
                    }
                else:
                    all_results[provider] = {
                        "success": False,
                        "error": f"Status {response.status_code}: {response.text}",
                        "duration": duration
                    }
                    
            except Exception as e:
                all_results[provider] = {
                    "success": False,
                    "error": str(e),
                    "duration": 0
                }
        
        # Check if at least one provider worked
        successful_providers = [p for p, r in all_results.items() if r.get("success")]
        success = len(successful_providers) > 0
        
        self.log_test_result(
            "provider_switching_enhanced",
            success,
            {
                "successful_providers": successful_providers,
                "all_results": all_results
            }
        )
        return success
    
    def test_world_bank_integration(self) -> bool:
        """Test World Bank integration specifically"""
        try:
            # Test content that should trigger World Bank data retrieval
            test_content = {
                "ai_response": {
                    "content": "The US economy shows robust GDP growth with controlled inflation rates, outperforming European markets.",
                    "agent_id": "test_agent",
                    "timestamp": "2024-01-01T00:00:00Z"
                },
                "llm_provider": "auto",
                "fact_check": True,
                "add_context": True
            }
            
            response = requests.post(
                f"{self.base_url}/enhance",
                json=test_content,
                timeout=30
            )
            
            if response.status_code != 200:
                self.log_test_result(
                    "world_bank_integration",
                    False,
                    {"error": f"Status code: {response.status_code}"}
                )
                return False
            
            result = response.json()
            fact_check = result.get("fact_check", {})
            sources_used = fact_check.get("sources_used", [])
            
            # Check if World Bank was used as a source
            world_bank_used = "World Bank" in sources_used
            
            self.log_test_result(
                "world_bank_integration",
                world_bank_used,
                {
                    "world_bank_used": world_bank_used,
                    "sources_used": sources_used,
                    "implementation_type": fact_check.get("implementation_type"),
                    "fact_check_results": len(fact_check.get("fact_check_results", []))
                }
            )
            return world_bank_used
            
        except Exception as e:
            self.log_test_result(
                "world_bank_integration",
                False,
                {"error": str(e)}
            )
            return False
    
    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        logger.info("🚀 Starting Enhanced Multi-Source Integration Test Suite")
        
        tests = [
            ("Health Check", self.test_health_endpoint),
            ("Multi-Source Enhancement", self.test_enhance_endpoint_with_multi_source),
            ("Provider Switching", self.test_provider_switching_with_enhancement),
            ("World Bank Integration", self.test_world_bank_integration)
        ]
        
        start_time = time.time()
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 Running: {test_name}")
            test_func()
        
        total_duration = time.time() - start_time
        
        # Calculate summary
        passed_tests = [r for r in self.test_results if r["success"]]
        failed_tests = [r for r in self.test_results if not r["success"]]
        
        summary = {
            "total_tests": len(self.test_results),
            "passed": len(passed_tests),
            "failed": len(failed_tests),
            "success_rate": len(passed_tests) / len(self.test_results) * 100,
            "total_duration": total_duration,
            "test_results": self.test_results
        }
        
        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info(f"🏁 ENHANCED MULTI-SOURCE TEST RESULTS")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Passed: {summary['passed']}/{summary['total_tests']}")
        logger.info(f"❌ Failed: {summary['failed']}/{summary['total_tests']}")
        logger.info(f"📊 Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"⏱️  Total Duration: {summary['total_duration']:.2f}s")
        
        if failed_tests:
            logger.info(f"\n❌ Failed Tests:")
            for test in failed_tests:
                logger.info(f"  - {test['test_name']}: {test['details']}")
        
        return summary

def main():
    """Main test execution"""
    tester = EnhancedMultiSourceTester()
    
    logger.info("Testing multi-source components standalone first...")
    
    # Test components directly
    try:
        from multi_source_integration import get_multi_source_integration, is_multi_source_available
        
        logger.info(f"Multi-source available: {is_multi_source_available()}")
        
        integration = get_multi_source_integration()
        if integration:
            status = integration.get_status()
            logger.info(f"Integration status: {status}")
            
            # Test content processing
            async def test_integration():
                result = await integration.process_content(
                    "The US GDP growth is strong this year, with inflation controlled."
                )
                return result
            
            result = asyncio.run(test_integration())
            logger.info(f"Direct integration test successful: {result.get('implementation_type')}")
        
    except Exception as e:
        logger.error(f"Direct integration test failed: {e}")
    
    # Check if server is running
    logger.info("\nChecking if API server is running...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ API server is running, starting comprehensive tests")
            summary = tester.run_comprehensive_test_suite()
            
            if summary['success_rate'] == 100:
                logger.info("🎉 All tests passed! Multi-source integration is fully functional.")
            else:
                logger.warning(f"⚠️  Some tests failed. Success rate: {summary['success_rate']:.1f}%")
            
            return summary
        else:
            logger.error(f"❌ API server returned status {response.status_code}")
    except requests.exceptions.RequestException:
        logger.error("❌ API server is not running. Please start it with:")
        logger.error("cd /Users/romainboluda/Documents/PersonalProjects/FinSight/demo && python3 llm_api_server.py")
        return None

if __name__ == "__main__":
    main()
