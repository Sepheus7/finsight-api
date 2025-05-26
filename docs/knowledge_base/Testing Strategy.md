# Testing Strategy - FinSight Quality Assurance

*Last Updated: May 24, 2025*

## Overview

Comprehensive testing strategy for the FinSight financial fact-checking system, covering unit tests, integration tests, performance tests, and quality assurance processes.

## Testing Pyramid

### 🏗️ **Testing Architecture**

```
                    🎭 E2E Tests (5%)
                   Manual & Automated
                 ┌─────────────────────┐
                 │  User Journey Tests │
                 │  Production Smoke   │
                 └─────────────────────┘

              🔗 Integration Tests (25%)
            ┌───────────────────────────────┐
            │    API Integration Tests      │
            │   External Service Tests      │
            │  Component Integration Tests  │
            └───────────────────────────────┘

      🧪 Unit Tests (70%)
┌─────────────────────────────────────────────┐
│           Business Logic Tests              │
│            Utility Function Tests           │
│           Data Model Validation Tests       │
│            Error Handling Tests             │
└─────────────────────────────────────────────┘
```

## Test Coverage Strategy

### 📊 **Current Coverage Metrics**

```python
coverage_report = {
    "overall_coverage": "89.2%",
    "by_component": {
        "core_logic": "94.7%",
        "api_handlers": "87.3%", 
        "data_models": "91.8%",
        "utilities": "96.2%",
        "llm_integration": "82.4%",
        "external_apis": "78.9%"
    },
    "target_coverage": "90%",
    "critical_path_coverage": "98.1%"
}
```

### 🎯 **Coverage Targets by Component**

| Component | Current | Target | Priority |
|-----------|---------|---------|----------|
| Fact Checking Core | 94.7% | 95% | Critical |
| LLM Integration | 82.4% | 90% | High |
| External APIs | 78.9% | 85% | Medium |
| Data Validation | 91.8% | 95% | High |
| Error Handling | 87.3% | 90% | High |

## Unit Testing

### 🧪 **Test Structure**

```python
# Example test organization
tests/
├── unit/
│   ├── test_fact_checker.py
│   ├── test_llm_extractor.py
│   ├── test_data_models.py
│   ├── test_utils.py
│   └── test_config.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_llm_providers.py
│   ├── test_data_sources.py
│   └── test_end_to_end.py
├── performance/
│   ├── test_load.py
│   ├── test_stress.py
│   └── test_benchmarks.py
└── fixtures/
    ├── sample_claims.json
    ├── mock_responses/
    └── test_data/
```

### 🔬 **Unit Test Examples**

#### **Fact Checker Core Logic**
```python
import pytest
from src.handlers.enhanced_fact_check_handler import EnhancedFactCheckHandler
from src.models.financial_claim import FinancialClaim

class TestEnhancedFactChecker:
    def setup_method(self):
        self.fact_checker = EnhancedFactCheckHandler()
    
    def test_market_cap_verification_accurate(self):
        """Test accurate market cap claim verification"""
        claim = FinancialClaim(
            text="Microsoft's market cap is approximately $2.8 trillion",
            company="Microsoft",
            metric="market_cap",
            value=2.8e12,
            currency="USD"
        )
        
        result = self.fact_checker.verify_claim(claim)
        
        assert result.is_accurate is True
        assert result.confidence > 0.8
        assert "Microsoft" in result.explanation
        assert result.sources is not None
    
    def test_market_cap_verification_inaccurate(self):
        """Test inaccurate market cap claim detection"""
        claim = FinancialClaim(
            text="Apple's market cap is $500 billion",
            company="Apple",
            metric="market_cap", 
            value=5e11,
            currency="USD"
        )
        
        result = self.fact_checker.verify_claim(claim)
        
        assert result.is_accurate is False
        assert result.confidence > 0.7
        assert "significantly different" in result.explanation.lower()
    
    @pytest.mark.parametrize("company,expected_ticker", [
        ("Microsoft", "MSFT"),
        ("Apple Inc.", "AAPL"),
        ("Alphabet", "GOOGL"),
        ("Tesla Motors", "TSLA")
    ])
    def test_ticker_resolution(self, company, expected_ticker):
        """Test company name to ticker resolution"""
        ticker = self.fact_checker.resolve_ticker(company)
        assert ticker == expected_ticker
```

