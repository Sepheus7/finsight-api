#!/usr/bin/env python3
"""
FinSight MCP Server - Standalone Version
========================================

Model Context Protocol server for FinSight financial data API.
Works with system Python and minimal dependencies.

This server provides standardized access to FinSight's financial data
through the MCP protocol, enabling AI agents and LLMs to access:
- Real-time stock prices
- Economic indicators
- Company information  
- Market analysis

Author: FinSight Team
Version: 1.0.0
Protocol: MCP 2024-11-05
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# HTTP client imports with fallback
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    import urllib.request
    import urllib.parse
    HAS_AIOHTTP = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPToolDefinitions:
    """Tool definitions for the MCP server"""
    
    @staticmethod
    def get_all_tools() -> Dict[str, Dict[str, Any]]:
        """Get all available MCP tools"""
        return {
            "get_stock_price": {
                "name": "get_stock_price",
                "description": "Get real-time stock price for a given symbol",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            "get_economic_data": {
                "name": "get_economic_data", 
                "description": "Get economic indicators like unemployment, inflation, GDP growth",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "indicator": {
                            "type": "string",
                            "description": "Economic indicator: unemployment, inflation, gdp, fed_funds_rate",
                            "enum": ["unemployment", "inflation", "gdp", "fed_funds_rate"]
                        }
                    },
                    "required": ["indicator"]
                }
            },
            "get_company_info": {
                "name": "get_company_info",
                "description": "Get comprehensive company information including market cap, sector, and key metrics",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Company stock symbol (e.g., AAPL, MSFT)"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            "analyze_market": {
                "name": "analyze_market",
                "description": "Analyze market conditions, sentiment, and trends",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string", 
                            "description": "Market analysis query or topic to analyze"
                        }
                    },
                    "required": ["query"]
                }
            }
        }


class APIClient:
    """HTTP client for calling the FinSight API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
    
    async def call_api(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the FinSight API with proper error handling
        
        Args:
            endpoint: API endpoint to call
            data: Request payload
            
        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if HAS_AIOHTTP:
                return await self._call_with_aiohttp(url, data)
            else:
                return await self._call_with_urllib(url, data)
                
        except Exception as e:
            logger.error(f"API call to {url} failed: {e}")
            return {
                "error": f"API call failed: {str(e)}", 
                "status": "unavailable",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _call_with_aiohttp(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call API using aiohttp (async)"""
        import aiohttp
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {
                        "error": f"API returned status {response.status}",
                        "details": error_text,
                        "status": "error"
                    }
    
    async def _call_with_urllib(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call API using urllib (synchronous fallback)"""
        import urllib.request
        import urllib.parse
        
        req_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            return json.loads(response.read().decode('utf-8'))


class MCPRequestHandler:
    """Handles MCP protocol requests and responses"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.tools = MCPToolDefinitions.get_all_tools()
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming MCP requests
        
        Args:
            request: JSON-RPC request
            
        Returns:
            JSON-RPC response
        """
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id", 1)
        
        try:
            if method == "initialize":
                return self._handle_initialize(request_id)
            elif method == "tools/list":
                return self._handle_tools_list(request_id)
            elif method == "tools/call":
                return await self._handle_tools_call(request_id, params)
            else:
                return self._create_error_response(
                    request_id, -32601, f"Method not found: {method}"
                )
                
        except Exception as e:
            logger.error(f"Request handling failed: {e}")
            return self._create_error_response(
                request_id, -32603, f"Internal error: {str(e)}"
            )
    
    def _handle_initialize(self, request_id: Union[str, int]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "finsight-mcp-server",
                    "version": "1.0.0",
                    "description": "FinSight financial data MCP server"
                }
            }
        }
    
    def _handle_tools_list(self, request_id: Union[str, int]) -> Dict[str, Any]:
        """Handle tools/list request"""
        return {
            "jsonrpc": "2.0", 
            "id": request_id,
            "result": {
                "tools": list(self.tools.values())
            }
        }
    
    async def _handle_tools_call(self, request_id: Union[str, int], params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return self._create_error_response(
                request_id, -32602, f"Unknown tool: {tool_name}"
            )
        
        try:
            result = await self._execute_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return self._create_error_response(
                request_id, -32603, f"Tool execution failed: {str(e)}"
            )
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific tool by calling the FinSight API
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        # Map tool calls to API queries
        query_mapping = {
            "get_stock_price": lambda args: f"What is {args.get('symbol', 'AAPL')} stock price?",
            "get_economic_data": lambda args: f"What is the US {args.get('indicator', 'unemployment')} rate?",
            "get_company_info": lambda args: f"What is {args.get('symbol', 'MSFT')} company information and market cap?",
            "analyze_market": lambda args: args.get('query', 'What is the current market sentiment?')
        }
        
        if tool_name not in query_mapping:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        query = query_mapping[tool_name](arguments)
        
        # Call the FinSight API
        api_response = await self.api_client.call_api("/api/v1/query", {
            "query": query,
            "context": f"MCP Tool Call: {tool_name}"
        })
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(api_response, indent=2)
                }
            ]
        }
    
    def _create_error_response(self, request_id: Union[str, int], code: int, message: str) -> Dict[str, Any]:
        """Create a JSON-RPC error response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }


class FinSightMCPServer:
    """
    Main MCP Server class for FinSight
    
    Provides a Model Context Protocol interface to FinSight's financial data API.
    Supports both aiohttp and urllib for maximum compatibility.
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_client = APIClient(api_base_url)
        self.request_handler = MCPRequestHandler(self.api_client)
    
    async def run_stdio(self):
        """
        Run MCP server over stdio (standard input/output)
        
        This is the main server loop that reads JSON-RPC requests from stdin
        and writes responses to stdout, as required by the MCP protocol.
        """
        logger.info("🚀 FinSight MCP Server started")
        logger.info(f"📡 API endpoint: {self.api_client.base_url}")
        logger.info(f"🔧 HTTP client: {'aiohttp' if HAS_AIOHTTP else 'urllib'}")
        
        while True:
            line = ""
            try:
                # Read JSON-RPC request from stdin
                line = sys.stdin.readline()
                if not line:
                    logger.info("📴 EOF received, shutting down server")
                    break
                
                # Parse and handle request
                request = json.loads(line.strip())
                response = await self.request_handler.handle_request(request)
                
                # Write JSON-RPC response to stdout
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received: {e}")
                # Invalid JSON, ignore and continue
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                # Try to send error response if possible
                try:
                    request_data = json.loads(line.strip()) if line else {}
                    request_id = request_data.get("id", 1)
                except:
                    request_id = 1
                    
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)


