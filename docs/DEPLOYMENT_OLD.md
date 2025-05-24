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
curl -X POST http://localhost:8000/fact-check \
  -H "Content-Type: application/json" \
  -d '{"content": "Microsoft market cap is $3 trillion"}'
```

---

## 🐳 **Option 2: Docker Deployment with Ollama**

### Multi-Container Setup
```yaml
# docker-compose.yml
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_MODELS=llama3.2:3b
    
  finsight:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FINSIGHT_LLM_PROVIDER=ollama
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=llama3.2:3b
    depends_on:
      - ollama
    volumes:
      - ./data:/app/data

volumes:
  ollama_data:
```

### Deploy Commands
```bash
# Build and run
docker-compose up -d

# Pull Ollama model
docker-compose exec ollama ollama pull llama3.2:3b

# Check health
curl http://localhost:8000/health
```

---

## ☁️ **Option 3: AWS Lambda (Serverless - Cloud LLM)**

> **⚠️ Important**: AWS Lambda cannot run Ollama locally. For detailed AWS deployment with Ollama-aware configuration, see [AWS Deployment Guide](./AWS_DEPLOYMENT_OLLAMA_AWARE.md).

**Quick AWS Deployment:**
```bash
cd deployment/aws

# Development with OpenAI
./deploy.sh deploy --stage dev --llm-provider openai --openai-key "$OPENAI_API_KEY"

# Production with Anthropic  
./deploy.sh deploy --stage prod --llm-provider anthropic --anthropic-key "$ANTHROPIC_API_KEY"

# Cost-free deployment (regex only)
./deploy.sh deploy --stage dev --llm-provider regex
```

**Key Features:**
- ✅ Automatic LLM provider fallback (OpenAI → Anthropic → Regex)
- ✅ Secure API key management  
- ✅ Cost optimization by deployment stage
- ✅ CloudWatch monitoring and alerting
- ✅ Production-ready scaling and performance

**📖 For comprehensive AWS deployment instructions, including:**
- Detailed LLM provider configuration
- Cost optimization strategies 
- Monitoring and troubleshooting
- CI/CD integration examples
- Security best practices

**👉 See [Complete AWS Deployment Guide](./AWS_DEPLOYMENT_OLLAMA_AWARE.md)**

---

## 🐳 **Option 4: Docker Deployment**

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

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finai-quality-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: finai-quality-api
  template:
    metadata:
      labels:
        app: finai-quality-api
    spec:
      containers:
      - name: api
        image: finai-quality-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
---
apiVersion: v1
kind: Service
metadata:
  name: finai-quality-api-service
spec:
  selector:
    app: finai-quality-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 🌐 Domain & SSL Setup

### Custom Domain (After Deployment)
1. **Purchase domain** (e.g., `finai-quality.com`)
2. **Configure DNS:**
   - Point A record to your deployment IP
   - Add CNAME for `api.finai-quality.com`
3. **SSL Certificate:**
   - Most platforms provide free SSL
   - For custom: Use Let's Encrypt or Cloudflare

### Example DNS Configuration
```
Type  | Name | Value
------|------|------
A     | @    | 123.456.789.0
CNAME | api  | your-app.railway.app
CNAME | www  | your-app.railway.app
```

## 📊 Monitoring Setup

### Health Check Endpoint
Add to your API:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

### Basic Monitoring
```python
# Add to finai_quality_api.py
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## 🔐 Security for Production

### Environment Variables
```bash
# Create .env file (don't commit to git)
DATABASE_URL=postgresql://user:pass@localhost/finai
REDIS_URL=redis://localhost:6379
API_SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=https://your-frontend.com,https://another-domain.com
```

### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/enhance")
@limiter.limit("100/minute")
async def enhance_ai_response(request: Request, data: EnrichmentRequest):
    # Your existing code
```

## 💰 Cost Estimates

### Development/Demo (Free Tiers)
- **Railway**: Free for 5GB bandwidth/month
- **Render**: Free tier with 750 hours/month
- **Vercel**: Free for personal projects

### Production Estimates
- **Google Cloud Run**: ~$20-50/month for moderate traffic
- **AWS App Runner**: ~$30-80/month 
- **Digital Ocean**: ~$25-100/month for VPS

## 🚀 Quick Start Commands

Choose your deployment method:

```bash
# Railway (Easiest)
npm install -g @railway/cli
railway login
railway init
railway up

# Render
git push origin main  # Auto-deploys if connected

# Google Cloud
gcloud run deploy --source .

# Docker (Local testing)
docker build -t finai-api .
docker run -p 8000:8000 finai-api
```

## 📈 Post-Deployment Checklist

- [ ] API accessible at public URL
- [ ] Health check endpoint working
- [ ] Interactive docs available at `/docs`
- [ ] HTTPS/SSL configured
- [ ] Custom domain configured (optional)
- [ ] Monitoring/logging enabled
- [ ] Rate limiting configured
- [ ] Backup strategy implemented
- [ ] CI/CD pipeline setup

## 🎯 Next Steps After Deployment

1. **Share Demo URL** with potential customers
2. **Set up analytics** to track usage
3. **Create landing page** explaining the service
4. **Add authentication** for production use
5. **Implement billing/subscription** system
6. **Scale based on demand**

---

**Your MVP will be live and accessible worldwide! 🌍**