#### **LLM Integration Tests**
```python
import pytest
from unittest.mock import Mock, patch
from src.utils.llm_claim_extractor import LLMClaimExtractor

class TestLLMClaimExtractor:
    def setup_method(self):
        self.extractor = LLMClaimExtractor()
    
    @patch('openai.ChatCompletion.create')
    def test_openai_claim_extraction(self, mock_openai):
        """Test OpenAI claim extraction"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "claims": [{
                "text": "Apple's revenue was $365 billion in 2021",
                "company": "Apple",
                "metric": "revenue",
                "value": 365000000000,
                "time_period": "2021"
            }]
        }
        '''
        mock_openai.return_value = mock_response
        
        result = self.extractor.extract_claims("Apple reported strong revenue")
        
        assert len(result) == 1
        assert result[0].company == "Apple"
        assert result[0].metric == "revenue"
        assert result[0].value == 365000000000
    
    def test_regex_fallback(self):
        """Test regex fallback when LLM unavailable"""
        text = "Microsoft's market cap is $2.8 trillion"
        
        # Simulate LLM failure
        with patch.object(self.extractor, '_use_llm', return_value=False):
            claims = self.extractor.extract_claims(text)
        
        assert len(claims) > 0
        assert any("Microsoft" in claim.text for claim in claims)
```

#### **Data Model Validation**
```python
import pytest
from src.models.financial_claim import FinancialClaim
from src.models.fact_check_result import FactCheckResult

class TestDataModels:
    def test_financial_claim_validation(self):
        """Test financial claim data validation"""
        claim = FinancialClaim(
            text="Valid claim text",
            company="Test Corp",
            metric="market_cap",
            value=1000000000,
            currency="USD"
        )
        
        assert claim.is_valid()
        assert claim.company == "Test Corp"
        assert claim.value == 1000000000
    
    def test_financial_claim_invalid_value(self):
        """Test invalid financial claim handling"""
        with pytest.raises(ValueError):
            FinancialClaim(
                text="Invalid claim",
                company="Test Corp",
                metric="market_cap",
                value=-1000000000,  # Negative market cap
                currency="USD"
            )
    
    def test_fact_check_result_serialization(self):
        """Test fact check result JSON serialization"""
        result = FactCheckResult(
            is_accurate=True,
            confidence=0.95,
            explanation="Test explanation",
            sources=["source1", "source2"]
        )
        
        json_data = result.to_json()
        assert "is_accurate" in json_data
        assert json_data["confidence"] == 0.95
        
        # Test deserialization
        reconstructed = FactCheckResult.from_json(json_data)
        assert reconstructed.is_accurate == result.is_accurate
        assert reconstructed.confidence == result.confidence
```

## Integration Testing

### 🔗 **API Integration Tests**

```python
import pytest
import httpx
from fastapi.testclient import TestClient
from src.main import app

class TestAPIIntegration:
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """Test API health check"""
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_fact_check_endpoint_success(self):
        """Test successful fact check API call"""
        payload = {
            "text": "Microsoft's market cap is approximately $2.8 trillion",
            "use_llm": False  # Use regex for consistent testing
        }
        
        response = self.client.post("/fact-check", json=payload)
        
        assert response.status_code == 200
        result = response.json()
        assert "is_accurate" in result
        assert "confidence" in result
        assert "explanation" in result
        assert isinstance(result["confidence"], float)
    
    def test_fact_check_endpoint_invalid_input(self):
        """Test API error handling for invalid input"""
        payload = {"invalid": "data"}
        
        response = self.client.post("/fact-check", json=payload)
        
        assert response.status_code == 422  # Validation error
        assert "error" in response.json()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent API requests"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            tasks = []
            for i in range(10):
                payload = {
                    "text": f"Test claim {i}",
                    "use_llm": False
                }
                task = client.post("/fact-check", json=payload)
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
```

