"""
Health Check Handler for AWS Lambda
Provides API health status endpoint
"""

import json
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda handler for health check endpoint
    """
    try:
        logger.info("Health check requested")
        
        # Basic health check response
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Financial AI Quality Enhancement API",
            "version": "1.0.0-serverless",
            "aws_request_id": getattr(context, 'aws_request_id', 'test-request'),
            "remaining_time_ms": getattr(context, 'get_remaining_time_in_millis', lambda: 30000)(),
            "memory_limit_mb": getattr(context, 'memory_limit_in_mb', 1024)
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps(health_data)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        
        error_response = {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "aws_request_id": getattr(context, 'aws_request_id', 'test-request')
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps(error_response)
        }
