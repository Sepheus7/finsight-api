"""
Simplified Multi-Source Fact Checker for Demo
Self-contained implementation without complex import dependencies
"""

import json
import logging
import asyncio
import requests
import re
import os
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple data structures
class ClaimType(Enum):
    PRICE = "price"
    PERFORMANCE = "performance"
    FINANCIAL_METRIC = "financial_metric"
    MARKET_DATA = "market_data"
    ECONOMIC_INDICATOR = "economic_indicator"
    GENERAL = "general"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class FinancialClaim:
    text: str
    claim_type: ClaimType
    entities: List[str]
    confidence: float
    risk_level: RiskLevel
    
    def to_dict(self):
        return asdict(self)

@dataclass
class FactCheckResult:
    claim: FinancialClaim
    verified: bool
    confidence: float
    sources: List[str]
    explanation: str
    risk_assessment: str
    context_data: Dict[str, Any]
    
    def to_dict(self):
        result = asdict(self)
        result['claim'] = self.claim.to_dict()
        return result

class SimpleAlphaVantageClient:
    """Simple Alpha Vantage API client for financial data"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = "https://www.alphavantage.co/query"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FinSight-Demo/1.0'
        })
        self.available = self.api_key is not None
        
        if not self.available:
            logger.warning("Alpha Vantage API key not found. Set ALPHA_VANTAGE_API_KEY environment variable.")
    
    def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Get current stock price and basic info from Alpha Vantage"""
        if not self.available:
            return None
            
        try:
            # Use GLOBAL_QUOTE function for current price
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            quote = data.get('Global Quote', {})
            
            if quote:
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
                
        except Exception as e:
            logger.warning(f"Failed to get Alpha Vantage data for {symbol}: {e}")
        
        return None
    
    def get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """Get company overview data from Alpha Vantage"""
        if not self.available:
            return None
            
        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and 'Symbol' in data:
                return {
                    'symbol': data.get('Symbol'),
                    'company_name': data.get('Name'),
                    'market_cap': int(data.get('MarketCapitalization', 0)) if data.get('MarketCapitalization', '').isdigit() else None,
                    'pe_ratio': float(data.get('PERatio', 0)) if data.get('PERatio') != 'None' else None,
                    'dividend_yield': float(data.get('DividendYield', 0)) if data.get('DividendYield') != 'None' else None,
                    'sector': data.get('Sector'),
                    'industry': data.get('Industry'),
                    'exchange': data.get('Exchange'),
                    'currency': data.get('Currency'),
                    'country': data.get('Country'),
                    'source': 'alpha_vantage'
                }
                
        except Exception as e:
            logger.warning(f"Failed to get Alpha Vantage overview for {symbol}: {e}")
        
        return None
    
    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Any]:
        """Get data for multiple stock symbols"""
        results = {}
        for symbol in symbols:
            data = self.get_stock_data(symbol)
            if data:
                results[symbol] = data
            # Rate limiting - Alpha Vantage free tier allows 5 requests per minute
            if self.api_key and len(symbols) > 1:
                import time
                time.sleep(12)  # 12 seconds between requests for free tier
        return results

