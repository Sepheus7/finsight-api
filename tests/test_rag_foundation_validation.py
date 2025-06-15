#!/usr/bin/env python3
"""
RAG Foundation Validation Test Suite
Comprehensive end-to-end validation of the Core RAG Foundation

This test validates:
1. All imports and dependencies work correctly
2. Components initialize without errors
3. Query processing pipeline functions properly
4. Error handling is robust
5. Performance meets requirements
6. Integration points work as expected

Run this before proceeding to Step 2: Data Pipeline Optimization
"""

import asyncio
import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, List, Any

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

class RAGFoundationValidator:
    """Comprehensive validator for RAG Foundation"""
    
    def __init__(self):
        self.test_results = []
        self.handler = None
        self.critical_failures = []
        
    def log_test(self, test_name: str, status: str, details: str = "", duration_ms: float = 0, critical: bool = False):
        """Log test results with better categorization"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'duration_ms': round(duration_ms, 2),
            'critical': critical
        }
        self.test_results.append(result)
        
        if status == "FAIL" and critical:
            self.critical_failures.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️" if status == "WARN" else "⏭️"
        critical_marker = " [CRITICAL]" if critical else ""
        print(f"{status_emoji} {test_name}: {status}{critical_marker}")
        if details:
            print(f"   {details}")
        if duration_ms > 0:
            print(f"   Duration: {duration_ms:.2f}ms")
        print()
    
    async def run_validation(self):
        """Run the complete validation suite"""
        print("🔍 RAG Foundation Validation Test Suite")
        print("=" * 60)
        print("Validating Core RAG Foundation before Step 2...")
        print()
        
        # Phase 1: Critical Dependencies
        await self.validate_critical_dependencies()
        
        # Phase 2: Component Initialization
        await self.validate_component_initialization()
        
        # Phase 3: Core Functionality
        await self.validate_core_functionality()
        
        # Phase 4: Error Resilience
        await self.validate_error_resilience()
        
        # Phase 5: Performance Requirements
        await self.validate_performance_requirements()
        
        # Phase 6: Integration Validation
        await self.validate_integration_points()
        
        # Generate validation report
        self.generate_validation_report()
    
    async def validate_critical_dependencies(self):
        """Phase 1: Validate critical dependencies that must work"""
        print("🔧 Phase 1: Critical Dependencies Validation")
        print("-" * 50)
        
        # Test 1.1: Core RAG Handler Import (CRITICAL)
        start_time = time.time()
        try:
            from handlers.rag_handler import FinancialRAGHandler
            duration = (time.time() - start_time) * 1000
            self.log_test("Core RAG Handler Import", "PASS", 
                         "FinancialRAGHandler imported successfully", duration, critical=True)
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test("Core RAG Handler Import", "FAIL", 
                         f"CRITICAL: Cannot import FinancialRAGHandler - {e}", duration, critical=True)
            return False
        
        # Test 1.2: Essential Component Imports (CRITICAL)
        essential_components = [
            ("DataAggregator", "integrations.data_aggregator", "DataAggregator"),
            ("CacheManager", "utils.cache_manager", "CacheManager"),
            ("ClaimExtractor", "utils.claim_extractor", "ClaimExtractor"),
        ]
        
        for component_name, module_path, class_name in essential_components:
            start_time = time.time()
            try:
                module = __import__(module_path, fromlist=[class_name])
                getattr(module, class_name)
                duration = (time.time() - start_time) * 1000
                self.log_test(f"{component_name} Import", "PASS", 
                             f"Successfully imported {class_name}", duration, critical=True)
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                self.log_test(f"{component_name} Import", "FAIL", 
                             f"CRITICAL: Cannot import {class_name} - {e}", duration, critical=True)
        
        # Test 1.3: Model Imports (NON-CRITICAL but important)
        start_time = time.time()
        try:
            from models.enrichment_models import DataPoint, DataSourceType
            duration = (time.time() - start_time) * 1000
            self.log_test("Enrichment Models Import", "PASS", 
                         "Successfully imported DataPoint and DataSourceType", duration)
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test("Enrichment Models Import", "WARN", 
                         f"Model imports failed but may not be critical - {e}", duration)
        
        return len(self.critical_failures) == 0
    
    async def validate_component_initialization(self):
        """Phase 2: Validate component initialization"""
        print("🚀 Phase 2: Component Initialization Validation")
        print("-" * 50)
        
        if self.critical_failures:
            self.log_test("Component Initialization", "SKIP", 
                         "Skipping due to critical import failures", critical=True)
            return False
        
        # Test 2.1: RAG Handler Initialization (CRITICAL)
        start_time = time.time()
        try:
            from handlers.rag_handler import FinancialRAGHandler
            self.handler = FinancialRAGHandler()
            duration = (time.time() - start_time) * 1000
            self.log_test("RAG Handler Initialization", "PASS", 
                         "Handler initialized successfully", duration, critical=True)
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test("RAG Handler Initialization", "FAIL", 
                         f"CRITICAL: Handler initialization failed - {e}", duration, critical=True)
            return False
        
        # Test 2.2: Component Accessibility
        components_to_test = [
            ("data_aggregator", "DataAggregator component"),
            ("cache_manager", "CacheManager component"),
            ("claim_extractor", "ClaimExtractor component")
        ]
        
        for attr_name, description in components_to_test:
            start_time = time.time()
            try:
                component = getattr(self.handler, attr_name, None)
                if component is not None:
                    duration = (time.time() - start_time) * 1000
                    self.log_test(f"{description} Accessibility", "PASS", 
                                 "Component accessible and not None", duration)
                else:
                    duration = (time.time() - start_time) * 1000
                    self.log_test(f"{description} Accessibility", "FAIL", 
                                 f"Component is None or not accessible", duration)
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                self.log_test(f"{description} Accessibility", "FAIL", 
                             f"Component access failed - {e}", duration)
        
        return self.handler is not None
    
    async def validate_core_functionality(self):
        """Phase 3: Validate core functionality"""
        print("📊 Phase 3: Core Functionality Validation")
        print("-" * 50)
        
        if not self.handler:
            self.log_test("Core Functionality", "SKIP", 
                         "Skipping due to handler initialization failure", critical=True)
            return False
        
        # Test 3.1: Basic Query Processing (CRITICAL)
        start_time = time.time()
        try:
            result = await self.handler.get_financial_context(
                query="Test query for validation",
                symbols=None,
                include_economic=False,
                include_market_context=False
            )
            duration = (time.time() - start_time) * 1000
            
            if isinstance(result, dict):
                if 'error' in result:
                    self.log_test("Basic Query Processing", "WARN", 
                                 f"Query processed but returned error: {result.get('error', 'Unknown error')}", 
                                 duration)
                else:
                    # Validate response structure
                    required_keys = ['query_analysis', 'financial_data', 'metadata']
                    missing_keys = [key for key in required_keys if key not in result]
                    
                    if not missing_keys:
                        self.log_test("Basic Query Processing", "PASS", 
                                     "Query processed successfully with correct structure", duration, critical=True)
                    else:
                        self.log_test("Basic Query Processing", "FAIL", 
                                     f"CRITICAL: Missing response keys: {missing_keys}", duration, critical=True)
            else:
                self.log_test("Basic Query Processing", "FAIL", 
                             f"CRITICAL: Unexpected response type: {type(result)}", duration, critical=True)
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test("Basic Query Processing", "FAIL", 
                         f"CRITICAL: Query processing crashed - {e}", duration, critical=True)
        
        # Test 3.2: Intent Detection
        intent_test_cases = [
            ("What's the price of Apple?", "valuation"),
            ("Compare Apple vs Microsoft", "comparison"),
            ("Portfolio allocation analysis", "portfolio_analysis"),
            ("Economic indicators", "economic_analysis")
        ]
        
        for query, expected_intent in intent_test_cases:
            start_time = time.time()
            try:
                detected_intent = self.handler._analyze_query_intent(query)
                duration = (time.time() - start_time) * 1000
                
                if detected_intent == expected_intent:
                    self.log_test(f"Intent Detection: {expected_intent}", "PASS", 
                                 f"Correctly detected '{detected_intent}' for '{query[:30]}...'", duration)
                else:
                    self.log_test(f"Intent Detection: {expected_intent}", "WARN", 
                                 f"Expected '{expected_intent}', got '{detected_intent}' for '{query[:30]}...'", duration)
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                self.log_test(f"Intent Detection: {expected_intent}", "FAIL", 
                             f"Intent detection failed - {e}", duration)
        
        # Test 3.3: Complexity Assessment
        complexity_test_cases = [
            ("Simple query", [], "low"),
            ("Compare multiple stocks with analysis", ["AAPL", "MSFT"], "medium"),
            ("Comprehensive portfolio analysis with risk assessment and correlation", ["AAPL", "MSFT", "GOOGL", "AMZN"], "high")
        ]
        
        for query, symbols, expected_complexity in complexity_test_cases:
            start_time = time.time()
            try:
                detected_complexity = self.handler._assess_query_complexity(query, symbols)
                duration = (time.time() - start_time) * 1000
                
                if detected_complexity == expected_complexity:
                    self.log_test(f"Complexity Assessment: {expected_complexity}", "PASS", 
                                 f"Correctly assessed as '{detected_complexity}'", duration)
                else:
                    self.log_test(f"Complexity Assessment: {expected_complexity}", "WARN", 
                                 f"Expected '{expected_complexity}', got '{detected_complexity}'", duration)
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                self.log_test(f"Complexity Assessment: {expected_complexity}", "FAIL", 
                             f"Complexity assessment failed - {e}", duration)
        
        return True
    
    async def validate_error_resilience(self):
        """Phase 4: Validate error handling and resilience"""
        print("🛡️ Phase 4: Error Resilience Validation")
        print("-" * 50)
        
        if not self.handler:
            self.log_test("Error Resilience", "SKIP", "Handler not available")
            return False
        
        # Test 4.1: Edge Cases
        edge_cases = [
            ("Empty Query", "", None),
            ("Very Long Query", "A" * 500, None),
            ("Special Characters", "What's the price of @#$%^&*()?", None),
            ("Invalid Symbols", "Stock analysis", ["INVALID123", "NOTREAL"]),
            ("Non-English Query", "¿Cuál es el precio de Apple?", None)
        ]
        
        for test_name, query, symbols in edge_cases:
            start_time = time.time()
            try:
                result = await self.handler.get_financial_context(
                    query=query,
                    symbols=symbols,
                    include_economic=False,
                    include_market_context=False
                )
                duration = (time.time() - start_time) * 1000
                
                # Check that handler doesn't crash and returns structured response
                if isinstance(result, dict):
                    self.log_test(f"Edge Case: {test_name}", "PASS", 
                                 "Handler gracefully handled edge case", duration)
                else:
                    self.log_test(f"Edge Case: {test_name}", "FAIL", 
                                 f"Unexpected response type: {type(result)}", duration)
                    
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                self.log_test(f"Edge Case: {test_name}", "FAIL", 
                             f"Handler crashed on edge case - {e}", duration)
        
        return True
    
    async def validate_performance_requirements(self):
        """Phase 5: Validate performance requirements"""
        print("⚡ Phase 5: Performance Requirements Validation")
        print("-" * 50)
        
        if not self.handler:
            self.log_test("Performance Requirements", "SKIP", "Handler not available")
            return False
        
        # Test 5.1: Response Time Requirements
        performance_tests = [
            {
                "name": "Single Symbol Query",
                "query": "Apple stock price",
                "symbols": ["AAPL"],
                "max_time_ms": 3000,  # 3 seconds max for single symbol
                "critical": False
            },
            {
                "name": "Multiple Symbol Query",
                "query": "Tech stock comparison",
                "symbols": ["AAPL", "MSFT", "GOOGL"],
                "max_time_ms": 8000,  # 8 seconds max for multiple symbols
                "critical": False
            },
            {
                "name": "Intent Analysis Speed",
                "query": "Complex portfolio analysis with risk assessment",
                "symbols": None,
                "max_time_ms": 100,  # Intent analysis should be very fast
                "critical": True,
                "test_intent_only": True
            }
        ]
        
        for test_case in performance_tests:
            start_time = time.time()
            try:
                if test_case.get("test_intent_only"):
                    # Test just intent analysis speed
                    self.handler._analyze_query_intent(test_case["query"])
                    duration = (time.time() - start_time) * 1000
                else:
                    # Test full query processing
                    result = await self.handler.get_financial_context(
                        query=test_case["query"],
                        symbols=test_case["symbols"],
                        include_economic=False,
                        include_market_context=False
                    )
                    duration = (time.time() - start_time) * 1000
                
                if duration <= test_case["max_time_ms"]:
                    self.log_test(f"Performance: {test_case['name']}", "PASS", 
                                 f"Completed in {duration:.2f}ms (limit: {test_case['max_time_ms']}ms)", 
                                 duration, critical=test_case["critical"])
                else:
                    status = "FAIL" if test_case["critical"] else "WARN"
                    self.log_test(f"Performance: {test_case['name']}", status, 
                                 f"Exceeded {test_case['max_time_ms']}ms limit", 
                                 duration, critical=test_case["critical"])
                    
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                self.log_test(f"Performance: {test_case['name']}", "FAIL", 
                             f"Performance test failed - {e}", duration, critical=test_case["critical"])
        
        return True
    
    async def validate_integration_points(self):
        """Phase 6: Validate integration points"""
        print("🔗 Phase 6: Integration Points Validation")
        print("-" * 50)
        
        if not self.handler:
            self.log_test("Integration Points", "SKIP", "Handler not available")
            return False
        
        # Test 6.1: Market Insights Generation
        start_time = time.time()
        try:
            mock_stock_data = {
                "AAPL": {"change_percent": 2.5, "volume": 60000000},
                "MSFT": {"change_percent": -1.2, "volume": 30000000}
            }
            insights = self.handler._generate_market_insights(mock_stock_data, {})
            duration = (time.time() - start_time) * 1000
            
            if isinstance(insights, list) and len(insights) > 0:
                self.log_test("Market Insights Generation", "PASS", 
                             f"Generated {len(insights)} insights", duration)
            else:
                self.log_test("Market Insights Generation", "FAIL", 
                             "No insights generated or wrong type", duration)
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test("Market Insights Generation", "FAIL", 
                         f"Insights generation failed - {e}", duration)
        
        # Test 6.2: Summary Generation
        start_time = time.time()
        try:
            mock_stock_data = {"AAPL": {"change_percent": 2.5}}
            summary = self.handler._generate_summary("Test query", mock_stock_data, {})
            duration = (time.time() - start_time) * 1000
            
            if isinstance(summary, str) and len(summary) > 0:
                self.log_test("Summary Generation", "PASS", 
                             f"Generated summary: '{summary[:50]}...'", duration)
            else:
                self.log_test("Summary Generation", "FAIL", 
                             "No summary generated or wrong type", duration)
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test("Summary Generation", "FAIL", 
                         f"Summary generation failed - {e}", duration)
        
        return True
    
    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        print("📋 RAG Foundation Validation Report")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warned_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        skipped_tests = len([r for r in self.test_results if r['status'] == 'SKIP'])
        critical_failures = len(self.critical_failures)
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⚠️  Warnings: {warned_tests}")
        print(f"   ⏭️  Skipped: {skipped_tests}")
        print(f"   🚨 Critical Failures: {critical_failures}")
        print()
        
        # Calculate success rate
        testable_tests = total_tests - skipped_tests
        success_rate = (passed_tests / testable_tests) * 100 if testable_tests > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print()
        
        # Performance summary
        durations = [r['duration_ms'] for r in self.test_results if r['duration_ms'] > 0]
        if durations:
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            print(f"⚡ Performance Summary:")
            print(f"   Average Test Duration: {avg_duration:.2f}ms")
            print(f"   Longest Test Duration: {max_duration:.2f}ms")
            print()
        
        # Validation Result
        print("🎯 VALIDATION RESULT:")
        print("-" * 30)
        
        if critical_failures > 0:
            print("❌ RAG FOUNDATION: FAILED")
            print("   Critical components are not working properly.")
            print("   Fix these issues before proceeding to Step 2.")
            print()
            print("🚨 Critical Issues:")
            for failure in self.critical_failures:
                print(f"   • {failure['test']}: {failure['details']}")
        elif failed_tests > 3:
            print("⚠️  RAG FOUNDATION: PARTIAL")
            print("   Core functionality works but several issues detected.")
            print("   Consider fixing issues before proceeding to Step 2.")
        elif failed_tests > 0 or warned_tests > 2:
            print("⚠️  RAG FOUNDATION: ACCEPTABLE")
            print("   Minor issues detected but core functionality is solid.")
            print("   Safe to proceed to Step 2 with monitoring.")
        else:
            print("✅ RAG FOUNDATION: VALIDATED")
            print("   All core functionality working correctly!")
            print("   Ready to proceed to Step 2: Data Pipeline Optimization!")
        
        print()
        
        # Detailed failure analysis
        failures = [r for r in self.test_results if r['status'] == 'FAIL']
        if failures:
            print("🔍 Failure Analysis:")
            print("-" * 30)
            for failure in failures:
                critical_marker = " [CRITICAL]" if failure.get('critical') else ""
                print(f"❌ {failure['test']}{critical_marker}")
                print(f"   {failure['details']}")
                print()
        
        # Save detailed report
        self.save_validation_report()
        
        # Return validation status
        return critical_failures == 0 and failed_tests <= 3
    
    def save_validation_report(self):
        """Save detailed validation report to file"""
        try:
            report_data = {
                'validation_timestamp': time.time(),
                'validation_status': 'PASSED' if len(self.critical_failures) == 0 else 'FAILED',
                'test_results': self.test_results,
                'summary': {
                    'total_tests': len(self.test_results),
                    'passed': len([r for r in self.test_results if r['status'] == 'PASS']),
                    'failed': len([r for r in self.test_results if r['status'] == 'FAIL']),
                    'warnings': len([r for r in self.test_results if r['status'] == 'WARN']),
                    'skipped': len([r for r in self.test_results if r['status'] == 'SKIP']),
                    'critical_failures': len(self.critical_failures)
                },
                'critical_failures': self.critical_failures
            }
            
            with open('rag_foundation_validation_report.json', 'w') as f:
                json.dump(report_data, f, indent=2)
            
            print("📄 Detailed validation report saved to: rag_foundation_validation_report.json")
            
        except Exception as e:
            print(f"⚠️  Could not save validation report: {e}")


async def main():
    """Run the RAG Foundation validation"""
    print("🚀 Starting RAG Foundation Validation...")
    print("This validates the core foundation before Step 2: Data Pipeline Optimization")
    print()
    
    validator = RAGFoundationValidator()
    await validator.run_validation()


if __name__ == "__main__":
    asyncio.run(main()) 