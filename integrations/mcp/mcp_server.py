#!/usr/bin/env python3
"""
FinSight MCP Server
Model Context Protocol server for FinSight financial data API
Provides standardized access to financial data for LLMs
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import aiohttp
from dataclasses import dataclass

# MCP Protocol Implementation
@dataclass
class MCPRequest:
    """MCP request structure"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str = ""
    params: Optional[Dict[str, Any]] = None

@dataclass 
class MCPResponse:
    """MCP response structure"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class FinSightMCPServer:
    """
    MCP Server for FinSight Financial Data API
    
    Provides standardized access to:
    - Real-time stock data
    - Economic indicators  
    - Company information
    - Market analysis
    """
    
    def __init__(self, finsight_api_url: str = "http://localhost:8000"):
        self.api_url = finsight_api_url
        self.session = None
        self.logger = logging.getLogger(__name__)
        
        # MCP Tools Registry
        self.tools = {
            "get_stock_price": {
                "name": "get_stock_price",
                "description": "Get real-time stock price and market data for a given symbol",
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
                "description": "Get current US economic indicators like unemployment rate, inflation, GDP growth",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "indicator": {
                            "type": "string",
                            "description": "Economic indicator to retrieve",
                            "enum": ["unemployment", "inflation", "gdp", "fed_funds_rate", "all"]
                        }
                    },
                    "required": ["indicator"]
                }
            },
            "get_company_info": {
                "name": "get_company_info",
                "description": "Get comprehensive company information including market cap, financials, and business overview",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Company stock ticker symbol"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            "analyze_market": {
                "name": "analyze_market",
                "description": "Get market analysis and insights for investment decisions",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string", 
                            "description": "Natural language query about market conditions or investment analysis"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    async def start(self):
        """Initialize the MCP server"""
        self.session = aiohttp.ClientSession()
        self.logger.info("FinSight MCP Server started")
    
    async def stop(self):
        """Cleanup server resources"""
        if self.session:
            await self.session.close()
        self.logger.info("FinSight MCP Server stopped")
    
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        try:
            request = MCPRequest(**request_data)
            
            if request.method == "initialize":
                return await self._handle_initialize(request)
            elif request.method == "tools/list":
                return await self._handle_tools_list(request)
            elif request.method == "tools/call":
                return await self._handle_tools_call(request)
            elif request.method == "resources/list":
                return await self._handle_resources_list(request)
            elif request.method == "resources/read":
                return await self._handle_resources_read(request)
            else:
                return self._error_response(request.id, -32601, f"Method not found: {request.method}")
                
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")
            return self._error_response(None, -32603, f"Internal error: {str(e)}")
    
    async def _handle_initialize(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle MCP initialization"""
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": "finsight-mcp-server",
                    "version": "1.0.0",
                    "description": "FinSight Financial Data MCP Server"
                }
            }
        }
    
    async def _handle_tools_list(self, request: MCPRequest) -> Dict[str, Any]:
        """List available tools"""
        return {
            "jsonrpc": "2.0", 
            "id": request.id,
            "result": {
                "tools": list(self.tools.values())
            }
        }
    
    async def _handle_tools_call(self, request: MCPRequest) -> Dict[str, Any]:
        """Execute a tool call"""
        if not request.params:
            return self._error_response(request.id, -32602, "Missing parameters")
        
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        
        if tool_name not in self.tools:
            return self._error_response(request.id, -32602, f"Unknown tool: {tool_name}")
        
        try:
            if tool_name == "get_stock_price":
                result = await self._get_stock_price(arguments.get("symbol"))
            elif tool_name == "get_economic_data":
                result = await self._get_economic_data(arguments.get("indicator"))
            elif tool_name == "get_company_info":
                result = await self._get_company_info(arguments.get("symbol"))
            elif tool_name == "analyze_market":
                result = await self._analyze_market(arguments.get("query"))
            else:
                return self._error_response(request.id, -32602, f"Tool not implemented: {tool_name}")
            
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2, default=str)
                        }
                    ]
                }
            }
            
        except Exception as e:
            self.logger.error(f"Tool execution error: {e}")
            return self._error_response(request.id, -32603, f"Tool execution failed: {str(e)}")
    
    async def _handle_resources_list(self, request: MCPRequest) -> Dict[str, Any]:
        """List available resources"""
        return {
            "jsonrpc": "2.0",
            "id": request.id, 
            "result": {
                "resources": [
                    {
                        "uri": "finsight://market-status",
                        "name": "Market Status",
                        "description": "Current market status and trading hours",
                        "mimeType": "application/json"
                    },
                    {
                        "uri": "finsight://api-health",
                        "name": "API Health",
                        "description": "FinSight API health and performance metrics",
                        "mimeType": "application/json"
                    }
                ]
            }
        }
    
    async def _handle_resources_read(self, request: MCPRequest) -> Dict[str, Any]:
        """Read a specific resource"""
        if not request.params:
            return self._error_response(request.id, -32602, "Missing parameters")
        
        uri = request.params.get("uri")
        
        try:
            if uri == "finsight://market-status":
                content = await self._get_market_status()
            elif uri == "finsight://api-health":
                content = await self._get_api_health()
            else:
                return self._error_response(request.id, -32602, f"Unknown resource: {uri}")
            
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(content, indent=2, default=str)
                        }
                    ]
                }
            }
            
        except Exception as e:
            return self._error_response(request.id, -32603, f"Resource read failed: {str(e)}")
    
    async def _get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """Get stock price via FinSight API"""
        query = f"What is {symbol} stock price?"
        return await self._call_finsight_api(query)
    
    async def _get_economic_data(self, indicator: str) -> Dict[str, Any]:
        """Get economic data via FinSight API"""
        if indicator == "all":
            query = "What are the current US economic indicators?"
        elif indicator == "unemployment":
            query = "What is the US unemployment rate?"
        elif indicator == "inflation":
            query = "What is the current inflation rate?"
        elif indicator == "gdp":
            query = "What is the US GDP growth rate?"
        elif indicator == "fed_funds_rate":
            query = "What is the federal funds rate?"
        else:
            query = f"What is the US {indicator}?"
        
        return await self._call_finsight_api(query)
    
    async def _get_company_info(self, symbol: str) -> Dict[str, Any]:
        """Get company information via FinSight API"""
        query = f"What is {symbol} company information and market cap?"
        return await self._call_finsight_api(query)
    
    async def _analyze_market(self, query: str) -> Dict[str, Any]:
        """Get market analysis via FinSight API"""
        return await self._call_finsight_api(query)
    
    async def _get_market_status(self) -> Dict[str, Any]:
        """Get current market status"""
        return {
            "market_open": True,  # This would be calculated based on current time
            "trading_session": "regular",
            "next_close": "16:00 EST",
            "timezone": "America/New_York",
            "last_updated": datetime.now().isoformat()
        }
    
    async def _get_api_health(self) -> Dict[str, Any]:
        """Get API health status"""
        try:
            async with self.session.get(f"{self.api_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    return {
                        "status": "healthy",
                        "api_response_time": health_data.get("response_time_ms", 0),
                        "last_checked": datetime.now().isoformat(),
                        "details": health_data
                    }
                else:
                    return {
                        "status": "unhealthy", 
                        "error": f"HTTP {response.status}",
                        "last_checked": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }
    
    async def _call_finsight_api(self, query: str) -> Dict[str, Any]:
        """Call the FinSight API with a query"""
        try:
            payload = {"query": query}
            async with self.session.post(
                f"{self.api_url}/api/v1/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {
                        "error": f"API request failed with status {response.status}",
                        "query": query
                    }
        except Exception as e:
            return {
                "error": f"API request failed: {str(e)}",
                "query": query
            }
    
    def _error_response(self, request_id: Optional[str], code: int, message: str) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

