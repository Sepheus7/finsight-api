"""
Optimized Enhancement Handler for AWS Lambda
Implements parallel processing and performance optimizations
Target: Reduce processing time from ~16s to <8s
"""

import json
import os
import boto3
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import logging

# Import performance optimization utilities
try:
    from ..utils.performance_optimizer import get_optimizer, async_cached
    from ..handlers.ai_evaluator_handler import lambda_handler as ai_evaluator
except ImportError:
    from utils.performance_optimizer import get_optimizer, async_cached
    from handlers.ai_evaluator_handler import lambda_handler as ai_evaluator

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
FACT_CHECK_FUNCTION = os.environ.get('FACT_CHECK_FUNCTION')
CONTEXT_ENRICHMENT_FUNCTION = os.environ.get('CONTEXT_ENRICHMENT_FUNCTION')
COMPLIANCE_CHECK_FUNCTION = os.environ.get('COMPLIANCE_CHECK_FUNCTION')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')

def lambda_handler(event, context):
    """
    Optimized Lambda handler for enhancing AI responses with parallel processing
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

        logger.info(f"Processing OPTIMIZED enhancement request {request_id} for content length: {len(content)}")

        # Use asyncio for parallel processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                process_enhancement_async(content, request_id, fact_check, add_context, enrichment_level)
            )
        finally:
            loop.close()

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Store enhancement history
        enhancement_record = {
            'id': request_id,
            'timestamp': start_time.isoformat(),
            'original_content_length': len(content),
            'enhanced_content_length': len(result.get('enhanced_content', '')),
            'fact_checks_count': len(result.get('fact_checks', [])),
            'context_additions_count': len(result.get('context_additions', [])),
            'compliance_flags_count': len(result.get('compliance_flags', [])),
            'quality_score': result.get('quality_score', 0.75),
            'processing_time_ms': processing_time,
            'enrichment_level': enrichment_level,
            'optimization_enabled': True  # Flag to track optimized processing
        }
        
        store_enhancement_history(enhancement_record)

        # Add processing metrics to response
        optimizer = get_optimizer()
        performance_metrics = optimizer.get_performance_metrics()
        
        result.update({
            'processing_time_ms': int(processing_time),
            'request_id': request_id,
            'performance_metrics': performance_metrics,
            'optimization_enabled': True
        })

        logger.info(f"OPTIMIZED processing completed in {processing_time:.1f}ms with {performance_metrics.get('cache_hit_rate', 0):.1%} cache hit rate")

        return create_success_response(result)

    except Exception as e:
        logger.error(f"Optimized enhancement failed: {str(e)}")
        return create_error_response(500, f"Enhancement failed: {str(e)}")


async def process_enhancement_async(content: str, request_id: str, fact_check: bool, 
                                  add_context: bool, enrichment_level: str) -> Dict[str, Any]:
    """
    Asynchronous processing pipeline with parallel execution
    """
    optimizer = get_optimizer()
    await optimizer.initialize_session()
    
    try:
        # Prepare parallel tasks
        tasks = []
        
        # Fact checking task
        if fact_check:
            tasks.append({
                'type': 'fact_check',
                'function_name': FACT_CHECK_FUNCTION,
                'payload': {
                    'content': content,
                    'request_id': request_id,
                    'use_llm': True  # Enable LLM for better accuracy
                }
            })

        # Context enrichment task
        if add_context:
            tasks.append({
                'type': 'context',
                'function_name': CONTEXT_ENRICHMENT_FUNCTION,
                'payload': {
                    'content': content,
                    'enrichment_level': enrichment_level,
                    'request_id': request_id
                }
            })

        # Compliance checking task
        tasks.append({
            'type': 'compliance',
            'function_name': COMPLIANCE_CHECK_FUNCTION,
            'payload': {
                'content': content,
                'request_id': request_id
            }
        })

        # Execute all microservices in parallel
        logger.info(f"Executing {len(tasks)} tasks in parallel")
        parallel_start = datetime.now()
        
        results = await optimizer.parallel_lambda_invoke(tasks)
        
        parallel_time = (datetime.now() - parallel_start).total_seconds() * 1000
        logger.info(f"Parallel execution completed in {parallel_time:.1f}ms")

        # Process results
        fact_checks = []
        context_additions = []
        compliance_flags = []

        if 'fact_check' in results and 'fact_checks' in results['fact_check']:
            fact_checks = results['fact_check']['fact_checks']

        if 'context' in results and 'context_additions' in results['context']:
            context_additions = results['context']['context_additions']

        if 'compliance' in results and 'compliance_flags' in results['compliance']:
            compliance_flags = results['compliance']['compliance_flags']

        # Generate enhanced content in parallel with AI evaluation
        ai_evaluation_task = asyncio.create_task(
            get_ai_evaluation_async(content, fact_checks, context_additions, compliance_flags, request_id)
        )
        
        enhanced_content_task = asyncio.create_task(
            generate_enhanced_content_async(content, fact_checks, context_additions, compliance_flags)
        )
        
        # Wait for both tasks to complete
        ai_evaluation, enhanced_content = await asyncio.gather(
            ai_evaluation_task,
            enhanced_content_task,
            return_exceptions=True
        )

        # Handle exceptions in parallel tasks
        if isinstance(ai_evaluation, Exception):
            logger.warning(f"AI evaluation failed: {str(ai_evaluation)}")
            ai_evaluation = None
            
        if isinstance(enhanced_content, Exception):
            logger.error(f"Content generation failed: {str(enhanced_content)}")
            enhanced_content = content  # Fallback to original content

        # Calculate quality score (enhanced with AI if available)
        quality_score = calculate_optimized_quality_score(
            fact_checks, context_additions, compliance_flags, ai_evaluation
        )

        return {
            'original_content': content,
            'enhanced_content': enhanced_content,
            'fact_checks': fact_checks,
            'context_additions': context_additions,
            'quality_score': quality_score,
            'compliance_flags': compliance_flags,
            'ai_evaluation': ai_evaluation
        }
        
    finally:
        await optimizer.close_session()


@async_cached(ttl=300)  # Cache AI evaluations for 5 minutes
async def get_ai_evaluation_async(content: str, fact_checks: List[Dict], 
                                context_additions: List[Dict], compliance_flags: List[str], 
                                request_id: str) -> Dict[str, Any]:
    """
    Get AI evaluation asynchronously with caching
    """
    try:
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
        
        logger.info("AI evaluation completed successfully (async)")
        return ai_evaluation
        
    except Exception as e:
        logger.warning(f"AI evaluation failed: {str(e)}")
        return None


async def generate_enhanced_content_async(content: str, fact_checks: List[Dict], 
                                        context_additions: List[Dict], compliance_flags: List[str]) -> str:
    """
    Generate enhanced content asynchronously
    """
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


def calculate_optimized_quality_score(fact_checks: List[Dict], context_additions: List[Dict], 
                                    compliance_flags: List[str], ai_evaluation: Dict = None) -> float:
    """
    Calculate quality score with AI enhancement and optimization
    """
    # Use AI evaluation score if available
    if ai_evaluation and 'overall_score' in ai_evaluation:
        ai_score = ai_evaluation['overall_score']
        logger.info(f"Using AI-enhanced quality score: {ai_score:.3f}")
        return ai_score
    
    # Fallback to enhanced algorithm
    base_score = 0.85
    
    # Fact check scoring
    fact_check_score = 0.0
    if fact_checks:
        verified_count = sum(1 for fc in fact_checks if fc.get('verified', False))
        total_confidence = sum(fc.get('confidence', 0.5) for fc in fact_checks)
        avg_confidence = total_confidence / len(fact_checks) if fact_checks else 0.5
        
        verified_ratio = verified_count / len(fact_checks)
        fact_check_score = 0.15 * (verified_ratio * 0.7 + avg_confidence * 0.3)
    
    # Context enrichment bonus
    context_bonus = min(0.1, len(context_additions) * 0.02)
    
    # Compliance scoring with severity levels
    compliance_score = 0.0
    if compliance_flags:
        high_severity = sum(1 for flag in compliance_flags if 'high' in flag.lower() or 'severe' in flag.lower())
        medium_severity = sum(1 for flag in compliance_flags if 'medium' in flag.lower())
        low_severity = len(compliance_flags) - high_severity - medium_severity
        
        compliance_penalty = (high_severity * 0.15) + (medium_severity * 0.08) + (low_severity * 0.03)
        compliance_score = -min(0.3, compliance_penalty)
    
    # Content analysis bonus
    content_bonus = 0.02
    
    # Calculate final score
    final_score = base_score + fact_check_score + context_bonus + compliance_score + content_bonus
    final_score = max(0.4, min(1.0, final_score))
    
    logger.info(f"Optimized quality score: {final_score:.3f} (Base: {base_score:.2f}, Facts: {fact_check_score:.2f}, Context: {context_bonus:.2f}, Compliance: {compliance_score:.2f})")
    
    return round(final_score, 3)


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


def enhance_financial_claim_optimized(claim: str) -> Dict[str, Any]:
    """
    Optimized standalone function to enhance a single financial claim
    Uses the new parallel processing pipeline
    """
    try:
        event = {
            'ai_response': {
                'content': claim,
            },
            'fact_check': True,
            'add_context': True,
            'enrichment_level': 'standard'
        }
        
        class MockContext:
            aws_request_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        return lambda_handler(event, MockContext())
        
    except Exception as e:
        logger.error(f"Optimized claim enhancement failed: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e)
        }
