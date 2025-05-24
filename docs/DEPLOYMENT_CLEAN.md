# 🚀 FinSight Deployment Guide - Multi-Environment Setup

## 🎯 Deployment Strategy Overview

FinSight supports multiple deployment configurations to accommodate different LLM hosting preferences:

### **Deployment Matrix**

| Environment | Primary LLM | Fallback | Use Case |
|-------------|-------------|----------|----------|
| **Local Development** | Ollama (localhost) | Regex | Development, testing |
| **Docker (Ollama)** | Ollama (container) | Regex | On-premise, air-gapped |
| **AWS Lambda** | OpenAI/Anthropic | Regex | Serverless, cloud-native |
| **Cloud Run (Hybrid)** | Ollama + Cloud APIs | Regex | Flexible cloud deployment |

---

## 🦙 **Option 1: Local Development with Ollama (Recommended)**

### Prerequisites

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended model
ollama pull llama3.2:3b

# Start Ollama server
ollama serve
```

### Setup FinSight

```bash
# Clone and setup
git clone <repository-url>
cd FinSight
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env: FINSIGHT_LLM_PROVIDER=ollama

# Run locally
python src/main.py --interactive
```

### API Server (Local)

```bash
# Start FastAPI server with Ollama
python finai_quality_api.py

# Test endpoint
curl http://localhost:8000/health
```

---

## ☁️ **Option 2: AWS Lambda (Serverless - Cloud LLM)**

> **⚠️ Important**: AWS Lambda cannot run Ollama locally. For detailed AWS deployment with Ollama-aware configuration, see [AWS Deployment Guide](./AWS_DEPLOYMENT_OLLAMA_AWARE.md).

### Quick AWS Deployment

```bash
cd deployment/aws

# Development with OpenAI
./deploy.sh deploy --stage dev --llm-provider openai --openai-key "$OPENAI_API_KEY"

# Production with Anthropic  
./deploy.sh deploy --stage prod --llm-provider anthropic --anthropic-key "$ANTHROPIC_API_KEY"

# Cost-free deployment (regex only)
./deploy.sh deploy --stage dev --llm-provider regex
```

### Key Features

- ✅ Automatic LLM provider fallback (OpenAI → Anthropic → Regex)
- ✅ Secure API key management  
- ✅ Cost optimization by deployment stage
- ✅ CloudWatch monitoring and alerting
- ✅ Production-ready scaling and performance

### 📖 Complete AWS Guide

For comprehensive AWS deployment instructions, including:

- Detailed LLM provider configuration
- Cost optimization strategies 
- Monitoring and troubleshooting
- CI/CD integration examples
- Security best practices

**👉 See [Complete AWS Deployment Guide](./AWS_DEPLOYMENT_OLLAMA_AWARE.md)**

---

## 🐳 **Option 3: Docker Deployment**

### Basic Docker Deployment

```bash
# Build image
docker build -t finsight-api .

# Run with environment variables
docker run -p 8000:8000 \
  -e FINSIGHT_LLM_PROVIDER=openai \
  -e OPENAI_API_KEY=your-key-here \
  finsight-api
```

### Docker Compose (Full Stack)

```yaml
version: '3.8'
services:
  finsight-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/finai
      - REDIS_URL=redis://redis:6379
      - FINSIGHT_LLM_PROVIDER=openai
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=finai
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine
    
volumes:
  postgres_data:
```

### Docker with Ollama Support

```yaml
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  
  finsight-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FINSIGHT_LLM_PROVIDER=ollama
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama

volumes:
  ollama_data:
```

---

## ⚡ **Option 4: Cloud Platforms**

### Heroku

```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create your-finsight-api

# Set environment variables
heroku config:set FINSIGHT_LLM_PROVIDER=openai
heroku config:set OPENAI_API_KEY=your-key-here

# Deploy
git push heroku main
```

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway link
railway up
```

### Vercel (Serverless)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

---

## 🔧 **Environment Configuration**

### Environment Variables

Create `.env` file (don't commit to git):

```bash
# LLM Configuration
FINSIGHT_LLM_PROVIDER=ollama  # or 'openai', 'anthropic', 'regex'
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_BASE_URL=http://localhost:11434

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/finai
REDIS_URL=redis://localhost:6379

# API Configuration
API_KEY=your-secure-api-key
DEBUG_MODE=false
```

### Rate Limiting & Security

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/fact-check")
@limiter.limit("10/minute")
async def fact_check_endpoint(request: Request):
    # Implementation
    pass
```

---

## 💰 **Cost Comparison**

### Monthly Estimates (1000 requests/day)

- **Local/Docker**: $0 (hardware costs only)
- **AWS Lambda**: $5-15/month (depending on LLM usage)
- **Heroku**: $25-50/month
- **AWS App Runner**: $30-80/month
- **Railway**: $20-40/month
- **Digital Ocean**: $25-100/month for VPS

### LLM API Costs (per 1M tokens)

- **OpenAI GPT-4o-mini**: $0.15 input / $0.60 output
- **Anthropic Claude-3-Haiku**: $0.25 input / $1.25 output
- **Ollama (self-hosted)**: $0 (hardware/compute costs only)

---

## 📈 **Post-Deployment Checklist**

### Basic Health Checks

- [ ] API responds to `/health` endpoint
- [ ] LLM provider connection working
- [ ] Interactive docs available at `/docs`
- [ ] Error handling working properly

### Production Readiness

- [ ] HTTPS/SSL configured
- [ ] Rate limiting enabled
- [ ] Monitoring/logging configured
- [ ] Environment variables secured
- [ ] Backup strategy in place
- [ ] Custom domain configured (optional)

### Performance Testing

```bash
# Basic load test
curl -X POST "https://your-api.com/api/fact-check" \
  -H "Content-Type: application/json" \
  -d '{"text": "Apple Inc. reported record revenue in Q4 2023.", "ticker": "AAPL"}'

# Load testing with Apache Bench
ab -n 100 -c 10 https://your-api.com/health
```

---

## 🚨 **Troubleshooting**

### Common Issues

1. **Ollama Connection Failed**
   - Check if Ollama service is running: `ollama serve`
   - Verify model is downloaded: `ollama list`
   - Check OLLAMA_BASE_URL environment variable

2. **LLM API Errors**
   - Verify API keys are set correctly
   - Check API quotas and billing
   - Monitor rate limits

3. **Memory Issues**
   - Increase Lambda memory allocation (AWS)
   - Use lighter LLM models for resource-constrained environments
   - Implement request caching

### Debug Mode

```bash
# Enable debug logging
export DEBUG_MODE=true
python finai_quality_api.py
```

---

## 🔗 **Related Documentation**

- [AWS Deployment Guide (Ollama-Aware)](./AWS_DEPLOYMENT_OLLAMA_AWARE.md)
- [Local LLM Setup Guide](./LOCAL_LLM_SETUP.md)
- [Architecture Overview](./ARCHITECTURE.md)
- [API Documentation](./README.md)

---

**Need help?** Check our [troubleshooting guide](./AWS_DEPLOYMENT_OLLAMA_AWARE.md#troubleshooting) or open an issue on GitHub.
