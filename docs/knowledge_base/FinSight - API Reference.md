# FinSight - API Reference

*Last Updated: May 24, 2025*  
*Version: 2.1.0*  
*Documentation Type: API Documentation*

## 🌐 API Overview

FinSight provides a comprehensive RESTful API for financial fact-checking and claim verification. The API supports both synchronous and asynchronous processing with multiple output formats and configuration options.

## 🔗 Base URL & Authentication

### Production Endpoints
```
AWS Lambda: https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
Local Development: http://localhost:8000
Docker: http://localhost:8000
```

### Authentication
```bash
# API Key Authentication (Header)
X-API-Key: your-api-key-here

# Alternative: Query Parameter
?api_key=your-api-key-here
```

## 🚀 Core Endpoints

### 1. Fact Check Single Claim

**POST** `/api/v1/fact-check`

Analyze a single text input for financial claims and verify them against real-time data.

**Request:**
```json
{
  "text": "Apple's market cap is $3 trillion and Tesla stock is trading at $200",
  "options": {
    "use_llm": true,
    "llm_provider": "openai",
    "include_context": true,
    "risk_assessment": true,
    "cache_enabled": true
  }
}
```

**Response:**
```json
{
  "request_id": "req_1234567890",
  "timestamp": "2025-05-24T10:30:00Z",
  "processing_time": 1.234,
  "claims": [
    {
      "original_text": "Apple's market cap is $3 trillion",
      "entity": "Apple Inc.",
      "ticker": "AAPL",
      "claim_type": "market_cap",
      "claimed_value": 3000000000000,
      "actual_value": 2980000000000,
      "currency": "USD",
      "verification_status": "partially_correct",
      "confidence_score": 0.92,
      "accuracy_percentage": 99.33,
      "explanation": "Apple's current market cap is $2.98 trillion, very close to the claimed $3 trillion",
      "risk_level": "low",
      "data_source": "yahoo_finance",
      "last_updated": "2025-05-24T10:29:45Z"
    },
    {
      "original_text": "Tesla stock is trading at $200",
      "entity": "Tesla, Inc.",
      "ticker": "TSLA",
      "claim_type": "stock_price",
      "claimed_value": 200.00,
      "actual_value": 195.50,
      "currency": "USD",
      "verification_status": "incorrect",
      "confidence_score": 0.98,
      "accuracy_percentage": 97.75,
      "explanation": "Tesla is currently trading at $195.50, not $200.00",
      "risk_level": "low",
      "data_source": "yahoo_finance",
      "last_updated": "2025-05-24T10:29:50Z"
    }
  ],
  "summary": {
    "total_claims": 2,
    "verified_claims": 2,
    "accuracy_rate": 0.85,
    "avg_confidence": 0.95,
    "llm_provider_used": "openai",
    "cache_hit_rate": 0.5
  },
  "metadata": {
    "api_version": "2.1.0",
    "processing_method": "llm_enhanced",
    "region": "us-east-1"
  }
}
```

### 2. Health Check

**GET** `/api/v1/health`

