"""
Tool definitions and implementations for the Bedrock FinSight Agent.
This file centralizes all the tools that the agent can use,
including their JSON schemas for the Bedrock API and the
corresponding Python functions to execute them.
"""

import asyncio
from typing import Dict, List, Any

from integrations.data_aggregator import DataAggregator
from utils.web_search import perform_web_search, search_economic_indicators
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
    async with DataAggregator() as aggregator:
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
    Fetches key economic indicators like inflation rate and GDP growth for the US.
    
    Returns:
        A dictionary of economic indicators or an error message.
    """
    async with DataAggregator() as aggregator:
        indicators = await aggregator.get_economic_indicators()
        if indicators:
            return indicators
    
    # Fallback to web search for US economic data
    try:
        us_inflation = await search_economic_indicators("inflation rate", 5)
        us_unemployment = await search_economic_indicators("unemployment rate", 5)
        us_gdp = await search_economic_indicators("GDP growth", 5)
        
        fallback_data = {
            "source": "web_search_fallback",
            "inflation_data": us_inflation,
            "unemployment_data": us_unemployment,
            "gdp_data": us_gdp
        }
        
        # Extract key values if found
        summary_parts = []
        if us_inflation.get('found_data'):
            summary_parts.append(us_inflation['summary'])
        if us_unemployment.get('found_data'):
            summary_parts.append(us_unemployment['summary'])
        if us_gdp.get('found_data'):
            summary_parts.append(us_gdp['summary'])
        
        if summary_parts:
            fallback_data["summary"] = "; ".join(summary_parts)
            return fallback_data
        
    except Exception as e:
        pass
    
    return {"error": "Could not retrieve economic indicators from any source."}

async def get_country_economic_data(country: str, indicator: str = "general") -> Dict[str, Any]:
    """
    Get economic data for a specific country with enhanced source attribution
    
    Args:
        country: Country name (e.g., "France", "United Kingdom", "Germany")
        indicator: Type of economic indicator ("employment", "inflation", "unemployment", "general")
    
    Returns:
        Dictionary with economic data, sources, and as-of dates
    """
    try:
        # Map indicator to search terms
        indicator_mapping = {
            "employment": "employment rate",
            "unemployment": "unemployment rate", 
            "inflation": "inflation rate",
            "general": "economic indicators"
        }
        
        search_term = indicator_mapping.get(indicator, indicator)
        economic_data = await search_economic_indicators(search_term, 5)
        
        if economic_data.get('found_data'):
            # Format response with enhanced source attribution
            response = {
                "country": country,
                "indicator_type": indicator,
                "data_found": True,
                "summary": economic_data.get('summary', ''),
                "indicators": economic_data.get('indicators', {}),
                "sources": []
            }
            
            # Enhanced source formatting with as-of dates
            for source in economic_data.get('sources', []):
                source_info = {
                    "title": source.get('title', ''),
                    "url": source.get('url', ''),
                    "confidence": source.get('confidence', 0.5)
                }
                
                # Extract as-of date information if available
                if hasattr(source, 'get') and source.get('as_of_date'):
                    source_info['as_of_date'] = source['as_of_date']
                if hasattr(source, 'get') and source.get('source_agency'):
                    source_info['source_agency'] = source['source_agency']
                if hasattr(source, 'get') and source.get('data_type'):
                    source_info['data_type'] = source['data_type']
                    
                response["sources"].append(source_info)
            
            return response
        else:
            # Enhanced fallback with specific country economic data
            fallback_data = _get_country_fallback_data(country, indicator)
            return fallback_data
            
    except Exception as e:
        logger.error(f"Error getting economic data for {country}: {e}")
        return {
            "country": country,
            "indicator_type": indicator,
            "data_found": False,
            "error": f"Unable to retrieve economic data: {str(e)}",
            "summary": f"Economic data retrieval failed for {country}. Please try again later.",
            "sources": []
        }

def _get_country_fallback_data(country: str, indicator: str) -> Dict[str, Any]:
    """Provide clear information about data limitations instead of fake data"""
    
    # Official source URLs for different countries
    country_sources = {
        "France": {
            "agency": "INSEE (French National Institute of Statistics)",
            "url": "https://www.insee.fr/en/statistiques"
        },
        "United Kingdom": {
            "agency": "ONS (UK Office for National Statistics)",
            "url": "https://www.ons.gov.uk/"
        },
        "United States": {
            "agency": "BLS (Bureau of Labor Statistics) & BEA (Bureau of Economic Analysis)",
            "url": "https://www.bls.gov/"
        }
    }
    
    source_info = country_sources.get(country, {
        "agency": "Official statistical agency",
        "url": ""
    })
    
    return {
        "country": country,
        "indicator_type": indicator,
        "data_found": False,
        "summary": f"Real-time economic data for {country} is currently unavailable due to API limitations. For accurate and current economic statistics, please visit the official source: {source_info['agency']} directly.",
        "data_limitation": "Real-time data access currently unavailable",
        "recommended_action": f"Visit {source_info['url']} for current official data",
        "sources": [{
            "title": f"Official {country} Economic Statistics",
            "url": source_info["url"],
            "source_agency": source_info["agency"],
            "note": "Direct access required for current data",
            "confidence": 1.0
        }] if source_info["url"] else []
    }

async def perform_web_search(query: str) -> Dict[str, Any]:
    """
    Performs a web search for a given query to find recent information
    or validate entities.
    
    Args:
        query: The search query.
        
    Returns:
        A dictionary with a summary of search results or an error message.
    """
    results = await perform_web_search(query)
    if results:
        # Summarize for the model with more detail
        summaries = []
        for result in results[:3]:
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            confidence = result.get('confidence', 0.5)
            summaries.append(f"[{title}] {snippet} (confidence: {confidence:.1f})")
        
        return {
            "query": query,
            "summary": " | ".join(summaries),
            "total_results": len(results),
            "sources": [{"title": r.get('title'), "url": r.get('url')} for r in results[:3]]
        }
    return {"error": f"Web search for '{query}' yielded no results."}

# --- Tool Mapping and Schemas ---

# Mapping from tool name to the async function that implements it
TOOL_EXECUTOR_MAP = {
    "get_stock_data": get_stock_data,
    "get_company_info": get_company_info,
    "get_economic_indicators": get_economic_indicators,
    "get_country_economic_data": get_country_economic_data,
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
            "description": "Get key US economic indicators like the federal funds rate, unemployment rate, and inflation. For other countries, use get_country_economic_data.",
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
            "name": "get_country_economic_data",
            "description": "Get economic indicators for a specific country including inflation rate, unemployment rate, employment rate, and GDP growth. Use this for any country other than the US.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "country": {
                            "type": "string",
                            "description": "The country name, e.g., 'France', 'United Kingdom', 'Germany', 'Japan'"
                        },
                        "indicator": {
                            "type": "string",
                            "description": "Specific economic indicator to search for. Use 'general' for multiple indicators, or specify 'inflation', 'unemployment', 'employment', or 'gdp'",
                            "default": "general"
                        }
                    },
                    "required": ["country"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "web_search",
            "description": "Use a web search engine to find recent information, news, or details about companies, economic data, or other topics that are not available through other tools.",
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