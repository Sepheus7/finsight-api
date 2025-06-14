"""
Unified Data Aggregator for Financial Information
High-performance, multi-source financial data integration
Focus: Real-time data with intelligent caching and fallbacks
"""

import asyncio
import aiohttp
import yfinance as yf
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import json
import os

from models.enrichment_models import StockData, EconomicIndicator, MarketContext, DataPoint, DataSourceType
from utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class DataAggregator:
    """
    Unified interface for all financial data sources
    Handles parallel data fetching, caching, and fallbacks
    """
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.session = None
        
        # API configurations
        self.alpha_vantage_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        self.fred_key = os.environ.get('FRED_API_KEY')
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={'User-Agent': 'FinSight/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_stock_data(self, symbol: str) -> Optional[StockData]:
        """
        Get comprehensive stock data with fallback sources
        Priority: Yahoo Finance -> Alpha Vantage -> Cache
        """
        cache_key = f"stock_data_{symbol}_{datetime.now().strftime('%Y%m%d_%H')}"
        
        # Check cache first
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for {symbol} stock data")
            if isinstance(cached_data, dict):
                # Handle cached dictionary data - convert timestamp string back to datetime
                if 'timestamp' in cached_data and isinstance(cached_data['timestamp'], str):
                    try:
                        cached_data['timestamp'] = datetime.fromisoformat(cached_data['timestamp'].replace('Z', '+00:00'))
                    except:
                        cached_data['timestamp'] = datetime.now()
                # Ensure all required fields have default values
                cached_data.setdefault('timestamp', datetime.now())
                # Remove timestamp from dict before creating StockData since it has __post_init__
                timestamp = cached_data.pop('timestamp', datetime.now())
                stock_data = StockData(**cached_data)
                stock_data.timestamp = timestamp
                return stock_data
            else:
                # If cached_data is already a StockData object, ensure timestamp is datetime
                if hasattr(cached_data, 'timestamp') and isinstance(cached_data.timestamp, str):
                    cached_data.timestamp = datetime.now()
                return cached_data
        
        try:
            # Primary: Yahoo Finance (fast and reliable)
            stock_data = await self._get_yahoo_stock_data(symbol)
            if stock_data:
                await self.cache_manager.set(cache_key, stock_data.to_dict(), ttl=3600)  # 1 hour
                return stock_data
        except Exception as e:
            logger.warning(f"Yahoo Finance failed for {symbol}: {e}")
        
        try:
            # Fallback: Alpha Vantage
            if self.alpha_vantage_key:
                stock_data = await self._get_alpha_vantage_stock_data(symbol)
                if stock_data:
                    await self.cache_manager.set(cache_key, stock_data.to_dict(), ttl=3600)
                    return stock_data
        except Exception as e:
            logger.warning(f"Alpha Vantage failed for {symbol}: {e}")
        
        logger.error(f"All stock data sources failed for {symbol}")
        return None
    
    async def _get_yahoo_stock_data(self, symbol: str) -> Optional[StockData]:
        """Fetch stock data from Yahoo Finance"""
        try:
            # Use yfinance in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            ticker_data = await loop.run_in_executor(None, self._fetch_yahoo_data, symbol)
            
            if not ticker_data:
                return None
            
            info = ticker_data.get('info', {})
            history = ticker_data.get('history', {})
            
            if history.empty:
                return None
            
            latest = history.iloc[-1]
            previous_close = info.get('previousClose', latest['Close'])
            
            return StockData(
                symbol=symbol.upper(),
                price=round(float(latest['Close']), 2),
                change=round(float(latest['Close'] - previous_close), 2),
                change_percent=round(((latest['Close'] - previous_close) / previous_close) * 100, 2),
                volume=int(latest['Volume']),
                market_cap=info.get('marketCap'),
                pe_ratio=info.get('trailingPE'),
                day_high=round(float(latest['High']), 2),
                day_low=round(float(latest['Low']), 2),
                year_high=info.get('fiftyTwoWeekHigh'),
                year_low=info.get('fiftyTwoWeekLow')
            )
            
        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
            return None
    
    def _fetch_yahoo_data(self, symbol: str) -> Dict[str, Any]:
        """Synchronous Yahoo Finance fetch for thread pool"""
        try:
            ticker = yf.Ticker(symbol)
            return {
                'info': ticker.info,
                'history': ticker.history(period='5d')
            }
        except Exception as e:
            logger.error(f"Yahoo fetch error: {e}")
            return {}
    
    async def _get_alpha_vantage_stock_data(self, symbol: str) -> Optional[StockData]:
        """Fetch stock data from Alpha Vantage as fallback"""
        if not self.alpha_vantage_key or not self.session:
            return None
        
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                
                quote = data.get('Global Quote', {})
                if not quote:
                    return None
                
                price = float(quote.get('05. price', 0))
                change = float(quote.get('09. change', 0))
                change_percent = float(quote.get('10. change percent', '0%').replace('%', ''))
                
                return StockData(
                    symbol=symbol.upper(),
                    price=round(price, 2),
                    change=round(change, 2),
                    change_percent=round(change_percent, 2),
                    volume=int(float(quote.get('06. volume', 0))),
                    day_high=round(float(quote.get('03. high', 0)), 2),
                    day_low=round(float(quote.get('04. low', 0)), 2)
                )
                
        except Exception as e:
            logger.error(f"Alpha Vantage error for {symbol}: {e}")
            return None
    
    async def get_economic_indicators(self) -> Dict[str, Any]:
        """
        Get key economic indicators from FRED
        """
        cache_key = f"economic_indicators_{datetime.now().strftime('%Y%m%d')}"
        
        # Check cache (daily data)
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            logger.info("Cache hit for economic indicators")
            return cached_data
        
        indicators = {}
        
        # Key economic indicators to fetch
        fred_indicators = {
            'fed_funds_rate': 'FEDFUNDS',
            'unemployment_rate': 'UNRATE',
            'inflation_rate': 'CPIAUCSL',
            'gdp_growth': 'GDP'
        }
        
        for name, fred_code in fred_indicators.items():
            try:
                indicator_data = await self._get_fred_indicator(fred_code, name)
                if indicator_data:
                    indicators[name] = indicator_data.to_dict()
            except Exception as e:
                logger.warning(f"Failed to fetch {name}: {e}")
        
        if indicators:
            await self.cache_manager.set(cache_key, indicators, ttl=86400)  # 24 hours
        
        return indicators
    
    async def _get_fred_indicator(self, series_id: str, name: str) -> Optional[EconomicIndicator]:
        """Fetch economic indicator from FRED API"""
        if not self.fred_key or not self.session:
            return None
        
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.fred_key,
                'file_type': 'json',
                'limit': 1,
                'sort_order': 'desc'
            }
            
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                
                observations = data.get('observations', [])
                if not observations:
                    return None
                
                latest = observations[0]
                value = latest.get('value')
                
                if value == '.' or value is None:
                    return None
                
                return EconomicIndicator(
                    indicator_name=name,
                    value=float(value),
                    unit='%' if 'rate' in name else 'index',
                    period=latest.get('date', ''),
                    release_date=datetime.strptime(latest.get('date', '2024-01-01'), '%Y-%m-%d')
                )
                
        except Exception as e:
            logger.error(f"FRED API error for {series_id}: {e}")
            return None
    
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get market context data for a symbol
        """
        cache_key = f"market_context_{symbol}_{datetime.now().strftime('%Y%m%d_%H')}"
        
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Get sector information and performance
            market_context = await self._get_market_context(symbol)
            if market_context:
                context_data = {f"{symbol}_market_context": market_context.to_dict()}
                await self.cache_manager.set(cache_key, context_data, ttl=3600)
                return context_data
                
        except Exception as e:
            logger.error(f"Market context error for {symbol}: {e}")
        
        return {}
    
    async def _get_market_context(self, symbol: str) -> Optional[MarketContext]:
        """Get market context using Yahoo Finance sector data"""
        try:
            loop = asyncio.get_event_loop()
            ticker_info = await loop.run_in_executor(None, self._fetch_ticker_info, symbol)
            
            if not ticker_info:
                return None
            
            sector = ticker_info.get('sector', 'Unknown')
            industry = ticker_info.get('industry', 'Unknown')
            
            # Simple market trend analysis based on price movement
            price_change = ticker_info.get('regularMarketChangePercent', 0)
            
            if price_change > 2:
                trend = "Strong Positive"
            elif price_change > 0:
                trend = "Positive"
            elif price_change > -2:
                trend = "Negative"
            else:
                trend = "Strong Negative"
            
            return MarketContext(
                sector=sector,
                sector_performance=price_change,
                market_trend=trend,
                volatility_index=None,  # Could add VIX data here
                related_news=[]  # Could add news integration
            )
            
        except Exception as e:
            logger.error(f"Market context error: {e}")
            return None
    
    def _fetch_ticker_info(self, symbol: str) -> Dict[str, Any]:
        """Synchronous ticker info fetch for thread pool"""
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info
        except Exception as e:
            logger.error(f"Ticker info error: {e}")
            return {}
    
    async def get_batch_stock_data(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get stock data for multiple symbols in parallel
        """
        tasks = [self.get_stock_data(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        batch_data = {}
        for result in results:
            if isinstance(result, dict) and not isinstance(result, Exception):
                batch_data.update(result)
        
        return batch_data


# Utility function for easy usage
async def fetch_financial_data(symbols: List[str], include_economic: bool = True) -> Dict[str, Any]:
    """
    Convenience function to fetch comprehensive financial data
    """
    async with DataAggregator() as aggregator:
        data = {}
        
        # Get stock data for all symbols
        if symbols:
            stock_data = await aggregator.get_batch_stock_data(symbols)
            data.update(stock_data)
        
        # Get economic indicators
        if include_economic:
            economic_data = await aggregator.get_economic_indicators()
            data.update(economic_data)
        
        return data