### 🌐 **External Service Integration**

```python
import pytest
from unittest.mock import patch, Mock
from src.utils.data_fetcher import DataFetcher

class TestExternalServiceIntegration:
    def setup_method(self):
        self.data_fetcher = DataFetcher()
    
    @pytest.mark.integration
    def test_yahoo_finance_integration(self):
        """Test real Yahoo Finance API integration"""
        # This test requires internet connection
        data = self.data_fetcher.fetch_stock_data("AAPL")
        
        assert data is not None
        assert "price" in data
        assert "market_cap" in data
        assert isinstance(data["price"], (int, float))
    
    @patch('requests.get')
    def test_yahoo_finance_error_handling(self, mock_get):
        """Test Yahoo Finance error handling"""
        mock_get.side_effect = Exception("Network error")
        
        result = self.data_fetcher.fetch_stock_data("INVALID")
        
        assert result is None
        mock_get.assert_called_once()
    
    @pytest.mark.integration
    def test_sec_edgar_integration(self):
        """Test SEC EDGAR API integration"""
        # Test with known public company
        filing_data = self.data_fetcher.fetch_sec_filing("AAPL", "10-K")
        
        assert filing_data is not None
        assert "revenue" in filing_data or "total_revenue" in filing_data
```

## Performance Testing

### ⚡ **Load Testing**

```python
import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.handlers.enhanced_fact_check_handler import EnhancedFactCheckHandler

class TestPerformance:
    def setup_method(self):
        self.fact_checker = EnhancedFactCheckHandler()
    
    def test_single_request_performance(self):
        """Test single request response time"""
        claim_text = "Microsoft's market cap is $2.8 trillion"
        
        start_time = time.time()
        result = self.fact_checker.process_claim(claim_text, use_llm=False)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 2.0  # Should complete within 2 seconds
        assert result is not None
    
    def test_concurrent_request_handling(self):
        """Test concurrent request processing"""
        claim_texts = [
            "Apple's market cap is $3 trillion",
            "Microsoft's revenue is $200 billion", 
            "Google's stock price is $150",
            "Tesla's market cap is $800 billion",
            "Amazon's revenue is $500 billion"
        ]
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(
                    self.fact_checker.process_claim, 
                    claim_text, 
                    use_llm=False
                )
                for claim_text in claim_texts
            ]
            
            results = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle 5 concurrent requests in under 5 seconds
        assert total_time < 5.0
        assert len(results) == 5
        assert all(result is not None for result in results)
    
    @pytest.mark.performance
    def test_memory_usage(self):
        """Test memory consumption under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process 100 claims
        for i in range(100):
            claim = f"Test company {i} has market cap of ${i} billion"
            self.fact_checker.process_claim(claim, use_llm=False)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB)
        assert memory_increase < 100 * 1024 * 1024
```

### 🎯 **Benchmark Testing**

