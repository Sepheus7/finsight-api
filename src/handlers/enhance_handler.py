"""
Main Enhancement Handler for AWS Lambda
Orchestrates fact-checking, context enrichment, and compliance checking
"""

import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any, List
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')

# Environment variables
FACT_CHECK_FUNCTION = os.environ.get('FACT_CHECK_FUNCTION')
CONTEXT_ENRICHMENT_FUNCTION = os.environ.get('CONTEXT_ENRICHMENT_FUNCTION')
COMPLIANCE_CHECK_FUNCTION = os.environ.get('COMPLIANCE_CHECK_FUNCTION')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')

def lambda_handler(event, context):
    """
    Main Lambda handler for enhancing AI responses
    """
    try:
        # Parse the request body
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event

        # Extract request data
        ai_response = body.get('ai_response', {})
        enrichment_level = body.get('enrichment_level', 'standard')
        fact_check = body.get('fact_check', True)
        add_context = body.get('add_context', True)

        content = ai_response.get('content', '')
        if not content:
            return create_error_response(400, "Missing required field: ai_response.content")

        start_time = datetime.now()
        request_id = context.aws_request_id

        logger.info(f"Processing enhancement request {request_id} for content length: {len(content)}")

        # Initialize results
        fact_checks = []
        context_additions = []
        compliance_flags = []

        # Parallel invocation of microservices
        tasks = []

        # Fact checking
        if fact_check:
            fact_check_payload = {
                'content': content,
                'request_id': request_id
            }
            tasks.append(invoke_lambda_async(FACT_CHECK_FUNCTION, fact_check_payload, 'fact_check'))

        # Context enrichment
        if add_context:
            context_payload = {
                'content': content,
                'enrichment_level': enrichment_level,
                'request_id': request_id
            }
            tasks.append(invoke_lambda_async(CONTEXT_ENRICHMENT_FUNCTION, context_payload, 'context'))

        # Compliance checking
        compliance_payload = {
            'content': content,
            'request_id': request_id
        }
        tasks.append(invoke_lambda_async(COMPLIANCE_CHECK_FUNCTION, compliance_payload, 'compliance'))

        # Wait for all tasks to complete
        results = {}
        for task in tasks:
            task_type = task['type']
            response = task['future']
            
            try:
                if response['StatusCode'] == 200:
                    result_payload = json.loads(response['Payload'].read())
                    results[task_type] = result_payload
                    logger.info(f"Successfully completed {task_type} processing")
                else:
                    logger.error(f"Failed {task_type} processing with status: {response['StatusCode']}")
                    results[task_type] = {'error': f"Service unavailable"}
            except Exception as e:
                logger.error(f"Error processing {task_type}: {str(e)}")
                results[task_type] = {'error': str(e)}

        # Process results
        if 'fact_check' in results and 'fact_checks' in results['fact_check']:
            fact_checks = results['fact_check']['fact_checks']

        if 'context' in results and 'context_additions' in results['context']:
            context_additions = results['context']['context_additions']

        if 'compliance' in results and 'compliance_flags' in results['compliance']:
            compliance_flags = results['compliance']['compliance_flags']

        # Generate enhanced content
        enhanced_content = generate_enhanced_content(
            content, fact_checks, context_additions, compliance_flags
        )

        # AI-enhanced evaluation (if available)
        ai_evaluation = None
        try:
            from ai_evaluator_handler import lambda_handler as ai_evaluator
            
            class MockContext:
                aws_request_id = request_id
            
            ai_event = {
                'content': content,
                'fact_checks': fact_checks,
                'context_additions': context_additions,
                'compliance_flags': compliance_flags
            }
            
            ai_response = ai_evaluator(ai_event, MockContext())
            ai_evaluation = ai_response.get('ai_evaluation', {})
            logger.info("AI evaluation completed successfully")
            
        except Exception as e:
            logger.warning(f"AI evaluation failed, using fallback: {str(e)}")
            ai_evaluation = None

        # Calculate quality score (enhanced with AI if available)
        if ai_evaluation and 'overall_score' in ai_evaluation:
            quality_score = ai_evaluation['overall_score']
            # Apply AI confidence adjustments to fact checks
            if 'confidence_adjustments' in ai_evaluation:
                fact_checks = apply_ai_confidence_adjustments(fact_checks, ai_evaluation['confidence_adjustments'])
        else:
            quality_score = calculate_quality_score(fact_checks, context_additions, compliance_flags)

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Store enhancement history
        enhancement_record = {
            'id': request_id,
            'timestamp': start_time.isoformat(),
            'original_content_length': len(content),
            'enhanced_content_length': len(enhanced_content),
            'fact_checks_count': len(fact_checks),
            'context_additions_count': len(context_additions),
            'compliance_flags_count': len(compliance_flags),
            'quality_score': quality_score,
            'processing_time_ms': processing_time,
            'enrichment_level': enrichment_level
        }
        
        store_enhancement_history(enhancement_record)

        # Prepare response
        response_data = {
            'original_content': content,
            'enhanced_content': enhanced_content,
            'fact_checks': fact_checks,
            'context_additions': context_additions,
            'quality_score': quality_score,
            'compliance_flags': compliance_flags,
            'ai_evaluation': ai_evaluation,  # Include AI evaluation results
            'processing_time_ms': int(processing_time),
            'request_id': request_id
        }

        return create_success_response(response_data)

    except Exception as e:
        logger.error(f"Enhancement failed: {str(e)}")
        return create_error_response(500, f"Enhancement failed: {str(e)}")


