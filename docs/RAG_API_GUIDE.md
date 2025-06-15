# 🎯 FinSight Financial RAG API Guide

**The Ultimate Financial Data API for AI Agents**

## 🌟 Overview

The FinSight RAG (Retrieval-Augmented Generation) API is a **one-stop financial data endpoint** designed specifically for AI agents. Instead of building complex fact-checking and compliance systems, focus on what matters: **getting rich, contextual financial data fast**.

### ✨ Why This RAG API?

- **🚀 Single Endpoint**: One API call gets you everything
- **⚡ High Performance**: Parallel data fetching, intelligent caching
- **🎯 AI-Optimized**: Structured responses perfect for AI consumption
- **📊 Multi-Source**: Yahoo Finance, FRED, Alpha Vantage fallbacks
- **🔍 Smart Extraction**: Automatically extracts financial entities from queries

## 🏗️ Architecture

```
AI Agent Query → RAG API → [Data Aggregator] → Multiple Sources
                    ↓
              Structured Context ← [Context Builder] ← Parallel Processing
```

## 🚀 Quick Start

### 1. Start the Server

```bash
python demo/llm_api_server.py
```

### 2. Make Your First RAG Request

```bash
curl -X POST http://localhost:8000/rag \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Apple stock price and how is it performing?",
    "include_economic": true
  }'
```

### 3. Get Rich Financial Context

```json
{
  "query_analysis": {
    "original_query": "What is Apple stock price and how is it performing?",
    "extracted_symbols": ["AAPL"],
    "query_intent": "valuation"
  },
  "financial_data": {
    "stocks": {
      "AAPL": {
        "symbol": "AAPL",
        "price": 196.45,
        "change": -1.38,
        "change_percent": -0.70,
        "volume": 45234567,
        "market_cap": 3045000000000,
        "day_range": "$195.12 - $198.23"
      }
    },
    "count": 1
  },
  "market_insights": [
    "Market sentiment is mixed with recent volatility",
    "Tech sector showing resilience despite broader market concerns"
  ],
  "economic_context": {
    "fed_funds_rate": 5.25,
    "unemployment_rate": 3.7,
    "inflation_rate": 3.2
  },
  "summary": "Analyzed 1 stock with average change of -0.70%. Economic context includes 3 indicators",
  "metadata": {
    "processing_time_ms": 234,
    "symbols_analyzed": ["AAPL"],
    "data_sources_used": 2,
    "cache_hit_rate": 0.0,
    "timestamp": "2025-01-27T10:30:00Z"
  }
}
```

## 📋 API Reference

### Endpoint: `POST /rag`

**Purpose**: Get comprehensive financial context for AI agents

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | No* | "" | Natural language financial query |
| `symbols` | array | No* | [] | List of stock symbols to analyze |
| `include_economic` | boolean | No | true | Include economic indicators |
| `include_market_context` | boolean | No | true | Include market sentiment and trends |

*Either `query` or `symbols` must be provided

#### Response Structure

```typescript
interface RAGResponse {
  query_analysis: {
    original_query: string;
    extracted_symbols: string[];
    query_intent: "comparison" | "trend_analysis" | "portfolio_analysis" | 
                  "economic_analysis" | "valuation" | "general_inquiry";
  };
  financial_data: {
    stocks: Record<string, StockData>;
    count: number;
  };
  market_insights: string[];
  economic_context: Record<string, any>;
  summary: string;
  metadata: {
    processing_time_ms: number;
    symbols_analyzed: string[];
    data_sources_used: number;
    cache_hit_rate: number;
    timestamp: string;
  };
}
```

## 🎯 Use Cases for AI Agents

### 1. **Investment Research Assistant**

