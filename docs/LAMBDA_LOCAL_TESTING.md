# 🚀 Running FinSight Lambda Handlers Locally

This guide shows you **4 different ways** to run your AWS Lambda handlers locally for development and testing.

## Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# For SAM CLI method (optional)
brew install aws-sam-cli  # macOS
# or
pip install aws-sam-cli
```

## Method 1: Direct Python Execution ⚡ (Fastest)

**Best for**: Quick testing and debugging

```bash
# Run the test script
python test_lambda_local.py

# Or test individual handlers
python -c "
import sys, os
sys.path.insert(0, 'src')
from handlers.financial_enrichment_handler import lambda_handler
import json

event = {
    'body': json.dumps({
        'content': 'Apple (AAPL) stock is trading at \$195, up 2.3% today',
        'enrichment_types': ['stock_data'],
        'include_compliance': True
    })
}

class MockContext:
    aws_request_id = 'test-123'

response = lambda_handler(event, MockContext())
print(json.dumps(json.loads(response['body']), indent=2))
"
```

## Method 2: AWS SAM Local 🏗️ (Production-like)

**Best for**: Testing with API Gateway simulation

```bash
# Start local API Gateway + Lambda
sam local start-api --template template-local.yaml --port 3000

# Test endpoints
curl -X POST http://localhost:3000/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Apple (AAPL) stock is trading at $195, up 2.3% today",
    "enrichment_types": ["stock_data", "market_context"],
    "include_compliance": true
  }'

# Test individual function
sam local invoke FinancialEnrichmentFunction \
  --template template-local.yaml \
  --event events/test-enrich.json
```

### Create test events

```bash
mkdir -p events
```

**events/test-enrich.json:**

```json
{
  "body": "{\"content\": \"Apple (AAPL) stock is trading at $195, up 2.3% today\", \"enrichment_types\": [\"stock_data\"], \"include_compliance\": true}",
  "headers": {
    "Content-Type": "application/json"
  },
  "httpMethod": "POST",
  "path": "/enrich"
}
```

## Method 3: Using Your Existing API Server 🌐 (Current Setup)

**Best for**: Full integration testing

```bash
# Start your existing server (already working!)
python src/api_server.py

# Test via HTTP
curl -X POST http://localhost:8000/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Apple (AAPL) stock is trading at $195, up 2.3% today",
    "enrichment_types": ["stock_data", "market_context"],
    "include_compliance": true
  }'
```

## Method 4: Docker Container 🐳 (Isolated Environment)

**Best for**: Consistent environment across teams

```bash
# Build container
docker build -t finsight-lambda -f deployment/docker/Dockerfile .

# Run container
docker run -p 8080:8080 \
  -e FINSIGHT_LLM_PROVIDER=bedrock \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  finsight-lambda

# Test
curl -X POST http://localhost:8080/2015-03-31/functions/function/invocations \
  -d '{
    "body": "{\"content\": \"Apple stock is up 5% today\", \"enrichment_types\": [\"stock_data\"]}"
  }'
```

## Available Lambda Handlers

| Handler | File | Purpose |
|---------|------|---------|
| **Financial Enrichment** | `handlers/financial_enrichment_handler.py` | Main enrichment with real-time data |
| **Enhanced Fact Check** | `handlers/enhanced_fact_check_handler.py` | LLM-powered fact checking |
| **Health Check** | `handlers/health_handler.py` | System health monitoring |
| **Compliance Check** | `handlers/compliance_handler.py` | Financial compliance validation |
| **Context Enrichment** | `handlers/context_enrichment_handler.py` | Market context addition |

## Testing Examples

### Financial Enrichment Handler

```python
# Test event
{
  "body": json.dumps({
    "content": "Apple (AAPL) stock is trading at $195, up 2.3% today. Tesla is also performing well.",
    "enrichment_types": ["stock_data", "market_context", "economic_indicators"],
    "include_compliance": True,
    "format_style": "enhanced",
    "max_response_time": 5000
  })
}

# Expected response
{
  "statusCode": 200,
  "body": {
    "enriched_content": "...",
    "claims": [...],
    "data_points": [...],
    "metrics": {
      "processing_time_ms": 2500,
      "claims_processed": 2,
      "data_sources_used": 1
    }
  }
}
```

### Enhanced Fact Check Handler

```python
# Test event
{
  "body": json.dumps({
    "content": "Apple stock is guaranteed to double in value next month!",
    "include_context": True,
    "llm_provider": "bedrock",
    "confidence_threshold": 0.8
  })
}

# Expected response
{
  "statusCode": 200,
  "body": {
    "claims": [...],
    "fact_check_results": [...],
    "warnings": ["Contains guarantee language"],
    "confidence_score": 0.95
  }
}
```

### Health Check Handler

```python
# Test event
{}

# Expected response
{
  "statusCode": 200,
  "body": {
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "1.0.0",
    "services": {
      "bedrock": "available",
      "yahoo_finance": "available"
    }
  }
}
```

## Environment Variables

Set these for local testing:

```bash
export FINSIGHT_LLM_PROVIDER=bedrock
export FINSIGHT_BEDROCK_MODEL=anthropic.claude-3-haiku-20240307-v1:0
export FINSIGHT_CACHE_ENABLED=true
export FINSIGHT_DEBUG=true
export AWS_REGION=us-east-1

# Optional: External API keys
export ALPHA_VANTAGE_API_KEY=your_key_here
export FRED_API_KEY=your_key_here
```

## Debugging Tips

1. **Enable Debug Logging:**

   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Mock AWS Services:**

   ```python
   # Use moto for AWS service mocking
   pip install moto
   ```

3. **Profile Performance:**

   ```python
   import cProfile
   cProfile.run('lambda_handler(event, context)')
   ```

4. **Test Error Handling:**

   ```python
   # Test with invalid input
   event = {"body": "invalid json"}
   response = lambda_handler(event, context)
   assert response["statusCode"] == 400
   ```

## Performance Benchmarks

| Handler | Cold Start | Warm Start | Memory Usage |
|---------|------------|------------|--------------|
| Financial Enrichment | ~3s | ~1.5s | ~200MB |
| Enhanced Fact Check | ~2s | ~800ms | ~150MB |
| Health Check | ~500ms | ~50ms | ~50MB |
| Compliance Check | ~1s | ~300ms | ~100MB |

## Troubleshooting

### Common Issues

1. **Import Errors:**

   ```bash
   # Add src to Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

2. **AWS Credentials:**

   ```bash
   aws configure
   # or
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   ```

3. **Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Port Conflicts:**

   ```bash
   # Use different ports
   sam local start-api --port 3001
   ```

## Next Steps

- **Deploy to AWS:** Use `sam deploy` with the full template
- **CI/CD Integration:** Add these tests to your GitHub Actions
- **Monitoring:** Add CloudWatch logs and metrics
- **Load Testing:** Use `artillery` or `locust` for performance testing

---

🎯 **Quick Start:** Run `python test_lambda_local.py` to test all handlers at once!
