"""
FinSight RAG Handler - Core Financial Data API for AI Agents
Production-ready handler for retrieving comprehensive financial context
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import from src structure
from integrations.data_aggregator import DataAggregator
from utils.cache_manager import CacheManager
from utils.claim_extractor import ClaimExtractor
from models.enrichment_models import DataPoint, DataSourceType

logger = logging.getLogger(__name__)


class FinancialRAGHandler:
    """
    Core RAG handler for AI agents
    Provides comprehensive financial context in a single API call
    
    Features:
    - Smart entity extraction from natural language
    - Parallel data fetching from multiple sources
    - Intelligent caching for performance
    - AI-optimized response structure
    """
    
    def __init__(self):
        """Initialize the RAG handler with required components"""
        try:
            self.data_aggregator = DataAggregator()
            self.cache_manager = CacheManager()
            self.claim_extractor = ClaimExtractor()
            logger.info("FinancialRAGHandler initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG handler: {e}")
            raise
    
    async def get_financial_context(self, query: str, symbols: Optional[List[str]] = None, 
                                  include_economic: bool = True,
                                  include_market_context: bool = True,
                                  max_symbols: int = 10,
                                  use_bedrock_orchestration: bool = False) -> Dict[str, Any]:
        """
        Main RAG endpoint - get comprehensive financial context for AI agents
        
        Args:
            query: Natural language query from AI agent
            symbols: Optional list of stock symbols to focus on
            include_economic: Include economic indicators (Fed rates, inflation, etc.)
            include_market_context: Include market sentiment and trends
            max_symbols: Maximum number of symbols to process (performance limit)
            use_bedrock_orchestration: Use Bedrock orchestration for data fetching
            
        Returns:
            Structured financial context ready for AI consumption
        """
        start_time = datetime.now()
        request_id = f"rag_{int(start_time.timestamp())}"
        
        logger.info(f"[{request_id}] Processing RAG request: query='{query[:50]}...', symbols={symbols}")
        
        try:
            # 1. Extract financial entities from query if symbols not provided
            extracted_symbols = []
            if not symbols:
                try:
                    claims = await self.claim_extractor.extract_claims(query)
                    extracted_symbols = [claim.entities[0] for claim in claims if claim.entities]
                    extracted_symbols = list(set(extracted_symbols))  # Remove duplicates
                    logger.info(f"[{request_id}] Extracted symbols from query: {extracted_symbols}")
                except Exception as e:
                    logger.warning(f"[{request_id}] Entity extraction failed: {e}")
                    extracted_symbols = []
            
            # Use provided symbols or extracted ones
            final_symbols = symbols or extracted_symbols
            final_symbols = final_symbols[:max_symbols]  # Limit for performance
            
            # 2. Gather financial data in parallel
            data_tasks = []
            
            # Stock data for mentioned symbols
            if final_symbols:
                logger.info(f"[{request_id}] Fetching stock data for {len(final_symbols)} symbols")
                for symbol in final_symbols:
                    data_tasks.append(self._fetch_stock_data_safe(symbol, request_id))
            
            # Economic indicators
            if include_economic:
                logger.info(f"[{request_id}] Including economic indicators")
                data_tasks.append(self._fetch_economic_data_safe(request_id))
            
            # Market context (limit to top 3 symbols for performance)
            if include_market_context and final_symbols:
                logger.info(f"[{request_id}] Including market context for top symbols")
                for symbol in final_symbols[:3]:
                    data_tasks.append(self._fetch_market_data_safe(symbol, request_id))
            
            # Execute all data gathering in parallel
            logger.info(f"[{request_id}] Executing {len(data_tasks)} data tasks in parallel")
            results = await asyncio.gather(*data_tasks, return_exceptions=True)
            
            # 3. Structure the response for AI consumption
            context = await self._build_ai_context(query, final_symbols, results, request_id)
            
            # 4. Add metadata
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            context['metadata'] = {
                'request_id': request_id,
                'processing_time_ms': round(processing_time, 2),
                'symbols_analyzed': final_symbols,
                'symbols_extracted': extracted_symbols,
                'data_sources_used': len([r for r in results if not isinstance(r, Exception)]),
                'cache_hit_rate': self.cache_manager.get_hit_rate(),
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            
            logger.info(f"[{request_id}] RAG processing completed in {processing_time:.2f}ms")
            return context
            
        except Exception as e:
            logger.error(f"[{request_id}] RAG context generation failed: {str(e)}")
            return {
                'error': str(e),
                'request_id': request_id,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _fetch_stock_data_safe(self, symbol: str, request_id: str) -> Any:
        """Safely fetch stock data with error handling"""
        try:
            return await self.data_aggregator.get_stock_data(symbol)
        except Exception as e:
            logger.warning(f"[{request_id}] Failed to fetch stock data for {symbol}: {e}")
            return None
    
    async def _fetch_economic_data_safe(self, request_id: str) -> Any:
        """Safely fetch economic data with error handling"""
        try:
            return await self.data_aggregator.get_economic_indicators()
        except Exception as e:
            logger.warning(f"[{request_id}] Failed to fetch economic data: {e}")
            return None
    
    async def _fetch_market_data_safe(self, symbol: str, request_id: str) -> Any:
        """Safely fetch market data with error handling"""
        try:
            return await self.data_aggregator.get_market_data(symbol)
        except Exception as e:
            logger.warning(f"[{request_id}] Failed to fetch market data for {symbol}: {e}")
            return None
    
    async def _build_ai_context(self, query: str, symbols: List[str], 
                              results: List[Any], request_id: str) -> Dict[str, Any]:
        """
        Build structured context optimized for AI agent consumption
        """
        context = {
            'query_analysis': {
                'original_query': query,
                'extracted_symbols': symbols,
                'query_intent': self._analyze_query_intent(query),
                'complexity': self._assess_query_complexity(query, symbols)
            },
            'financial_data': {
                'stocks': {},
                'count': 0
            },
            'market_insights': [],
            'economic_context': {},
            'summary': '',
            'response': '',
            'sources': []
        }
        
        # Process results
        stock_data = {}
        economic_data = {}
        market_contexts = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"[{request_id}] Result {i} was an exception: {result}")
                continue
            elif result is None:
                continue
            elif hasattr(result, 'symbol'):  # Stock data
                try:
                    stock_data[result.symbol] = {
                        'symbol': result.symbol,
                        'price': result.price,
                        'change': result.change,
                        'change_percent': result.change_percent,
                        'volume': result.volume,
                        'market_cap': result.market_cap,
                        'pe_ratio': result.pe_ratio,
                        'day_range': f"${result.day_low} - ${result.day_high}" if hasattr(result, 'day_low') else None,
                        'timestamp': result.timestamp.isoformat() if hasattr(result, 'timestamp') and result.timestamp else None
                    }
                except Exception as e:
                    logger.warning(f"[{request_id}] Failed to process stock data for {getattr(result, 'symbol', 'unknown')}: {e}")
            elif isinstance(result, dict):
                if 'fed_funds_rate' in result or 'unemployment_rate' in result:
                    economic_data.update(result)
                elif any('market_context' in key for key in result.keys()):
                    market_contexts.append(result)
        
        # Build final context
        context['financial_data']['stocks'] = stock_data
        context['financial_data']['count'] = len(stock_data)
        context['economic_context'] = economic_data
        context['market_insights'] = self._generate_market_insights(stock_data, economic_data)
        context['summary'] = self._generate_summary(query, stock_data, economic_data)
        
        # Add plain English response with sources
        context['response'] = self._generate_plain_english_response(query, stock_data, economic_data, context['market_insights'])
        context['sources'] = self._generate_sources_list(stock_data, economic_data)
        
        logger.info(f"[{request_id}] Built context with {len(stock_data)} stocks, {len(economic_data)} economic indicators")
        return context
    
    def _analyze_query_intent(self, query: str) -> str:
        """Analyze the intent of the query for better context"""
        query_lower = query.lower()
        
        # Define intent patterns
        intent_patterns = {
            'comparison': ['compare', 'vs', 'versus', 'against', 'better than', 'worse than'],
            'trend_analysis': ['trend', 'performance', 'over time', 'historical', 'chart', 'graph'],
            'portfolio_analysis': ['portfolio', 'allocation', 'diversification', 'holdings', 'balance'],
            'economic_analysis': ['economy', 'economic', 'gdp', 'inflation', 'fed', 'interest rate'],
            'valuation': ['price', 'value', 'worth', 'cost', 'expensive', 'cheap', 'fair value'],
            'news_sentiment': ['news', 'sentiment', 'opinion', 'analyst', 'recommendation'],
            'risk_analysis': ['risk', 'volatility', 'safe', 'dangerous', 'stable', 'risky']
        }
        
        # Score each intent
        intent_scores = {}
        for intent, patterns in intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Return highest scoring intent or default
        if intent_scores:
            return max(intent_scores.keys(), key=lambda x: intent_scores[x])
        else:
            return 'general_inquiry'
    
    def _assess_query_complexity(self, query: str, symbols: List[str]) -> str:
        """Assess the complexity of the query"""
        complexity_indicators = [
            'compare', 'analyze', 'correlation', 'impact', 'trend', 'forecast', 
            'predict', 'recommend', 'portfolio', 'allocation', 'risk'
        ]
        
        query_lower = query.lower()
        complexity_score = sum(1 for indicator in complexity_indicators if indicator in query_lower)
        
        # Factor in number of symbols
        symbol_complexity = len(symbols) if symbols else 0
        
        total_score = complexity_score + (symbol_complexity * 0.5)
        
        if total_score >= 4:
            return 'high'
        elif total_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _generate_market_insights(self, stock_data: Dict, economic_data: Dict) -> List[str]:
        """Generate actionable market insights for AI agents"""
        insights = []
        
        if stock_data:
            # Performance insights
            positive_stocks = [s for s, data in stock_data.items() if data.get('change_percent', 0) > 0]
            negative_stocks = [s for s, data in stock_data.items() if data.get('change_percent', 0) < 0]
            
            if len(positive_stocks) > len(negative_stocks):
                insights.append(f"Market sentiment is positive with {len(positive_stocks)} stocks up vs {len(negative_stocks)} down")
            elif len(negative_stocks) > len(positive_stocks):
                insights.append(f"Market sentiment is negative with {len(negative_stocks)} stocks down vs {len(positive_stocks)} up")
            else:
                insights.append("Market sentiment is mixed with equal numbers of gainers and losers")
            
            # Volatility insights
            high_volatility = [s for s, data in stock_data.items() if abs(data.get('change_percent', 0)) > 3]
            if high_volatility:
                insights.append(f"High volatility detected in: {', '.join(high_volatility)}")
            
            # Volume insights
            high_volume_stocks = []
            for symbol, data in stock_data.items():
                volume = data.get('volume', 0)
                if volume > 50000000:  # 50M+ shares
                    high_volume_stocks.append(symbol)
            
            if high_volume_stocks:
                insights.append(f"High trading volume observed in: {', '.join(high_volume_stocks)}")
        
        if economic_data:
            # Economic insights
            if 'fed_funds_rate' in economic_data:
                insights.append("Federal Reserve monetary policy data available for context")
            if 'unemployment_rate' in economic_data:
                insights.append("Employment data provides economic backdrop")
            if 'inflation_rate' in economic_data:
                insights.append("Inflation metrics available for purchasing power analysis")
        
        return insights
    
    def _generate_summary(self, query: str, stock_data: Dict, economic_data: Dict) -> str:
        """Generate a concise summary for AI agents"""
        summary_parts = []
        
        if stock_data:
            stock_count = len(stock_data)
            if stock_count > 0:
                avg_change = sum(data.get('change_percent', 0) for data in stock_data.values()) / stock_count
                summary_parts.append(f"Analyzed {stock_count} stocks with average change of {avg_change:.2f}%")
        
        if economic_data:
            summary_parts.append(f"Economic context includes {len(economic_data)} indicators")
        
        if not summary_parts:
            summary_parts.append("No specific financial data found for this query")
        
        return ". ".join(summary_parts)

    def _generate_plain_english_response(self, query: str, stock_data: Dict, economic_data: Dict, insights: List[str]) -> str:
        """Generate a plain English response based on the financial data"""
        response_parts = []
        
        # Start with a contextual greeting based on the query
        query_lower = query.lower()
        if 'price' in query_lower:
            response_parts.append("Here's the current pricing information:")
        elif 'performance' in query_lower or 'performing' in query_lower:
            response_parts.append("Here's how the stocks are performing:")
        elif 'compare' in query_lower:
            response_parts.append("Here's a comparison of the requested stocks:")
        else:
            response_parts.append("Based on your query, here's the financial information:")
        
        # Add stock-specific information
        if stock_data:
            for symbol, data in stock_data.items():
                price = data.get('price', 0)
                change = data.get('change', 0)
                change_percent = data.get('change_percent', 0)
                volume = data.get('volume', 0)
                
                # Format the stock information
                direction = "up" if change_percent > 0 else "down" if change_percent < 0 else "unchanged"
                stock_info = f"{symbol} is trading at ${price:.2f}, {direction} {abs(change_percent):.2f}% (${change:+.2f})"
                
                # Add volume context if significant
                if volume > 50000000:
                    stock_info += f" with high trading volume of {volume:,} shares"
                elif volume > 0:
                    stock_info += f" with {volume:,} shares traded"
                
                response_parts.append(stock_info)
        
        # Add market insights in plain English
        if insights:
            response_parts.append("\nMarket insights:")
            for insight in insights:
                response_parts.append(f"• {insight}")
        
        # Add economic context if available
        if economic_data:
            response_parts.append("\nEconomic context is also available for broader market analysis.")
        
        return "\n".join(response_parts)

    def _generate_sources_list(self, stock_data: Dict, economic_data: Dict) -> List[str]:
        """Generate a list of sources used for the response"""
        sources = []
        
        if stock_data:
            sources.append("Yahoo Finance - Real-time stock market data")
            sources.append("Financial Market Data Providers - Price and volume information")
        
        if economic_data:
            sources.append("Federal Reserve Economic Data (FRED) - Economic indicators")
            sources.append("U.S. Bureau of Labor Statistics - Employment and inflation data")
        
        # Add timestamp for data freshness
        sources.append(f"Data retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        return sources


# Standalone test function
async def test_rag_handler():
    """Test the RAG handler with sample queries"""
    print("🚀 Testing FinSight RAG Handler")
    print("=" * 50)
    
    try:
        handler = FinancialRAGHandler()
        
        # Test cases
        test_cases = [
            {
                "name": "Stock Price Query",
                "query": "What's the current price of Apple?",
                "symbols": None
            },
            {
                "name": "Multiple Symbols",
                "query": "Compare tech giants",
                "symbols": ["AAPL", "MSFT", "GOOGL"]
            },
            {
                "name": "Economic Context",
                "query": "Current economic indicators for market analysis",
                "symbols": None
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📊 Test {i}: {test_case['name']}")
            print(f"Query: {test_case['query']}")
            if test_case['symbols']:
                print(f"Symbols: {test_case['symbols']}")
            print("-" * 30)
            
            try:
                result = await handler.get_financial_context(
                    query=test_case['query'],
                    symbols=test_case['symbols']
                )
                
                if 'error' in result:
                    print(f"❌ Error: {result['error']}")
                else:
                    print(f"✅ Success!")
                    metadata = result.get('metadata', {})
                    print(f"⚡ Processing time: {metadata.get('processing_time_ms', 0):.1f}ms")
                    print(f"📈 Symbols: {metadata.get('symbols_analyzed', [])}")
                    print(f"🎯 Intent: {result.get('query_analysis', {}).get('query_intent', 'unknown')}")
                    
                    # Show data summary
                    financial_data = result.get('financial_data', {})
                    if financial_data.get('count', 0) > 0:
                        print(f"💰 Retrieved data for {financial_data['count']} stocks")
                    
                    summary = result.get('summary', '')
                    if summary:
                        print(f"📋 Summary: {summary}")
                        
                    # Show plain English response and sources
                    response = result.get('response', '')
                    if response:
                        print(f"📋 Response: {response}")
                    
                    sources = result.get('sources', [])
                    if sources:
                        print(f"📋 Sources:")
                        for source in sources:
                            print(f"  - {source}")
                        
            except Exception as e:
                print(f"❌ Test failed: {str(e)}")
        
        print(f"\n🎉 RAG Handler testing completed!")
        
    except Exception as e:
        print(f"❌ Failed to initialize RAG handler: {e}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_rag_handler()) 