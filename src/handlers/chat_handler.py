"""
FinSight AI Chat Handler
Powered by AWS Bedrock for intelligent financial conversations
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

from utils.claim_extractor import ClaimExtractor
from integrations.data_aggregator import DataAggregator

# Import Bedrock client with error handling
try:
    from utils.bedrock_client import BedrockLLMClient
except ImportError:
    BedrockLLMClient = None

# Data aggregator handles all external data sources

logger = logging.getLogger(__name__)

class FinSightChatHandler:
    """
    Advanced AI chat handler for financial conversations
    Integrates with Bedrock for natural language processing and 
    existing data sources for comprehensive financial analysis
    """
    
    def __init__(self):
        self.bedrock_client = BedrockLLMClient() if BedrockLLMClient else None
        self.claim_extractor = ClaimExtractor()
        self.data_aggregator = DataAggregator()
        
        # Chat context management
        self.chat_contexts = {}
        self.max_context_length = 10
        
        logger.info("FinSight Chat Handler initialized with available integrations")
    
    async def process_chat_message(self, message: str, chat_id: Optional[str] = None, 
                                 context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Process a chat message and generate an intelligent response
        
        Args:
            message: User's message
            chat_id: Optional chat session ID
            context: Optional conversation context
            
        Returns:
            Dict containing response and any relevant data
        """
        try:
            start_time = datetime.now()
            
            # Initialize or update chat context
            if chat_id:
                if chat_id not in self.chat_contexts:
                    self.chat_contexts[chat_id] = []
                chat_context = self.chat_contexts[chat_id]
            else:
                chat_context = context or []
            
            # Analyze the message to determine intent and extract financial entities
            analysis = await self._analyze_message(message)
            
            # Gather relevant financial data based on analysis
            financial_data = await self._gather_financial_data(analysis)
            
            # Generate AI response using Bedrock
            ai_response = await self._generate_ai_response(
                message, chat_context, analysis, financial_data
            )
            
            # Update chat context
            if chat_id:
                self._update_chat_context(chat_id, message, ai_response['response'])
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(f"Chat message processed in {processing_time:.2f}ms")
            
            return {
                'response': ai_response['response'],
                'data': financial_data,
                'analysis': analysis,
                'processing_time_ms': processing_time,
                'chat_id': chat_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            return {
                'response': "I apologize, but I encountered an error processing your request. Please try again or rephrase your question.",
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _analyze_message(self, message: str) -> Dict[str, Any]:
        """
        Analyze the user's message to determine intent and extract entities
        """
        analysis = {
            'intent': 'general_inquiry',
            'entities': {
                'stocks': [],
                'companies': [],
                'economic_indicators': [],
                'time_periods': [],
                'financial_metrics': []
            },
            'query_type': 'informational',
            'complexity': 'medium'
        }
        
        # Extract financial claims and entities
        try:
            claims = await self.claim_extractor.extract_claims(message)
            for claim in claims:
                # Use getattr for safe attribute access
                ticker = getattr(claim, 'ticker', None)
                if ticker:
                    analysis['entities']['stocks'].append(ticker)
                company = getattr(claim, 'company', None)
                if company:
                    analysis['entities']['companies'].append(company)
        except Exception as e:
            logger.warning(f"Error extracting claims: {e}")
        
        # Pattern matching for common financial queries
        patterns = {
            'portfolio_analysis': [
                r'portfolio.*performance', r'ytd.*return', r'fund.*vs.*s&p',
                r'portfolio.*changes', r'asset.*allocation'
            ],
            'stock_analysis': [
                r'stock.*analysis', r'investment.*recommendation', r'financial.*health',
                r'company.*fundamentals', r'stock.*price'
            ],
            'economic_analysis': [
                r'economic.*indicator', r'inflation.*trend', r'gdp.*growth',
                r'unemployment.*rate', r'interest.*rate'
            ],
            'market_analysis': [
                r'market.*condition', r'sector.*performance', r'market.*trend',
                r'volatility', r'market.*outlook'
            ],
            'risk_analysis': [
                r'risk.*assessment', r'compliance.*review', r'risk.*mitigation',
                r'regulatory.*compliance'
            ]
        }
        
        message_lower = message.lower()
        for intent, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, message_lower):
                    analysis['intent'] = intent
                    break
            if analysis['intent'] != 'general_inquiry':
                break
        
        # Extract stock symbols and company names
        stock_pattern = r'\b([A-Z]{1,5})\b'
        potential_stocks = re.findall(stock_pattern, message)
        analysis['entities']['stocks'].extend(potential_stocks)
        
        # Remove duplicates
        analysis['entities']['stocks'] = list(set(analysis['entities']['stocks']))
        analysis['entities']['companies'] = list(set(analysis['entities']['companies']))
        
        # Determine query complexity
        complexity_indicators = [
            'compare', 'analyze', 'vs', 'versus', 'correlation', 'impact',
            'trend', 'forecast', 'predict', 'recommend'
        ]
        
        complexity_score = sum(1 for indicator in complexity_indicators 
                             if indicator in message_lower)
        
        if complexity_score >= 3:
            analysis['complexity'] = 'high'
        elif complexity_score >= 1:
            analysis['complexity'] = 'medium'
        else:
            analysis['complexity'] = 'low'
        
        return analysis
    
    async def _gather_financial_data(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gather relevant financial data based on message analysis
        """
        financial_data = {}
        
        try:
            # Gather stock data if stocks mentioned
            if analysis['entities']['stocks']:
                stock_data = {}
                for symbol in analysis['entities']['stocks'][:5]:  # Limit to 5 stocks
                    try:
                        data = await self.data_aggregator.get_stock_data(symbol)
                        if data:
                            stock_data[symbol] = {
                                'symbol': getattr(data, 'symbol', symbol),
                                'price': getattr(data, 'price', 0),
                                'change': getattr(data, 'change', 0),
                                'change_percent': getattr(data, 'change_percent', 0),
                                'volume': getattr(data, 'volume', 0),
                                'market_cap': getattr(data, 'market_cap', None),
                                'pe_ratio': getattr(data, 'pe_ratio', None),
                                'timestamp': data.timestamp.isoformat() if hasattr(data, 'timestamp') and data.timestamp else None
                            }
                    except Exception as e:
                        logger.warning(f"Error fetching data for {symbol}: {e}")
                
                if stock_data:
                    financial_data['stock_data'] = stock_data
            
            # Economic data would be gathered here if World Bank integration was available
            if analysis['intent'] == 'economic_analysis':
                # Mock economic data for demonstration
                financial_data['economic_data'] = {
                    'gdp_growth': 2.1,  # Mock GDP growth rate
                    'inflation_rate': 3.2  # Mock inflation rate
                }
            
            # Generate portfolio data for portfolio analysis
            if analysis['intent'] == 'portfolio_analysis':
                # Mock portfolio data - in real implementation, this would come from portfolio management system
                portfolio_data = {
                    'ytd_return': 12.5,  # Mock YTD return
                    'benchmark_return': 8.3,  # Mock S&P 500 YTD
                    'total_value': 1250000,  # Mock portfolio value
                    'top_holdings': [
                        {'symbol': 'AAPL', 'weight': 15.2, 'return': 18.5},
                        {'symbol': 'MSFT', 'weight': 12.8, 'return': 22.1},
                        {'symbol': 'GOOGL', 'weight': 10.5, 'return': 15.3}
                    ],
                    'sector_allocation': {
                        'Technology': 45.2,
                        'Healthcare': 18.7,
                        'Financial': 15.3,
                        'Consumer': 12.1,
                        'Other': 8.7
                    }
                }
                financial_data['portfolio_data'] = portfolio_data
            
            # Add market context data
            if analysis['intent'] in ['market_analysis', 'stock_analysis']:
                try:
                    # Get S&P 500 data as market context
                    sp500_data = await self.data_aggregator.get_stock_data('^GSPC')
                    if sp500_data:
                        financial_data['market_context'] = {
                            'sp500_price': sp500_data.price,
                            'sp500_change': sp500_data.change_percent,
                            'market_sentiment': 'bullish' if sp500_data.change_percent > 0 else 'bearish'
                        }
                except Exception as e:
                    logger.warning(f"Error fetching market context: {e}")
            
        except Exception as e:
            logger.error(f"Error gathering financial data: {e}")
        
        return financial_data
    
    async def _generate_ai_response(self, message: str, context: List[Dict], 
                                  analysis: Dict[str, Any], financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI response using Bedrock
        """
        try:
            # Build comprehensive prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(message, context, analysis, financial_data)
            
            # Call Bedrock
            if self.bedrock_client:
                response = self.bedrock_client.generate_text(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    max_tokens=2000,
                    temperature=0.7
                )
            else:
                raise Exception("Bedrock client not available")
            
            return {
                'response': response,
                'model_used': 'claude-3-haiku',
                'tokens_used': len(response.split()) * 1.3  # Rough estimate
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return {
                'response': self._generate_fallback_response(analysis, financial_data),
                'model_used': 'fallback',
                'error': str(e)
            }
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the AI"""
        return """You are FinSight AI, an expert financial assistant with access to real-time market data, economic indicators, and portfolio analytics. You provide comprehensive, accurate, and actionable financial insights.

Your capabilities include:
- Real-time stock market analysis
- Portfolio performance evaluation
- Economic indicator interpretation
- Risk assessment and compliance review
- Investment recommendations with proper disclaimers
- Market trend analysis and forecasting

Guidelines:
1. Always base responses on provided data when available
2. Clearly distinguish between facts and analysis/opinions
3. Include appropriate financial disclaimers for investment advice
4. Use professional but accessible language
5. Provide specific, actionable insights when possible
6. Acknowledge limitations and uncertainties
7. Format responses with clear structure and bullet points when helpful

Remember: You have access to current financial data and should reference it in your responses."""
    
    def _build_user_prompt(self, message: str, context: List[Dict], 
                          analysis: Dict[str, Any], financial_data: Dict[str, Any]) -> str:
        """Build the user prompt with context and data"""
        prompt_parts = []
        
        # Add conversation context
        if context:
            prompt_parts.append("CONVERSATION CONTEXT:")
            for msg in context[-3:]:  # Last 3 messages for context
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                prompt_parts.append(f"{role.upper()}: {content}")
            prompt_parts.append("")
        
        # Add current query analysis
        prompt_parts.append(f"CURRENT QUERY: {message}")
        prompt_parts.append(f"DETECTED INTENT: {analysis['intent']}")
        prompt_parts.append(f"QUERY COMPLEXITY: {analysis['complexity']}")
        prompt_parts.append("")
        
        # Add financial data
        if financial_data:
            prompt_parts.append("AVAILABLE FINANCIAL DATA:")
            
            if 'stock_data' in financial_data:
                prompt_parts.append("Stock Data:")
                for symbol, data in financial_data['stock_data'].items():
                    prompt_parts.append(f"- {symbol}: ${data['price']:.2f} ({data['change_percent']:+.2f}%)")
            
            if 'portfolio_data' in financial_data:
                portfolio = financial_data['portfolio_data']
                prompt_parts.append("Portfolio Data:")
                prompt_parts.append(f"- YTD Return: {portfolio['ytd_return']}%")
                prompt_parts.append(f"- S&P 500 YTD: {portfolio['benchmark_return']}%")
                prompt_parts.append(f"- Total Value: ${portfolio['total_value']:,}")
            
            if 'economic_data' in financial_data:
                econ = financial_data['economic_data']
                prompt_parts.append("Economic Data:")
                if 'gdp_growth' in econ:
                    prompt_parts.append(f"- GDP Growth: {econ['gdp_growth']}%")
                if 'inflation_rate' in econ:
                    prompt_parts.append(f"- Inflation Rate: {econ['inflation_rate']}%")
            
            if 'market_context' in financial_data:
                market = financial_data['market_context']
                prompt_parts.append("Market Context:")
                prompt_parts.append(f"- S&P 500: {market['sp500_change']:+.2f}% ({market['market_sentiment']})")
            
            prompt_parts.append("")
        
        prompt_parts.append("Please provide a comprehensive response based on the query and available data. Include specific insights, analysis, and actionable recommendations where appropriate.")
        
        return "\n".join(prompt_parts)
    
    def _generate_fallback_response(self, analysis: Dict[str, Any], financial_data: Dict[str, Any]) -> str:
        """Generate a fallback response when AI is unavailable"""
        intent = analysis['intent']
        
        if intent == 'portfolio_analysis' and 'portfolio_data' in financial_data:
            portfolio = financial_data['portfolio_data']
            return f"""Based on the available portfolio data:

**Performance Summary:**
- Your portfolio YTD return: {portfolio['ytd_return']}%
- S&P 500 benchmark YTD: {portfolio['benchmark_return']}%
- Outperformance: {portfolio['ytd_return'] - portfolio['benchmark_return']:+.1f}%

**Portfolio Value:** ${portfolio['total_value']:,}

Your portfolio is currently outperforming the S&P 500 benchmark, which indicates strong performance. However, I recommend consulting with a financial advisor for detailed analysis and recommendations.

*This is a simplified analysis. For comprehensive portfolio review, please consult with a qualified financial professional.*"""
        
        elif intent == 'stock_analysis' and 'stock_data' in financial_data:
            stocks = financial_data['stock_data']
            response_parts = ["**Stock Analysis Summary:**\n"]
            
            for symbol, data in stocks.items():
                change_direction = "up" if data['change_percent'] > 0 else "down"
                response_parts.append(f"- **{symbol}**: ${data['price']:.2f} ({data['change_percent']:+.2f}%) - Currently trending {change_direction}")
            
            response_parts.append("\n*For detailed investment recommendations, please consult with a qualified financial advisor.*")
            return "\n".join(response_parts)
        
        else:
            return """I understand you're looking for financial insights. While I'm currently experiencing some technical difficulties with my AI processing, I can still help you with:

- Real-time stock quotes and market data
- Portfolio performance tracking
- Economic indicator analysis
- Risk assessment and compliance reviews

Please try rephrasing your question or ask about specific stocks, economic indicators, or portfolio metrics."""
    
    def _update_chat_context(self, chat_id: str, user_message: str, ai_response: str):
        """Update chat context for future reference"""
        if chat_id not in self.chat_contexts:
            self.chat_contexts[chat_id] = []
        
        context = self.chat_contexts[chat_id]
        
        # Add user message and AI response
        context.extend([
            {'role': 'user', 'content': user_message, 'timestamp': datetime.now().isoformat()},
            {'role': 'assistant', 'content': ai_response, 'timestamp': datetime.now().isoformat()}
        ])
        
        # Keep only recent messages
        if len(context) > self.max_context_length:
            context = context[-self.max_context_length:]
        
        self.chat_contexts[chat_id] = context
    
    def get_chat_context(self, chat_id: str) -> List[Dict]:
        """Get chat context for a specific chat ID"""
        return self.chat_contexts.get(chat_id, [])
    
    def clear_chat_context(self, chat_id: str):
        """Clear chat context for a specific chat ID"""
        if chat_id in self.chat_contexts:
            del self.chat_contexts[chat_id] 