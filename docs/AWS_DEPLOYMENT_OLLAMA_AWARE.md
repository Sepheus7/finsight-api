# 🚀 FinSight AWS Deployment Guide - Ollama-Aware Configuration

## 🎯 AWS Deployment Overview

FinSight's AWS deployment is optimized for serverless environments where Ollama cannot run locally. The system gracefully falls back to cloud-based LLM providers (OpenAI/Anthropic) or regex-based extraction.

## ⚠️ **Important: Ollama Limitations in AWS Lambda**

**Ollama is NOT supported in AWS Lambda** due to:
- Container size limitations (10GB max)
- Memory constraints for model loading
- Cold start performance issues
- Network restrictions for model downloads

**Recommended LLM Strategy for AWS:**
1. **Primary**: OpenAI GPT-4o-mini (cost-efficient, fast)
2. **Alternative**: Anthropic Claude 3 Haiku (high quality)
3. **Fallback**: Regex-based claim extraction (always available)

---

## 🛠️ **Prerequisites**

### Install Required Tools

```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Install SAM CLI
brew install aws-sam-cli

# Install jq for JSON processing (optional)
brew install jq

# Verify installations
aws --version
sam --version
```

### Configure AWS Credentials

```bash
# Configure AWS credentials
aws configure

# Or use AWS SSO
aws configure sso

# Verify access
aws sts get-caller-identity
```

---

## 🔑 **LLM Configuration**

### Option 1: OpenAI (Recommended)

```bash
# Get API key from https://platform.openai.com/
export OPENAI_API_KEY="sk-your-openai-api-key-here"

# Set provider
export FINSIGHT_LLM_PROVIDER="openai"
```

### Option 2: Anthropic Claude

```bash
# Get API key from https://console.anthropic.com/
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key-here"

# Set provider  
export FINSIGHT_LLM_PROVIDER="anthropic"
```

### Option 3: Regex Only (No LLM costs)

```bash
# No API keys required
export FINSIGHT_LLM_PROVIDER="regex"
```

---

## 🚀 **Deployment Commands**

### Quick Start Deployments

```bash
# Navigate to deployment directory
cd deployment/aws

# Development deployment with OpenAI
./deploy.sh --stage dev --llm-provider openai --openai-key "$OPENAI_API_KEY"

# Production deployment with Anthropic
./deploy.sh --stage prod --llm-provider anthropic --anthropic-key "$ANTHROPIC_API_KEY"

# Cost-free deployment (regex only)
./deploy.sh --stage dev --llm-provider regex

# Debug-enabled deployment
./deploy.sh --stage dev --llm-provider openai --debug --openai-key "$OPENAI_API_KEY"
```

### Advanced Deployment Options

```bash
# Custom region deployment
./deploy.sh --stage prod --region us-west-2 --llm-provider anthropic

# Custom models
./deploy.sh --stage prod \
  --llm-provider openai \
  --openai-model gpt-4o \
  --openai-key "$OPENAI_API_KEY"

# Multiple environment deployment
./deploy.sh --stage staging --llm-provider anthropic --anthropic-model claude-3-sonnet-20240229
```

### Manual SAM Deployment

```bash
# Build application
sam build --template template-ollama-aware.yaml --use-container

# Deploy with guided prompts
sam deploy --guided --template-file template-ollama-aware.yaml

# Deploy with parameters
sam deploy \
  --template-file template-ollama-aware.yaml \
  --stack-name finsight-api-dev \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Stage=dev \
    LLMProvider=openai \
    OpenAIApiKey="$OPENAI_API_KEY" \
    DebugMode=true
```

---

## 📋 **CloudFormation Template Features**

### New Ollama-Aware Template (`template-ollama-aware.yaml`)

**Key Improvements:**
- ✅ LLM provider selection (openai/anthropic/regex)
- ✅ Secure API key management with NoEcho parameters
- ✅ Conditional deployment based on stage (dev/staging/prod)
- ✅ Enhanced Lambda memory and timeout for LLM processing
- ✅ CloudWatch monitoring and alerting
- ✅ Cost optimization features
- ✅ Performance dashboards

**Parameters:**
```yaml
LLMProvider: [openai, anthropic, regex]
OpenAIApiKey: Secure NoEcho parameter
AnthropicApiKey: Secure NoEcho parameter
OpenAIModel: Default "gpt-4o-mini"
AnthropicModel: Default "claude-3-haiku-20240307"
Stage: [dev, staging, prod]
DebugMode: [true, false]
```

**Enhanced Lambda Configuration:**
- Memory: 1024-1536MB (increased for LLM processing)
- Timeout: 60-120s (extended for API calls)
- Environment variables for LLM configuration
- Graceful fallback handling

---

## 🧪 **Testing Your Deployment**

### Get Deployment Information

```bash
# Get API URL
API_URL=$(aws cloudformation describe-stacks \
  --stack-name finsight-api \
  --query 'Stacks[0].Outputs[?OutputKey==`FinancialAIApiUrl`].OutputValue' \
  --output text)

echo "API URL: $API_URL"
```

