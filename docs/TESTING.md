# FinSight Testing Guide

## Overview

This guide covers testing strategies and procedures for the FinSight system, including unit tests, integration tests, performance tests, and end-to-end tests.

## Test Structure

```
tests/
├── unit/
│   ├── test_handlers/
│   ├── test_models/
│   └── test_utils/
├── integration/
│   ├── test_api/
│   └── test_data_sources/
├── performance/
│   └── test_load/
└── e2e/
    └── test_workflows/
```

## Unit Testing

### Running Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_handlers/test_financial_enrichment.py

# Run with coverage
pytest --cov=src tests/unit/
```

### Example Unit Test

```python
import pytest
from src.handlers.financial_enrichment import FinancialEnrichmentHandler

def test_stock_data_enrichment():
    handler = FinancialEnrichmentHandler()
    content = "AAPL stock is trading at $195"
    
    result = handler.enrich(content, ["stock_data"])
    
    assert result.enriched_content is not None
    assert "AAPL" in result.enriched_content
    assert result.metadata.confidence_score > 0.8
```

## Integration Testing

### Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run specific test suite
pytest tests/integration/test_api/
```

### Example Integration Test

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_enrich_endpoint():
    response = client.post(
        "/enrich",
        json={
            "content": "AAPL stock is trading at $195",
            "enrichment_types": ["stock_data"],
            "format_style": "enhanced"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "enriched_content" in data
    assert "metadata" in data
```

## Performance Testing

### Running Performance Tests

```bash
# Run load tests
pytest tests/performance/test_load.py

# Run with specific parameters
pytest tests/performance/test_load.py --users 100 --spawn-rate 10
```

### Example Performance Test

```python
import pytest
from locust import HttpUser, task, between

class FinSightUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def enrich_content(self):
        self.client.post(
            "/enrich",
            json={
                "content": "AAPL stock is trading at $195",
                "enrichment_types": ["stock_data"],
                "format_style": "enhanced"
            }
        )
```

## End-to-End Testing

### Running E2E Tests

```bash
# Run all E2E tests
pytest tests/e2e/

# Run specific workflow
pytest tests/e2e/test_workflows/test_stock_enrichment.py
```

### Example E2E Test

```python
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By

def test_stock_enrichment_workflow():
    driver = webdriver.Chrome()
    try:
        driver.get("http://localhost:8000")
        
        # Input stock data
        input_field = driver.find_element(By.ID, "content-input")
        input_field.send_keys("AAPL stock is trading at $195")
        
        # Submit form
        submit_button = driver.find_element(By.ID, "submit-button")
        submit_button.click()
        
        # Verify result
        result = driver.find_element(By.ID, "enriched-content")
        assert "AAPL" in result.text
        assert "Market cap" in result.text
    finally:
        driver.quit()
```

## Test Data

### Mock Data

```python
@pytest.fixture
def mock_stock_data():
    return {
        "symbol": "AAPL",
        "price": 195.00,
        "market_cap": "3.02T",
        "volume": "52.3M",
        "timestamp": "2024-03-20T14:30:00Z"
    }
```

### Test Configuration

```python
@pytest.fixture(scope="session")
def test_config():
    return {
        "api_url": "http://localhost:8000",
        "api_key": "test-key",
        "timeout": 5,
        "retry_attempts": 3
    }
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          
      - name: Run tests
        run: |
          pytest tests/unit/
          pytest tests/integration/
          
      - name: Run performance tests
        run: |
          pytest tests/performance/
```

## Test Coverage

### Coverage Configuration

```ini
[run]
source = src
omit = 
    src/tests/*
    src/__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
```

### Running Coverage

```bash
# Generate coverage report
coverage run -m pytest
coverage report
coverage html
```

## Best Practices

1. **Test Organization**
   - Group tests by functionality
   - Use descriptive test names
   - Keep tests independent
   - Clean up test data

2. **Test Data Management**
   - Use fixtures for common data
   - Mock external services
   - Use test databases
   - Clean up after tests

3. **Performance Considerations**
   - Run tests in parallel
   - Use appropriate timeouts
   - Mock slow operations
   - Profile test execution

4. **Error Handling**
   - Test error cases
   - Verify error messages
   - Check error status codes
   - Test retry logic

## Troubleshooting

### Common Issues

1. **Test Failures**
   - Check test data
   - Verify environment setup
   - Check for race conditions
   - Review error messages

2. **Performance Issues**
   - Check resource usage
   - Review test timeouts
   - Monitor system load
   - Check network latency

3. **Coverage Issues**
   - Review excluded files
   - Check test organization
   - Verify test execution
   - Review coverage settings

## Test Maintenance

1. **Regular Updates**
   - Update test data
   - Review test coverage
   - Update dependencies
   - Check test performance

2. **Documentation**
   - Update test documentation
   - Document test data
   - Maintain test README
   - Document test procedures

3. **Review Process**
   - Review test coverage
   - Check test quality
   - Verify test results
   - Update test strategy 