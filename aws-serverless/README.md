# AWS Serverless Deployment Guide
# Financial AI Quality Enhancement API

## 🏗️ Architecture Overview

This serverless implementation splits the monolithic FastAPI application into microservices running on AWS Lambda:

```
┌─────────────────────────────────────────────────────────────────┐
│                          API Gateway                             │
├─────────────────────────────────────────────────────────────────┤
│  /enhance (POST)  │  /health (GET)  │  / (GET)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │                         │                         │
┌───▼───┐               ┌────▼────┐               ┌────▼────┐
│Enhance│               │ Health  │               │  Root   │
│Lambda │               │ Lambda  │               │ Lambda  │
└───┬───┘               └─────────┘               └─────────┘
    │
    ├─────────────────────────────────────────────────────┐
    │                         │                           │
┌───▼──────┐         ┌───────▼──────┐         ┌─────────▼─────────┐
│Fact Check│         │   Context    │         │   Compliance     │
│ Lambda   │         │ Enrichment   │         │   Check Lambda   │
│          │         │   Lambda     │         │                  │
└──────────┘         └──────────────┘         └───────────────────┘
    │                         │                           │
┌───▼───┐               ┌────▼────┐               ┌───────▼───────┐
│  S3   │               │   S3    │               │   DynamoDB    │
│ Cache │               │  Cache  │               │ Compliance    │
└───────┘               └─────────┘               │    Rules      │
                                                  └───────────────┘
                    ┌─────────────────────────────────┐
                    │          DynamoDB               │
                    │     Enhancement History         │
                    └─────────────────────────────────┘
```

## 🚀 Deployment Options

### Option 1: AWS SAM (Recommended)

SAM (Serverless Application Model) provides a simple way to deploy serverless applications.

#### Prerequisites
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Install SAM CLI
brew install aws-sam-cli

# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# Configure AWS credentials
aws configure
```

#### Deployment Steps
```bash
# Navigate to the serverless directory
cd aws-serverless

# Deploy the application
./deploy.sh

# Or deploy with custom parameters
STACK_NAME=my-finai-api REGION=us-west-2 STAGE=prod ./deploy.sh
```

#### Deployment Commands
```bash
# Full deployment
./deploy.sh deploy

# Build only
./deploy.sh build

# Validate template
./deploy.sh validate

# Show outputs
./deploy.sh outputs

# View logs
./deploy.sh logs

# Clean up
./deploy.sh cleanup
```

### Option 2: AWS CDK

CDK provides more flexibility and programmatic infrastructure definition.

#### Prerequisites
```bash
# Install Node.js and npm
brew install node

# Install AWS CDK
npm install -g aws-cdk

# Install Python dependencies
cd cdk
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Deployment Steps
```bash
# Navigate to CDK directory
cd aws-serverless/cdk

# Deploy the application
./deploy-cdk.sh

# Or use specific commands
./deploy-cdk.sh bootstrap  # First time only
./deploy-cdk.sh synth      # Generate CloudFormation
./deploy-cdk.sh deploy     # Deploy to AWS
./deploy-cdk.sh destroy    # Clean up
```

## 📊 Resource Breakdown

### Lambda Functions
- **enhance_handler**: Main orchestration (512MB, 30s timeout)
- **fact_check_handler**: Financial claim verification (512MB, 60s timeout)
- **context_enrichment_handler**: Market context addition (512MB, 30s timeout)
- **compliance_handler**: Regulatory compliance checking (512MB, 30s timeout)
- **health_handler**: Health check endpoint (512MB, 30s timeout)
- **root_handler**: API information endpoint (512MB, 30s timeout)

### Storage
- **DynamoDB**: Enhancement history and compliance rules
- **S3**: Market data caching (7-day lifecycle)

### API Gateway
- REST API with CORS enabled
- Stage-based deployment (dev/staging/prod)
- CloudWatch logging and tracing
- Rate limiting and throttling

## 🔧 Configuration

### Environment Variables
```bash
# Required for all Lambda functions
DYNAMODB_TABLE=finai-quality-api-enhancement-history
S3_BUCKET=finai-quality-api-data-cache-{account-id}

# Additional for specific functions
FACT_CHECK_FUNCTION=finai-quality-api-FactCheckFunction
CONTEXT_ENRICHMENT_FUNCTION=finai-quality-api-ContextEnrichmentFunction
COMPLIANCE_CHECK_FUNCTION=finai-quality-api-ComplianceCheckFunction
COMPLIANCE_RULES_TABLE=finai-quality-api-compliance-rules
```

