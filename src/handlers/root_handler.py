"""
Root Handler for AWS Lambda
Provides API information and available endpoints
"""

import json
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda handler for root API information endpoint
    """
    try:
        logger.info("Root endpoint accessed")
        
        # Extract base URL from event
        headers = event.get('headers', {})
        host = headers.get('Host', 'unknown')
        stage = event.get('requestContext', {}).get('stage', 'unknown')
        
        base_url = f"https://{host}/{stage}" if stage != 'unknown' else f"https://{host}"
        
        api_info = {
            "message": "Financial AI Quality Enhancement API - Serverless Edition",
            "description": "Enhance AI agent outputs with context enrichment, fact checking, and compliance validation",
            "version": "1.0.0-serverless",
            "architecture": "AWS Lambda + API Gateway",
            "timestamp": datetime.now().isoformat(),
            "endpoints": {
                "enhance": {
                    "method": "POST",
                    "path": f"{base_url}/enhance",
                    "description": "Enhance AI responses with fact-checking, context, and compliance checking"
                },
                "health": {
                    "method": "GET", 
                    "path": f"{base_url}/health",
                    "description": "Health check endpoint"
                },
                "root": {
                    "method": "GET",
                    "path": f"{base_url}/",
                    "description": "API information (this endpoint)"
                }
            },
            "documentation": {
                "api_docs": f"{base_url}/docs",
                "openapi_spec": f"{base_url}/openapi.json"
            },
            "features": [
                "Real-time fact checking of financial claims",
                "Context enrichment with market data",
                "Regulatory compliance validation", 
                "Quality scoring and enhancement",
                "Serverless scalability",
                "AWS native integration"
            ],
            "supported_content_types": [
                "Financial advice and recommendations",
                "Investment analysis",
                "Market commentary",
                "Economic discussions",
                "Trading strategies",
                "Portfolio guidance"
            ],
            "compliance_checks": [
                "Investment advice disclaimers",
                "Risk disclosure requirements",
                "Guaranteed return claims",
                "Market manipulation language",
                "Suitability assessments",
                "Anti-money laundering flags"
            ],
            "aws_request_id": context.aws_request_id,
            "lambda_info": {
                "function_name": context.function_name,
                "memory_limit_mb": context.memory_limit_in_mb,
                "remaining_time_ms": context.get_remaining_time_in_millis()
            }
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,GET,POST'
            },
            'body': json.dumps(api_info, indent=2)
        }
        
    except Exception as e:
        logger.error(f"Root endpoint failed: {str(e)}")
        
        error_response = {
            "error": "Internal server error",
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
            "aws_request_id": context.aws_request_id
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,GET,POST'
            },
            'body': json.dumps(error_response)
        }