def invoke_lambda_async(function_name: str, payload: Dict[str, Any], task_type: str) -> Dict[str, Any]:
    """Invoke Lambda function asynchronously"""
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        return {
            'type': task_type,
            'future': response
        }
    except Exception as e:
        logger.error(f"Failed to invoke {function_name}: {str(e)}")
        raise


def generate_enhanced_content(content: str, fact_checks: List[Dict], 
                            context_additions: List[Dict], compliance_flags: List[str]) -> str:
    """Generate enhanced content with fact checks and context"""
    enhanced_content = content

    # Add context if available
    if context_additions:
        context_text = "\n\n📊 Additional Context:\n"
        for ctx in context_additions:
            context_text += f"• {ctx.get('content', '')} (Source: {ctx.get('source', 'Unknown')})\n"
        enhanced_content += context_text

    # Add fact-check warnings if needed
    failed_checks = [fc for fc in fact_checks if not fc.get('verified', True)]
    if failed_checks:
        warning_text = "\n\n⚠️ Fact Check Alerts:\n"
        for fc in failed_checks:
            warning_text += f"• {fc.get('claim', '')} - {fc.get('explanation', '')}\n"
        enhanced_content += warning_text

    # Add compliance warnings
    if compliance_flags:
        compliance_text = "\n\n⚖️ Compliance Notices:\n"
        for flag in compliance_flags:
            compliance_text += f"• {flag}\n"
        enhanced_content += compliance_text

    return enhanced_content


def calculate_quality_score(fact_checks: List[Dict], context_additions: List[Dict], 
                          compliance_flags: List[str]) -> float:
    """Calculate quality score based on enhancements"""
    base_score = 0.7

    # Fact check impact
    if fact_checks:
        verified_ratio = sum(1 for fc in fact_checks if fc.get('verified', False)) / len(fact_checks)
        fact_check_score = 0.3 * verified_ratio
    else:
        fact_check_score = 0.0

    # Context enrichment impact
    context_score = min(0.2, len(context_additions) * 0.05)

    # Compliance penalty
    compliance_penalty = len(compliance_flags) * 0.1

    final_score = base_score + fact_check_score + context_score - compliance_penalty
    return max(0.0, min(1.0, final_score))


def store_enhancement_history(record: Dict[str, Any]) -> None:
    """Store enhancement record in DynamoDB"""
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        table.put_item(Item=record)
        logger.info(f"Stored enhancement history for request {record['id']}")
    except Exception as e:
        logger.error(f"Failed to store enhancement history: {str(e)}")


def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create successful API response"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(data, default=str)
    }


def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create error API response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({'error': message})
    }


def apply_ai_confidence_adjustments(fact_checks: List[Dict], adjustments: Dict[str, float]) -> List[Dict]:
    """Apply AI-suggested confidence adjustments to fact checks"""
    try:
        confidence_multiplier = adjustments.get('fact_check_confidence', 1.0)
        
        for fact_check in fact_checks:
            original_confidence = fact_check.get('confidence', 0.5)
            # Apply multiplier but keep within valid range
            adjusted_confidence = min(0.99, max(0.01, original_confidence * confidence_multiplier))
            fact_check['confidence'] = adjusted_confidence
            fact_check['ai_adjusted'] = True
            
        logger.info(f"Applied AI confidence adjustments with multiplier {confidence_multiplier}")
        return fact_checks
        
    except Exception as e:
        logger.error(f"Error applying AI confidence adjustments: {str(e)}")
        return fact_checks


def enhance_financial_claim(claim: str) -> Dict[str, Any]:
    """
    Standalone function to enhance a single financial claim
    This is useful for testing and direct API calls
    """
    try:
        # Create a mock event for the claim
        event = {
            'ai_response': {
                'content': claim,
                'agent_id': 'test_agent',
                'timestamp': datetime.now().isoformat()
            },
            'enrichment_level': 'comprehensive',
            'fact_check': True,
            'add_context': True,
            'compliance_check': True
        }
        
        # Create a mock context
        class MockContext:
            aws_request_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Call the main lambda handler
        response = lambda_handler(event, MockContext())
        
        # Extract and return the enhanced data
        if response.get('statusCode') == 200:
            body = json.loads(response['body'])
            
            # Extract confidence scores for comparison
            fact_checks = body.get('fact_checks', [])
            original_confidence = None
            enhanced_confidence = None
            
            if fact_checks:
                # Calculate average confidence from fact checks
                confidences = [fc.get('confidence', 0.5) for fc in fact_checks]
                original_confidence = sum(confidences) / len(confidences)
                
                # If AI adjustments were applied, this represents enhanced confidence
                enhanced_confidence = original_confidence
                
                # Check if AI evaluation provided additional confidence info
                ai_eval = body.get('ai_evaluation', {})
                if ai_eval and 'confidence_adjustment' in ai_eval:
                    enhanced_confidence = min(0.99, max(0.01, 
                        original_confidence + ai_eval['confidence_adjustment']))
            
            # Return structured response
            return {
                'original_confidence': original_confidence,
                'enhanced_confidence': enhanced_confidence,
                'verification_status': 'verified' if all(fc.get('verified', False) for fc in fact_checks) else 'unverified',
                'ai_evaluation': body.get('ai_evaluation', {}),
                'evidence': [
                    {
                        'description': fc.get('explanation', ''),
                        'source': fc.get('source', ''),
                        'confidence': fc.get('confidence', 0.5)
                    }
                    for fc in fact_checks
                ],
                'quality_score': body.get('quality_score', 0.5),
                'processing_time_ms': body.get('processing_time_ms', 0)
            }
        else:
            return {'error': f"Enhancement failed with status {response.get('statusCode')}"}
            
    except Exception as e:
        return {'error': str(e)}