Check system health and available services.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-05-24T10:30:00Z",
  "version": "2.1.0",
  "services": {
    "fact_checker": "operational",
    "llm_provider": "openai",
    "data_sources": {
      "yahoo_finance": "operational",
      "sec_edgar": "operational",
      "federal_reserve": "operational"
    },
    "cache": "operational"
  },
  "performance": {
    "avg_response_time": 1.2,
    "success_rate": 99.5,
    "uptime": "99.9%"
  }
}
```

### 3. Batch Processing

**POST** `/api/v1/batch-check`

Process multiple texts in a single request for efficient bulk operations.

**Request:**
```json
{
  "texts": [
    "Microsoft's revenue is $200 billion annually",
    "Google stock price is $150 per share",
    "Amazon market cap exceeds $1.5 trillion"
  ],
  "options": {
    "use_llm": true,
    "parallel_processing": true,
    "max_concurrent": 5,
    "timeout": 30
  }
}
```

**Response:**
```json
{
  "request_id": "batch_1234567890",
  "timestamp": "2025-05-24T10:30:00Z",
  "total_processing_time": 3.456,
  "results": [
    {
      "text_index": 0,
      "text": "Microsoft's revenue is $200 billion annually",
      "claims": [/* claim objects */],
      "processing_time": 1.2,
      "status": "completed"
    },
    {
      "text_index": 1,
      "text": "Google stock price is $150 per share", 
      "claims": [/* claim objects */],
      "processing_time": 1.1,
      "status": "completed"
    },
    {
      "text_index": 2,
      "text": "Amazon market cap exceeds $1.5 trillion",
      "claims": [/* claim objects */],
      "processing_time": 1.3,
      "status": "completed"
    }
  ],
  "summary": {
    "total_texts": 3,
    "successful_processing": 3,
    "total_claims_found": 7,
    "avg_processing_time": 1.2,
    "parallel_efficiency": 0.85
  }
}
```

### 4. Provider Information

**GET** `/api/v1/providers`

Get information about available LLM providers and their status.

**Response:**
```json
{
  "available_providers": [
    {
      "name": "openai",
      "status": "active",
      "models": ["gpt-4o-mini", "gpt-4o"],
      "capabilities": ["claim_extraction", "context_enhancement"],
      "rate_limits": {
        "requests_per_minute": 3000,
        "tokens_per_minute": 150000
      }
    },
    {
      "name": "anthropic", 
      "status": "available",
      "models": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229"],
      "capabilities": ["claim_extraction", "compliance_check"],
      "rate_limits": {
        "requests_per_minute": 1000,
        "tokens_per_minute": 50000
      }
    },
    {
      "name": "regex",
      "status": "always_available",
      "models": ["pattern_based"],
      "capabilities": ["basic_extraction"],
      "rate_limits": null
    }
  ],
  "current_primary": "openai",
  "fallback_chain": ["openai", "anthropic", "regex"]
}
```

### 5. Ticker Resolution

**POST** `/api/v1/resolve-ticker`

Resolve company names to stock ticker symbols with confidence scores.

**Request:**
```json
{
  "entities": [
    "Apple Inc.",
    "Microsoft Corporation", 
    "Tesla",
    "Alphabet Inc."
  ],
  "options": {
    "include_confidence": true,
    "include_alternatives": true,
    "market_preference": "US"
  }
}
```

**Response:**
```json
{
  "resolutions": [
    {
      "entity": "Apple Inc.",
      "ticker": "AAPL",
      "confidence": 0.99,
      "exchange": "NASDAQ",
      "country": "US",
      "alternatives": []
    },
    {
      "entity": "Microsoft Corporation",
      "ticker": "MSFT", 
      "confidence": 0.98,
      "exchange": "NASDAQ",
      "country": "US",
      "alternatives": []
    },
    {
      "entity": "Tesla",
      "ticker": "TSLA",
      "confidence": 0.95,
      "exchange": "NASDAQ", 
      "country": "US",
      "alternatives": [
        {"ticker": "TL0.DE", "exchange": "XETRA", "confidence": 0.85}
      ]
    },
    {
      "entity": "Alphabet Inc.",
      "ticker": "GOOGL",
      "confidence": 0.97,
      "exchange": "NASDAQ",
      "country": "US", 
      "alternatives": [
        {"ticker": "GOOG", "exchange": "NASDAQ", "confidence": 0.97}
      ]
    }
  ],
  "resolution_stats": {
    "total_entities": 4,
    "resolved_count": 4,
    "avg_confidence": 0.97,
    "resolution_rate": 1.0
  }
}
```

### 6. Metrics & Analytics

**GET** `/api/v1/metrics`

Retrieve system performance metrics and usage statistics.

**Response:**
```json
{
  "timestamp": "2025-05-24T10:30:00Z",
  "time_period": "last_24_hours",
  "performance_metrics": {
    "total_requests": 15420,
    "successful_requests": 15298,
    "error_rate": 0.79,
    "avg_response_time": 1.234,
    "p95_response_time": 2.1,
    "p99_response_time": 4.5
  },
  "claim_statistics": {
    "total_claims_processed": 45678,
    "verification_accuracy": 0.94,
    "claim_types": {
      "market_cap": 12345,
      "stock_price": 18903,
      "revenue": 8901,
      "other": 5529
    }
  },
  "llm_usage": {
    "openai": {
      "requests": 12000,
      "tokens_used": 2500000,
      "avg_response_time": 0.8,
      "success_rate": 99.2
    },
    "anthropic": {
      "requests": 2000,
      "tokens_used": 450000,
      "avg_response_time": 1.2,
      "success_rate": 98.8
    },
    "regex_fallback": {
      "requests": 1298,
      "success_rate": 85.0
    }
  },
  "cache_performance": {
    "hit_rate": 0.78,
    "total_hits": 12028,
    "total_misses": 3392,
    "cache_size": "2.1GB"
  }
}
```

## 🔧 Request/Response Format

### Request Headers
```http
Content-Type: application/json
X-API-Key: your-api-key-here
User-Agent: YourApp/1.0
Accept: application/json
X-Request-ID: optional-unique-request-id
```

### Common Request Options
```json
{
  "options": {
    "use_llm": true,                    // Enable LLM processing
    "llm_provider": "openai",           // Specific provider preference
    "include_context": true,            // Add market context
    "risk_assessment": true,            // Include risk analysis
    "cache_enabled": true,              // Use caching
    "timeout": 30,                      // Request timeout in seconds
    "confidence_threshold": 0.8,        // Minimum confidence for results
    "max_claims": 10,                   // Limit claims per request
    "output_format": "detailed"         // Response detail level
  }
}
```

### Response Status Codes
```
200 OK                    - Success
400 Bad Request          - Invalid request format
401 Unauthorized         - Invalid API key
429 Too Many Requests    - Rate limit exceeded
500 Internal Server Error - Server error
503 Service Unavailable  - System maintenance
```

### Error Response Format
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Request validation failed",
    "details": {
      "field": "text",
      "issue": "Text field is required"
    },
    "request_id": "req_error_123",
    "timestamp": "2025-05-24T10:30:00Z"
  }
}
```