```javascript
// AI Agent: "Research Apple's current performance"
const context = await fetch('/rag', {
  method: 'POST',
  body: JSON.stringify({
    query: "Research Apple's current performance and market position",
    include_economic: true,
    include_market_context: true
  })
});

// Use the structured data to generate insights
const response = `Apple (AAPL) is currently trading at $${context.financial_data.stocks.AAPL.price} 
with a ${context.financial_data.stocks.AAPL.change_percent}% change. 
${context.market_insights.join(' ')}`;
```

### 2. **Portfolio Analysis Bot**

```python
# AI Agent: "Compare my tech holdings"
import requests

response = requests.post('http://localhost:8000/rag', json={
    "query": "Compare performance of my tech holdings",
    "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN"],
    "include_market_context": True
})

context = response.json()
# Generate portfolio insights using structured data
```

### 3. **Economic Context Provider**

```python
# AI Agent: "What's the economic environment for investing?"
response = requests.post('http://localhost:8000/rag', json={
    "query": "Current economic environment for tech investments",
    "include_economic": True,
    "include_market_context": False
})

economic_data = response.json()['economic_context']
# Use economic indicators to inform investment advice
```

### 4. **Real-time Market Monitor**

```javascript
// AI Agent: Monitor specific stocks
const monitorStocks = async (symbols) => {
  const context = await fetch('/rag', {
    method: 'POST',
    body: JSON.stringify({
      symbols: symbols,
      query: "Monitor these stocks for changes",
      include_economic: false
    })
  });
  
  return context.financial_data.stocks;
};
```

## 🔧 Integration Examples

### Python Integration

```python
import asyncio
import aiohttp

class FinancialRAGClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    async def get_financial_context(self, query=None, symbols=None, **kwargs):
        async with aiohttp.ClientSession() as session:
            payload = {"query": query or "", "symbols": symbols or [], **kwargs}
            async with session.post(f"{self.base_url}/rag", json=payload) as resp:
                return await resp.json()

# Usage
client = FinancialRAGClient()
context = await client.get_financial_context(
    query="How is Tesla performing vs traditional automakers?",
    symbols=["TSLA", "F", "GM"]
)
```

### JavaScript/Node.js Integration

```javascript
class FinancialRAGClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }
  
  async getFinancialContext(options) {
    const response = await fetch(`${this.baseUrl}/rag`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options)
    });
    
    return await response.json();
  }
}

// Usage
const client = new FinancialRAGClient();
const context = await client.getFinancialContext({
  query: "What's happening with Apple stock?",
  include_economic: true
});
```

### cURL Examples

```bash
# Basic stock query
curl -X POST http://localhost:8000/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "Apple stock analysis"}'

# Multiple symbols comparison
curl -X POST http://localhost:8000/rag \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "query": "Compare these tech giants",
    "include_market_context": true
  }'

# Economic indicators only
curl -X POST http://localhost:8000/rag \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Current economic indicators",
    "include_economic": true,
    "include_market_context": false
  }'
```

## ⚡ Performance Features

### Intelligent Caching
- **Stock Data**: 1-hour cache for price data
- **Economic Data**: 24-hour cache for indicators
- **Market Context**: 1-hour cache for sentiment data

### Parallel Processing
- Multiple data sources fetched simultaneously
- Async/await throughout the pipeline
- Connection pooling for external APIs

### Fallback Strategy
1. **Primary**: Yahoo Finance (fast, reliable)
2. **Secondary**: Alpha Vantage (requires API key)
3. **Tertiary**: Cached data (if available)

## 🎯 Query Intent Recognition

The API automatically recognizes query intent to optimize data retrieval:

| Intent | Triggers | Optimizations |
|--------|----------|---------------|
| `comparison` | "vs", "compare", "versus" | Fetches multiple symbols |
| `trend_analysis` | "trend", "performance", "over time" | Includes historical context |
| `portfolio_analysis` | "portfolio", "allocation" | Adds sector data |
| `economic_analysis` | "economy", "gdp", "inflation" | Prioritizes economic indicators |
| `valuation` | "price", "value", "worth" | Focuses on pricing data |