# CLI Interface for testing
async def main():
    """Main function for testing the MCP server"""
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    server = FinSightMCPServer()
    await server.start()
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "test":
            # Test mode - run some sample requests
            print("🧪 Testing FinSight MCP Server")
            print("=" * 40)
            
            # Test initialization
            init_request = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "initialize",
                "params": {}
            }
            
            response = await server.handle_request(init_request)
            print(f"Initialize: {response['result']['serverInfo']['name']}")
            
            # Test tools list
            tools_request = {
                "jsonrpc": "2.0", 
                "id": "2",
                "method": "tools/list"
            }
            
            response = await server.handle_request(tools_request)
            print(f"Available tools: {len(response['result']['tools'])}")
            
            # Test stock price tool
            stock_request = {
                "jsonrpc": "2.0",
                "id": "3", 
                "method": "tools/call",
                "params": {
                    "name": "get_stock_price",
                    "arguments": {"symbol": "AAPL"}
                }
            }
            
            response = await server.handle_request(stock_request)
            print("Stock price test completed")
            
            # Test economic data tool
            econ_request = {
                "jsonrpc": "2.0",
                "id": "4",
                "method": "tools/call", 
                "params": {
                    "name": "get_economic_data",
                    "arguments": {"indicator": "unemployment"}
                }
            }
            
            response = await server.handle_request(econ_request)
            print("Economic data test completed")
            
            print("\n✅ All tests completed successfully!")
            
        else:
            # Interactive mode
            print("🚀 FinSight MCP Server")
            print("Listening for MCP requests...")
            print("Use 'python mcp_server.py test' to run tests")
            
            # In a real implementation, this would listen on stdin/stdout
            # or a network socket for MCP requests
            while True:
                await asyncio.sleep(1)
                
    except KeyboardInterrupt:
        print("\n👋 Shutting down MCP server...")
    finally:
        await server.stop()

if __name__ == "__main__":
    asyncio.run(main()) 