```python
import pytest
import time
from src.utils.llm_claim_extractor import LLMClaimExtractor

class TestBenchmarks:
    def setup_method(self):
        self.extractor = LLMClaimExtractor()
    
    @pytest.mark.benchmark
    def test_regex_extraction_speed(self):
        """Benchmark regex-based claim extraction"""
        test_text = """
        Apple reported quarterly revenue of $123.9 billion.
        Microsoft's market capitalization reached $2.8 trillion.
        Tesla's stock price closed at $187.50 per share.
        Amazon's annual revenue was $469.8 billion.
        """
        
        start_time = time.time()
        for _ in range(100):  # Run 100 times
            claims = self.extractor.extract_claims_regex(test_text)
        end_time = time.time()
        
        avg_time_per_extraction = (end_time - start_time) / 100
        
        # Should extract claims in under 50ms on average
        assert avg_time_per_extraction < 0.05
        assert len(claims) > 0
    
    @pytest.mark.benchmark
    @pytest.mark.skipif(not has_llm_access(), reason="LLM access required")
    def test_llm_extraction_speed(self):
        """Benchmark LLM-based claim extraction"""
        test_text = "Apple's quarterly revenue exceeded expectations."
        
        start_time = time.time()
        claims = self.extractor.extract_claims_llm(test_text)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # LLM extraction should complete within 5 seconds
        assert response_time < 5.0
        assert len(claims) >= 0  # May be empty for simple text
```

## Test Data Management

### 📊 **Test Data Strategy**

```python
# Test data organization
test_data_structure = {
    "fixtures": {
        "valid_claims": "tests/fixtures/valid_claims.json",
        "invalid_claims": "tests/fixtures/invalid_claims.json", 
        "edge_cases": "tests/fixtures/edge_cases.json",
        "performance_data": "tests/fixtures/performance_claims.json"
    },
    "mock_responses": {
        "yahoo_finance": "tests/fixtures/mock_responses/yahoo/",
        "sec_edgar": "tests/fixtures/mock_responses/sec/",
        "llm_responses": "tests/fixtures/mock_responses/llm/"
    },
    "golden_datasets": {
        "accuracy_benchmark": "tests/data/accuracy_benchmark.json",
        "regression_tests": "tests/data/regression_test_cases.json"
    }
}
```

#### **Sample Test Data**
```json
{
  "valid_claims": [
    {
      "id": "VC001",
      "text": "Apple's market cap is approximately $3 trillion",
      "expected_company": "Apple",
      "expected_metric": "market_cap",
      "expected_accuracy": true,
      "expected_confidence_min": 0.8
    },
    {
      "id": "VC002", 
      "text": "Microsoft reported quarterly revenue of $56.2 billion",
      "expected_company": "Microsoft",
      "expected_metric": "revenue",
      "expected_accuracy": true,
      "expected_confidence_min": 0.85
    }
  ],
  "invalid_claims": [
    {
      "id": "IC001",
      "text": "Apple's market cap is $500 billion",
      "expected_accuracy": false,
      "reason": "Significantly undervalued"
    }
  ]
}
```

### 🎭 **Mock Data Generation**

```python
import json
from datetime import datetime, timedelta

class TestDataGenerator:
    def generate_mock_yahoo_response(self, ticker, market_cap=None):
        """Generate mock Yahoo Finance API response"""
        return {
            "symbol": ticker,
            "regularMarketPrice": 150.00,
            "marketCap": market_cap or 2500000000000,
            "regularMarketVolume": 50000000,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_mock_llm_response(self, claims_count=1):
        """Generate mock LLM API response"""
        claims = []
        for i in range(claims_count):
            claims.append({
                "text": f"Sample claim {i+1}",
                "company": f"Company {i+1}",
                "metric": "market_cap",
                "value": (i+1) * 1000000000,
                "currency": "USD"
            })
        
        return {
            "claims": claims,
            "confidence": 0.9,
            "processing_time": 1.5
        }
```

## Automated Testing Pipeline

### 🔄 **CI/CD Integration**

```yaml
# .github/workflows/test.yml
name: Automated Testing Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run integration tests
        run: |
          pytest tests/integration/ -v -m "not slow"
        env:
          # Use test API keys for integration tests
          OPENAI_API_KEY: ${{ secrets.TEST_OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.TEST_ANTHROPIC_API_KEY }}

  performance-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Run performance benchmarks
        run: |
          pytest tests/performance/ -v --benchmark-only
```

### 📊 **Test Reporting**