## 🔍 Smart Entity Extraction

The API automatically extracts financial entities from natural language:

```python
# Input: "How is Apple and Microsoft performing compared to Google?"
# Extracted: ["AAPL", "MSFT", "GOOGL"]

# Input: "What's the current tech sector outlook?"
# Extracted: [] (will fetch general market data)

# Input: "Tesla vs Ford stock comparison"
# Extracted: ["TSLA", "F"]
```

## 📊 Data Sources

### Primary Sources
- **Yahoo Finance**: Real-time stock prices, market caps, trading data
- **FRED (Federal Reserve)**: Economic indicators, interest rates, inflation
- **Alpha Vantage**: Backup stock data, technical indicators

### Data Types Available
- **Stock Data**: Price, volume, market cap, P/E ratio, day range
- **Economic Indicators**: Fed funds rate, unemployment, inflation, GDP
- **Market Context**: Sector performance, sentiment, volatility

## 🚀 Getting Started for AI Agents

### 1. **Simple Integration**
Start with basic queries to get familiar with the response structure.

### 2. **Structured Queries**
Use specific symbols when you know what you're looking for.

### 3. **Context-Aware Responses**
Leverage the `query_intent` and `market_insights` for better AI responses.

### 4. **Performance Optimization**
Monitor `processing_time_ms` and `cache_hit_rate` for optimization opportunities.

## 🔧 Configuration

### Environment Variables
```bash
# Optional: For enhanced data sources
ALPHA_VANTAGE_API_KEY=your_key_here
FRED_API_KEY=your_key_here

# Server configuration
PORT=8000
HOST=0.0.0.0
```

### Rate Limiting
- Default: 60 requests/minute
- Burst capacity: 10 requests
- Configurable via environment variables

## 📈 Monitoring & Health

### Health Check
```bash
curl http://localhost:8000/health
```

### Performance Stats
```bash
curl http://localhost:8000/performance-stats
```

### System Health
```bash
curl http://localhost:8000/system-health
```

## 🎯 Best Practices for AI Agents

### 1. **Cache-Friendly Queries**
- Reuse similar queries within the cache window
- Batch multiple symbols in single requests

### 2. **Error Handling**
```python
try:
    context = await rag_client.get_financial_context(query)
    if 'error' in context:
        # Handle API errors gracefully
        fallback_response = "Unable to fetch current market data"
except Exception as e:
    # Handle network/connection errors
    fallback_response = "Market data temporarily unavailable"
```

### 3. **Response Processing**
```python
def process_rag_response(context):
    # Always check for data availability
    stocks = context.get('financial_data', {}).get('stocks', {})
    if not stocks:
        return "No stock data available for this query"
    
    # Use structured insights
    insights = context.get('market_insights', [])
    summary = context.get('summary', '')
    
    # Build AI response using structured data
    return build_ai_response(stocks, insights, summary)
```

### 4. **Performance Monitoring**
```python
# Monitor API performance
metadata = context.get('metadata', {})
if metadata.get('processing_time_ms', 0) > 5000:
    logger.warning("Slow RAG response detected")

# Track cache efficiency
cache_hit_rate = metadata.get('cache_hit_rate', 0)
if cache_hit_rate < 0.3:
    logger.info("Low cache hit rate, consider query optimization")
```

## 🔗 Next Steps

1. **Start Simple**: Begin with basic stock queries
2. **Explore Intents**: Try different query types to see intent recognition
3. **Optimize Performance**: Monitor response times and cache usage
4. **Scale Up**: Integrate into your AI agent's decision-making pipeline

## 📚 Additional Resources

- **Interactive API Docs**: http://localhost:8000/docs
- **Health Dashboard**: http://localhost:8000/system-health
- **Test Script**: `python test_rag_api.py`

---

**🎉 You now have a powerful financial RAG API that can provide rich, contextual financial data to any AI agent in a single API call!** 