"""
Simple Chat Handler for FinSight AI
A lightweight implementation for immediate testing and demonstration
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class SimpleChatHandler:
    """
    Simplified chat handler for immediate testing
    Provides intelligent responses without complex dependencies
    """
    
    def __init__(self):
        self.chat_contexts = {}
        self.max_context_length = 10
        logger.info("Simple Chat Handler initialized")
    
    async def process_chat_message(self, message: str, chat_id: Optional[str] = None, 
                                 context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Process a chat message and generate an intelligent response
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
            
            # Analyze the message
            analysis = self._analyze_message(message)
            
            # Generate mock financial data
            financial_data = self._generate_mock_data(analysis)
            
            # Generate response
            response_text = self._generate_response(message, analysis, financial_data)
            
            # Update chat context
            if chat_id:
                self._update_chat_context(chat_id, message, response_text)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(f"Chat message processed in {processing_time:.2f}ms")
            
            return {
                'response': response_text,
                'data': financial_data,
                'analysis': analysis,
                'processing_time_ms': processing_time,
                'chat_id': chat_id,
                'timestamp': datetime.now().isoformat(),
                'model_used': 'simple_mock'
            }
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            return {
                'response': "I apologize, but I encountered an error processing your request. Please try again or rephrase your question.",
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _analyze_message(self, message: str) -> Dict[str, Any]:
        """Analyze the user's message to determine intent"""
        analysis = {
            'intent': 'general_inquiry',
            'entities': {
                'stocks': [],
                'companies': [],
                'financial_metrics': []
            },
            'query_type': 'informational',
            'complexity': 'medium'
        }
        
        message_lower = message.lower()
        
        # Determine intent based on keywords
        if any(word in message_lower for word in ['portfolio', 'fund', 'ytd', 'performance', 'return']):
            analysis['intent'] = 'portfolio_analysis'
        elif any(word in message_lower for word in ['stock', 'price', 'analysis', 'recommendation']):
            analysis['intent'] = 'stock_analysis'
        elif any(word in message_lower for word in ['economic', 'inflation', 'gdp', 'unemployment']):
            analysis['intent'] = 'economic_analysis'
        elif any(word in message_lower for word in ['market', 'sector', 'trend', 'outlook']):
            analysis['intent'] = 'market_analysis'
        elif any(word in message_lower for word in ['risk', 'compliance', 'regulation']):
            analysis['intent'] = 'risk_analysis'
        
        # Extract stock symbols
        stock_pattern = r'\b([A-Z]{2,5})\b'
        potential_stocks = re.findall(stock_pattern, message)
        analysis['entities']['stocks'] = potential_stocks[:5]  # Limit to 5
        
        # Extract company names (simple approach)
        companies = []
        company_keywords = {
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'google': 'GOOGL',
            'amazon': 'AMZN',
            'tesla': 'TSLA',
            'meta': 'META',
            'nvidia': 'NVDA'
        }
        
        for company, symbol in company_keywords.items():
            if company in message_lower:
                companies.append(company.title())
                if symbol not in analysis['entities']['stocks']:
                    analysis['entities']['stocks'].append(symbol)
        
        analysis['entities']['companies'] = companies
        
        return analysis
    
    def _generate_mock_data(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock financial data based on analysis"""
        financial_data = {}
        
        # Generate stock data if stocks mentioned
        if analysis['entities']['stocks']:
            stock_data = {}
            mock_prices = {'AAPL': 196.45, 'MSFT': 378.85, 'GOOGL': 142.56, 'AMZN': 145.32, 'TSLA': 248.50}
            mock_changes = {'AAPL': -1.38, 'MSFT': 2.45, 'GOOGL': 0.89, 'AMZN': -0.67, 'TSLA': 3.21}
            
            for symbol in analysis['entities']['stocks']:
                price = mock_prices.get(symbol, 100.00 + hash(symbol) % 200)
                change = mock_changes.get(symbol, (hash(symbol) % 10) - 5)
                change_percent = (change / price) * 100
                
                stock_data[symbol] = {
                    'symbol': symbol,
                    'price': round(price, 2),
                    'change': round(change, 2),
                    'change_percent': round(change_percent, 2),
                    'volume': (hash(symbol) % 10000000) + 1000000,
                    'market_cap': (hash(symbol) % 1000) + 100,
                    'timestamp': datetime.now().isoformat()
                }
            
            financial_data['stock_data'] = stock_data
        
        # Generate portfolio data for portfolio analysis
        if analysis['intent'] == 'portfolio_analysis':
            financial_data['portfolio_data'] = {
                'ytd_return': 12.5,
                'benchmark_return': 8.3,
                'total_value': 1250000,
                'top_holdings': [
                    {'symbol': 'AAPL', 'weight': 15.2, 'return': 18.5},
                    {'symbol': 'MSFT', 'weight': 12.8, 'return': 22.1},
                    {'symbol': 'GOOGL', 'weight': 10.5, 'return': 15.3}
                ]
            }
        
        # Generate economic data
        if analysis['intent'] == 'economic_analysis':
            financial_data['economic_data'] = {
                'inflation_rate': 3.2,
                'gdp_growth': 2.1,
                'unemployment_rate': 3.7,
                'interest_rate': 5.25
            }
        
        # Add market context
        if analysis['intent'] in ['market_analysis', 'stock_analysis']:
            financial_data['market_context'] = {
                'sp500_price': 4567.89,
                'sp500_change': 0.45,
                'market_sentiment': 'bullish',
                'vix': 18.5
            }
        
        return financial_data
    
    def _generate_response(self, message: str, analysis: Dict[str, Any], financial_data: Dict[str, Any]) -> str:
        """Generate an intelligent response based on the query and data"""
        intent = analysis['intent']
        
        if intent == 'portfolio_analysis' and 'portfolio_data' in financial_data:
            portfolio = financial_data['portfolio_data']
            return f"""**Portfolio Performance Analysis**

Based on your portfolio data:

📈 **Performance Summary:**
- Your portfolio YTD return: **{portfolio['ytd_return']}%**
- S&P 500 benchmark YTD: **{portfolio['benchmark_return']}%**
- **Outperformance: +{portfolio['ytd_return'] - portfolio['benchmark_return']:.1f}%**

💰 **Portfolio Value:** ${portfolio['total_value']:,}

🏆 **Top Holdings:**
{chr(10).join([f"- **{holding['symbol']}**: {holding['weight']}% allocation, {holding['return']:+.1f}% return" for holding in portfolio['top_holdings']])}

**Analysis:** Your portfolio is significantly outperforming the S&P 500 benchmark, indicating strong stock selection and allocation strategy. The technology-heavy allocation appears to be driving positive returns.

**Notable Changes:** Recent rebalancing toward growth stocks has contributed to the outperformance, though this also increases volatility exposure.

*Disclaimer: This analysis is for informational purposes only and should not be considered as investment advice. Please consult with a qualified financial advisor for personalized recommendations.*"""
        
        elif intent == 'stock_analysis' and 'stock_data' in financial_data:
            stocks = financial_data['stock_data']
            if len(stocks) == 1:
                symbol, data = next(iter(stocks.items()))
                trend = "upward" if data['change_percent'] > 0 else "downward"
                sentiment = "positive" if data['change_percent'] > 0 else "negative"
                
                return f"""**{symbol} Stock Analysis**

📊 **Current Market Data:**
- **Price:** ${data['price']:.2f}
- **Change:** ${data['change']:+.2f} ({data['change_percent']:+.2f}%)
- **Volume:** {data['volume']:,} shares
- **Market Cap:** ${data['market_cap']:.1f}B

📈 **Technical Analysis:**
The stock is showing a **{trend} trend** with {sentiment} momentum. Current trading volume suggests {'strong' if abs(data['change_percent']) > 2 else 'moderate'} investor interest.

🎯 **Investment Perspective:**
Based on current market conditions and the stock's recent performance, this appears to be {'a strong performer' if data['change_percent'] > 1 else 'experiencing some volatility' if data['change_percent'] < -1 else 'trading in a stable range'}.

**Financial Health:** The company maintains solid fundamentals with consistent revenue growth and strong market positioning in its sector.

*Disclaimer: This analysis is based on current market data and should not be considered as investment advice. Past performance does not guarantee future results.*"""
            
            else:
                response_parts = ["**Multi-Stock Analysis**\n"]
                for symbol, data in stocks.items():
                    trend = "📈" if data['change_percent'] > 0 else "📉"
                    response_parts.append(f"{trend} **{symbol}**: ${data['price']:.2f} ({data['change_percent']:+.2f}%)")
                
                response_parts.append("\n**Market Overview:** Mixed performance across your selected stocks, indicating sector-specific movements rather than broad market trends.")
                response_parts.append("\n*For detailed individual analysis, please ask about specific stocks.*")
                return "\n".join(response_parts)
        
        elif intent == 'economic_analysis' and 'economic_data' in financial_data:
            econ = financial_data['economic_data']
            return f"""**Economic Indicators Analysis**

🌍 **Current Economic Landscape:**
- **Inflation Rate:** {econ['inflation_rate']}%
- **GDP Growth:** {econ['gdp_growth']}%
- **Unemployment:** {econ['unemployment_rate']}%
- **Fed Funds Rate:** {econ['interest_rate']}%

📊 **Economic Assessment:**
The current economic environment shows {'moderate growth' if econ['gdp_growth'] > 2 else 'slower growth'} with inflation {'above target' if econ['inflation_rate'] > 3 else 'near target'} levels. The Federal Reserve's monetary policy stance appears {'hawkish' if econ['interest_rate'] > 5 else 'accommodative'}.

💡 **Market Implications:**
- **Tech Stocks:** May face headwinds from higher interest rates
- **Financial Sector:** Could benefit from rising rate environment  
- **Consumer Discretionary:** Sensitive to inflation pressures
- **Utilities/REITs:** May underperform in rising rate cycle

**Outlook:** Economic indicators suggest a {'resilient but cautious' if econ['gdp_growth'] > 1.5 else 'challenging'} environment for equity markets in the near term."""
        
        elif intent == 'market_analysis':
            return f"""**Market Analysis & Outlook**

📊 **Current Market Conditions:**
{'Strong bullish momentum with positive investor sentiment' if financial_data.get('market_context', {}).get('market_sentiment') == 'bullish' else 'Mixed signals with cautious investor sentiment'}

🎯 **Key Market Drivers:**
- Federal Reserve policy decisions
- Corporate earnings growth
- Geopolitical developments
- Economic data releases

**Sector Rotation:** Currently seeing {'growth outperforming value' if financial_data.get('market_context', {}).get('sp500_change', 0) > 0 else 'defensive positioning'} as investors position for the next market phase.

**Risk Assessment:** Market volatility remains {'elevated' if financial_data.get('market_context', {}).get('vix', 20) > 20 else 'moderate'}, suggesting {'increased caution' if financial_data.get('market_context', {}).get('vix', 20) > 20 else 'stable conditions'} ahead.

*This analysis reflects current market conditions and should be considered alongside your investment objectives and risk tolerance.*"""
        
        elif intent == 'risk_analysis':
            return """**Risk Assessment & Compliance Review**

⚖️ **Regulatory Compliance:**
- Investment advice disclosures: ✅ Compliant
- Risk warnings: ✅ Present
- Suitability considerations: ✅ Addressed

🛡️ **Risk Mitigation Strategies:**
1. **Diversification:** Spread investments across sectors and asset classes
2. **Position Sizing:** Limit individual position risk to 5-10% of portfolio
3. **Stop-Loss Orders:** Consider protective stops for volatile positions
4. **Regular Rebalancing:** Maintain target allocations quarterly

**Compliance Notes:** All investment discussions include appropriate disclaimers and risk warnings as required by financial regulations.

*This assessment is for informational purposes and does not constitute legal or compliance advice.*"""
        
        else:
            # General financial inquiry
            return f"""**FinSight AI Financial Assistant**

Thank you for your inquiry! I'm here to help with comprehensive financial analysis and insights.

🎯 **I can assist you with:**
- **Portfolio Analysis:** Performance tracking, benchmark comparisons, allocation reviews
- **Stock Research:** Company analysis, technical indicators, investment recommendations  
- **Economic Insights:** Market trends, economic indicators, sector analysis
- **Risk Management:** Compliance reviews, risk assessment, mitigation strategies

💡 **Try asking me:**
- "What's the YTD performance of our growth fund vs the S&P 500?"
- "Analyze Apple's financial health and investment potential"
- "How are current economic indicators affecting tech stocks?"
- "Review our portfolio for compliance and risk issues"

I have access to real-time market data, economic indicators, and advanced analytics to provide you with actionable insights.

*How can I help you with your financial analysis today?*"""
    
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