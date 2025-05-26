# FinSight Cost Optimization Guide

## Overview

FinSight now includes comprehensive cost optimization features that automatically:
- Detect your environment (local development vs AWS deployment)
- Choose the most cost-effective LLM provider based on context
- Provide fallback to cheaper models when primary models fail
- Estimate costs for different model options

## Key Features

### 1. Environment-Aware Provider Selection

The system automatically detects your environment and selects the optimal provider:

- **Local Development**: Prefers Ollama (free local inference)
- **AWS Lambda**: Uses Bedrock with cost-optimized models
- **Cloud Development**: Falls back to OpenAI/Anthropic API keys
- **Fallback**: Uses regex-based extraction when no LLM is available

### 2. Bedrock Fallback Models

When using AWS Bedrock, the system now supports automatic fallback to cheaper models:

- **Primary Model**: `anthropic.claude-3-haiku-20240307-v1:0` ($0.25/$1.25 per 1M tokens)
- **Fallback Model**: `amazon.titan-text-express-v1` ($0.20/$0.60 per 1M tokens)

### 3. Cost Estimation

Built-in cost estimation for different models helps you make informed decisions:

```python
from src.utils.bedrock_client import get_bedrock_client

client = get_bedrock_client()
cost_info = client.get_cost_estimate()
print(f"Input cost: ${cost_info['input']} per {cost_info['per']}")
print(f"Output cost: ${cost_info['output']} per {cost_info['per']}")
```

## Configuration

### Environment Variables

Configure cost optimization through environment variables:

```bash
# LLM Provider Configuration
export FINSIGHT_LLM_PROVIDER=bedrock              # Primary provider
export FINSIGHT_BEDROCK_MODEL=anthropic.claude-3-haiku-20240307-v1:0
export FINSIGHT_BEDROCK_FALLBACK_MODEL=amazon.titan-text-express-v1
export FINSIGHT_BEDROCK_REGION=us-east-1

# Alternative Providers (for fallback)
export OPENAI_API_KEY=your-openai-key
export ANTHROPIC_API_KEY=your-anthropic-key

# Model Parameters
export FINSIGHT_TEMPERATURE=0.1
export FINSIGHT_MAX_TOKENS=1000
```

### Programmatic Configuration

```python
from src.config import FinSightConfig, LLMConfig

# Load configuration with environment detection
config = FinSightConfig.from_env()
print(f"Auto-detected provider: {config.llm.provider}")

# Manual configuration
llm_config = LLMConfig(
    provider="bedrock",
    bedrock_model="anthropic.claude-3-haiku-20240307-v1:0",
    bedrock_fallback_model="amazon.titan-text-express-v1",
    temperature=0.1
)
```

## Usage Examples

### 1. Automatic Provider Detection

```python
from src.utils.llm_claim_extractor import LLMClaimExtractor

# Automatically selects best available provider
extractor = LLMClaimExtractor(provider="auto")
print(f"Using provider: {extractor.provider}")

# Extract claims with cost optimization
claims = extractor.extract_claims("Apple reported $95B revenue in Q4 2024")
```

### 2. Bedrock with Fallback

```python
from src.utils.bedrock_client import get_bedrock_client

# Client with automatic fallback to cheaper model
client = get_bedrock_client(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    fallback_model_id="amazon.titan-text-express-v1"
)

# If primary model fails, automatically tries fallback
response = client.generate_text("Analyze this financial statement...")

# Check if fallback was used
if client.using_fallback:
    print("Using cost-optimized fallback model")
```

### 3. Cost Monitoring

```python
# Monitor costs across different models
from src.utils.bedrock_client import BedrockLLMClient

models = [
    "anthropic.claude-3-haiku-20240307-v1:0",
    "anthropic.claude-3-sonnet-20240229-v1:0", 
    "amazon.titan-text-express-v1"
]

for model in models:
    client = BedrockLLMClient.__new__(BedrockLLMClient)
    client.model_id = model
    cost = client.get_cost_estimate()
    print(f"{model}: ${cost['input']}/{cost['output']} per {cost['per']}")
```

## Cost Comparison

| Model | Input Cost | Output Cost | Best For |
|-------|------------|-------------|----------|
| Claude 3 Haiku | $0.25/1M | $1.25/1M | Balanced performance/cost |
| Claude 3 Sonnet | $3.00/1M | $15.00/1M | High-quality analysis |
| Titan Express | $0.20/1M | $0.60/1M | Cost-optimized fallback |
| Titan Lite | $0.15/1M | $0.20/1M | Basic text processing |
| Ollama (Local) | Free | Free | Development/testing |

## Environment Detection Logic

The system uses the following priority order:

1. **Check for Ollama** (local development)
   - Attempts connection to `http://localhost:11434`
   - Uses if available and models are installed

