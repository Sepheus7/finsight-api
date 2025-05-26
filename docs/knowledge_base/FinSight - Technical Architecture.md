# FinSight - Technical Architecture

## 🏗️ System Architecture Overview

### **High-Level Architecture**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  FinSight Core   │───▶│   Response      │
│                 │    │                  │    │                 │
│ • CLI Interface │    │ • Claim Extract  │    │ • Fact Check    │
│ • API Requests  │    │ • Ticker Resolve │    │ • Confidence    │
│ • Web Frontend  │    │ • Data Retrieval │    │ • Compliance    │
└─────────────────┘    │ • LLM Analysis   │    └─────────────────┘
                       │ • Compliance     │
                       └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     External Integrations                       │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   LLM Providers │   Data Sources  │      Infrastructure        │
│                 │                 │                             │
│ • Ollama Local  │ • Yahoo Finance │ • AWS Lambda               │
│ • OpenAI API    │ • Financial APIs│ • CloudWatch               │
│ • Anthropic API │ • Market Data   │ • DynamoDB                 │
│ • Regex Fallback│ • Company Info  │ • S3 Caching              │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

---

## 🔄 Core Processing Pipeline

### **1. Claim Extraction**
```python
# File: src/utils/llm_claim_extractor.py
Input: "Apple stock is trading at $150"
↓
LLM Analysis: Extract financial claims
↓
Output: {
  "company": "Apple",
  "claim_type": "stock_price", 
  "value": 150,
  "currency": "USD"
}
```

### **2. Ticker Resolution**
```python
# File: src/utils/enhanced_ticker_resolver.py
Input: "Apple"
↓
Fuzzy Matching + Company Database
↓
Output: {
  "ticker": "AAPL",
  "confidence": 0.98,
  "company_name": "Apple Inc."
}
```

### **3. Data Retrieval**
```python
# File: src/utils/financial_data_fetcher.py
Input: "AAPL"
↓
Yahoo Finance API + Caching (24h TTL)
↓
Output: {
  "current_price": 173.50,
  "last_updated": "2025-05-24T10:30:00Z",
  "market_cap": "2.7T"
}
```

### **4. Fact Checking**
```python
# File: src/handlers/enhanced_fact_check_handler.py
Compare: Claim ($150) vs Reality ($173.50)
↓
Analysis: Price difference, percentage variance
↓
Output: {
  "accuracy": "INACCURATE",
  "actual_value": 173.50,
  "variance": 15.7%
}
```

---

## 🤖 LLM Integration Architecture

### **Multi-LLM Strategy**
```
Primary: Ollama (Local)
    ↓ (if AWS Lambda)
Fallback: OpenAI/Anthropic (Cloud)
    ↓ (if API failure)
Emergency: Regex Patterns (No LLM)
```

### **LLM Configuration by Environment**
| Environment | Primary LLM | Fallback | Notes |
|-------------|-------------|----------|-------|
| **Local Dev** | Ollama (llama3.2:3b) | Regex | Best accuracy, free |
| **AWS Lambda** | OpenAI GPT-4o-mini | Anthropic | Serverless compatible |
| **Docker** | Ollama + Cloud | Regex | Hybrid approach |
| **CI/CD** | Regex only | None | Fast, reliable testing |

---

## 🗄️ Data Architecture

### **Data Flow**
```
User Input → Claim Extraction → Ticker Cache → Yahoo Finance API → Response Cache → User
                    ↑                 ↑              ↑              ↑
                    └─ LLM Cache ─────┴─ Ticker DB ──┴─ Market Data ─┘
```

### **Caching Strategy**
- **Ticker Resolution**: 7 days TTL (company mappings change rarely)
- **Market Data**: 5 minutes TTL (real-time pricing)
- **LLM Responses**: 1 hour TTL (claim patterns)
- **Company Database**: 30 days TTL (static company info)

### **Data Sources**
```python
# Primary Data Sources
YAHOO_FINANCE_API = "yfinance library"
COMPANY_DATABASE = "Built-in ticker mapping"
FINANCIAL_APIS = "Future integration points"

# Caching Layers
LOCAL_CACHE = "In-memory TTL cache"
REDIS_CACHE = "Distributed caching (future)"
S3_CACHE = "AWS deployment caching"
```

---

## ☁️ AWS Architecture

### **Serverless Components**
```
API Gateway → Lambda Functions → DynamoDB/S3
     ↓              ↓              ↓
  Rate Limiting  Auto-scaling   Data Storage
  Authentication  Monitoring    Caching
```