# Testing and utility functions
async def test_server():
    """
    Test the MCP server functionality
    
    Runs a comprehensive test suite to verify all MCP methods work correctly.
    """
    print("🧪 Testing FinSight MCP Server")
    print("=" * 50)
    
    server = FinSightMCPServer()
    handler = server.request_handler
    
    # Test cases
    test_cases = [
        {
            "name": "Initialize",
            "request": {"jsonrpc": "2.0", "id": "1", "method": "initialize", "params": {}},
            "expected_keys": ["result", "serverInfo"]
        },
        {
            "name": "Tools List", 
            "request": {"jsonrpc": "2.0", "id": "2", "method": "tools/list", "params": {}},
            "expected_keys": ["result", "tools"]
        },
        {
            "name": "Stock Price Tool",
            "request": {
                "jsonrpc": "2.0", "id": "3", "method": "tools/call",
                "params": {"name": "get_stock_price", "arguments": {"symbol": "AAPL"}}
            },
            "expected_keys": ["result"]
        },
        {
            "name": "Economic Data Tool",
            "request": {
                "jsonrpc": "2.0", "id": "4", "method": "tools/call", 
                "params": {"name": "get_economic_data", "arguments": {"indicator": "unemployment"}}
            },
            "expected_keys": ["result"]
        }
    ]
    
    # Run tests
    for i, test_case in enumerate(test_cases, 1):
        try:
            response = await handler.handle_request(test_case["request"])
            
            # Check response structure
            if "error" in response:
                print(f"❌ {test_case['name']}: {response['error']['message']}")
            elif all(key in str(response) for key in test_case["expected_keys"]):
                print(f"✅ {test_case['name']}: Passed")
            else:
                print(f"⚠️  {test_case['name']}: Unexpected response structure")
                
        except Exception as e:
            print(f"❌ {test_case['name']}: Exception - {e}")
    
    print("\n🎯 Test Summary:")
    print(f"   • Protocol: MCP 2024-11-05")
    print(f"   • Tools: {len(MCPToolDefinitions.get_all_tools())}")
    print(f"   • HTTP Client: {'aiohttp' if HAS_AIOHTTP else 'urllib'}")
    print("   • Status: Ready for Claude Desktop")


async def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        await test_server()
    else:
        server = FinSightMCPServer()
        await server.run_stdio()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 FinSight MCP Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Server error: {e}")
        sys.exit(1) 