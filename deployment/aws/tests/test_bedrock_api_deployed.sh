#!/bin/bash

# FinSight Bedrock API Test Script
# Tests the deployed AWS API with proper IAM authentication

set -e

API_URL="https://jfho5me3zi.execute-api.us-east-1.amazonaws.com/dev"
REGION="us-east-1"

echo "🧪 FinSight Bedrock API Test Suite"
echo "=================================="
echo ""
echo "🔗 API Endpoint: $API_URL"
echo "🌍 Region: $REGION"
echo ""

# Test 1: Health Check
echo "📊 Test 1: Health Check"
echo "----------------------"
curl -s -X GET "$API_URL/health" \
  --aws-sigv4 "aws:amz:$REGION:execute-api" \
  --user "$(aws configure get aws_access_key_id):$(aws configure get aws_secret_access_key)" | jq .
echo ""

# Test 2: Root endpoint
echo "📊 Test 2: API Information"
echo "--------------------------"
curl -s -X GET "$API_URL/" \
  --aws-sigv4 "aws:amz:$REGION:execute-api" \
  --user "$(aws configure get aws_access_key_id):$(aws configure get aws_secret_access_key)" | jq .
echo ""

# Test 3: Enhanced Fact Check with Bedrock
echo "📊 Test 3: Enhanced Fact Check (Bedrock)"
echo "---------------------------------------"
curl -s -X POST "$API_URL/fact-check" \
  --aws-sigv4 "aws:amz:$REGION:execute-api" \
  --user "$(aws configure get aws_access_key_id):$(aws configure get aws_secret_access_key)" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Apple Inc. reported record quarterly revenue of $123.9 billion in Q4 2024, representing a 15% increase year-over-year.",
    "enhanced": true
  }' | jq .
echo ""

# Test 4: Response Enhancement
echo "📊 Test 4: Response Enhancement"
echo "------------------------------"
curl -s -X POST "$API_URL/enhance" \
  --aws-sigv4 "aws:amz:$REGION:execute-api" \
  --user "$(aws configure get aws_access_key_id):$(aws configure get aws_secret_access_key)" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Tesla stock is expected to perform well next quarter due to strong delivery numbers.",
    "enhanced": true
  }' | jq .

echo ""
echo "✅ Bedrock API testing complete!"
