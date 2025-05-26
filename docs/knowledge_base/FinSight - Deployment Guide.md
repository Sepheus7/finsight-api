# FinSight - Deployment Guide

*Last Updated: May 24, 2025*  
*Version: 2.1.0*  
*Documentation Type: Deployment & Operations*

## 🎯 Deployment Overview

FinSight supports multiple deployment environments with comprehensive automation and configuration management. This guide covers all deployment scenarios from local development to production AWS Lambda deployment.

## 🚀 Quick Start Deployment

### 🦙 Local Development (Recommended for Testing)

**Prerequisites:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended model
ollama pull llama3.2:3b

# Start Ollama server
ollama serve
```

**FinSight Setup:**
```bash
# Clone and setup
git clone <repository-url>
cd FinSight
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env: FINSIGHT_LLM_PROVIDER=ollama

# Start development server
python finai_quality_api.py
# Access at http://localhost:8000/docs
```

### ☁️ AWS Lambda Production Deployment

**Prerequisites:**
```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Install SAM CLI
brew install aws-sam-cli

# Configure AWS credentials
aws configure
```

**Deploy to AWS:**
```bash
cd deployment/aws

# Deploy with OpenAI provider (recommended for production)
./deploy.sh deploy \
    --stage prod \
    --llm-provider openai \
    --openai-key $OPENAI_API_KEY \
    --region us-east-1

# Deploy with Anthropic provider (alternative)
./deploy.sh deploy \
    --stage prod \
    --llm-provider anthropic \
    --anthropic-key $ANTHROPIC_API_KEY
```

### 🐳 Docker Deployment

**Basic Docker:**
```bash
# Build image
docker build -t finsight .

# Run with Ollama support
docker run -p 8000:8000 \
  -e FINSIGHT_LLM_PROVIDER=ollama \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  finsight

# Run with OpenAI
docker run -p 8000:8000 \
  -e FINSIGHT_LLM_PROVIDER=openai \
  -e OPENAI_API_KEY=your-key-here \
  finsight
```

**Docker Compose (Full Stack):**
```yaml
version: '3.8'
services:
  finsight-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FINSIGHT_LLM_PROVIDER=ollama
      - OLLAMA_BASE_URL=http://ollama:11434
      - FINSIGHT_CACHE_ENABLED=true
    depends_on:
      - ollama
      - redis
  
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
  
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    
volumes:
  ollama_data:
```

## 🔧 Detailed Deployment Configuration

### Environment Variables

**Core Configuration:**
```bash
# LLM Provider Selection
FINSIGHT_LLM_PROVIDER=ollama|openai|anthropic

# Ollama Configuration (Local Development)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# OpenAI Configuration (Production)
OPENAI_API_KEY=sk-...
FINSIGHT_OPENAI_MODEL=gpt-4o-mini

# Anthropic Configuration (Alternative)
ANTHROPIC_API_KEY=sk-ant-...
FINSIGHT_ANTHROPIC_MODEL=claude-3-haiku-20240307

# System Configuration
FINSIGHT_DEBUG=false
FINSIGHT_CACHE_ENABLED=true
FINSIGHT_CACHE_HOURS=24
FINSIGHT_MAX_RETRIES=3
FINSIGHT_REQUEST_TIMEOUT=30

# AWS Configuration (Lambda deployment)
AWS_REGION=us-east-1
S3_BUCKET=finsight-cache-bucket
LAMBDA_TIMEOUT=300
LAMBDA_MEMORY=1024
```

### AWS Lambda Deployment Details

**CloudFormation Template:** `deployment/aws/template-ollama-aware.yaml`

Key components deployed:
- **API Gateway:** RESTful API endpoints with custom domain support
- **Lambda Functions:** Specialized functions for different tasks
- **S3 Bucket:** Caching and temporary storage
- **CloudWatch:** Comprehensive logging and monitoring
- **IAM Roles:** Secure service permissions

**Deployment Script Features:**
```bash
# Full deployment with all options
./deploy.sh deploy \
    --stack-name my-finsight \
    --stage production \
    --region us-west-2 \
    --llm-provider openai \
    --openai-key $OPENAI_API_KEY \
    --debug false \
    --cache-hours 48

# Update existing deployment
./deploy.sh update --stage production

# Clean deployment (rebuild everything)
./deploy.sh clean-deploy --stage production

# Destroy deployment
./deploy.sh destroy --stage production
```

## 🏗️ AWS Infrastructure Architecture

### Lambda Functions
```
1. RootFunction (API Router)
   - Memory: 1024MB
   - Timeout: 300s
   - Role: Request routing and coordination

2. EnhancedFactCheckFunction (Core Logic)
   - Memory: 1024MB  
   - Timeout: 300s
   - Role: Main fact-checking pipeline

3. ContextEnrichmentFunction (LLM Enhancement)
   - Memory: 512MB
   - Timeout: 180s
   - Role: Response quality improvement

4. ComplianceCheckFunction (Regulatory)
   - Memory: 512MB
   - Timeout: 120s
   - Role: Financial compliance validation

5. HealthCheckFunction (Monitoring)
   - Memory: 256MB
   - Timeout: 30s
   - Role: System health checks
