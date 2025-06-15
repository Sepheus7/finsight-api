#!/bin/bash

# Exit on error
set -e

# Default values
STAGE="dev"
REGION="us-east-1"
STACK_NAME="finsight"
LLM_PROVIDER="bedrock"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --stage|-s)
            STAGE="$2"
            shift
            shift
            ;;
        --region|-r)
            REGION="$2"
            shift
            shift
            ;;
        --stack-name|-n)
            STACK_NAME="$2"
            shift
            shift
            ;;
        --llm-provider|-l)
            LLM_PROVIDER="$2"
            shift
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate stage
if [[ "$STAGE" != "dev" && "$STAGE" != "staging" && "$STAGE" != "prod" ]]; then
    echo "Error: Stage must be either 'dev', 'staging', or 'prod'"
    exit 1
fi

# Validate LLM provider
if [[ "$LLM_PROVIDER" != "bedrock" && "$LLM_PROVIDER" != "openai" && "$LLM_PROVIDER" != "anthropic" && "$LLM_PROVIDER" != "regex" ]]; then
    echo "Error: LLM provider must be one of: bedrock, openai, anthropic, regex"
    exit 1
fi

echo "Deploying FinSight to $STAGE environment in $REGION..."
echo "Using LLM provider: $LLM_PROVIDER"

# Build the SAM application
echo "Building SAM application..."
sam build --template-file templates/main.yaml

# Prepare deployment parameters
PARAMS="Stage=$STAGE LLMProvider=$LLM_PROVIDER"

# Add API keys if needed
if [[ "$LLM_PROVIDER" == "openai" ]]; then
    if [[ -z "$OPENAI_API_KEY" ]]; then
        echo "Error: OPENAI_API_KEY environment variable is required for OpenAI deployment"
        exit 1
    fi
    PARAMS="$PARAMS OpenAIApiKey=$OPENAI_API_KEY"
fi

if [[ "$LLM_PROVIDER" == "anthropic" ]]; then
    if [[ -z "$ANTHROPIC_API_KEY" ]]; then
        echo "Error: ANTHROPIC_API_KEY environment variable is required for Anthropic deployment"
        exit 1
    fi
    PARAMS="$PARAMS AnthropicApiKey=$ANTHROPIC_API_KEY"
fi

# Deploy the SAM application
echo "Deploying SAM application..."
sam deploy \
    --template-file .aws-sam/build/template.yaml \
    --stack-name "$STACK_NAME-$STAGE" \
    --parameter-overrides $PARAMS \
    --capabilities CAPABILITY_IAM \
    --region "$REGION" \
    --no-fail-on-empty-changeset

# Get the API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME-$STAGE" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
    --output text \
    --region "$REGION")

echo "Deployment complete!"
echo "API Endpoint: $API_ENDPOINT"
echo "Update your frontend configuration to use this endpoint for the $STAGE environment."
