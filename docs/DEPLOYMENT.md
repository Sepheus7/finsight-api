# 🚀 Deployment Guide - Making FinSight Available Online

## Quick Deploy Options

### 🟢 Option 1: Railway (Easiest - 5 minutes)
**Perfect for MVP demos and testing**

1. **Prepare the project:**
```bash
# Create a startup script
echo 'uvicorn finai_quality_api:app --host 0.0.0.0 --port $PORT' > start.sh
chmod +x start.sh
```

2. **Deploy to Railway:**
- Visit [railway.app](https://railway.app)
- Connect your GitHub repository
- Railway auto-detects Python and deploys
- Your API will be live at: `https://your-app.railway.app`

---

### 🟡 Option 2: Render (Free Tier Available)
**Great for showcasing to potential customers**

1. **Create render.yaml:**
```yaml
services:
  - type: web
    name: finai-quality-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn finai_quality_api:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.16
```

2. **Deploy:**
- Visit [render.com](https://render.com)
- Connect GitHub repository
- Automatic deployments on git push
- Free tier includes HTTPS and custom domains

---

### 🔵 Option 3: Google Cloud Run (Scalable)
**Production-ready with auto-scaling**

1. **Setup:**
```bash
# Install Google Cloud CLI
brew install google-cloud-sdk

# Login and set project
gcloud auth login
gcloud config set project your-project-id
```

2. **Deploy:**
```bash
# Build and deploy
gcloud run deploy finai-quality-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

### 🟠 Option 4: AWS App Runner (Enterprise)
**Fully managed with AWS integration**

1. **Create apprunner.yaml:**
```yaml
version: 1.0
runtime: python3
build:
  commands:
    build:
      - pip install -r requirements.txt
run:
  runtime-version: 3.9.16
  command: uvicorn finai_quality_api:app --host 0.0.0.0 --port 8000
  network:
    port: 8000
    env: PORT
```

---

## 📦 Production-Ready Deployment

### Docker Compose for Local Testing
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/finai
      - REDIS_URL=redis://redis:6379
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
