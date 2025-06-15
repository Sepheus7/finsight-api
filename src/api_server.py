#!/usr/bin/env python3
"""
FinSight API Server
Simple HTTP server for testing the streamlined frontend
"""

import asyncio
import sys
import os
import logging
import time
from aiohttp import web, web_response
import json
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import traceback
import re
from pathlib import Path

# Load environment variables from .env.local if it exists
if os.path.exists('.env.local'):
    load_dotenv('.env.local')
    print("Loaded environment variables from .env.local")
elif os.path.exists('.env'):
    load_dotenv('.env')
    print("Loaded environment variables from .env")

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from models.enrichment_models import EnrichmentRequest
from handlers.financial_enrichment_handler import FinancialEnrichmentHandler
from handlers.financial_enrichment_handler import lambda_handler as enrichment_lambda_handler
from handlers.simple_fact_check_handler import lambda_handler as fact_check_lambda_handler
from handlers.compliance_handler import lambda_handler as compliance_lambda_handler
from handlers.enhanced_fact_check_handler_optimized import OptimizedFinancialFactChecker
from handlers.compliance_handler import ComplianceChecker
from handlers.rag_handler import FinancialRAGHandler

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the handlers
try:
    enrichment_handler = FinancialEnrichmentHandler()
    fact_checker = OptimizedFinancialFactChecker(use_llm=True)
    compliance_checker = ComplianceChecker()
    rag_handler = FinancialRAGHandler()
    logger.info("✅ All handlers initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize handlers: {e}")
    enrichment_handler = None
    fact_checker = None
    compliance_checker = None
    rag_handler = None

# Initialize chat handler with error handling
try:
    from handlers.chat_handler import FinSightChatHandler
    chat_handler = FinSightChatHandler()
    logger.info("✅ Chat handler initialized successfully")
except Exception as e:
    logger.warning(f"⚠️ Chat handler initialization failed: {e}")
    chat_handler = None

# Initialize Bedrock Router Agent with error handling
try:
    from handlers.bedrock_router_agent import BedrockRouterAgent
    router_agent = BedrockRouterAgent()
    logger.info("✅ Bedrock Router Agent initialized successfully")
except Exception as e:
    logger.warning(f"⚠️ Bedrock Router Agent initialization failed: {e}")
    router_agent = None

async def health_check(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "handlers": {
            "enrichment": enrichment_handler is not None,
            "fact_checker": fact_checker is not None,
            "compliance": compliance_checker is not None,
            "rag": rag_handler is not None,
            "chat": chat_handler is not None,
            "router_agent": router_agent is not None
        }
    })

