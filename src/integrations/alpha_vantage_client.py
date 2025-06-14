"""
Alpha Vantage API Client for FinSight
Provides comprehensive financial data as secondary source to Yahoo Finance
"""

import requests
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import logging
import os
import time
from dataclasses import dataclass

from ..utils.data_sources import (
    DataSource, DataSourceMetadata, DataSourceType, DataSourceReliability,
    DataQuery, DataResponse
)

logger = logging.getLogger(__name__)


@dataclass
class AlphaVantageQuote:
    """Alpha Vantage stock quote data"""
    symbol: str
    price: float
    change: float
    change_percent: str
    volume: int
    previous_close: float
    open_price: float
    high: float
    low: float
    last_updated: str


@dataclass
class AlphaVantageCompany:
    """Alpha Vantage company overview data"""
    symbol: str
    name: str
    market_cap: Optional[int]
    pe_ratio: Optional[float]
    dividend_yield: Optional[float]
    sector: Optional[str]
    industry: Optional[str]
    exchange: Optional[str]
    currency: Optional[str]
    country: Optional[str]


class AlphaVantageDataSource(DataSource):
    """Alpha Vantage API client for financial data"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None, config: Dict[str, Any] = None):
        # Initialize metadata
        metadata = DataSourceMetadata(
            name="alpha_vantage",
            description="Alpha Vantage - Real-time and historical financial data",
            data_types=[DataSourceType.MARKET_DATA, DataSourceType.COMPANY_FUNDAMENTALS],
            reliability=DataSourceReliability.HIGH,
            rate_limit=5,  # 5 requests per minute on free tier
            cost_per_request=0.0,  # Free tier available
            requires_auth=True,
            base_url=self.BASE_URL,
            documentation_url="https://www.alphavantage.co/documentation/"
        )
        
        super().__init__(metadata, config)
        
        # API configuration
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FinSight/2.1.0 (+https://github.com/finsight/finsight)'
        })
        
        # Rate limiting
        self._last_request_time = None
        self._request_count = 0
        self._rate_limit_window = 60  # 1 minute
        self._max_requests_per_window = 5
        
        # Availability check
        self.available = self.api_key is not None
        if not self.available:
            logger.warning("Alpha Vantage API key not found. Set ALPHA_VANTAGE_API_KEY environment variable.")
    
    async def query(self, query: DataQuery) -> DataResponse:
        """Execute a query against Alpha Vantage API"""
        if not self.available:
            return DataResponse(
                source_name=self.metadata.name,
                query=query,
                data=None,
                timestamp=datetime.now(),
                confidence=0.0,
                metadata={},
                error="API key not available"
            )
        
        # Rate limiting check
        if not self._rate_limit_check():
            return DataResponse(
                source_name=self.metadata.name,
                query=query,
                data=None,
                timestamp=datetime.now(),
                confidence=0.0,
                metadata={},
                error="Rate limit exceeded"
            )
        
        try:
            if query.query_type == "stock_price":
                data = await self._get_stock_quote(query.parameters.get("symbol"))
            elif query.query_type == "company_overview":
                data = await self._get_company_overview(query.parameters.get("symbol"))
            elif query.query_type == "market_cap":
                # Get market cap from company overview
                overview = await self._get_company_overview(query.parameters.get("symbol"))
                data = {"market_cap": overview.market_cap} if overview else None
            else:
                data = None
            
            if data:
                return DataResponse(
                    source_name=self.metadata.name,
                    query=query,
                    data=data,
                    timestamp=datetime.now(),
                    confidence=0.9,  # High confidence for Alpha Vantage data
                    metadata={"rate_limited": False}
                )
            else:
                return DataResponse(
                    source_name=self.metadata.name,
                    query=query,
                    data=None,
                    timestamp=datetime.now(),
                    confidence=0.0,
                    metadata={},
                    error="No data available"
                )
                
        except Exception as e:
            logger.error(f"Alpha Vantage API error: {e}")
            return DataResponse(
                source_name=self.metadata.name,
                query=query,
                data=None,
                timestamp=datetime.now(),
                confidence=0.0,
                metadata={},
                error=str(e)
            )
    
    async def _get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current stock quote from Alpha Vantage"""
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            quote = data.get('Global Quote', {})
            
            if quote and '01. symbol' in quote:
                return {
                    'symbol': quote.get('01. symbol'),
                    'current_price': float(quote.get('05. price', 0)),
                    'change': float(quote.get('09. change', 0)),
                    'change_percent': quote.get('10. change percent', '').replace('%', ''),
                    'volume': int(quote.get('06. volume', 0)),
                    'previous_close': float(quote.get('08. previous close', 0)),
                    'open': float(quote.get('02. open', 0)),
                    'high': float(quote.get('03. high', 0)),
                    'low': float(quote.get('04. low', 0)),
                    'last_updated': quote.get('07. latest trading day'),
                    'source': 'alpha_vantage'
                }
            
            # Check for API errors
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
            elif 'Note' in data:
                logger.warning(f"Alpha Vantage API notice: {data['Note']}")
                
        except Exception as e:
            logger.error(f"Failed to get Alpha Vantage quote for {symbol}: {e}")
        
        return None
    
    async def _get_company_overview(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company overview from Alpha Vantage"""
        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and 'Symbol' in data:
                market_cap = data.get('MarketCapitalization')
                market_cap_int = None
                if market_cap and market_cap.isdigit():
                    market_cap_int = int(market_cap)
                
                pe_ratio = data.get('PERatio')
                pe_ratio_float = None
                if pe_ratio and pe_ratio != 'None':
                    try:
                        pe_ratio_float = float(pe_ratio)
                    except ValueError:
                        pass
                
                dividend_yield = data.get('DividendYield')
                dividend_yield_float = None
                if dividend_yield and dividend_yield != 'None':
                    try:
                        dividend_yield_float = float(dividend_yield)
                    except ValueError:
                        pass
                
                return {
                    'symbol': data.get('Symbol'),
                    'company_name': data.get('Name'),
                    'market_cap': market_cap_int,
                    'pe_ratio': pe_ratio_float,
                    'dividend_yield': dividend_yield_float,
                    'sector': data.get('Sector'),
                    'industry': data.get('Industry'),
                    'exchange': data.get('Exchange'),
                    'currency': data.get('Currency'),
                    'country': data.get('Country'),
                    'description': data.get('Description'),
                    'source': 'alpha_vantage'
                }
                
        except Exception as e:
            logger.error(f"Failed to get Alpha Vantage overview for {symbol}: {e}")
        
        return None
    
    def _rate_limit_check(self) -> bool:
        """Check if we're within rate limits (5 requests per minute)"""
        now = time.time()
        
        # Reset counter if window has passed
        if (self._last_request_time is None or 
            now - self._last_request_time >= self._rate_limit_window):
            self._request_count = 0
            self._last_request_time = now
        
        # Check if we can make another request
        if self._request_count >= self._max_requests_per_window:
            logger.warning("Alpha Vantage rate limit reached, throttling requests")
            return False
        
        self._request_count += 1
        return True
    
    async def health_check(self) -> bool:
        """Check if Alpha Vantage API is available"""
        if not self.available:
            return False
        
        try:
            # Test with a simple quote request for AAPL
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'AAPL',
                'apikey': self.api_key
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            # Check if we got a valid response
            return 'Global Quote' in data or 'Error Message' not in data
            
        except Exception as e:
            logger.error(f"Alpha Vantage health check failed: {e}")
            return False
    
    def supports_query_type(self, query_type: str) -> bool:
        """Check if this source supports a specific query type"""
        supported_types = {
            "stock_price", "market_cap", "company_overview", 
            "pe_ratio", "dividend_yield", "company_fundamentals"
        }
        return query_type in supported_types


# Convenience functions for direct usage
def get_alpha_vantage_client(api_key: Optional[str] = None) -> AlphaVantageDataSource:
    """Get an Alpha Vantage client instance"""
    return AlphaVantageDataSource(api_key=api_key)


async def test_alpha_vantage_integration():
    """Test function for Alpha Vantage integration"""
    client = get_alpha_vantage_client()
    
    if not client.available:
        print("❌ Alpha Vantage API key not available")
        return
    
    print("🧪 Testing Alpha Vantage Integration...")
    
    # Health check
    health = await client.health_check()
    print(f"Alpha Vantage API Health: {'✅ OK' if health else '❌ Failed'}")
    
    if health:
        # Test stock quote
        query = DataQuery(
            query_type="stock_price",
            parameters={"symbol": "AAPL"}
        )
        
        result = await client.query(query)
        if result.is_successful:
            print(f"✅ AAPL Stock Price: ${result.data['current_price']}")
        else:
            print(f"❌ Stock price query failed: {result.error}")


if __name__ == "__main__":
    asyncio.run(test_alpha_vantage_integration())