```

### API Endpoints
```
POST /api/v1/fact-check
GET  /api/v1/health
GET  /api/v1/providers
POST /api/v1/batch-check
GET  /api/v1/metrics
```

### Monitoring & Observability
```bash
# CloudWatch Metrics
- Duration: Function execution time
- Invocations: Request count
- Errors: Error rate
- Throttles: Rate limiting events

# Custom Metrics  
- ClaimProcessingSuccess
- LLMProviderSwitches
- TickerResolutionAccuracy
- CacheHitRate

# Alarms
- High error rate (>5%)
- Slow response (>10s)
- Memory usage (>90%)
- Concurrent executions (>80% limit)
```

## 🔒 Security Deployment

### API Security
```bash
# API Key Authentication
X-API-Key: your-api-key-here

# Rate Limiting
- 100 requests/minute per key
- Burst capacity: 200 requests

# Input Validation
- Request size limits: 1MB
- Content type validation
- SQL injection protection
```

### AWS Security Best Practices
```yaml
# IAM Role Permissions (Least Privilege)
LambdaExecutionRole:
  - logs:CreateLogGroup
  - logs:CreateLogStream  
  - logs:PutLogEvents
  - s3:GetObject
  - s3:PutObject
  - ssm:GetParameter (for secrets)

# VPC Configuration (Optional)
VpcConfig:
  SecurityGroupIds:
    - sg-secure-lambda
  SubnetIds:
    - subnet-private-1
    - subnet-private-2
```

## 📊 Performance Optimization

### Caching Strategy
```python
# Multi-level caching
1. Lambda Memory Cache (warm instances)
2. S3 Bucket Cache (persistent)
3. External API Rate Limiting

# Cache Configuration
FINSIGHT_CACHE_ENABLED=true
FINSIGHT_CACHE_HOURS=24
S3_CACHE_PREFIX=finsight-cache/
```

### Cold Start Optimization
```python
# Techniques applied:
- Minimal import optimization
- Connection pooling
- Warm-up functions
- Provisioned concurrency (optional)

# Monitoring cold starts
- Average cold start: <2s
- Warm execution: <200ms
- Cache hit improvement: 80%+
```

## 🧪 Testing Deployment

### Local Testing
```bash
# Test CLI interface
python src/main.py --interactive

# Test API server
python finai_quality_api.py
curl -X POST "http://localhost:8000/api/v1/fact-check" \
  -H "Content-Type: application/json" \
  -d '{"text": "Apple market cap is $3 trillion"}'

# Run comprehensive tests
python tests/comprehensive_demo.py
```

### AWS Testing
```bash
# Test deployment
aws lambda invoke \
  --function-name finsight-api-prod-RootFunction \
  --payload '{"body": "{\"text\": \"TSLA is $200 per share\"}"}' \
  response.json

# Load testing (optional)
artillery quick --count 10 --num 100 \
  https://your-api-gateway-url.amazonaws.com/api/v1/fact-check
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy FinSight
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
          
      - name: Install dependencies
        run: pip install -r requirements.txt
        
      - name: Run tests
        run: python -m pytest tests/
        
      - name: Deploy to AWS
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          cd deployment/aws
          ./deploy.sh deploy --stage prod --llm-provider openai
```

## 🚨 Troubleshooting

### Common Issues
```bash
# Ollama connection issues
Error: "Cannot connect to Ollama"
Solution: Ensure Ollama is running on correct port
Check: curl http://localhost:11434/api/tags

# AWS deployment failures  
Error: "Stack creation failed"
Solution: Check CloudFormation events in AWS console
Debug: Enable CloudWatch logs for Lambda functions

# LLM provider errors
Error: "API key invalid"
Solution: Verify API keys in environment variables
Test: Direct API call to provider

# Memory/timeout issues
Error: "Task timed out after 300.00 seconds"
Solution: Increase Lambda timeout or optimize code
Monitor: CloudWatch metrics for resource usage
```

### Health Check Endpoints
```bash
# Local health check
curl http://localhost:8000/health

# AWS health check  
curl https://your-api-url.amazonaws.com/api/v1/health

# Expected response:
{
  "status": "healthy",
  "version": "2.1.0",
  "llm_provider": "openai",
  "cache_enabled": true,
  "timestamp": "2025-05-24T10:30:00Z"
}
```

## 🔗 Related Documentation

- [[FinSight - Application Overview]] - System overview and capabilities
- [[FinSight - Technical Architecture]] - Detailed technical design
- [[FinSight - LLM Integration]] - LLM provider configuration
- [[AWS Cost Optimization]] - Cost management strategies
- [[Performance Benchmarks]] - Performance analysis and tuning

## 📋 Deployment Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] API keys secured and tested
- [ ] AWS credentials configured
- [ ] Dependencies installed
- [ ] Tests passing locally

### Deployment
- [ ] Choose appropriate deployment method
- [ ] Configure staging environment first
- [ ] Deploy with monitoring enabled
- [ ] Verify health check endpoints
- [ ] Test core functionality

### Post-deployment
- [ ] Monitor CloudWatch metrics
- [ ] Verify cache performance
- [ ] Test failover scenarios
- [ ] Document any customizations
- [ ] Schedule regular health checks

---

*This deployment guide provides comprehensive instructions for all FinSight deployment scenarios. For troubleshooting specific issues, consult the AWS CloudWatch logs and the troubleshooting section above.*
