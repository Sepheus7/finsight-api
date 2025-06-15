# FinSight Deployment Guide

This directory contains everything needed to deploy FinSight to AWS and other cloud platforms.

## 🚀 Quick Deploy to AWS

### Prerequisites
- AWS CLI configured
- Docker installed
- Python 3.9+ installed
- Valid AWS credentials with appropriate permissions

### 1. Environment Setup
```bash
# Copy and configure environment
cp deployment/config/production.env.template .env.production
# Edit .env.production with your values

# Install dependencies
pip install -r requirements.txt
```

### 2. AWS Infrastructure
```bash
# Deploy infrastructure using CloudFormation
aws cloudformation deploy \
  --template-file deployment/aws/templates/infrastructure.yaml \
  --stack-name finsight-infrastructure \
  --capabilities CAPABILITY_IAM

# Deploy application
aws cloudformation deploy \
  --template-file deployment/aws/templates/application.yaml \
  --stack-name finsight-app \
  --capabilities CAPABILITY_IAM
```

### 3. Docker Deployment
```bash
# Build and push Docker image
docker build -t finsight:latest .
docker tag finsight:latest your-account.dkr.ecr.us-east-1.amazonaws.com/finsight:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/finsight:latest

# Deploy to ECS
aws ecs update-service \
  --cluster finsight-cluster \
  --service finsight-service \
  --force-new-deployment
```

## 📁 Directory Structure

```
deployment/
├── aws/                    # AWS-specific deployment files
│   ├── templates/          # CloudFormation templates
│   └── tests/             # Infrastructure tests
├── docker/                # Docker configuration
│   ├── Dockerfile         # Production Docker image
│   └── docker-compose.yml # Local development
├── config/                # Configuration templates
│   └── production.env.template
└── scripts/               # Deployment scripts
```

## 🔧 Configuration

### Environment Variables
See `config/production.env.template` for all available configuration options.

### Required AWS Services
- **EC2/ECS**: Application hosting
- **RDS**: Database (optional)
- **ElastiCache**: Redis caching (optional)
- **CloudWatch**: Logging and monitoring
- **Bedrock**: AI/ML services
- **API Gateway**: API management (optional)

### Required API Keys
- **AWS Bedrock**: For AI capabilities
- **FRED API**: For economic data
- **Alpha Vantage**: For financial data (backup)

## 🏗️ Architecture Options

### Option 1: ECS Fargate (Recommended)
- Serverless container hosting
- Auto-scaling
- Managed infrastructure
- Cost-effective for variable workloads

### Option 2: EC2 with Auto Scaling
- More control over infrastructure
- Better for consistent high-traffic
- Custom instance types

### Option 3: Lambda + API Gateway
- Serverless functions
- Pay-per-request
- Good for low-traffic or development

## 🔍 Monitoring & Observability

### CloudWatch Integration
- Application logs
- Performance metrics
- Custom dashboards
- Alerts and notifications

### Health Checks
- `/health` endpoint for load balancer
- `/status` endpoint for detailed system status
- Custom health check scripts

## 🔒 Security

### Network Security
- VPC with private subnets
- Security groups with minimal access
- NAT Gateway for outbound traffic
- Application Load Balancer with SSL

### Application Security
- Environment variable encryption
- Secrets Manager integration
- IAM roles with least privilege
- API rate limiting

## 📊 Performance

### Scaling Configuration
- Auto Scaling Groups
- Target tracking policies
- CloudWatch metrics-based scaling
- Load balancer health checks

### Optimization
- Connection pooling
- Response caching
- CDN for static assets
- Database query optimization

## 🧪 Testing

### Pre-deployment Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Test specific components
python tests/validate_system.py
python tests/test_integration.py

# Load testing
python tests/test_cost_optimization.py
```

### Post-deployment Validation
```bash
# Health check
curl https://your-domain.com/health

# API functionality
curl -X POST https://your-domain.com/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AAPL stock price?"}'

# MCP server test
python integrations/mcp/mcp_server_standalone.py test
```

## 🚨 Troubleshooting

### Common Issues
1. **Bedrock Access**: Ensure proper IAM permissions
2. **API Keys**: Verify all external API keys are valid
3. **Network**: Check security group rules
4. **Memory**: Monitor container memory usage
5. **Logs**: Check CloudWatch logs for errors

### Debug Commands
```bash
# Check container logs
aws logs tail /aws/ecs/finsight --follow

# Check service status
aws ecs describe-services --cluster finsight-cluster --services finsight-service

# Test connectivity
curl -v https://your-domain.com/health
```

## 📈 Cost Optimization

### Recommendations
- Use Spot Instances for development
- Enable auto-scaling to handle traffic spikes
- Monitor CloudWatch costs
- Use reserved instances for production
- Implement caching to reduce API calls

### Cost Monitoring
- Set up billing alerts
- Use AWS Cost Explorer
- Monitor per-service costs
- Regular cost reviews

## 🔄 CI/CD Pipeline

### GitHub Actions (Recommended)
```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to AWS
        run: ./deployment/scripts/deploy.sh
```

### Manual Deployment
```bash
# Build and deploy
./deployment/scripts/build.sh
./deployment/scripts/deploy.sh production
```

## 📞 Support

For deployment issues:
1. Check the troubleshooting section
2. Review CloudWatch logs
3. Validate configuration
4. Test individual components
5. Contact the development team

## 🔗 Related Documentation

- [API Documentation](../docs/api/)
- [Development Guide](../docs/development/)
- [MCP Integration](../integrations/mcp/)
- [Testing Guide](../tests/) 