async def enrich_content(request):
    """Financial enrichment endpoint"""
    try:
        if not enrichment_handler:
            return web.json_response({
                "error": "Enrichment functionality is not available. Please check server configuration.",
                "timestamp": datetime.now().isoformat()
            }, status=503)
        
        # Parse request data
        data = await request.json()
        logger.info(f"Received enrichment request: {data.get('content', '')[:100]}...")
        
        # Create enrichment request
        enrich_request = EnrichmentRequest(
            content=data.get('content', ''),
            enrichment_types=data.get('enrichment_types', ['stock_data', 'market_context']),
            format_style=data.get('format_style', 'enhanced'),
            include_compliance=data.get('include_compliance', False)
        )
        
        # Process enrichment
        start_time = datetime.now()
        response = await enrichment_handler.enrich_content(enrich_request)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Convert to JSON response
        result = {
            "enriched_content": response.enriched_content,
            "data_points": [dp.to_dict() for dp in response.data_points],
            "claims": [claim.to_dict() for claim in response.claims],
            "data_sources": response.data_sources,
            "compliance_warnings": response.compliance_warnings,
            "metrics": {
                "processing_time_ms": processing_time,
                "claims_processed": response.metrics.claims_processed,
                "data_sources_used": response.metrics.data_sources_used,
                "cache_hit_rate": response.metrics.cache_hit_rate
            },
            "timestamp": response.timestamp.isoformat()
        }
        
        logger.info(f"Enrichment completed in {processing_time:.2f}ms")
        return web.json_response(result)
        
    except Exception as e:
        logger.error(f"Enrichment failed: {str(e)}")
        return web.json_response({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=500)

async def fact_check_content(request):
    """Enhanced fact check endpoint"""
    try:
        # Parse request data
        data = await request.json()
        logger.info(f"Received fact-check request: {data.get('content', '')[:100]}...")
        
        # Create mock Lambda event
        event = {
            'body': json.dumps({
                'content': data.get('content', ''),
                'use_llm': data.get('use_llm', True),
                'include_context': data.get('include_context', True),
                'confidence_threshold': data.get('confidence_threshold', 0.8)
            })
        }
        
        # Create mock context
        class MockContext:
            def __init__(self):
                self.function_name = 'enhanced-fact-check-handler'
                self.function_version = '1.0'
                self.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:enhanced-fact-check-handler'
                self.memory_limit_in_mb = '512'
                self.remaining_time_in_millis = lambda: 30000
                self.log_group_name = '/aws/lambda/enhanced-fact-check-handler'
                self.log_stream_name = '2025/06/13/[$LATEST]test'
                self.aws_request_id = 'test-request-id'
        
        context = MockContext()
        
        # Process fact check
        start_time = datetime.now()
        response = await fact_check_lambda_handler(event, context)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Parse response if it's a Lambda response format
        if isinstance(response, dict) and 'body' in response:
            result = json.loads(response['body'])
        else:
            result = response
        
        # Add processing time
        if isinstance(result, dict):
            result['processing_time_ms'] = processing_time
        
        logger.info(f"Fact check completed in {processing_time:.2f}ms")
        return web.json_response(result)
        
    except Exception as e:
        logger.error(f"Fact check failed: {str(e)}")
        return web.json_response({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=500)

async def check_compliance(request):
    """Compliance analysis endpoint"""
    try:
        # Parse request data
        data = await request.json()
        logger.info(f"Received compliance request: {data.get('content', '')[:100]}...")
        
        # Create mock Lambda event
        event = {
            'body': json.dumps({
                'content': data.get('content', ''),
                'check_types': data.get('check_types', ['investment_advice', 'guarantees', 'disclaimers'])
            })
        }
        
        # Create mock context
        class MockContext:
            def __init__(self):
                self.function_name = 'compliance-handler'
                self.function_version = '1.0'
                self.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:compliance-handler'
                self.memory_limit_in_mb = '512'
                self.remaining_time_in_millis = lambda: 30000
                self.log_group_name = '/aws/lambda/compliance-handler'
                self.log_stream_name = '2025/06/13/[$LATEST]test'
                self.aws_request_id = 'test-request-id'
        
        context = MockContext()
        
        # Process compliance check
        start_time = datetime.now()
        response = compliance_lambda_handler(event, context)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Parse response if it's a Lambda response format
        if isinstance(response, dict) and 'body' in response:
            result = json.loads(response['body'])
        else:
            result = response
        
        # Add processing time
        if isinstance(result, dict):
            result['processing_time_ms'] = processing_time
        
        logger.info(f"Compliance check completed in {processing_time:.2f}ms")
        return web.json_response(result)
        
    except Exception as e:
        logger.error(f"Compliance check failed: {str(e)}")
        return web.json_response({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=500)

async def chat_endpoint(request):
    """AI Chat endpoint powered by Bedrock"""
    try:
        if not chat_handler:
            return web.json_response({
                "error": "Chat functionality is not available. Please check server configuration.",
                "timestamp": datetime.now().isoformat()
            }, status=503)
        
        # Parse request data
        data = await request.json()
        message = data.get('message', '').strip()
        
        if not message:
            return web.json_response({
                "error": "Message is required",
                "timestamp": datetime.now().isoformat()
            }, status=400)
        
        logger.info(f"Received chat message: {message[:100]}...")
        
        # Extract optional parameters
        chat_id = data.get('chat_id')
        context = data.get('context', [])
        
        # Process chat message
        start_time = datetime.now()
        response = await chat_handler.process_chat_message(
            message=message,
            chat_id=chat_id,
            context=context
        )
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Add processing time to response
        response['processing_time_ms'] = processing_time
        
        logger.info(f"Chat message processed in {processing_time:.2f}ms")
        return web.json_response(response)
        
    except Exception as e:
        logger.error(f"Chat endpoint failed: {str(e)}")
        return web.json_response({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=500)

async def route_query_endpoint(request):
    """Bedrock Router Agent endpoint for intelligent query routing"""
    try:
        if not router_agent:
            return web.json_response({
                "error": "Bedrock Router Agent is not available. Please check server configuration.",
                "timestamp": datetime.now().isoformat()
            }, status=503)
        
        # Parse request data
        data = await request.json()
        query = data.get('query', '').strip()
        
        if not query:
            return web.json_response({
                "error": "Query is required",
                "timestamp": datetime.now().isoformat()
            }, status=400)
        
        logger.info(f"Received router query: {query[:100]}...")
        
        # Extract optional parameters
        conversation_id = data.get('conversation_id')
        use_function_calling = data.get('use_function_calling', True)
        
        # Process query through router agent
        start_time = datetime.now()
        response = await router_agent.route_query(query)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Add processing time to response if not already present
        if 'routing_metadata' in response and 'processing_time_ms' not in response['routing_metadata']:
            response['routing_metadata']['processing_time_ms'] = processing_time
        
        logger.info(f"Router query processed in {processing_time:.2f}ms")
        return web.json_response(response)
        
    except Exception as e:
        logger.error(f"Router endpoint failed: {str(e)}")
        return web.json_response({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=500)

async def get_system_status(request):
    """Get system status and performance metrics"""
    try:
        # Get cache statistics
        from utils.cache_manager import CacheManager
        cache_manager = CacheManager()
        cache_info = await cache_manager.get_cache_info()
        
        return web.json_response({
            "status": "operational",
            "cache_statistics": cache_info,
            "uptime": "running",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return web.json_response({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=500)

async def get_config(request):
    """Get frontend configuration including AWS credentials"""
    try:
        # Load environment variables
        config = {
            "aws": {
                "region": os.getenv('AWS_REGION', 'us-east-1'),
                "accessKeyId": os.getenv('AWS_ACCESS_KEY_ID'),
                "secretAccessKey": os.getenv('AWS_SECRET_ACCESS_KEY')
            },
            "api": {
                "baseUrl": f"http://localhost:{os.getenv('PORT', 8000)}"
            },
            "features": {
                "chatEnabled": chat_handler is not None,
                "bedrockEnabled": bool(os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'))
            }
        }
        
        # Only include AWS credentials if they exist
        if not config["aws"]["accessKeyId"] or not config["aws"]["secretAccessKey"]:
            config["aws"] = {"region": config["aws"]["region"]}
        
        return web.json_response(config)
        
    except Exception as e:
        logger.error(f"Config endpoint failed: {str(e)}")
        return web.json_response({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=500)

async def cors_handler(request):
    """Handle CORS preflight requests"""
    return web.Response(
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        }
    )

async def rag_endpoint(request):
    """Unified RAG endpoint with Bedrock Router orchestration"""
    try:
        data = await request.json()
        query = data.get('query', '')
        
        if not query:
            return web.json_response({'error': 'Query is required'}, status=400)
        
        logger.info(f"Received RAG query: {query[:50]}...")
        
        # Use Bedrock Router for intelligent orchestration
        from handlers.bedrock_router_agent import BedrockRouterAgent
        router = BedrockRouterAgent()
        
        response = await router.route_query(query)
        
        logger.info(f"RAG query processed in {response.get('routing_metadata', {}).get('processing_time_ms', 0):.2f}ms")
        return web.json_response(response)
        
    except Exception as e:
        logger.error(f"RAG endpoint error: {str(e)}")
        return web.json_response({'error': str(e)}, status=500)

async def rag_smart_endpoint(request):
    """Legacy endpoint - redirects to unified RAG endpoint"""
    return await rag_endpoint(request)

async def _parse_response_to_structured_data(response_data: str, query: str) -> dict:
    """Parse router response into structured data format"""
    try:
        # Try to extract structured data based on query type
        query_lower = query.lower()
        
        if 'stock' in query_lower or 'price' in query_lower:
            # Extract stock data - look for common stock symbols (1-5 uppercase letters)
            # Exclude common words like WHAT, THE, etc.
            excluded_words = {'WHAT', 'THE', 'IS', 'ARE', 'AND', 'OR', 'BUT', 'FOR', 'WITH', 'FROM', 'TO', 'OF', 'IN', 'ON', 'AT', 'BY'}
            
            # Find all potential symbols (1-5 uppercase letters)
            potential_symbols = re.findall(r'\b([A-Z]{1,5})\b', query.upper())
            
            # Filter out excluded words and pick the first valid symbol
            symbol = 'UNKNOWN'
            for potential in potential_symbols:
                if potential not in excluded_words:
                    symbol = potential
                    break
            
            # Look for price in response
            price_match = re.search(r'\$?(\d+\.?\d*)', response_data)
            price = float(price_match.group(1)) if price_match else 0.0
            
            return {
                'symbol': symbol,
                'price': price,
                'currency': 'USD',
                'timestamp': datetime.now().isoformat() + 'Z'
            }
            
        elif 'unemployment' in query_lower or 'employment' in query_lower:
            # Check if the response indicates data unavailability
            unavailable_indicators = [
                'unavailable', 'not available', 'unable to provide', 'api limitations',
                'data is currently unavailable', 'real-time data is currently unavailable'
            ]
            
            if any(indicator in response_data.lower() for indicator in unavailable_indicators):
                return {
                    'indicator': 'employment_rate' if 'employment' in query_lower else 'unemployment_rate',
                    'status': 'unavailable',
                    'message': 'Real-time data currently unavailable',
                    'timestamp': datetime.now().isoformat() + 'Z'
                }
            
            # Extract employment data only if we have actual numeric data
            rate_match = re.search(r'(\d+\.?\d*)%?', response_data)
            if rate_match:
                rate = float(rate_match.group(1))
                return {
                    'indicator': 'employment_rate' if 'employment' in query_lower else 'unemployment_rate',
                    'value': rate,
                    'unit': 'percent',
                    'timestamp': datetime.now().isoformat() + 'Z'
                }
            else:
                # No numeric data found, but no explicit unavailability message either
                return {
                    'indicator': 'employment_rate' if 'employment' in query_lower else 'unemployment_rate',
                    'status': 'no_data_found',
                    'message': 'No numeric data found in response',
                    'raw_response': response_data,
                    'timestamp': datetime.now().isoformat() + 'Z'
                }
            
        elif 'inflation' in query_lower:
            # Check if the response indicates data unavailability
            unavailable_indicators = [
                'unavailable', 'not available', 'unable to provide', 'api limitations',
                'data is currently unavailable', 'real-time data is currently unavailable'
            ]
            
            if any(indicator in response_data.lower() for indicator in unavailable_indicators):
                return {
                    'indicator': 'inflation_rate',
                    'status': 'unavailable',
                    'message': 'Real-time data currently unavailable',
                    'timestamp': datetime.now().isoformat() + 'Z'
                }
            
            # Extract inflation data only if we have actual numeric data
            rate_match = re.search(r'(\d+\.?\d*)%?', response_data)
            if rate_match:
                rate = float(rate_match.group(1))
                return {
                    'indicator': 'inflation_rate',
                    'value': rate,
                    'unit': 'percent',
                    'timestamp': datetime.now().isoformat() + 'Z'
                }
            else:
                # No numeric data found, but no explicit unavailability message either
                return {
                    'indicator': 'inflation_rate',
                    'status': 'no_data_found',
                    'message': 'No numeric data found in response',
                    'raw_response': response_data,
                    'timestamp': datetime.now().isoformat() + 'Z'
                }
            
        else:
            # Generic response
            return {
                'response': response_data,
                'timestamp': datetime.now().isoformat() + 'Z'
            }
            
    except Exception as e:
        logger.warning(f"Failed to parse structured data: {e}")
        return {
            'response': response_data,
            'timestamp': datetime.now().isoformat() + 'Z'
        }

def _determine_sources_used(metadata: dict, query: str) -> list:
    """Determine which data sources were used based on metadata and query"""
    sources = []
    
    # Check for specific data source indicators
    if 'yahoo' in str(metadata).lower() or 'stock' in query.lower():
        sources.append('yahoo_finance')
    
    if 'fred' in str(metadata).lower() or any(term in query.lower() for term in ['unemployment', 'inflation', 'gdp']):
        sources.append('fred_api')
    
    if 'web_search' in str(metadata).lower():
        sources.append('web_search')
    
    # Default fallback
    if not sources:
        sources.append('internal_processing')
    
    return sources

def create_app():
    """Create the web application"""
    app = web.Application()
    
    # Add CORS middleware
    @web.middleware
    async def cors_middleware(request, handler):
        if request.method == 'OPTIONS':
            return await cors_handler(request)
        
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    app = web.Application(middlewares=[cors_middleware])
    
    # Add routes
    app.router.add_get('/health', health_check)
    app.router.add_post('/enrich', enrich_content)
    app.router.add_post('/fact-check', fact_check_content)
    app.router.add_post('/compliance', check_compliance)
    app.router.add_post('/chat', chat_endpoint)
    app.router.add_post('/route-query', route_query_endpoint)
    app.router.add_get('/status', get_system_status)
    app.router.add_get('/config', get_config)
    app.router.add_post('/rag', rag_endpoint)
    app.router.add_post('/rag-smart', rag_smart_endpoint)
    app.router.add_options('/{path:.*}', cors_handler)

    # Serve enhanced interface at root
    async def index(request):
        return web.FileResponse('frontend/src/main-simple.html')
    app.router.add_get('/', index)
    
    # Serve chat interface
    async def chat_ui(request):
        return web.FileResponse('frontend/src/chat.html')
    app.router.add_get('/chat-ui', chat_ui)
    
    # Serve API showcase
    async def api_showcase(request):
        return web.FileResponse('frontend/src/api-showcase.html')
    app.router.add_get('/api-showcase', api_showcase)

    # Serve static files (frontend)
    app.router.add_static('/static/', path='frontend/src', name='static')
    
    async def debug_env(request):
        """Debug endpoint to check environment variables (remove in production)"""
        return web.json_response({
            'fred_api_key_set': bool(os.environ.get('FRED_API_KEY')),
            'alpha_vantage_key_set': bool(os.environ.get('ALPHA_VANTAGE_API_KEY')),
            'aws_region': os.environ.get('AWS_REGION', 'not set')
        })
    
    app.router.add_get('/debug-env', debug_env)

    # API v1 endpoints for external AI agents
    async def api_v1_query(request):
        """
        Unified query endpoint for external AI agents
        
        Request:
        {
          "query": "Get AAPL stock price",
          "context": "Building a portfolio analysis"  // optional
        }
        
        Response:
        {
          "data": {
            "symbol": "AAPL",
            "price": 150.25,
            "currency": "USD",
            "timestamp": "2025-06-14T10:30:00Z"
          },
          "sources": ["alpha_vantage"],
          "cached": false
        }
        """
        try:
            data = await request.json()
            query = data.get('query', '')
            context = data.get('context', '')
            
            if not query:
                return web.json_response({
                    'error': 'Query parameter is required'
                }, status=400)
            
            # Route the query through the existing router agent
            if router_agent:
                router_response = await router_agent.route_query(query)
            else:
                return web.json_response({
                    'error': 'Router agent not available'
                }, status=503)
            
            # Extract structured data from the router response
            response_data = router_response.get('response', '')
            metadata = router_response.get('routing_metadata', {})
            
            # Parse the response to extract structured data
            structured_data = await _parse_response_to_structured_data(response_data, query)
            
            # Determine sources used
            sources = _determine_sources_used(metadata, query)
            
            # Check if data was cached
            cached = metadata.get('cached', False)
            
            return web.json_response({
                'data': structured_data,
                'sources': sources,
                'cached': cached,
                'metadata': {
                    'processing_time_ms': metadata.get('processing_time_ms', 0),
                    'timestamp': metadata.get('timestamp', ''),
                    'context': context
                }
            })
            
        except Exception as e:
            logger.error(f"API v1 query error: {e}")
            return web.json_response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=500)

    # Register the API v1 route
    app.router.add_post('/api/v1/query', api_v1_query)

    # MCP Server Control Endpoints
    mcp_server_process = None
    
    async def start_mcp_server(request):
        """Start the MCP server"""
        nonlocal mcp_server_process
        try:
            if mcp_server_process and mcp_server_process.returncode is None:
                return web.json_response({
                    'status': 'already_running',
                    'message': 'MCP server is already running'
                })
            
            # Start MCP server process
            import subprocess
            mcp_server_process = subprocess.Popen(
                ['python', 'mcp_server.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            return web.json_response({
                'status': 'started',
                'message': 'MCP server started successfully',
                'pid': mcp_server_process.pid
            })
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            return web.json_response({
                'status': 'error',
                'message': f'Failed to start MCP server: {str(e)}'
            }, status=500)
    
    async def stop_mcp_server(request):
        """Stop the MCP server"""
        nonlocal mcp_server_process
        try:
            if not mcp_server_process or mcp_server_process.returncode is not None:
                return web.json_response({
                    'status': 'not_running',
                    'message': 'MCP server is not running'
                })
            
            mcp_server_process.terminate()
            mcp_server_process.wait(timeout=5)
            mcp_server_process = None
            
            return web.json_response({
                'status': 'stopped',
                'message': 'MCP server stopped successfully'
            })
            
        except Exception as e:
            logger.error(f"Failed to stop MCP server: {e}")
            return web.json_response({
                'status': 'error',
                'message': f'Failed to stop MCP server: {str(e)}'
            }, status=500)
    
    async def mcp_server_status(request):
        """Get MCP server status"""
        nonlocal mcp_server_process
        try:
            if mcp_server_process and mcp_server_process.returncode is None:
                return web.json_response({
                    'status': 'running',
                    'pid': mcp_server_process.pid,
                    'message': 'MCP server is running'
                })
            else:
                return web.json_response({
                    'status': 'stopped',
                    'message': 'MCP server is not running'
                })
                
        except Exception as e:
            logger.error(f"Failed to get MCP server status: {e}")
            return web.json_response({
                'status': 'error',
                'message': f'Failed to get status: {str(e)}'
            }, status=500)
    
    async def test_mcp_tool(request):
        """Test an MCP tool by calling the underlying API"""
        try:
            data = await request.json()
            tool = data.get('tool', '')
            args = data.get('args', {})
            
            if not tool:
                return web.json_response({
                    'error': 'Tool parameter is required'
                }, status=400)
            
            # Map MCP tool calls to API queries
            query_mapping = {
                'get_stock_price': lambda args: f"What is {args.get('symbol', 'AAPL')} stock price?",
                'get_economic_data': lambda args: f"What is the US {args.get('indicator', 'unemployment')} rate?",
                'get_company_info': lambda args: f"What is {args.get('symbol', 'MSFT')} company information and market cap?",
                'analyze_market': lambda args: args.get('query', 'What is the current market sentiment?')
            }
            
            if tool not in query_mapping:
                return web.json_response({
                    'error': f'Unknown tool: {tool}'
                }, status=400)
            
            # Generate query from tool and args
            query = query_mapping[tool](args)
            
            # Call the main API
            if router_agent:
                router_response = await router_agent.route_query(query)
                response_data = router_response.get('response', '')
                metadata = router_response.get('routing_metadata', {})
                structured_data = await _parse_response_to_structured_data(response_data, query)
                sources = _determine_sources_used(metadata, query)
                
                # Format as MCP response
                mcp_response = {
                    'jsonrpc': '2.0',
                    'id': f'test-{int(time.time() * 1000)}',
                    'result': {
                        'content': [
                            {
                                'type': 'text',
                                'text': json.dumps({
                                    'data': structured_data,
                                    'sources': sources,
                                    'metadata': metadata
                                }, indent=2)
                            }
                        ]
                    }
                }
                
                return web.json_response(mcp_response)
            else:
                return web.json_response({
                    'jsonrpc': '2.0',
                    'id': f'test-{int(time.time() * 1000)}',
                    'error': {
                        'code': -32603,
                        'message': 'Router agent not available'
                    }
                })
                
        except Exception as e:
            logger.error(f"MCP tool test error: {e}")
            return web.json_response({
                'jsonrpc': '2.0',
                'id': f'test-{int(time.time() * 1000)}',
                'error': {
                    'code': -32603,
                    'message': f'Tool execution failed: {str(e)}'
                }
            })
    
    # Register MCP endpoints
    app.router.add_post('/api/v1/mcp/start', start_mcp_server)
    app.router.add_post('/api/v1/mcp/stop', stop_mcp_server)
    app.router.add_get('/api/v1/mcp/status', mcp_server_status)
    app.router.add_post('/api/v1/mcp/test', test_mcp_tool)

    return app

async def main():
    """Start the server"""
    app = create_app()
    
    # Start the server
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    
    logger.info(f"🚀 Starting FinSight API Server on {host}:{port}")
    logger.info(f"🌐 Frontend available at: http://localhost:{port}/")
    logger.info(f"📊 Health check: http://localhost:{port}/health")
    logger.info(f"🔧 System status: http://localhost:{port}/status")
    logger.info(f"💰 Enrichment: http://localhost:{port}/enrich")
    logger.info(f"🔍 Fact Check: http://localhost:{port}/fact-check")
    logger.info(f"⚖️ Compliance: http://localhost:{port}/compliance")
    if chat_handler:
        logger.info(f"💬 AI Chat: http://localhost:{port}/chat")
        logger.info(f"🤖 Chat Interface: http://localhost:{port}/chat-ui")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    logger.info("✅ Server started successfully!")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down server...")
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
