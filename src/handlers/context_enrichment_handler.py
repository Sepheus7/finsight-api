"""
Context Enrichment Handler for AWS Lambda
Adds relevant financial context to AI responses
"""

import json
import os
import boto3
import re
from datetime import datetime
from typing import List, Dict, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')
S3_BUCKET = os.environ.get('S3_BUCKET')

def lambda_handler(event, context):
    """
    Lambda handler for context enrichment
    """
    try:
        content = event.get('content', '')
        enrichment_level = event.get('enrichment_level', 'standard')
        request_id = event.get('request_id', context.aws_request_id)

        logger.info(f"Processing context enrichment for request {request_id} at level {enrichment_level}")

        enricher = ContextEnricher()
        
        # Identify topics that need context
        topics = enricher.identify_topics(content)
        logger.info(f"Identified topics: {topics}")

        # Get context for identified topics
        context_additions = enricher.get_context_for_topics(topics, enrichment_level)

        response_data = {
            'context_additions': context_additions,
            'topics_identified': topics,
            'enrichment_level': enrichment_level,
            'request_id': request_id
        }

        return response_data

    except Exception as e:
        logger.error(f"Context enrichment failed: {str(e)}")
        return {
            'error': str(e),
            'context_additions': [],
            'topics_identified': []
        }


