#!/bin/bash

# AWS SAM Deployment Script for Financial AI Quality Enhancement API
# This script deploys the serverless application to AWS

set -e  # Exit on any error

# Configuration
STACK_NAME="finsight-api"
TEMPLATE_FILE="template-ollama-aware.yaml"
REGION="us-east-1"
PROFILE=""  # Set your AWS profile if needed
STAGE="dev"
LLM_PROVIDER="openai"  # Default for AWS Lambda (ollama not supported)
DEBUG_MODE="false"

# LLM Configuration
OPENAI_API_KEY=""
ANTHROPIC_API_KEY=""
OPENAI_MODEL="gpt-4o-mini"
ANTHROPIC_MODEL="claude-3-haiku-20240307"

# Change to the deployment directory if not already there
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if SAM CLI is installed
    if ! command -v sam &> /dev/null; then
        print_error "SAM CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker ps &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_status "Prerequisites check passed!"
}

# Function to check LLM configuration
check_llm_configuration() {
    print_status "Checking LLM configuration for AWS Lambda deployment..."
    
    if [ "$LLM_PROVIDER" = "ollama" ]; then
        print_warning "Ollama is not supported in AWS Lambda serverless environment."
        print_warning "Switching to OpenAI as default LLM provider for Lambda deployment."
        LLM_PROVIDER="openai"
    fi
    
    if [ "$LLM_PROVIDER" = "openai" ] && [ -z "$OPENAI_API_KEY" ]; then
        print_warning "OpenAI API key not provided. The system will fall back to regex-based extraction."
        print_warning "For best results, set OPENAI_API_KEY environment variable."
    fi
    
    if [ "$LLM_PROVIDER" = "anthropic" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
        print_warning "Anthropic API key not provided. The system will fall back to regex-based extraction."
        print_warning "For best results, set ANTHROPIC_API_KEY environment variable."
    fi
    
    print_status "LLM configuration: Provider=$LLM_PROVIDER"
}

# Function to validate template
validate_template() {
    print_status "Validating SAM template..."
    sam validate --template $TEMPLATE_FILE
    print_status "Template validation passed!"
}

# Function to build the application
build_application() {
    print_status "Building SAM application..."
    sam build --template $TEMPLATE_FILE --use-container
    print_status "Build completed successfully!"
}

# Function to deploy the application
deploy_application() {
    print_status "Deploying application to AWS..."
    
    # Set AWS profile if provided
    PROFILE_FLAG=""
    if [ -n "$PROFILE" ]; then
        PROFILE_FLAG="--profile $PROFILE"
    fi
    
    # Get API keys from environment if not set
    if [ -z "$OPENAI_API_KEY" ]; then
        OPENAI_API_KEY="${OPENAI_API_KEY:-""}"
    fi
    
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-""}"
    fi
    
    # Deploy with SAM
    sam deploy \
        --template-file $TEMPLATE_FILE \
        --stack-name $STACK_NAME \
        --region $REGION \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides \
            Stage=$STAGE \
            LLMProvider=$LLM_PROVIDER \
            OpenAIApiKey="$OPENAI_API_KEY" \
            AnthropicApiKey="$ANTHROPIC_API_KEY" \
            OpenAIModel="$OPENAI_MODEL" \
            AnthropicModel="$ANTHROPIC_MODEL" \
            DebugMode="$DEBUG_MODE" \
        --confirm-changeset \
        --resolve-s3 \
        $PROFILE_FLAG
    
    print_status "Deployment completed successfully!"
}

