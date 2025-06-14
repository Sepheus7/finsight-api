# FinSight Deployment Guide

## Overview

This guide covers the deployment of FinSight across different environments, from local development to production AWS deployment.

## Prerequisites

- Python 3.8+
- AWS CLI configured
- AWS SAM CLI installed
- Docker (for containerized deployment)

## Local Development

### 1. Setup Environment

```bash
# Clone repository
git clone https://github.com/your-username/FinSight.git
cd FinSight

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.template` to `.env` and configure:

```bash
# Financial Data APIs
ALPHA_VANTAGE_API_KEY=your_key_here  # Optional: Enhanced data
FRED_API_KEY=your_key_here           # Optional: Economic indicators

# Performance Tuning
CACHE_TTL_STOCK_DATA=3600           # 1 hour cache
MAX_CONCURRENT_REQUESTS=10          # Concurrent limit
```

### 3. Start Development Server

```bash
python api_server.py
```

The server will be available at `http://localhost:8000`

## AWS Deployment

### 1. AWS Lambda Deployment

```bash
cd deployment/aws

# Deploy to dev environment
./deploy.sh --stage dev

# Deploy to production
./deploy.sh --stage prod
```

### 2. Configuration Options

The deployment script supports several options:

```bash
./deploy.sh --stage dev --region us-east-1 --stack-name finsight
```

Options:
- `--stage`: Deployment stage (dev, staging, prod)
- `--region`: AWS region
- `--stack-name`: CloudFormation stack name
- `--llm-provider`: LLM provider (bedrock, openai, anthropic, regex)

### 3. Environment-Specific Configuration

#### Development
- Uses local file caching
- Debug mode enabled
- No rate limiting

#### Production
- DynamoDB caching
- CloudWatch monitoring
- Rate limiting enabled
- API Gateway caching

## Docker Deployment

### 1. Build Image

```bash
docker build -t finsight .
```

### 2. Run Container

```bash
docker run -p 8000:8000 \
  -e ALPHA_VANTAGE_API_KEY=your_key \
  -e FRED_API_KEY=your_key \
  finsight
```

## Monitoring & Maintenance

### 1. Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check system status
curl http://localhost:8000/status
```

### 2. AWS CloudWatch

- View logs in CloudWatch Logs
- Monitor metrics in CloudWatch Metrics
- Set up alarms for error rates

### 3. Performance Monitoring

- Cache hit rates
- Response times
- Error rates
- API usage

## Troubleshooting

### Common Issues

1. **API Connection Issues**
   - Check API keys
   - Verify network connectivity
   - Check rate limits

2. **Performance Issues**
   - Monitor cache hit rates
   - Check concurrent request limits
   - Verify data source availability

3. **Deployment Failures**
   - Check AWS credentials
   - Verify IAM permissions
   - Check CloudFormation logs

## Security Considerations

1. **API Keys**
   - Store securely in AWS Secrets Manager
   - Rotate regularly
   - Use environment-specific keys

2. **Access Control**
   - Use IAM roles
   - Implement API Gateway authorizers
   - Enable CORS appropriately

3. **Data Protection**
   - Encrypt sensitive data
   - Use HTTPS
   - Implement rate limiting

## Scaling Considerations

1. **Vertical Scaling**
   - Increase Lambda memory
   - Adjust concurrent execution limits
   - Optimize cache settings

2. **Horizontal Scaling**
   - Use API Gateway caching
   - Implement DynamoDB auto-scaling
   - Use CloudFront for static content

## Backup & Recovery

1. **Data Backup**
   - Regular DynamoDB backups
   - S3 versioning
   - CloudWatch log retention

2. **Disaster Recovery**
   - Multi-region deployment
   - Cross-region replication
   - Regular recovery testing