```python
# Custom test reporter
class FinSightTestReporter:
    def __init__(self):
        self.results = {}
    
    def generate_test_report(self, test_results):
        """Generate comprehensive test report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": test_results["total"],
                "passed": test_results["passed"],
                "failed": test_results["failed"],
                "skipped": test_results["skipped"],
                "success_rate": f"{(test_results['passed']/test_results['total'])*100:.1f}%"
            },
            "coverage": test_results.get("coverage", {}),
            "performance": test_results.get("benchmarks", {}),
            "critical_failures": test_results.get("critical_failures", [])
        }
        
        return report
    
    def alert_on_failures(self, report):
        """Send alerts for test failures"""
        if report["summary"]["success_rate"] < 95:
            self.send_alert(f"Test success rate below threshold: {report['summary']['success_rate']}")
        
        if report.get("critical_failures"):
            self.send_critical_alert(report["critical_failures"])
```

## Quality Gates

### 🚦 **Deployment Gates**

```python
class QualityGates:
    def __init__(self):
        self.gates = {
            "unit_test_coverage": 90,      # Minimum 90% coverage
            "integration_test_pass": 100,   # All integration tests must pass
            "performance_regression": 10,   # No more than 10% regression
            "critical_bugs": 0,            # Zero critical bugs
            "security_scan": "pass"        # Security scan must pass
        }
    
    def evaluate_quality_gates(self, test_results):
        """Evaluate if code meets quality gates"""
        gate_results = {}
        
        # Check coverage gate
        coverage = test_results.get("coverage", {}).get("total", 0)
        gate_results["coverage"] = coverage >= self.gates["unit_test_coverage"]
        
        # Check integration tests
        integration_success = test_results.get("integration", {}).get("success_rate", 0)
        gate_results["integration"] = integration_success >= self.gates["integration_test_pass"]
        
        # Check performance regression
        performance_change = test_results.get("performance", {}).get("regression", 0)
        gate_results["performance"] = performance_change <= self.gates["performance_regression"]
        
        return gate_results
    
    def can_deploy(self, gate_results):
        """Determine if deployment should proceed"""
        return all(gate_results.values())
```

## Test Maintenance

### 🔧 **Test Maintenance Strategy**

#### **Regular Maintenance Tasks**
1. **Weekly**: Update test data with current market values
2. **Monthly**: Review and update external API mock responses
3. **Quarterly**: Performance benchmark review and adjustment
4. **Annually**: Complete test strategy review

#### **Test Data Refresh**
```python
def refresh_test_data():
    """Refresh test data with current market information"""
    # Update market cap data for test companies
    test_companies = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
    
    for ticker in test_companies:
        current_data = fetch_real_market_data(ticker)
        update_test_fixtures(ticker, current_data)
    
    # Validate test cases still pass with new data
    run_validation_tests()
```

### 📈 **Test Metrics Tracking**

```python
test_metrics = {
    "test_execution_time": {
        "unit_tests": "2m 45s",
        "integration_tests": "8m 12s", 
        "performance_tests": "15m 30s",
        "total_pipeline": "26m 27s"
    },
    "test_reliability": {
        "flaky_test_rate": "1.2%",
        "false_positive_rate": "0.8%",
        "test_maintenance_hours": "4.5h/month"
    },
    "quality_trends": {
        "coverage_trend": "89.2% → 91.5% → 89.8%",
        "bug_detection_rate": "94.3%",
        "regression_prevention": "98.7%"
    }
}
```

## Related Documentation

- [[FinSight - Technical Architecture]] - System architecture overview
- [[Performance Benchmarks]] - Detailed performance analysis
- [[Error Analysis]] - Error patterns and debugging strategies
- [[FinSight - Development Roadmap]] - Future testing enhancements

---

*This testing strategy is continuously evolved based on lessons learned and industry best practices. Regular reviews ensure optimal test coverage and quality assurance.*