## 📊 Data Models

### FinancialClaim Object
```json
{
  "original_text": "string",           // Original claim text
  "entity": "string",                 // Company/entity name
  "ticker": "string",                 // Stock ticker symbol
  "claim_type": "enum",              // market_cap, stock_price, revenue, etc.
  "claimed_value": "number",          // Value claimed in text
  "actual_value": "number",           // Verified actual value
  "currency": "string",               // Currency code (USD, EUR, etc.)
  "unit": "string",                   // Unit (billion, million, percent)
  "verification_status": "enum",      // correct, incorrect, partially_correct, unverified
  "confidence_score": "number",       // 0.0-1.0 confidence
  "accuracy_percentage": "number",    // 0-100 accuracy percentage
  "explanation": "string",            // Human-readable explanation
  "risk_level": "enum",              // low, medium, high
  "data_source": "string",            // Source of verification data
  "last_updated": "datetime",         // Data freshness timestamp
  "context": {                        // Optional market context
    "market_conditions": "string",
    "sector_performance": "string",
    "relevant_news": "array"
  }
}
```

### Claim Types Enum
```json
{
  "market_cap": "Market Capitalization",
  "stock_price": "Stock Price",
  "revenue": "Revenue/Sales",
  "earnings": "Earnings/Profit",
  "pe_ratio": "Price-to-Earnings Ratio",
  "dividend": "Dividend Information",
  "volume": "Trading Volume",
  "interest_rate": "Interest Rate",
  "inflation": "Inflation Rate",
  "gdp": "GDP Data",
  "exchange_rate": "Currency Exchange Rate",
  "commodity_price": "Commodity Price",
  "economic_indicator": "Economic Indicator"
}
```

### Verification Status Enum
```json
{
  "correct": "Claim is accurate",
  "incorrect": "Claim is inaccurate", 
  "partially_correct": "Claim is mostly accurate with minor discrepancies",
  "unverified": "Could not verify claim",
  "outdated": "Claim was accurate but data is outdated",
  "ambiguous": "Claim is unclear or ambiguous"
}
```

## 🚀 Rate Limiting

### Default Limits
```
Free Tier:
- 100 requests/hour
- 1,000 claims/day
- 5 concurrent requests

Professional:
- 1,000 requests/hour  
- 10,000 claims/day
- 20 concurrent requests

Enterprise:
- Custom limits
- Dedicated resources
- Priority support
```

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 3600
```

## 🔧 SDK Examples

### Python SDK
```python
import finsight

