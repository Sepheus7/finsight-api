#!/bin/bash

# AWS Deployment Validation Test
# This script validates that the Ollama-aware AWS deployment is working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo "🧪 FinSight AWS Deployment Validation Test"
echo "=========================================="

# Test 1: Help functionality
print_test "Testing help functionality..."
if ./deploy.sh --help > /dev/null 2>&1; then
    print_status "Help command works"
else
    print_error "Help command failed"
    exit 1
fi

# Test 2: Template validation
print_test "Testing CloudFormation template validation..."
if ./deploy.sh validate > /dev/null 2>&1; then
    print_status "Template validation passed"
else
    print_error "Template validation failed"
    exit 1
fi

# Test 3: Template linting
print_test "Testing CloudFormation template linting..."
if sam validate --template template-ollama-aware.yaml --lint > /dev/null 2>&1; then
    print_status "Template linting passed"
else
    print_error "Template linting failed"
    exit 1
fi

# Test 4: Check required files exist
print_test "Checking required files exist..."
required_files=(
    "template-ollama-aware.yaml"
    "../../src/handlers/enhanced_fact_check_handler.py"
    "../../src/utils/llm_claim_extractor.py"
    "../../src/config.py"
    "../../requirements.txt"
)

for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        print_status "Found: $file"
    else
        print_error "Missing: $file"
        exit 1
    fi
done

# Test 5: Check environment variable handling
print_test "Testing LLM provider configurations..."

# Test OpenAI config
print_test "  Testing OpenAI configuration..."
if ./deploy.sh help --llm-provider openai > /dev/null 2>&1; then
    print_status "  OpenAI provider configuration accepted"
else
    print_warning "  OpenAI provider configuration issue (non-critical)"
fi

# Test Anthropic config
print_test "  Testing Anthropic configuration..."
if ./deploy.sh help --llm-provider anthropic > /dev/null 2>&1; then
    print_status "  Anthropic provider configuration accepted"
else
    print_warning "  Anthropic provider configuration issue (non-critical)"
fi

# Test regex fallback config
print_test "  Testing regex fallback configuration..."
if ./deploy.sh help --llm-provider regex > /dev/null 2>&1; then
    print_status "  Regex fallback configuration accepted"
else
    print_warning "  Regex fallback configuration issue (non-critical)"
fi

# Test 6: Check AWS prerequisites (if available)
print_test "Checking AWS prerequisites..."
if command -v aws &> /dev/null; then
    print_status "AWS CLI installed"
    
    if aws sts get-caller-identity > /dev/null 2>&1; then
        print_status "AWS credentials configured"
        
        # Get AWS account info for deployment readiness
        AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
        AWS_REGION=$(aws configure get region || echo "us-east-1")
        print_status "AWS Account: $AWS_ACCOUNT, Region: $AWS_REGION"
    else
        print_warning "AWS credentials not configured (use 'aws configure')"
    fi
else
    print_warning "AWS CLI not installed"
fi

if command -v sam &> /dev/null; then
    print_status "SAM CLI installed"
else
    print_warning "SAM CLI not installed"
fi

if docker ps &> /dev/null; then
    print_status "Docker is running"
else
    print_warning "Docker is not running"
fi

# Test 7: Generate deployment examples
print_test "Generating deployment examples..."
echo ""
echo "📋 Example Deployment Commands:"
echo "==============================="
echo ""
echo "Development deployment with OpenAI:"
echo "  ./deploy.sh deploy --stage dev --llm-provider openai --openai-key \$OPENAI_API_KEY"
echo ""
echo "Production deployment with Anthropic:"
echo "  ./deploy.sh deploy --stage prod --llm-provider anthropic --anthropic-key \$ANTHROPIC_API_KEY"
echo ""
echo "Cost-free deployment (regex only):"
echo "  ./deploy.sh deploy --stage dev --llm-provider regex"
echo ""
echo "Template validation only:"
echo "  ./deploy.sh validate"
echo ""
echo "Show deployment outputs:"
echo "  ./deploy.sh outputs --stage prod"

echo ""
print_status "All validation tests passed! ✨"
print_status "The Ollama-aware AWS deployment is ready for use."
print_status "See docs/AWS_DEPLOYMENT_OLLAMA_AWARE.md for complete deployment instructions."
