# FinSight API Documentation

## Overview

The FinSight API provides real-time financial data enrichment for LLM applications. It offers high-performance endpoints for stock data, market context, and economic indicators.

## Base URL

- Development: `http://localhost:8000`
- Production: `https://api.finsight.ai`

## Authentication

All API requests require an API key, which should be included in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" https://api.finsight.ai/enrich
```

## Endpoints

### 1. Enrich Content

Enriches text content with financial data and market context.

```http
POST /enrich
```

#### Request Body

```json
{
  "content": "Apple (AAPL) stock is trading at $195",
  "enrichment_types": ["stock_data", "market_context"],
  "format_style": "enhanced"
}
```

| Field | Type | Description |
|-------|------|-------------|
| content | string | Text content to enrich |
| enrichment_types | array | Types of enrichment to apply |
| format_style | string | Output format style |

#### Response

```json
{
  "enriched_content": "Apple (AAPL) stock is trading at $195.00 (as of 2024-03-20 14:30:00 UTC). Market cap: $3.02T. 52-week range: $124.17 - $199.62. Volume: 52.3M shares.",
  "metadata": {
    "timestamp": "2024-03-20T14:30:00Z",
    "data_sources": ["Yahoo Finance"],
    "confidence_score": 0.98
  }
}
```

### 2. Health Check

Checks the API health status.

```http
GET /health
```

#### Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-03-20T14:30:00Z",
  "services": {
    "data_aggregator": "operational",
    "cache": "operational",
    "api_gateway": "operational"
  }
}
```

### 3. System Status

Provides detailed system status information.

```http
GET /status
```

#### Response

```json
{
  "status": "operational",
  "performance": {
    "response_time_ms": 45,
    "cache_hit_rate": 0.95,
    "requests_per_second": 120
  },
  "resources": {
    "memory_usage": "45%",
    "cpu_usage": "30%",
    "active_connections": 150
  },
  "last_updated": "2024-03-20T14:30:00Z"
}
```

## Enrichment Types

### Stock Data

Provides real-time stock information:

- Current price
- Market cap
- Volume
- 52-week range
- P/E ratio
- Dividend yield

### Market Context

Adds market context:

- Sector performance
- Market indices
- Related stocks
- News sentiment
- Economic indicators

### Economic Indicators

Includes economic data:

- Interest rates
- Inflation metrics
- GDP growth
- Employment data
- Consumer sentiment

## Format Styles

### Basic

Minimal enrichment with essential data:

```json
{
  "enriched_content": "AAPL: $195.00 (↑1.2%)"
}
```

### Enhanced

Detailed enrichment with context:

```json
{
  "enriched_content": "Apple (AAPL) stock is trading at $195.00, up 1.2% today. Market cap: $3.02T. Volume: 52.3M shares. Sector: Technology (↑0.8%)."
}
```

### Technical

Technical analysis focused:

```json
{
  "enriched_content": "AAPL: $195.00 (RSI: 65, MACD: Bullish, Support: $190, Resistance: $200)"
}
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid enrichment type specified",
    "details": {
      "field": "enrichment_types",
      "issue": "Unsupported type: 'invalid_type'"
    }
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| INVALID_REQUEST | Invalid request parameters |
| UNAUTHORIZED | Missing or invalid API key |
| RATE_LIMITED | Too many requests |
| DATA_UNAVAILABLE | Requested data not available |
| INTERNAL_ERROR | Server-side error |

## Rate Limiting

- Free tier: 100 requests/minute
- Pro tier: 1000 requests/minute
- Enterprise: Custom limits

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1616248800
```

## Best Practices

1. **Caching**
   - Cache responses when possible
   - Use ETags for conditional requests
   - Implement client-side caching

2. **Error Handling**
   - Implement exponential backoff
   - Handle rate limits gracefully
   - Log errors for debugging

3. **Performance**
   - Use compression (gzip)
   - Minimize request size
   - Batch requests when possible

## SDK Examples

### Python

```python
from finsight import FinSightClient

client = FinSightClient(api_key="your-api-key")

# Enrich content
response = client.enrich(
    content="Apple stock is trading at $195",
    enrichment_types=["stock_data", "market_context"],
    format_style="enhanced"
)

print(response.enriched_content)
```

### JavaScript

```javascript
const { FinSightClient } = require('finsight');

const client = new FinSightClient('your-api-key');

// Enrich content
client.enrich({
    content: 'Apple stock is trading at $195',
    enrichment_types: ['stock_data', 'market_context'],
    format_style: 'enhanced'
})
.then(response => console.log(response.enriched_content))
.catch(error => console.error(error));
```

## Webhook Integration

Configure webhooks to receive real-time updates:

```http
POST /webhooks
```

### Webhook Payload

```json
{
  "event": "price_update",
  "data": {
    "symbol": "AAPL",
    "price": 195.00,
    "timestamp": "2024-03-20T14:30:00Z"
  }
}
```

## Support

For API support:
- Email: api-support@finsight.ai
- Documentation: https://docs.finsight.ai
- Status: https://status.finsight.ai 