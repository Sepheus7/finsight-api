"""
Tool definitions and implementations for the Bedrock FinSight Agent.
This file centralizes all the tools that the agent can use,
including their JSON schemas for the Bedrock API and the
corresponding Python functions to execute them.
"""

import asyncio
from typing import Dict, List, Any

from integrations.data_aggregator import DataAggregator
from utils.web_search import web_search
from models.enrichment_models import StockData

# --- Tool Implementations ---

async def get_stock_data(symbol: str) -> Dict[str, Any]:
    """
    Fetches real-time stock data for a given symbol.
    
    Args:
        symbol: The stock ticker symbol (e.g., "AAPL" for Apple).
        
    Returns:
        A dictionary containing the latest stock data or an error message.
    """
    aggregator = DataAggregator()
    stock_data = await aggregator.get_stock_data(symbol)
    if stock_data:
        return stock_data.to_dict()
    return {"error": f"Could not retrieve stock data for {symbol}."}

async def get_company_info(symbol: str) -> Dict[str, Any]:
    """
    Fetches comprehensive company information for a given stock symbol.
    This includes market cap, P/E ratio, sector, and industry.
    
    Args:
        symbol: The stock ticker symbol (e.g., "MSFT" for Microsoft).
        
    Returns:
        A dictionary containing company information or an error message.
    """
    # Note: This currently uses the same method as get_stock_data.
    # For a real implementation, this could call a different endpoint
    # that returns more detailed company profile information.
    aggregator = DataAggregator()
    stock_data = await aggregator.get_stock_data(symbol)
    if stock_data and stock_data.market_cap is not None:
        return {
            "symbol": stock_data.symbol,
            "company_name": f"Company info for {stock_data.symbol}", # Placeholder
            "market_cap": stock_data.market_cap,
            "pe_ratio": stock_data.pe_ratio,
            "sector": "Technology", # Placeholder
            "industry": "Software", # Placeholder
        }
    return {"error": f"Could not retrieve company info for {symbol}."}

async def get_economic_indicators() -> Dict[str, Any]:
    """
    Fetches key economic indicators like inflation rate and GDP growth.
    
    Returns:
        A dictionary of economic indicators or an error message.
    """
    aggregator = DataAggregator()
    indicators = await aggregator.get_economic_indicators()
    if indicators:
        return indicators
    return {"error": "Could not retrieve economic indicators."}

async def perform_web_search(query: str) -> Dict[str, Any]:
    """
    Performs a web search for a given query to find recent information
    or validate entities.
    
    Args:
        query: The search query.
        
    Returns:
        A dictionary with a summary of search results or an error message.
    """
    results = await web_search(query)
    if results:
        # Summarize for the model
        summary = " ".join([r.get('snippet', '') for r in results[:3]])
        return {"summary": summary}
    return {"error": f"Web search for '{query}' yielded no results."}

# --- Tool Mapping and Schemas ---

# Mapping from tool name to the async function that implements it
TOOL_EXECUTOR_MAP = {
    "get_stock_data": get_stock_data,
    "get_company_info": get_company_info,
    "get_economic_indicators": get_economic_indicators,
    "web_search": perform_web_search,
}

# List of tool definitions for the Bedrock 'converse' API
AGENT_TOOLS = [
    {
        "toolSpec": {
            "name": "get_stock_data",
            "description": "Get the latest stock price and key metrics for a given stock symbol.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The stock ticker symbol, e.g., 'AAPL' for Apple."
                        }
                    },
                    "required": ["symbol"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_company_info",
            "description": "Get detailed information about a company, such as market capitalization, P/E ratio, and sector.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The stock ticker symbol, e.g., 'MSFT' for Microsoft."
                        }
                    },
                    "required": ["symbol"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_economic_indicators",
            "description": "Get key economic indicators like the federal funds rate, unemployment rate, and inflation.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "web_search",
            "description": "Use a web search engine to find recent information, news, or details about companies that are not well-known.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query to search for on the web."
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    }
] 