### DynamoDB Tables

#### Enhancement History Table
```
Partition Key: id (String) - Request ID
Sort Key: timestamp (String) - ISO timestamp
Attributes:
- original_content_length (Number)
- enhanced_content_length (Number)
- fact_checks_count (Number)
- context_additions_count (Number)
- compliance_flags_count (Number)
- quality_score (Number)
- processing_time_ms (Number)
- enrichment_level (String)
```

#### Compliance Rules Table
```
Partition Key: rule_id (String)
Attributes:
- rule_name (String)
- severity (String) - HIGH/MEDIUM/LOW
- description (String)
- created_at (String)
```

## 💰 Cost Estimation

### Monthly Cost Breakdown (1M requests/month)

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 1M requests, 2GB-seconds avg | $3.20 |
| API Gateway | 1M requests | $3.50 |
| DynamoDB | 10GB storage, 1M reads/writes | $2.50 |
| S3 | 5GB storage, 100K requests | $0.25 |
| CloudWatch Logs | 10GB logs | $5.00 |
| **Total** | | **$14.45** |

### Cost Optimization Tips
1. Use DynamoDB On-Demand for variable workloads
2. Set S3 lifecycle policies for cache cleanup
3. Configure appropriate CloudWatch log retention
4. Monitor Lambda cold starts and optimize memory allocation

## 🔒 Security Features

### IAM Permissions
- Least privilege access for each Lambda function
- Function-specific DynamoDB and S3 permissions
- No cross-function access except for orchestration

### Data Protection
- All data encrypted in transit and at rest
- S3 bucket with private access only
- DynamoDB point-in-time recovery enabled

### API Security
- CORS configuration for web clients
- Optional API key authentication
- CloudTrail logging for audit trail

## 📈 Monitoring & Observability

### CloudWatch Metrics
- Lambda function duration and error rates
- API Gateway request count and latency
- DynamoDB read/write capacity utilization
- Custom business metrics

### Logging
- Structured logging in all Lambda functions
- Centralized log aggregation
- 30-day log retention by default

### Tracing
- AWS X-Ray integration enabled
- End-to-end request tracing
- Performance bottleneck identification

## 🧪 Testing the Deployment

### Health Check
```bash
curl https://your-api-url/health
```

### API Information
```bash
curl https://your-api-url/
```

### Enhancement Request
```bash
curl -X POST https://your-api-url/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "ai_response": {
      "content": "AAPL stock is trading at $150 and offers guaranteed 20% returns."
    },
    "fact_check": true,
    "add_context": true
  }'
```

## 🐛 Troubleshooting

### Common Issues

#### Lambda Cold Starts
- **Symptom**: First request takes longer
- **Solution**: Implement provisioned concurrency for critical functions

#### DynamoDB Throttling
- **Symptom**: 400 errors with ProvisionedThroughputExceededException
- **Solution**: Switch to On-Demand billing or increase capacity

#### S3 Access Denied
- **Symptom**: 403 errors when accessing cached data
- **Solution**: Check IAM permissions and bucket policies

#### API Gateway 504 Timeout
- **Symptom**: Gateway timeout errors
- **Solution**: Increase Lambda timeout or optimize function performance

### Debugging Commands
```bash
# View Lambda logs
aws logs tail /aws/lambda/finai-quality-api-EnhanceResponseFunction --follow

# Check DynamoDB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=finai-quality-api-enhancement-history \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Sum

# Test individual Lambda function
aws lambda invoke \
  --function-name finai-quality-api-HealthCheckFunction \
  --payload '{}' \
  response.json
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy Serverless API
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: aws-actions/setup-sam@v2
      - uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - run: sam build
      - run: sam deploy --no-confirm-changeset --no-fail-on-empty-changeset
```

## 📚 Additional Resources

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)

## 🆘 Support

For issues with the serverless deployment:
1. Check CloudWatch logs for detailed error messages
2. Verify IAM permissions for all resources
3. Ensure all prerequisites are properly installed
4. Review the troubleshooting section above

The serverless architecture provides automatic scaling, high availability, and cost optimization while maintaining the same functionality as the monolithic version.