# Function to get stack outputs
get_stack_outputs() {
    print_status "Getting stack outputs..."
    
    PROFILE_FLAG=""
    if [ -n "$PROFILE" ]; then
        PROFILE_FLAG="--profile $PROFILE"
    fi
    
    # Get API URL
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`FinancialAIApiUrl`].OutputValue' \
        --output text $PROFILE_FLAG)
    
    # Get DynamoDB table name
    TABLE_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`EnhancementHistoryTableName`].OutputValue' \
        --output text $PROFILE_FLAG)
    
    # Get S3 bucket name
    BUCKET_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`DataCacheBucketName`].OutputValue' \
        --output text $PROFILE_FLAG)
    
    echo ""
    echo -e "${GREEN}=== Deployment Complete ===${NC}"
    echo -e "${GREEN}API URL:${NC} $API_URL"
    echo -e "${GREEN}DynamoDB Table:${NC} $TABLE_NAME"
    echo -e "${GREEN}S3 Bucket:${NC} $BUCKET_NAME"
    echo -e "${GREEN}LLM Provider:${NC} $LLM_PROVIDER"
    echo -e "${GREEN}Stage:${NC} $STAGE"
    echo ""
    echo -e "${YELLOW}Testing endpoints:${NC}"
    echo "curl $API_URL/health"
    echo "curl -X POST $API_URL/fact-check -H 'Content-Type: application/json' -d '{\"content\":\"Apple stock is trading at \$150\"}'"
    echo ""
}

# Function to test deployment
test_deployment() {
    print_status "Testing deployment..."
    
    if [ -n "$API_URL" ]; then
        # Test health endpoint
        echo "Testing health endpoint..."
        curl -s "$API_URL/health" | jq . || echo "Health check response received"
        
        echo ""
        echo "Testing fact-check endpoint..."
        curl -s -X POST "$API_URL/fact-check" \
            -H "Content-Type: application/json" \
            -d '{"content": "Apple stock is trading at $150"}' | jq . || echo "Fact-check response received"
    fi
}

# Function to set up DynamoDB data
setup_dynamodb_data() {
    print_status "Setting up DynamoDB compliance rules..."
    
    PROFILE_FLAG=""
    if [ -n "$PROFILE" ]; then
        PROFILE_FLAG="--profile $PROFILE"
    fi
    
    TABLE_NAME="${STACK_NAME}-compliance-rules"
    
    # Add some sample compliance rules
    aws dynamodb put-item \
        --table-name $TABLE_NAME \
        --item '{
            "rule_id": {"S": "investment_advice_disclaimer"},
            "rule_name": {"S": "Investment Advice Disclaimer"},
            "severity": {"S": "HIGH"},
            "description": {"S": "Investment advice must include appropriate disclaimers"},
            "created_at": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}
        }' \
        --region $REGION \
        $PROFILE_FLAG
    
    aws dynamodb put-item \
        --table-name $TABLE_NAME \
        --item '{
            "rule_id": {"S": "guaranteed_returns"},
            "rule_name": {"S": "Guaranteed Returns"},
            "severity": {"S": "HIGH"},
            "description": {"S": "No claims of guaranteed returns are allowed"},
            "created_at": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}
        }' \
        --region $REGION \
        $PROFILE_FLAG
    
    print_status "DynamoDB compliance rules setup completed!"
}

# Function to clean up resources
cleanup() {
    print_warning "Cleaning up resources..."
    
    PROFILE_FLAG=""
    if [ -n "$PROFILE" ]; then
        PROFILE_FLAG="--profile $PROFILE"
    fi
    
    sam delete \
        --stack-name $STACK_NAME \
        --region $REGION \
        --no-prompts \
        $PROFILE_FLAG
    
    print_status "Cleanup completed!"
}

# Function to show logs
show_logs() {
    print_status "Showing recent logs for all functions..."
    
    PROFILE_FLAG=""
    if [ -n "$PROFILE" ]; then
        PROFILE_FLAG="--profile $PROFILE"
    fi
    
    sam logs \
        --stack-name $STACK_NAME \
        --start-time '10 minutes ago' \
        --include-traces \
        $PROFILE_FLAG
}

# Main deployment function
main_deploy() {
    print_status "Starting FinSight AWS deployment with Ollama-aware configuration..."
    echo "Stack: $STACK_NAME"
    echo "Stage: $STAGE"
    echo "Region: $REGION"
    echo "LLM Provider: $LLM_PROVIDER"
    echo "Template: $TEMPLATE_FILE"
    echo ""
    
    check_prerequisites
    check_llm_configuration
    validate_template
    build_application
    deploy_application
    get_stack_outputs
    
    print_status "Deployment completed successfully!"
    
    # Optional testing
    read -p "Would you like to test the deployment? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_deployment
    fi
}