2. **Check for AWS Lambda** (cloud deployment)
   - Detects `AWS_LAMBDA_FUNCTION_NAME` environment variable
   - Uses Bedrock with fallback models

3. **Check for API Keys** (cloud development)
   - Uses OpenAI if `OPENAI_API_KEY` is available
   - Uses Anthropic if `ANTHROPIC_API_KEY` is available

4. **Fallback to Regex** (no LLM available)
   - Uses pattern-based extraction
   - Ensures system always works

## Deployment Considerations

### AWS Lambda

Update your CloudFormation template to include fallback model configuration:

```yaml
Parameters:
  BedrockFallbackModel:
    Type: String
    Default: amazon.titan-text-express-v1
    Description: Cheaper fallback model for cost optimization

Environment:
  Variables:
    FINSIGHT_BEDROCK_FALLBACK_MODEL: !Ref BedrockFallbackModel
```

### Local Development

1. **Install Ollama** (recommended for cost-free development):
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull a model
   ollama pull llama2
   
   # Start Ollama service
   ollama serve
   ```

2. **Alternative**: Use API keys for cloud providers
   ```bash
   export OPENAI_API_KEY=your-key
   # or
   export ANTHROPIC_API_KEY=your-key
   ```

### Docker Deployment

```dockerfile
# Include environment detection in Docker
ENV FINSIGHT_LLM_PROVIDER=auto
ENV FINSIGHT_BEDROCK_FALLBACK_MODEL=amazon.titan-text-express-v1

# Optional: Include Ollama for local inference
RUN curl -fsSL https://ollama.ai/install.sh | sh
```

## Monitoring and Alerting

### Cost Tracking

```python
import logging
from src.utils.bedrock_client import get_bedrock_client

# Enable cost logging
logging.basicConfig(level=logging.INFO)

client = get_bedrock_client()
if client.using_fallback:
    logging.info("Using cost-optimized fallback model")

# Log model costs
cost = client.get_cost_estimate()
logging.info(f"Model cost: ${cost['input']}-${cost['output']} per {cost['per']}")
```

### Usage Patterns

Monitor your usage patterns to optimize costs:

- **Development**: Use Ollama (free)
- **Testing**: Use cheaper models (Titan Express)
- **Production**: Use balanced models (Claude Haiku)
- **High-quality analysis**: Use premium models (Claude Sonnet) sparingly

## Best Practices

1. **Development Environment**:
   - Use Ollama for free local inference
   - Test with cheaper models before using expensive ones
   - Enable debug logging to monitor provider selection

2. **Production Environment**:
   - Set up proper fallback chains
   - Monitor costs and usage patterns
   - Use appropriate model tiers for different use cases

3. **Cost Optimization**:
   - Batch requests when possible
   - Use cheaper models for simple tasks
   - Cache results to avoid redundant API calls
   - Set reasonable token limits

4. **Error Handling**:
   - Always have a fallback plan (regex extraction)
   - Handle rate limiting gracefully
   - Log provider switches for debugging

## Troubleshooting

### Common Issues

1. **"No provider available"**:
   - Ensure at least one provider is configured
   - Check API keys and credentials
   - Verify Ollama is running (for local development)

2. **"Fallback model failed"**:
   - Check AWS permissions for both models
   - Verify model availability in your region
   - Review CloudWatch logs for detailed errors

3. **High costs**:
   - Review token usage patterns
   - Consider using cheaper models for development
   - Implement request caching
   - Set up cost alerts in AWS

### Debug Mode

Enable debug mode for detailed logging:

```bash
export FINSIGHT_DEBUG=true
```

This will log:
- Provider selection decisions
- Model fallback events
- Cost estimates
- API call details

## Migration Guide

If you're upgrading from a previous version:

1. **Update configuration** to include fallback model:
   ```python
   # Old
   config = LLMConfig(provider="bedrock", bedrock_model="claude-3-haiku")
   
   # New
   config = LLMConfig(
       provider="bedrock",
       bedrock_model="anthropic.claude-3-haiku-20240307-v1:0",
       bedrock_fallback_model="amazon.titan-text-express-v1"  # New!
   )
   ```

2. **Update environment variables**:
   ```bash
   # Add fallback model
   export FINSIGHT_BEDROCK_FALLBACK_MODEL=amazon.titan-text-express-v1
   ```

3. **Update AWS templates** to include new parameters

4. **Test the new auto-detection** to ensure it works for your environment

## Support

For issues with cost optimization features:

1. Check the logs for provider selection decisions
2. Verify your environment configuration
3. Test with different providers manually
4. Review the cost estimation output

The system is designed to always work, falling back to regex extraction if no LLM providers are available.
