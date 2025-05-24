#!/bin/bash

# AWS SAM Deployment Script for Financial AI Quality Enhancement API
# This script deploys the serverless application to AWS

set -e  # Exit on any error

# Configuration
STACK_NAME="finai-quality-api"
REGION="us-east-1"
PROFILE=""  # Set your AWS profile if needed
STAGE="dev"

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

# Function to validate template
validate_template() {
    print_status "Validating SAM template..."
    sam validate --template template.yaml
    print_status "Template validation passed!"
}

# Function to build the application
build_application() {
    print_status "Building SAM application..."
    sam build --use-container
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
    
    # Deploy with SAM
    sam deploy \
        --stack-name $STACK_NAME \
        --region $REGION \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides Stage=$STAGE \
        --confirm-changeset \
        --resolve-s3 \
        $PROFILE_FLAG
    
    print_status "Deployment completed successfully!"
}

# Function to get stack outputs
get_outputs() {
    print_status "Retrieving stack outputs..."
    
    PROFILE_FLAG=""
    if [ -n "$PROFILE" ]; then
        PROFILE_FLAG="--profile $PROFILE"
    fi
    
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`FinancialAIApiUrl`].OutputValue' \
        --output text \
        $PROFILE_FLAG)
    
    echo ""
    echo "==================================="
    echo "🚀 DEPLOYMENT SUCCESSFUL!"
    echo "==================================="
    echo "API URL: $API_URL"
    echo "Health Check: ${API_URL}health"
    echo "API Info: ${API_URL}"
    echo "Main Endpoint: ${API_URL}enhance"
    echo "==================================="
    echo ""
    
    # Test the health endpoint
    print_status "Testing health endpoint..."
    if curl -s "${API_URL}health" | grep -q "healthy"; then
        print_status "Health check passed! ✅"
    else
        print_warning "Health check failed. Please check the logs."
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

# Main execution
main() {
    echo "🏦 Financial AI Quality Enhancement API - AWS Deployment"
    echo "======================================================"
    
    # Parse command line arguments
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            validate_template
            build_application
            deploy_application
            setup_dynamodb_data
            get_outputs
            ;;
        "build")
            check_prerequisites
            validate_template
            build_application
            ;;
        "validate")
            validate_template
            ;;
        "outputs")
            get_outputs
            ;;
        "logs")
            show_logs
            ;;
        "cleanup")
            cleanup
            ;;
        "help")
            echo "Usage: $0 [command]"
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
            echo "Environment variables:"
            echo "  STACK_NAME - Stack name (default: finai-quality-api)"
            echo "  REGION     - AWS region (default: us-east-1)"
            echo "  PROFILE    - AWS profile to use"
            echo "  STAGE      - Deployment stage (default: dev)"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Run '$0 help' for usage information."
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