### **Lambda Functions**
- **EnhancedFactCheckFunction**: Main processing logic
- **HealthCheckFunction**: System health monitoring
- **ComplianceCheckFunction**: Regulatory validation
- **ContextEnrichmentFunction**: Additional data gathering

### **Infrastructure Resources**
```yaml
# CloudFormation Template: template-ollama-aware.yaml
Resources:
  - API Gateway (REST API)
  - Lambda Functions (Python 3.11)
  - DynamoDB Tables (compliance rules, history)
  - S3 Buckets (caching, logs)
  - CloudWatch (monitoring, alerting)
  - IAM Roles (least privilege access)
```

---

## 🔧 Configuration Management

### **Environment Variables**
```python
# Core Configuration (src/config.py)
LLM_PROVIDER = "ollama|openai|anthropic|regex"
OLLAMA_BASE_URL = "http://localhost:11434"
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
FINSIGHT_CACHE_ENABLED = "true"
FINSIGHT_CACHE_HOURS = "24"
FINSIGHT_DEBUG = "false"
```

### **Deployment-Specific Config**
```bash
# Local Development
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b

# AWS Production
LLM_PROVIDER=anthropic
ANTHROPIC_MODEL=claude-3-haiku-20240307

# Cost-Optimized
LLM_PROVIDER=regex
```

---

## 🔍 Monitoring & Observability

### **Metrics Collection**
- **Performance**: Response times, throughput, error rates
- **Accuracy**: Fact-check confidence scores, ticker resolution success
- **Usage**: API calls, LLM requests, cache hit rates
- **Costs**: AWS Lambda invocations, LLM API costs

### **Alerting Rules**
```yaml
# CloudWatch Alarms
HighErrorRate: >5% error rate for 5 minutes
SlowResponse: >10s response time
LowAccuracy: <80% fact-check confidence
CostThreshold: >$50/day AWS costs
```

### **Logging Strategy**
```python
# Structured Logging
{
  "timestamp": "2025-05-24T10:30:00Z",
  "level": "INFO",
  "component": "fact_checker",
  "claim": "Apple stock at $150",
  "ticker": "AAPL",
  "actual_price": 173.50,
  "accuracy": "INACCURATE",
  "confidence": 0.95,
  "llm_provider": "anthropic",
  "response_time_ms": 1250
}
```

---

## 🔒 Security Architecture

### **API Security**
- **Authentication**: AWS IAM, API Keys
- **Rate Limiting**: API Gateway throttling
- **Input Validation**: Sanitization, type checking
- **Output Filtering**: No sensitive data exposure

### **Data Protection**
- **Encryption in Transit**: HTTPS/TLS 1.3
- **Encryption at Rest**: AWS KMS, S3 encryption
- **API Key Management**: NoEcho CloudFormation parameters
- **Access Control**: Least privilege IAM policies

### **Compliance Considerations**
- **Financial Data**: No PII storage
- **Audit Logging**: All requests logged
- **Data Retention**: Configurable TTL policies
- **Regulatory**: Financial advice disclaimers

---

## 🚀 Scalability Design

### **Horizontal Scaling**
- **AWS Lambda**: Auto-scaling based on demand
- **API Gateway**: Built-in scalability
- **DynamoDB**: On-demand scaling
- **Caching**: Distributed cache strategy

### **Performance Optimization**
- **Cold Start**: Lambda provisioned concurrency
- **Caching**: Multi-layer cache strategy
- **Data**: Parallel API calls where possible
- **LLM**: Model size vs accuracy tradeoffs

### **Cost Optimization**
```python
# Stage-based Resource Allocation
ENVIRONMENTS = {
    "dev": {
        "lambda_memory": 512,
        "lambda_timeout": 30,
        "monitoring": "basic"
    },
    "prod": {
        "lambda_memory": 1536,
        "lambda_timeout": 120,
        "monitoring": "enhanced"
    }
}
```

---

## 📊 Technical Metrics

| Component | Current Performance | Target |
|-----------|-------------------|---------|
| **API Response Time** | <2s (local), <5s (cloud) | <1s, <3s |
| **Ticker Resolution** | 95% accuracy | 98% |
| **Cache Hit Rate** | 85% | 90% |
| **Lambda Cold Start** | ~500ms | <300ms |
| **Cost per Request** | $0.001 (AWS) | $0.0005 |

---

## 🔗 Related Documentation

- [[FinSight - Application Overview]]
- [[FinSight - Deployment Guide]]
- [[FinSight - LLM Integration]]
- [[FinSight - API Reference]]

---

*Last Updated: May 24, 2025*  
*Architecture Version: 2.0*