class SimpleWorldBankClient:
    """Simplified World Bank API client"""
    
    def __init__(self):
        self.base_url = "https://api.worldbank.org/v2"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FinSight-Demo/1.0'
        })
    
    def get_economic_data(self, country_code: str, indicator: str, years: int = 5) -> Dict[str, Any]:
        """Get economic data for a country and indicator"""
        try:
            end_year = datetime.now().year
            start_year = end_year - years
            
            url = f"{self.base_url}/country/{country_code}/indicator/{indicator}"
            params = {
                'format': 'json',
                'date': f"{start_year}:{end_year}",
                'per_page': 1000
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if len(data) > 1 and data[1]:
                return {
                    'country': country_code,
                    'indicator': indicator,
                    'data': data[1],
                    'source': 'World Bank'
                }
            
            return {'country': country_code, 'indicator': indicator, 'data': [], 'source': 'World Bank'}
            
        except Exception as e:
            logger.warning(f"Failed to get World Bank data: {e}")
            return {'error': str(e), 'source': 'World Bank'}
    
    def get_gdp_data(self, country_code: str = "USA") -> Dict[str, Any]:
        """Get GDP data for a country"""
        return self.get_economic_data(country_code, "NY.GDP.MKTP.CD")
    
    def get_inflation_data(self, country_code: str = "USA") -> Dict[str, Any]:
        """Get inflation data for a country"""
        return self.get_economic_data(country_code, "FP.CPI.TOTL.ZG")

class SimpleDataRegistry:
    """Simple data source registry with multi-provider fallback"""
    
    def __init__(self, enable_yahoo_finance: bool = True, enable_alpha_vantage: bool = True, enable_world_bank: bool = True):
        self.yahoo_finance = SimpleYahooFinanceClient() if enable_yahoo_finance else None
        self.alpha_vantage = SimpleAlphaVantageClient() if enable_alpha_vantage else None
        self.world_bank = SimpleWorldBankClient() if enable_world_bank else None
        self.available_sources = []
        
        if enable_yahoo_finance:
            self.available_sources.append('yahoo_finance')
        if enable_alpha_vantage and self.alpha_vantage and self.alpha_vantage.available:
            self.available_sources.append('alpha_vantage')
        if enable_world_bank:
            self.available_sources.append('world_bank')
    
    def query_stock_data(self, entities: List[str]) -> Dict[str, Any]:
        """Query stock data using fallback strategy: Yahoo Finance → Alpha Vantage → World Bank"""
        context_data = {}
        
        # Filter entities that look like stock tickers
        potential_tickers = []
        for entity in entities:
            # Stock tickers are typically 1-5 uppercase letters
            if entity and len(entity) <= 5 and entity.isupper() and entity.isalpha():
                potential_tickers.append(entity)
            # Also handle common company name to ticker mappings
            elif entity.lower() in ['apple', 'apple inc', 'apple inc.']:
                potential_tickers.append('AAPL')
            elif entity.lower() in ['tesla', 'tesla inc', 'tesla inc.']:
                potential_tickers.append('TSLA')
            elif entity.lower() in ['microsoft', 'microsoft corp', 'microsoft corporation']:
                potential_tickers.append('MSFT')
            elif entity.lower() in ['google', 'alphabet', 'alphabet inc']:
                potential_tickers.append('GOOGL')
            elif entity.lower() in ['amazon', 'amazon.com', 'amazon inc']:
                potential_tickers.append('AMZN')
        
        # Get stock data for potential tickers using fallback strategy
        if potential_tickers:
            for ticker in potential_tickers:
                stock_data = None
                sources_tried = []
                
                # Try Yahoo Finance first (primary)
                if self.yahoo_finance:
                    sources_tried.append('yahoo_finance')
                    try:
                        stock_data = self.yahoo_finance.get_stock_data(ticker)
                        if stock_data:
                            logger.info(f"Got {ticker} data from Yahoo Finance")
                    except Exception as e:
                        logger.warning(f"Yahoo Finance failed for {ticker}: {e}")
                
                # Fallback to Alpha Vantage if Yahoo Finance failed
                if not stock_data and self.alpha_vantage and self.alpha_vantage.available:
                    sources_tried.append('alpha_vantage')
                    try:
                        stock_data = self.alpha_vantage.get_stock_data(ticker)
                        if stock_data:
                            logger.info(f"Got {ticker} data from Alpha Vantage (fallback)")
                    except Exception as e:
                        logger.warning(f"Alpha Vantage failed for {ticker}: {e}")
                
                # Store successful result
                if stock_data:
                    context_data[f'stock_{ticker}'] = stock_data
                    context_data[f'stock_{ticker}']['sources_tried'] = sources_tried
                else:
                    logger.warning(f"All stock data sources failed for {ticker}. Tried: {sources_tried}")
        
        return context_data
    
    def query_economic_data(self, query: str, entities: List[str]) -> Dict[str, Any]:
        """Query economic data based on text and entities"""
        context_data = {}
        
        if not self.world_bank:
            return context_data
        
        # Simple heuristics for economic data queries
        if any(term in query.lower() for term in ['gdp', 'gross domestic product', 'economy']):
            for entity in entities:
                if len(entity) == 3 and entity.isupper():  # Likely country code
                    context_data[f'gdp_{entity}'] = self.world_bank.get_gdp_data(entity)
                elif entity.upper() in ['USA', 'US', 'UNITED STATES']:
                    context_data['gdp_USA'] = self.world_bank.get_gdp_data('USA')
        
        if any(term in query.lower() for term in ['inflation', 'price', 'cpi']):
            for entity in entities:
                if len(entity) == 3 and entity.isupper():  # Likely country code
                    context_data[f'inflation_{entity}'] = self.world_bank.get_inflation_data(entity)
                elif entity.upper() in ['USA', 'US', 'UNITED STATES']:
                    context_data['inflation_USA'] = self.world_bank.get_inflation_data('USA')
        
        return context_data
    
    def query_all_data(self, query: str, entities: List[str]) -> Dict[str, Any]:
        """Query all available data sources"""
        context_data = {}
        
        # Get stock data
        stock_data = self.query_stock_data(entities)
        context_data.update(stock_data)
        
        # Get economic data
        economic_data = self.query_economic_data(query, entities)
        context_data.update(economic_data)
        
        return context_data

class SimpleMultiSourceFactChecker:
    """Simplified multi-source fact checker with Yahoo Finance → Alpha Vantage → World Bank fallback"""
    
    def __init__(self, enable_world_bank: bool = True, enable_yahoo_finance: bool = True, enable_alpha_vantage: bool = True):
        self.enable_world_bank = enable_world_bank
        self.enable_yahoo_finance = enable_yahoo_finance
        self.enable_alpha_vantage = enable_alpha_vantage
        self.data_registry = SimpleDataRegistry(
            enable_yahoo_finance=enable_yahoo_finance,
            enable_alpha_vantage=enable_alpha_vantage,
            enable_world_bank=enable_world_bank
        )
        self.available = True
        
        logger.info(f"SimpleMultiSourceFactChecker initialized with Yahoo Finance: {enable_yahoo_finance}, Alpha Vantage: {enable_alpha_vantage}, World Bank: {enable_world_bank}")
        logger.info(f"Available sources: {self.data_registry.available_sources}")
    
    def extract_claims(self, content: str) -> List[FinancialClaim]:
        """Extract financial claims from content using enhanced decomposition"""
        claims = []
        
        # Enhanced claim extraction using sentence decomposition and pattern matching
        import re
        
        # Split content into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        logger.info(f"Processing {len(sentences)} sentences for claim extraction")
        
        for sentence in sentences:
            sentence_claims = self._extract_claims_from_sentence(sentence)
            claims.extend(sentence_claims)
            if sentence_claims:
                logger.info(f"Extracted {len(sentence_claims)} claims from: '{sentence[:100]}...'")
        
        # Additionally, look for complex sentences that contain multiple claims
        claims.extend(self._extract_multi_claim_sentences(content))
        
        # Remove duplicates based on text similarity
        claims = self._deduplicate_claims(claims)
        
        # If no individual claims found, create one for the whole content
        if not claims:
            claims.append(self._create_general_claim(content))
        
        logger.info(f"Final extracted claims: {len(claims)}")
        return claims
    
    def _extract_claims_from_sentence(self, sentence: str) -> List[FinancialClaim]:
        """Extract specific financial claims from a single sentence"""
        claims = []
        sentence_lower = sentence.lower()
        
        # Price/trading claims - Enhanced patterns
        price_patterns = [
            r'(\w+(?:\s+\w+)*)\s+\(([A-Z]{1,5})\)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?(?:trading\s+at|priced\s+at)\s+\$?(\d+(?:\.\d{2})?)',
            r'([A-Z]{1,5})\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?(?:trading\s+at|priced\s+at|price\s+is)\s+\$?(\d+(?:\.\d{2})?)',
            r'(\w+(?:\s+\w+)*)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?(?:trading\s+at|priced\s+at|costs)\s+\$?(\d+(?:\.\d{2})?)',
            r'\$?(\d+(?:\.\d{2})?)\s+(?:per\s+share|for\s+([A-Z]{1,5})|for\s+(\w+(?:\s+\w+)*))'
        ]
        
        for pattern in price_patterns:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                company = None
                ticker = None
                price = None
                
                # Pattern 1: Company (TICKER) trading at $price
                if len(groups) >= 3 and groups[0] and groups[1] and groups[2]:
                    company = groups[0].strip()
                    ticker = groups[1].strip()
                    price = groups[2].strip()
                # Pattern 2: TICKER trading at $price
                elif len(groups) >= 2 and groups[0] and groups[1]:
                    # Check if first group is a ticker (all caps, 1-5 chars)
                    if groups[0].isupper() and len(groups[0]) <= 5:
                        ticker = groups[0].strip()
                        company = ticker
                        price = groups[1].strip()
                    else:
                        company = groups[0].strip()
                        price = groups[1].strip()
                
                if company and price:
                    entities = self._extract_entities(sentence)
                    if ticker and ticker not in entities:
                        entities.append(ticker)
                    
                    claims.append(FinancialClaim(
                        text=f"{company} is trading at ${price}",
                        claim_type=ClaimType.PRICE,
                        entities=entities,
                        confidence=0.9,
                        risk_level=RiskLevel.LOW
                    ))
        
        # Performance/prediction claims - Enhanced to catch more patterns
        performance_patterns = [
            r'(will|guaranteed|definitely|certain)\s+(?:to\s+)?(?:increase|rise|go up|double|triple|gain)(?:\s+by\s+(\d+)%)?',
            r'(?:increase|rise|go up|double|triple)(?:\s+by\s+(\d+)%)?.*?(next\s+\w+|soon|tomorrow|this\s+\w+)',
            r'guaranteed.*?(?:profit|return|gain)',
            r'definitely.*?(?:increase|rise|double)',
            r'(?:expect|predict|forecast).*?(?:increase|rise|gain).*?(\d+)%',
            r'(?:will|should)\s+(?:reach|hit|achieve)\s+\$?(\d+)',
            r'(?:target|price target).*?\$?(\d+)'
        ]
        
        for pattern in performance_patterns:
            if re.search(pattern, sentence_lower):
                entities = self._extract_entities(sentence)
                # Extract percentage if mentioned
                percentage_match = re.search(r'(\d+)%', sentence)
                percentage = percentage_match.group(1) if percentage_match else None
                
                claim_text = sentence.strip()
                if percentage:
                    claim_text = f"Stock predicted to increase by {percentage}%"
                
                claims.append(FinancialClaim(
                    text=claim_text,
                    claim_type=ClaimType.PERFORMANCE,
                    entities=entities,
                    confidence=0.8,
                    risk_level=RiskLevel.CRITICAL  # Predictions are high risk
                ))
                break
        
        # Financial metrics claims
        metrics_patterns = [
            r'(revenue|profit|earnings|market cap|p/e ratio)',
            r'(quarterly|annual)\s+(?:results|earnings|revenue)',
            r'(dividend|yield|payout)',
            r'(eps|earnings per share)',
            r'(book value|assets|liabilities)'
        ]
        
        for pattern in metrics_patterns:
            if re.search(pattern, sentence_lower):
                entities = self._extract_entities(sentence)
                claims.append(FinancialClaim(
                    text=sentence.strip(),
                    claim_type=ClaimType.FINANCIAL_METRIC,
                    entities=entities,
                    confidence=0.7,
                    risk_level=RiskLevel.MEDIUM
                ))
                break
        
        return claims
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract potential stock tickers and company names"""
        import re
        entities = []
        
        # Extract stock tickers (1-5 capital letters)
        ticker_pattern = r'\b[A-Z]{1,5}\b'
        tickers = re.findall(ticker_pattern, text)
        entities.extend(tickers)
        
        # Extract company names (before "Inc", "Corp", "Ltd", etc.)
        company_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc|Corp|Corporation|Ltd|Limited|Co)\b'
        companies = re.findall(company_pattern, text)
        entities.extend(companies)
        
        return list(set(entities))  # Remove duplicates
    
    def _create_general_claim(self, content: str) -> FinancialClaim:
        """Create a general claim when no specific patterns are found"""
        content_lower = content.lower()
        entities = self._extract_entities(content)
        
        # Determine claim type based on content
        if any(kw in content_lower for kw in ['gdp', 'inflation', 'economy', 'growth', 'recession']):
            claim_type = ClaimType.ECONOMIC_INDICATOR
        elif any(kw in content_lower for kw in ['stock', 'price', 'trading', 'market']):
            claim_type = ClaimType.FINANCIAL_METRIC
        else:
            claim_type = ClaimType.GENERAL
        
        return FinancialClaim(
            text=content,
            claim_type=claim_type,
            entities=entities,
            confidence=0.6,
            risk_level=RiskLevel.MEDIUM
        )
    
    def verify_claim(self, claim: FinancialClaim) -> FactCheckResult:
        """Verify a financial claim using available data sources"""
        context_data = {}
        sources = []
        
        # Get context data from all available sources
        if self.data_registry:
            try:
                all_data = self.data_registry.query_all_data(claim.text, claim.entities)
                if all_data:
                    context_data.update(all_data)
                    
                    # Track which sources provided data
                    for key, value in all_data.items():
                        if isinstance(value, dict) and 'source' in value:
                            if value['source'] not in sources:
                                sources.append(value['source'])
                        elif key.startswith('stock_'):
                            if 'Yahoo Finance' not in sources:
                                sources.append('Yahoo Finance')
                        elif key.startswith(('gdp_', 'inflation_')):
                            if 'World Bank' not in sources:
                                sources.append('World Bank')
                
            except Exception as e:
                logger.warning(f"Failed to get context data: {e}")
        
        # Enhanced verification logic based on claim type and available data
        verified = True
        confidence = 0.7
        explanation = "Claim processed"
        
        if claim.claim_type == ClaimType.PRICE and context_data:
            # Check if we have stock data for price claims
            stock_entries = {k: v for k, v in context_data.items() if k.startswith('stock_')}
            if stock_entries:
                confidence = 0.9
                explanation = f"Price claim verified with real-time market data from {', '.join(sources)}"
                
                # Extract price from claim text
                import re
                price_match = re.search(r'\$?(\d+(?:\.\d{2})?)', claim.text)
                if price_match:
                    claimed_price = float(price_match.group(1))
                    
                    # Check against actual market data
                    for stock_key, stock_data in stock_entries.items():
                        if stock_data and 'current_price' in stock_data:
                            actual_price = stock_data['current_price']
                            price_diff = abs(claimed_price - actual_price) / actual_price
                            
                            if price_diff < 0.05:  # Within 5%
                                confidence = 0.95
                                explanation = f"Price claim accurate: claimed ${claimed_price}, actual ${actual_price}"
                            elif price_diff < 0.20:  # Within 20%
                                confidence = 0.75
                                explanation = f"Price claim approximately correct: claimed ${claimed_price}, actual ${actual_price}"
                            else:
                                confidence = 0.4
                                verified = False
                                explanation = f"Price claim inaccurate: claimed ${claimed_price}, actual ${actual_price}"
                            break
        
        elif claim.claim_type == ClaimType.PERFORMANCE:
            # Performance claims are speculative and should be flagged
            confidence = 0.3
            verified = False
            explanation = "Performance predictions cannot be verified and are speculative"
            if context_data:
                explanation += f". Market data available from {', '.join(sources)} for reference"
        
        elif context_data:
            confidence = 0.8
            explanation = f"Claim enhanced with additional context from {', '.join(sources)}"
        else:
            confidence = 0.6
            explanation = "Claim processed without additional external verification"
        
        risk_assessment = f"Risk level: {claim.risk_level.value}. "
        if context_data:
            risk_assessment += f"Enhanced with external data from: {', '.join(sources)}."
        else:
            risk_assessment += "Based on content analysis only."
        
        return FactCheckResult(
            claim=claim,
            verified=verified,
            confidence=confidence,
            sources=sources,
            explanation=explanation,
            risk_assessment=risk_assessment,
            context_data=context_data
        )
    
    def fact_check_content(self, content: str) -> Dict[str, Any]:
        """Fact check content and return enhanced results"""
        try:
            # Extract claims
            claims = self.extract_claims(content)
            
            # Verify each claim
            results = []
            for claim in claims:
                result = self.verify_claim(claim)
                results.append(result)
            
            # Aggregate results
            total_confidence = sum(r.confidence for r in results) / len(results) if results else 0.5
            all_sources = list(set(source for result in results for source in result.sources))
            
            enhanced_content = content
            if results and results[0].context_data:
                enhanced_content += f"\n\n[Enhanced with data from: {', '.join(all_sources)}]"
            
            return {
                'original_content': content,
                'enhanced_content': enhanced_content,
                'fact_check_results': [result.to_dict() for result in results],
                'overall_confidence': total_confidence,
                'sources_used': all_sources,
                'verification_timestamp': datetime.now().isoformat(),
                'multi_source_available': True
            }
            
        except Exception as e:
            logger.error(f"Error in fact checking: {e}")
            return {
                'original_content': content,
                'enhanced_content': content,
                'fact_check_results': [],
                'overall_confidence': 0.5,
                'sources_used': [],
                'verification_timestamp': datetime.now().isoformat(),
                'multi_source_available': False,
                'error': str(e)
            }
    
    def _extract_multi_claim_sentences(self, content: str) -> List[FinancialClaim]:
        """Extract claims from complex sentences containing multiple assertions"""
        claims = []
        import re
        
        # Look for sentences with multiple stock mentions
        multi_stock_pattern = r'([A-Z]{1,5})[^.!?]*(?:and|while|also)[^.!?]*([A-Z]{1,5})'
        matches = re.finditer(multi_stock_pattern, content)
        
        for match in matches:
            ticker1, ticker2 = match.groups()
            full_sentence = match.group(0)
            
            # Split the sentence around conjunctions and extract individual claims
            parts = re.split(r'\s+(?:and|while|also)\s+', full_sentence)
            for part in parts:
                if len(part.strip()) > 10:  # Only process meaningful parts
                    part_claims = self._extract_claims_from_sentence(part.strip())
                    claims.extend(part_claims)
        
        return claims
    
    def _deduplicate_claims(self, claims: List[FinancialClaim]) -> List[FinancialClaim]:
        """Remove duplicate claims based on text similarity"""
        unique_claims = []
        seen_texts = set()
        
        for claim in claims:
            # Normalize claim text for comparison
            normalized_text = re.sub(r'\s+', ' ', claim.text.lower().strip())
            
            # Check if we've seen a similar claim
            is_duplicate = False
            for seen_text in seen_texts:
                # Use simple similarity check (could be enhanced with more sophisticated NLP)
                if (normalized_text in seen_text or seen_text in normalized_text or
                    self._text_similarity(normalized_text, seen_text) > 0.8):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_claims.append(claim)
                seen_texts.add(normalized_text)
        
        return unique_claims
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity based on common words"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

class SimpleYahooFinanceClient:
    """Simple Yahoo Finance client for real-time stock data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FinSight-Demo/1.0'
        })
    
    def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Get current stock price and basic info"""
        try:
            # Try yfinance first if available
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="1d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    return {
                        'symbol': symbol,
                        'current_price': round(float(current_price), 2),
                        'company_name': info.get('longName', symbol),
                        'market_cap': info.get('marketCap'),
                        'pe_ratio': info.get('trailingPE'),
                        'volume': info.get('volume'),
                        'currency': info.get('currency', 'USD'),
                        'exchange': info.get('exchange'),
                        'last_updated': datetime.now().isoformat(),
                        'source': 'yfinance'
                    }
            except ImportError:
                pass
            
            # Fallback to direct Yahoo Finance API
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                chart = data.get('chart', {})
                result = chart.get('result', [])
                
                if result:
                    meta = result[0].get('meta', {})
                    return {
                        'symbol': symbol,
                        'current_price': meta.get('regularMarketPrice'),
                        'currency': meta.get('currency', 'USD'),
                        'market_cap': meta.get('marketCap'),
                        'volume': meta.get('regularMarketVolume'),
                        'exchange': meta.get('exchangeName'),
                        'last_updated': datetime.now().isoformat(),
                        'source': 'yahoo_finance_api'
                    }
        except Exception as e:
            logger.warning(f"Failed to get Yahoo Finance data for {symbol}: {e}")
        
        return None
    
    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Any]:
        """Get data for multiple stock symbols"""
        results = {}
        for symbol in symbols:
            data = self.get_stock_data(symbol)
            if data:
                results[symbol] = data
        return results

# Factory function for the integration
def get_simple_multi_source_fact_checker(enable_world_bank: bool = True, enable_yahoo_finance: bool = True, enable_alpha_vantage: bool = True) -> SimpleMultiSourceFactChecker:
    """Get a simple multi-source fact checker instance with Alpha Vantage support"""
    return SimpleMultiSourceFactChecker(
        enable_world_bank=enable_world_bank, 
        enable_yahoo_finance=enable_yahoo_finance,
        enable_alpha_vantage=enable_alpha_vantage
    )

def is_simple_multi_source_available() -> bool:
    """Check if simple multi-source components are available"""
    try:
        checker = get_simple_multi_source_fact_checker(enable_world_bank=False)
        return checker.available
    except Exception:
        return False

# Test function
def test_simple_multi_source():
    """Test the simple multi-source fact checker with Alpha Vantage integration"""
    checker = get_simple_multi_source_fact_checker(enable_world_bank=True, enable_yahoo_finance=True, enable_alpha_vantage=True)
    
    test_content = "Apple Inc (AAPL) stock is currently trading at $150 and will definitely increase by 50% next month. Tesla stock (TSLA) is also guaranteed to double in value."
    result = checker.fact_check_content(test_content)
    
    print("Simple Multi-Source Test Results (with Alpha Vantage):")
    print(f"Available Sources: {checker.data_registry.available_sources}")
    print(f"Original Content: {result['original_content']}")
    print(f"Enhanced Content: {result['enhanced_content'][:200]}...")
    print(f"Sources Used: {result['sources_used']}")
    print(f"Overall Confidence: {result['overall_confidence']}")
    print(f"Multi-Source Available: {result['multi_source_available']}")
    print(f"Number of Claims: {len(result['fact_check_results'])}")
    
    for i, claim_result in enumerate(result['fact_check_results'], 1):
        print(f"\nClaim {i}:")
        print(f"  Text: {claim_result['claim']['text']}")
        print(f"  Type: {claim_result['claim']['claim_type']}")
        print(f"  Verified: {claim_result['verified']}")
        print(f"  Confidence: {claim_result['confidence']}")
        print(f"  Sources: {claim_result['sources']}")
        
        # Show which data sources were tried for stock data
        if 'context_data' in claim_result:
            for key, value in claim_result['context_data'].items():
                if key.startswith('stock_') and isinstance(value, dict) and 'sources_tried' in value:
                    print(f"  Stock Data Sources Tried: {value['sources_tried']}")
                    print(f"  Stock Data Source Used: {value.get('source', 'unknown')}")
    
    return result

def test_alpha_vantage_specifically():
    """Test Alpha Vantage integration specifically"""
    print("\n=== Testing Alpha Vantage Integration ===")
    
    # Test with only Alpha Vantage enabled (no Yahoo Finance)
    checker = get_simple_multi_source_fact_checker(
        enable_world_bank=False, 
        enable_yahoo_finance=False, 
        enable_alpha_vantage=True
    )
    
    if 'alpha_vantage' not in checker.data_registry.available_sources:
        print("❌ Alpha Vantage not available (missing API key)")
        print("To test Alpha Vantage, set ALPHA_VANTAGE_API_KEY environment variable")
        return None
    
    test_content = "Microsoft (MSFT) stock price verification test"
    result = checker.fact_check_content(test_content)
    
    print(f"✅ Alpha Vantage Test Results:")
    print(f"Available Sources: {checker.data_registry.available_sources}")
    print(f"Sources Used: {result['sources_used']}")
    
    return result

if __name__ == "__main__":
    test_simple_multi_source()
    test_alpha_vantage_specifically()
