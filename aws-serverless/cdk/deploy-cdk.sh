#!/bin/bash

# CDK Deployment Script for Financial AI Quality Enhancement API
# Alternative deployment using AWS CDK instead of SAM

set -e  # Exit on any error

# Configuration
STACK_NAME="FinancialAIQualityApiStack"
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
    
    # Check if CDK is installed
    if ! command -v cdk &> /dev/null; then
        print_error "AWS CDK is not installed. Please install it with: npm install -g aws-cdk"
        exit 1
    fi
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_status "Prerequisites check passed!"
}

# Function to set up Python environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install CDK requirements
    pip install -r requirements.txt
    
    print_status "Python environment setup completed!"
}

# Function to bootstrap CDK
bootstrap_cdk() {
    print_status "Bootstrapping CDK..."
    
    PROFILE_FLAG=""
    if [ -n "$PROFILE" ]; then
        PROFILE_FLAG="--profile $PROFILE"
    fi
    
    # Check if already bootstrapped
    if aws cloudformation describe-stacks --stack-name CDKToolkit --region $REGION $PROFILE_FLAG &> /dev/null; then
        print_status "CDK already bootstrapped in this region."
    else
        cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text $PROFILE_FLAG)/$REGION $PROFILE_FLAG
        print_status "CDK bootstrap completed!"
    fi
}

# Function to synthesize the stack
synthesize_stack() {
    print_status "Synthesizing CDK stack..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    cdk synth --context stage=$STAGE
    print_status "Stack synthesis completed!"
}

# Function to deploy the stack
deploy_stack() {
    print_status "Deploying CDK stack..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    PROFILE_FLAG=""
    if [ -n "$PROFILE" ]; then
        PROFILE_FLAG="--profile $PROFILE"
    fi
    
    cdk deploy --context stage=$STAGE --require-approval never $PROFILE_FLAG
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
        --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
        --output text \
        $PROFILE_FLAG)
    
    echo ""
    echo "==================================="
    echo "🚀 CDK DEPLOYMENT SUCCESSFUL!"
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
    
    print_status "DynamoDB compliance rules setup completed!"
}

# Function to destroy the stack
destroy_stack() {
    print_warning "Destroying CDK stack..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    PROFILE_FLAG=""
    if [ -n "$PROFILE" ]; then
        PROFILE_FLAG="--profile $PROFILE"
    fi
    
    cdk destroy --force --context stage=$STAGE $PROFILE_FLAG
    print_status "Stack destruction completed!"
}

# Function to show stack diff
show_diff() {
    print_status "Showing stack differences..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    cdk diff --context stage=$STAGE
}

# Main execution
main() {
    echo "🏦 Financial AI Quality Enhancement API - CDK Deployment"
    echo "======================================================="
    
    # Parse command line arguments
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            setup_python_env
            bootstrap_cdk
            synthesize_stack
            deploy_stack
            setup_dynamodb_data
            get_outputs
            ;;
        "synth")
            check_prerequisites
            setup_python_env
            synthesize_stack
            ;;
        "diff")
            check_prerequisites
            setup_python_env
            show_diff
            ;;
        "bootstrap")
            check_prerequisites
            setup_python_env
            bootstrap_cdk
            ;;
        "outputs")
            get_outputs
            ;;
        "destroy")
            destroy_stack
            ;;
        "help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  deploy     - Full deployment (default)"
            echo "  synth      - Synthesize CloudFormation template"
            echo "  diff       - Show differences with deployed stack"
            echo "  bootstrap  - Bootstrap CDK in account/region"
            echo "  outputs    - Show stack outputs"
            echo "  destroy    - Destroy the stack"
            echo "  help       - Show this help"
            echo ""
            echo "Environment variables:"
            echo "  STACK_NAME - Stack name (default: FinancialAIQualityApiStack)"
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
STACK_NAME=${STACK_NAME:-"FinancialAIQualityApiStack"}
REGION=${REGION:-"us-east-1"}
STAGE=${STAGE:-"dev"}

# Run main function
main "$@"