class ContextEnricher:
    def __init__(self):
        self.context_cache = {}

    def identify_topics(self, text: str) -> List[str]:
        """Identify financial topics that could benefit from context"""
        topics = []
        
        topic_keywords = {
            "inflation": ["inflation", "cpi", "consumer price", "price level", "deflation"],
            "interest_rates": ["interest rate", "fed rate", "federal funds", "fed fund", "monetary policy", "yield"],
            "market_volatility": ["volatile", "volatility", "market risk", "uncertainty", "fluctuation"],
            "earnings": ["earnings", "eps", "quarterly results", "revenue", "profit", "income statement"],
            "economic_indicators": ["gdp", "unemployment", "jobs report", "economic growth", "recession"],
            "cryptocurrency": ["bitcoin", "crypto", "blockchain", "ethereum", "digital currency"],
            "commodities": ["gold", "oil", "silver", "commodity", "crude", "precious metals"],
            "housing_market": ["housing", "real estate", "mortgage", "home prices", "property market"],
            "banking": ["bank", "banking", "credit", "lending", "deposit", "loan"],
            "stock_market": ["stock", "equity", "shares", "market", "trading", "investment"],
            "bonds": ["bond", "treasury", "yield", "fixed income", "debt security"],
            "forex": ["currency", "exchange rate", "forex", "dollar", "euro", "yen"]
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return list(set(topics))  # Remove duplicates

    def get_context_for_topics(self, topics: List[str], enrichment_level: str) -> List[Dict[str, Any]]:
        """Get relevant context for identified topics"""
        enrichments = []
        
        for topic in topics:
            contexts = self._get_topic_context(topic, enrichment_level)
            enrichments.extend(contexts)
        
        # Sort by relevance score and limit based on enrichment level
        enrichments.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        if enrichment_level == 'basic':
            return enrichments[:2]
        elif enrichment_level == 'standard':
            return enrichments[:5]
        elif enrichment_level == 'comprehensive':
            return enrichments[:10]
        
        return enrichments[:5]  # Default

    def _get_topic_context(self, topic: str, enrichment_level: str) -> List[Dict[str, Any]]:
        """Get context for a specific topic"""
        context_data = {
            "inflation": [
                {
                    "type": "economic_indicator",
                    "content": "Current US inflation rate (CPI): Approximately 3.2% year-over-year as of latest data. The Federal Reserve targets 2% inflation.",
                    "relevance_score": 0.95,
                    "source": "Federal Reserve Economic Data (FRED)"
                },
                {
                    "type": "historical_context",
                    "content": "Inflation has been elevated since 2021, peaking at over 9% in June 2022 before moderating.",
                    "relevance_score": 0.8,
                    "source": "Bureau of Labor Statistics"
                }
            ],
            "interest_rates": [
                {
                    "type": "monetary_policy",
                    "content": "Federal funds rate: Currently 5.25-5.50% (as of latest FOMC meeting). This is the highest level since 2001.",
                    "relevance_score": 0.98,
                    "source": "Federal Reserve"
                },
                {
                    "type": "market_impact",
                    "content": "Higher interest rates typically reduce asset valuations and increase borrowing costs for companies and consumers.",
                    "relevance_score": 0.85,
                    "source": "Financial Theory"
                }
            ],
            "market_volatility": [
                {
                    "type": "market_data",
                    "content": "VIX (Volatility Index): Current levels indicate market uncertainty. Historical average is around 20.",
                    "relevance_score": 0.9,
                    "source": "CBOE"
                },
                {
                    "type": "risk_management",
                    "content": "High volatility periods require careful risk management and diversification strategies.",
                    "relevance_score": 0.75,
                    "source": "Investment Best Practices"
                }
            ],
            "earnings": [
                {
                    "type": "market_timing",
                    "content": "Earnings season occurs quarterly (Jan-Feb, Apr-May, Jul-Aug, Oct-Nov) when most companies report results.",
                    "relevance_score": 0.8,
                    "source": "Market Calendar"
                },
                {
                    "type": "analysis_note",
                    "content": "Focus on forward guidance and management commentary, not just backward-looking numbers.",
                    "relevance_score": 0.7,
                    "source": "Analyst Best Practices"
                }
            ],
            "economic_indicators": [
                {
                    "type": "economic_data",
                    "content": "Key indicators: GDP growth (~2-3% annually), unemployment rate (~3.5%), and leading economic indicators.",
                    "relevance_score": 0.85,
                    "source": "Bureau of Economic Analysis"
                }
            ],
            "cryptocurrency": [
                {
                    "type": "regulatory_warning",
                    "content": "Cryptocurrency investments are highly volatile and largely unregulated. Consider only risk capital.",
                    "relevance_score": 0.9,
                    "source": "SEC Investor Alerts"
                },
                {
                    "type": "market_data",
                    "content": "Bitcoin and crypto markets operate 24/7 and can experience extreme price swings.",
                    "relevance_score": 0.8,
                    "source": "Market Structure"
                }
            ],
            "commodities": [
                {
                    "type": "market_context",
                    "content": "Commodity prices are influenced by supply/demand, geopolitical events, and currency fluctuations.",
                    "relevance_score": 0.8,
                    "source": "Commodity Market Analysis"
                }
            ],
            "housing_market": [
                {
                    "type": "economic_context",
                    "content": "Housing market affected by interest rates, supply constraints, and demographic trends.",
                    "relevance_score": 0.85,
                    "source": "National Association of Realtors"
                }
            ],
            "banking": [
                {
                    "type": "regulatory_context",
                    "content": "Banks are heavily regulated with capital requirements and stress testing. FDIC insures deposits up to $250,000.",
                    "relevance_score": 0.9,
                    "source": "Federal Deposit Insurance Corporation"
                }
            ],
            "stock_market": [
                {
                    "type": "market_structure",
                    "content": "US stock market hours: 9:30 AM - 4:00 PM ET, Monday-Friday. Extended hours trading available.",
                    "relevance_score": 0.7,
                    "source": "NYSE/NASDAQ"
                },
                {
                    "type": "historical_context",
                    "content": "Long-term stock market returns have averaged ~10% annually, but with significant yearly variation.",
                    "relevance_score": 0.8,
                    "source": "Historical Market Data"
                }
            ],
            "bonds": [
                {
                    "type": "investment_context",
                    "content": "Bond prices move inversely to interest rates. Longer duration bonds are more sensitive to rate changes.",
                    "relevance_score": 0.85,
                    "source": "Fixed Income Principles"
                }
            ],
            "forex": [
                {
                    "type": "market_context",
                    "content": "Forex is the largest financial market, trading $7+ trillion daily. Currency values affected by economic policies.",
                    "relevance_score": 0.8,
                    "source": "Bank for International Settlements"
                }
            ]
        }

        topic_contexts = context_data.get(topic, [])
        
        # Add real-time context if comprehensive enrichment
        if enrichment_level == 'comprehensive':
            real_time_context = self._get_real_time_context(topic)
            if real_time_context:
                topic_contexts.extend(real_time_context)
        
        return topic_contexts

    def _get_real_time_context(self, topic: str) -> List[Dict[str, Any]]:
        """Get real-time context data (placeholder for external API integration)"""
        # In production, this would integrate with:
        # - Federal Reserve APIs (FRED)
        # - Financial news APIs
        # - Market data providers
        # - Economic calendar APIs
        
        real_time_contexts = []
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if topic == "interest_rates":
            real_time_contexts.append({
                "type": "real_time_data",
                "content": f"Latest fed funds futures indicate market expectations for rate changes. Data as of {current_time}.",
                "relevance_score": 0.9,
                "source": "Fed Funds Futures (CME)"
            })
        
        elif topic == "inflation":
            real_time_contexts.append({
                "type": "real_time_data",
                "content": f"Next CPI release scheduled for [next release date]. Market consensus estimates available. Data as of {current_time}.",
                "relevance_score": 0.85,
                "source": "Economic Calendar"
            })
        
        elif topic == "market_volatility":
            real_time_contexts.append({
                "type": "real_time_data",
                "content": f"Current market sentiment indicators and volatility measures. Data as of {current_time}.",
                "relevance_score": 0.8,
                "source": "Market Data Providers"
            })
        
        return real_time_contexts

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract financial entities from text"""
        entities = {
            'stocks': [],
            'currencies': [],
            'commodities': [],
            'indices': []
        }
        
        # Stock symbols (basic pattern)
        stock_pattern = r'\b[A-Z]{1,5}\b'
        potential_stocks = re.findall(stock_pattern, text)
        # Filter out common words that aren't stocks
        common_words = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HAD', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WHO', 'BOY', 'DID', 'USE', 'WAY', 'SHE', 'MANY', 'SOME', 'TIME', 'VERY', 'WHEN', 'MUCH', 'TAKE', 'THAN', 'ONLY', 'THINK', 'ALSO', 'BACK', 'AFTER', 'FIRST', 'WELL', 'YEAR', 'WORK', 'SUCH', 'MAKE', 'EVEN', 'HERE', 'GOOD', 'ANY', 'THOSE', 'BOTH', 'LET', 'PUT', 'TOO', 'OLD', 'WHY', 'LET', 'GREAT', 'SAME', 'BIG', 'GROUP', 'EVERY', 'STILL', 'JUST', 'KEEP', 'PART', 'HIGH', 'RIGHT', 'LARGE', 'SMALL', 'NEXT', 'EARLY', 'LONG', 'LITTLE', 'OWN', 'HAND', 'IMPORTANT', 'MOVE', 'DIFFERENT', 'PLACE', 'WANT', 'MADE', 'NEED', 'WHILE', 'COUNTRY', 'WITHOUT', 'WORLD', 'AGAINST', 'PROBLEM', 'GOVERNMENT', 'NUMBER', 'FACT', 'BUSINESS', 'COMPANY', 'SYSTEM', 'PROGRAM', 'QUESTION', 'RESULT', 'AREA', 'INFORMATION', 'DEVELOPMENT', 'WEEK', 'MONTH', 'NAME', 'SIDE', 'WATER', 'CASE', 'POINT', 'WAR', 'HISTORY', 'STUDY', 'BOOK', 'EYE', 'JOB', 'WORD', 'MONEY', 'STORY', 'SERVICE', 'STUDENT', 'ROOM', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'MOTHER', 'LOT', 'MIGHT', 'CAME', 'CALLED', 'MOST', 'PEOPLE', 'OVER', 'KNOW', 'WATER', 'THAN', 'CALL', 'FIRST', 'WHO', 'MAY', 'DOWN', 'SIDE', 'BEEN', 'NOW', 'FIND', 'HEAD', 'LONG', 'WAY', 'COME', 'COULD', 'LOOK', 'TIME', 'VERY', 'WHEN', 'COME', 'HERE', 'WELL', 'BACK', 'MUCH', 'BEFORE', 'THROUGH', 'WHEN', 'WHERE', 'MUCH', 'SHOULD', 'WELL', 'NEVER', 'LAST', 'ANOTHER', 'SEEMED', 'LIKE', 'BETWEEN', 'PLACE', 'TURNED', 'WANT', 'FOUND', 'EVERY', 'DOES', 'ANOTHER', 'CAME', 'WAY', 'COULD', 'AROUND', 'ALSO', 'YOUNG', 'DURING', 'MUCH', 'BEFORE', 'HERE', 'SOME', 'MORE', 'VERY', 'WHAT', 'SCHOOL', 'STILL', 'EVEN', 'NIGHT', 'MADE', 'BEFORE', 'HERE', 'ONLY', 'YEARS', 'CITY', 'UNDER', 'TOOK', 'SEEN', 'QUITE', 'UNTIL', 'ENOUGH', 'FAR', 'FEEL', 'TOGETHER', 'THOUGH', 'EYES', 'SOMETHING', 'FACE', 'TELL', 'ASKED', 'LATER', 'KNEW', 'IDEA', 'WHOLE', 'LESS', 'THOUGH', 'NOTHING', 'TURNED', 'ANOTHER', 'AROUND', 'MEANS', 'TOGETHER', 'TURNED', 'FOLLOWING', 'SEEMED', 'HOUSE', 'THINK', 'TURNED', 'MIGHT', 'ALONG', 'CLOSE', 'SOMETHING', 'BOTH', 'SINCE', 'TILL', 'REALLY', 'ALMOST', 'OFTEN', 'CERTAINLY', 'PROBABLY', 'ALREADY', 'SECOND', 'ENOUGH', 'BECAME', 'BECAME', 'SIDE', 'LOOKED', 'ANYTHING', 'WITHIN', 'EITHER', 'QUITE', 'TRYING', 'DONE', 'SOON', 'DURING', 'WITHOUT', 'AGAIN', 'HOWEVER', 'HEARD', 'SEEMED', 'FELT', 'KEPT', 'RATHER', 'BEGAN', 'ONCE', 'SEVERAL', 'USED', 'TOWARD', 'TAKEN', 'NEED', 'TAKEN', 'HOUSE', 'HOWEVER', 'ALONG', 'TURNED', 'ASKED', 'COURSE', 'CERTAIN', 'ITSELF', 'PERHAPS', 'NOTHING', 'EXAMPLE', 'EXPECT', 'ACROSS', 'ALTHOUGH', 'REMEMBER', 'USUALLY', 'CLOSE', 'COMMON', 'HOWEVER', 'INCLUDING', 'CONSIDERED', 'APPEARED', 'VARIOUS', 'PARTICULAR', 'KNOWN', 'RATHER', 'ACTUALLY', 'SURE', 'PERHAPS', 'NECESSARY', 'TOOK', 'SPECIAL', 'SMALL', 'CLEAR', 'FEELING', 'POLITICAL', 'COMPLETE', 'COLLEGE', 'TRYING', 'WORKED', 'CERTAIN', 'FULL', 'ALMOST', 'ENOUGH', 'TOOK', 'HARD', 'USING', 'GIVEN', 'REAL', 'DIFFICULT', 'GETTING', 'NOTHING', 'COURSE', 'AMONG', 'ANYTHING', 'SOCIAL', 'LONGER', 'SIMPLY', 'VARIOUS', 'QUITE', 'CLASS', 'STILL', 'PROBABLY', 'HUMAN', 'ACTUALLY', 'AVAILABLE', 'SURE', 'UNDERSTAND', 'WHETHER', 'WITHOUT', 'MEMBERS', 'RATHER', 'SINCE', 'OFTEN', 'PROVIDE', 'HOWEVER', 'HISTORY', 'DEVELOPMENT', 'DURING', 'REALLY', 'SOMETHING', 'CERTAINLY', 'CLEAR', 'THOUGH', 'EXPERIENCE', 'TRYING', 'MAJOR', 'PROBABLY', 'EVERYTHING', 'ESPECIALLY', 'HIMSELF', 'HELP', 'GOING', 'WANT', 'FACT', 'POSSIBLE', 'TODAY', 'OTHERS', 'CONTROL', 'OFFICE', 'NATIONAL', 'SEVERAL', 'INTEREST', 'POLICY', 'MEANS', 'TAKING', 'RATHER', 'QUITE', 'ITSELF', 'STARTED', 'COURSE', 'GETTING', 'MAKING', 'CHANGES', 'WORKING', 'GENERAL', 'AMERICAN', 'DOING', 'EITHER', 'USUALLY', 'COMING', 'RUNNING', 'BETTER', 'NOTHING', 'EXCEPT', 'TOLD', 'CANNOT', 'TIMES', 'LIKELY', 'DURING', 'INCLUDING', 'UNTIL', 'SOMETHING', 'ACTUALLY', 'IMPORTANT', 'THEMSELVES', 'THINGS', 'THOUGHT', 'LOOKING', 'DIFFERENT', 'PERHAPS', 'FOLLOWING', 'SEEMED', 'LATER', 'PROBABLY', 'BEGAN', 'AMONG', 'THOSE', 'NEVER', 'BEING', 'SINCE', 'ALONE', 'QUITE', 'ENOUGH', 'HOWEVER', 'EXAMPLE', 'BETWEEN', 'OFTEN', 'CERTAINLY', 'ALMOST', 'ALTHOUGH', 'CLOSE', 'MIGHT', 'GOING', 'SEEMED', 'NEXT', 'FEEL', 'TRYING', 'MEAN', 'HELP', 'ASKED', 'TURNED', 'GETTING', 'LESS', 'COURSE', 'NOTHING', 'TIMES', 'HUMAN', 'THOUGHT', 'SOCIAL', 'SINCE', 'PROVIDE', 'CURRENT', 'AVAILABLE', 'EITHER', 'INCREASE', 'NOTHING', 'THEMSELVES', 'BUSINESS', 'FEELING', 'MAKING', 'MEANS', 'MONEY', 'EVERY', 'USING', 'POINT', 'DIFFICULT', 'HOWEVER', 'PROBABLY', 'HARD', 'TRYING', 'CERTAINLY', 'WITHOUT', 'MAKING', 'WITHIN', 'POLITICAL', 'CLEAR', 'TRYING', 'MAJOR', 'CERTAINLY', 'ACTUALLY', 'USUALLY', 'SOMETHING', 'RATHER', 'ALMOST', 'PARTICULARLY', 'NOTHING', 'PROBABLY', 'BEING', 'QUITE', 'HOWEVER', 'CERTAINLY', 'STILL', 'OFTEN', 'THOUGH', 'LIKELY', 'GETTING', 'ESPECIALLY', 'NOTHING', 'THOUGH', 'PROBABLY', 'ACTUALLY', 'LIKELY', 'ALMOST', 'MAKING', 'USUALLY', 'QUITE', 'REALLY', 'OFTEN', 'CERTAINLY', 'PROBABLY', 'MAYBE', 'AMERICAN', 'SHALL'}
        stocks = [s for s in potential_stocks if s not in common_words and len(s) <= 5]
        entities['stocks'] = list(set(stocks))
        
        # Currency pairs
        currency_pattern = r'\b[A-Z]{3}\/[A-Z]{3}\b|\b[A-Z]{6}\b'
        entities['currencies'] = re.findall(currency_pattern, text)
        
        return entities