# Function to show usage information
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  deploy    - Full deployment (default)"
    echo "  build     - Build application only"
    echo "  validate  - Validate template only"
    echo "  outputs   - Show stack outputs"
    echo "  logs      - Show recent logs"
    echo "  cleanup   - Delete the stack"
    echo "  help      - Show this help"
    echo ""
    echo "Options:"
    echo "  -s, --stage STAGE           Deployment stage (dev, staging, prod). Default: dev"
    echo "  -r, --region REGION         AWS region. Default: us-east-1"
    echo "  -p, --profile PROFILE       AWS profile to use"
    echo "  -l, --llm-provider PROVIDER LLM provider (openai, anthropic, regex). Default: openai"
    echo "  -d, --debug                 Enable debug mode"
    echo "  --openai-key KEY           OpenAI API key"
    echo "  --anthropic-key KEY        Anthropic API key"
    echo "  --openai-model MODEL       OpenAI model. Default: gpt-4o-mini"
    echo "  --anthropic-model MODEL    Anthropic model. Default: claude-3-haiku-20240307"
    echo "  -h, --help                 Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  OPENAI_API_KEY             OpenAI API key"
    echo "  ANTHROPIC_API_KEY          Anthropic API key"
    echo "  STACK_NAME                 Stack name (default: finsight-api)"
    echo "  REGION                     AWS region (default: us-east-1)"
    echo "  STAGE                      Deployment stage (default: dev)"
    echo ""
    echo "Examples:"
    echo "  # Deploy to dev with OpenAI"
    echo "  $0 deploy --stage dev --llm-provider openai --openai-key sk-..."
    echo ""
    echo "  # Deploy to production with Anthropic"
    echo "  $0 deploy --stage prod --llm-provider anthropic --anthropic-key sk-ant-..."
    echo ""
    echo "  # Deploy with regex fallback only"
    echo "  $0 deploy --stage dev --llm-provider regex"
    echo ""
    echo "  # Just validate the template"
    echo "  $0 validate"
    echo ""
    echo "  # Show deployment outputs"
    echo "  $0 outputs --stage prod"
    echo ""
    echo "Note: Ollama is not supported in AWS Lambda. Use local/Docker deployment for Ollama."
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--stage)
                STAGE="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -p|--profile)
                PROFILE="$2"
                shift 2
                ;;
            -l|--llm-provider)
                LLM_PROVIDER="$2"
                shift 2
                ;;
            -d|--debug)
                DEBUG_MODE="true"
                shift
                ;;
            --openai-key)
                OPENAI_API_KEY="$2"
                shift 2
                ;;
            --anthropic-key)
                ANTHROPIC_API_KEY="$2"
                shift 2
                ;;
            --openai-model)
                OPENAI_MODEL="$2"
                shift 2
                ;;
            --anthropic-model)
                ANTHROPIC_MODEL="$2"
                shift 2
                ;;
            -h|--help|help)
                show_usage
                exit 0
                ;;
            deploy|build|validate|outputs|logs|cleanup|help)
                # Skip commands - they are handled separately
                shift
                ;;
            *)
                print_error "Unknown option $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Main execution
main() {
    echo "🏦 Financial AI Quality Enhancement API - AWS Deployment"
    echo "======================================================"
    
    # Parse command line arguments first
    parse_arguments "$@"
    
    # Determine command (look for non-flag arguments)
    COMMAND="deploy"  # default
    for arg in "$@"; do
        case $arg in
            -*)
                # Skip flags and their values
                continue
                ;;
            deploy|build|validate|outputs|logs|cleanup|help)
                COMMAND="$arg"
                break
                ;;
        esac
    done
    
    # Execute command
    case "$COMMAND" in
        "deploy")
            check_prerequisites
            check_llm_configuration
            validate_template
            build_application
            deploy_application
            setup_dynamodb_data
            get_stack_outputs
            ;;
        "build")
            check_prerequisites
            check_llm_configuration
            validate_template
            build_application
            ;;
        "validate")
            validate_template
            ;;
        "outputs")
            get_stack_outputs
            ;;
        "logs")
            show_logs
            ;;
        "cleanup")
            cleanup
            ;;
        "help")
            show_usage
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
}

# Override defaults with environment variables if set
STACK_NAME=${STACK_NAME:-"finai-quality-api"}
REGION=${REGION:-"us-east-1"}
STAGE=${STAGE:-"dev"}

# Run main function
main "$@"