# Initialize client
client = finsight.Client(api_key="your-api-key")

# Single fact check
result = client.fact_check(
    text="Apple market cap is $3 trillion",
    use_llm=True,
    include_context=True
)

# Batch processing
results = client.batch_check([
    "Microsoft revenue is $200B",
    "Tesla stock at $200", 
    "Google market cap $1.8T"
])

# Async processing
import asyncio

async def check_claims():
    result = await client.async_fact_check(
        text="Amazon stock price is $150"
    )
    return result

# Ticker resolution
ticker = client.resolve_ticker("Apple Inc.")
print(f"Ticker: {ticker.symbol}, Confidence: {ticker.confidence}")
```

### JavaScript SDK
```javascript
const FinSight = require('finsight-sdk');

// Initialize client
const client = new FinSight({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.finsight.com'
});

// Single fact check
const result = await client.factCheck({
  text: 'Apple market cap is $3 trillion',
  options: {
    useLLM: true,
    includeContext: true
  }
});

// Batch processing
const results = await client.batchCheck({
  texts: [
    'Microsoft revenue is $200B',
    'Tesla stock at $200',
    'Google market cap $1.8T'
  ],
  options: {
    parallelProcessing: true
  }
});

// Stream processing
const stream = client.streamFactCheck();
stream.on('claim', (claim) => {
  console.log('Verified claim:', claim);
});
stream.write('Apple stock is $180 per share');
```

### cURL Examples
```bash
# Single fact check
curl -X POST "https://api.finsight.com/api/v1/fact-check" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Apple market cap is $3 trillion",
    "options": {
      "use_llm": true,
      "include_context": true
    }
  }'

# Health check
curl -X GET "https://api.finsight.com/api/v1/health" \
  -H "X-API-Key: your-api-key"

# Batch processing
curl -X POST "https://api.finsight.com/api/v1/batch-check" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Microsoft revenue is $200 billion",
      "Tesla stock is $200"
    ],
    "options": {
      "parallel_processing": true
    }
  }'
```

## 🔒 Security & Best Practices

### API Key Security
```bash
# Environment variable (recommended)
export FINSIGHT_API_KEY="your-api-key"

# Never hardcode in source code
# ❌ Bad
api_key = "sk-1234567890"

# ✅ Good  
api_key = os.getenv("FINSIGHT_API_KEY")
```

### Request Validation
- **Input sanitization:** All inputs are sanitized for security
- **Size limits:** Maximum request size of 1MB
- **Rate limiting:** Automatic rate limiting protection
- **Content validation:** JSON schema validation

### Error Handling
```python
try:
    result = client.fact_check(text="Invalid claim")
except finsight.APIError as e:
    print(f"API Error: {e.message}")
    print(f"Error Code: {e.code}")
except finsight.RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after}")
except finsight.ValidationError as e:
    print(f"Validation error: {e.details}")
```

## 📋 Testing & Development

### Test Endpoints
```
Development: https://dev-api.finsight.com
Staging: https://staging-api.finsight.com  
Production: https://api.finsight.com
```

### Mock Data
```json
{
  "test_claims": [
    "Apple market cap is $3 trillion",
    "Tesla stock price is $200",
    "Microsoft revenue is $200 billion",
    "Amazon P/E ratio is 50",
    "Google dividend yield is 0%"
  ],
  "expected_accuracy": 0.95,
  "processing_time": "<2s"
}
```

## 🔗 Related Documentation

- [[FinSight - Application Overview]] - System overview and capabilities
- [[FinSight - Deployment Guide]] - API deployment instructions
- [[FinSight - LLM Integration]] - LLM provider details
- [[FinSight - Technical Architecture]] - System architecture

---

*This API reference provides comprehensive documentation for integrating with FinSight. For additional support, examples, and updates, visit our documentation portal or contact our developer support team.*

## 📞 Support & Resources

- **Developer Portal:** https://developers.finsight.com
- **API Status:** https://status.finsight.com
- **Support Email:** api-support@finsight.com
- **GitHub Issues:** https://github.com/finsight/api-issues
- **Community Forum:** https://community.finsight.com