### Test Health Endpoint

```bash
# Simple health check
curl "$API_URL/health"

# Formatted response
curl -s "$API_URL/health" | jq .
```

### Test Fact-Checking with LLM

```bash
# Test basic fact-checking
curl -X POST "$API_URL/fact-check" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Apple stock reached $200 per share today",
    "use_llm": true
  }' | jq .

# Test with complex financial claim
curl -X POST "$API_URL/fact-check" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Tesla Q3 2024 revenue was $25.18 billion, up 8% year-over-year",
    "use_llm": true
  }' | jq .
```

### Test Enhancement Endpoint

```bash
# Test AI response enhancement
curl -X POST "$API_URL/enhance" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Invest in TSLA for guaranteed 50% returns this quarter"
  }' | jq .
```

---

## 💰 **Cost Optimization**

### Recommended Configurations by Stage

| Stage | LLM Provider | Model | Lambda Memory | Est. Cost/Month |
|-------|-------------|-------|---------------|-----------------|
| **Dev** | regex | N/A | 512MB | $5-10 |
| **Dev** | openai | gpt-4o-mini | 1024MB | $15-25 |
| **Staging** | openai | gpt-4o-mini | 1024MB | $25-50 |
| **Staging** | anthropic | claude-3-haiku | 1024MB | $30-60 |
| **Production** | anthropic | claude-3-haiku | 1536MB | $50-150 |
| **Production** | openai | gpt-4o | 1536MB | $100-300 |

### Cost Control Features

**Included in Template:**
- ✅ DynamoDB on-demand billing
- ✅ S3 lifecycle policies (auto-delete old cache)
- ✅ CloudWatch log retention limits
- ✅ Lambda memory optimization
- ✅ Production vs development resource scaling

**Manual Cost Controls:**
```bash
# Set up billing alerts
aws budgets create-budget --account-id YOUR_ACCOUNT_ID \
  --budget file://budget-config.json

# Monitor LLM API usage
aws logs filter-log-events \
  --log-group-name '/aws/lambda/your-function' \
  --filter-pattern 'LLM API call'
```

---

## 📊 **Monitoring & Alerts**

### CloudWatch Features (Production Only)

**Automatic Monitoring:**
- Lambda function errors and duration
- API Gateway 4xx/5xx errors  
- DynamoDB throttling
- S3 cache hit/miss rates

**Custom Alarms:**
- Fact-check function error rate > 5%
- Average response time > 10 seconds
- Daily LLM API costs > threshold

### View Metrics

```bash
# Get CloudWatch dashboard URL
aws cloudformation describe-stacks \
  --stack-name finsight-api \
  --query 'Stacks[0].Outputs[?OutputKey==`DashboardUrl`].OutputValue' \
  --output text

# View recent Lambda logs
aws logs tail /aws/lambda/finsight-api-EnhancedFactCheckFunction --follow
```

---

## 🔧 **Troubleshooting**

### Common Issues

**1. LLM API Key Issues**
```bash
# Check if API key is set in Lambda
aws lambda get-function-configuration \
  --function-name finsight-api-EnhancedFactCheckFunction \
  --query 'Environment.Variables'
```

**2. Cold Start Performance**
```bash
# Check Lambda duration metrics
aws logs filter-log-events \
  --log-group-name '/aws/lambda/finsight-api-EnhancedFactCheckFunction' \
  --filter-pattern 'REPORT RequestId'
```

**3. Memory Issues**
```bash
# Monitor memory usage
aws logs filter-log-events \
  --log-group-name '/aws/lambda/finsight-api-EnhancedFactCheckFunction' \
  --filter-pattern 'Max Memory Used'
```

### Debugging Commands

```bash
# Enable debug mode
./deploy.sh --stage dev --llm-provider openai --debug

# Check function logs
sam logs -n EnhancedFactCheckFunction --stack-name finsight-api --tail

# Test locally
sam local start-api --template template-ollama-aware.yaml
```

---

## 🔄 **CI/CD Integration**

### GitHub Actions Example

```yaml
name: Deploy FinSight to AWS
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
      
      - name: Deploy to AWS
        run: |
          cd deployment/aws
          ./deploy.sh --stage prod \
            --llm-provider openai \
            --openai-key "${{ secrets.OPENAI_API_KEY }}"
```

---

## 📚 **Next Steps**

After successful deployment:

1. **📊 Monitor Performance**: Check CloudWatch dashboards
2. **🔐 Set Up Authentication**: Add API keys for production use
3. **📈 Scale Resources**: Adjust Lambda memory based on usage
4. **💰 Monitor Costs**: Set up billing alerts and cost controls
5. **🚀 Optimize**: Fine-tune LLM models based on accuracy vs cost

---

**Your FinSight API is now deployed with intelligent LLM fallback strategies! 🎉**

The system will automatically handle:
- ✅ OpenAI/Anthropic API failures → Regex fallback
- ✅ Cost optimization through model selection
- ✅ Performance monitoring and alerting
- ✅ Secure API key management
- ✅ Multi-environment deployment support
