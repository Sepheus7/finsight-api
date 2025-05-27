"""
Optimized Enhanced Fact Check Handler with Parallel Processing
Uses async/await and connection pooling for improved performance
"""

import json
import os
import boto3
import asyncio
import aiohttp
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from concurrent.futures import ThreadPoolExecutor
import time

# Import models and utilities
try:
    from ..models.financial_models import FinancialClaim, FactCheckResult, ClaimType, RiskLevel
    from ..utils.llm_claim_extractor import LLMClaimExtractor
    from ..utils.enhanced_ticker_resolver import EnhancedTickerResolver
    from ..utils.performance_optimizer import get_optimizer, async_cached, sync_cached
except ImportError:
    from models.financial_models import FinancialClaim, FactCheckResult, ClaimType, RiskLevel
    from utils.llm_claim_extractor import LLMClaimExtractor
    from utils.enhanced_ticker_resolver import EnhancedTickerResolver
    from utils.performance_optimizer import get_optimizer, async_cached, sync_cached

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')
S3_BUCKET = os.environ.get('S3_BUCKET')

def lambda_handler(event, context):
    """
    Optimized Lambda handler for fact-checking financial claims
    """
    try:
        content = event.get('content', '')
        request_id = event.get('request_id', context.aws_request_id)
        use_llm = event.get('use_llm', True)

        logger.info(f"Processing OPTIMIZED fact check for request {request_id} (LLM: {use_llm})")
        
        start_time = time.time()

        # Use asyncio for parallel processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            fact_checker = OptimizedFinancialFactChecker(use_llm=use_llm)
            result = loop.run_until_complete(
                fact_checker.process_claims_async(content, request_id)
            )
        finally:
            loop.close()

        processing_time = (time.time() - start_time) * 1000
        logger.info(f"OPTIMIZED fact check completed in {processing_time:.1f}ms")

        result.update({
            'processing_time_ms': processing_time,
            'optimization_enabled': True
        })

        return result

    except Exception as e:
        logger.error(f"Optimized fact checking failed: {str(e)}")
        return {
            'error': str(e),
            'fact_checks': [],
            'claims_processed': 0,
            'llm_enabled': False,
            'optimization_enabled': True
        }


class OptimizedFinancialFactChecker:
    """Optimized fact checker with parallel processing"""
    
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.cache_ttl_minutes = 15
        self.ticker_resolver = EnhancedTickerResolver()
        self.llm_extractor = None
        
        if self.use_llm:
            try:
                self.llm_extractor = LLMClaimExtractor()
                logger.info("LLM claim extractor initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM extractor: {str(e)}")
                self.use_llm = False

    async def process_claims_async(self, content: str, request_id: str) -> Dict[str, Any]:
        """
        Main async processing pipeline
        """
        optimizer = get_optimizer()
        await optimizer.initialize_session()
        
        try:
            # Extract claims (can be done synchronously as it's fast)
            claims = await self.extract_financial_claims_async(content)
            logger.info(f"Extracted {len(claims)} claims for verification")

            if not claims:
                return {
                    'fact_checks': [],
                    'claims_processed': 0,
                    'request_id': request_id,
                    'llm_enabled': self.use_llm
                }

            # Verify claims in parallel
            fact_check_results = await self.verify_claims_parallel(claims)

            # Convert results to serializable format
            serializable_results = []
            for result in fact_check_results:
                if isinstance(result, FactCheckResult):
                    serializable_results.append({
                        'claim': result.claim.text,
                        'claim_type': result.claim.claim_type.value,
                        'entities': result.claim.entities,
                        'values': result.claim.values,
                        'verified': result.verified,
                        'confidence': result.confidence,
                        'source': result.source,
                        'explanation': result.explanation,
                        'actual_value': result.actual_value,
                        'discrepancy': result.discrepancy
                    })
                else:
                    # Handle error results
                    serializable_results.append(result)

            return {
                'fact_checks': serializable_results,
                'claims_processed': len(claims),
                'request_id': request_id,
                'llm_enabled': self.use_llm
            }
            
        finally:
            await optimizer.close_session()

    async def extract_financial_claims_async(self, content: str) -> List[FinancialClaim]:
        """
        Extract financial claims using LLM or regex patterns
        """
        try:
            if self.use_llm and self.llm_extractor:
                # Run LLM extraction in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=2) as executor:
                    future = loop.run_in_executor(
                        executor, 
                        self.llm_extractor.extract_claims, 
                        content
                    )
                    llm_claims = await future
                
                # Convert LLM claims to FinancialClaim objects
                claims = []
                for claim_dict in llm_claims:
                    try:
                        claim = FinancialClaim(
                            text=claim_dict.get('claim', ''),
                            claim_type=ClaimType(claim_dict.get('type', 'unknown')),
                            entities=claim_dict.get('entities', {}),
                            values=claim_dict.get('values', {}),
                            confidence=claim_dict.get('confidence', 0.5),
                            context=claim_dict.get('context', ''),
                            risk_level=RiskLevel(claim_dict.get('risk_level', 'medium'))
                        )
                        claims.append(claim)
                    except Exception as e:
                        logger.warning(f"Failed to parse LLM claim: {str(e)}")
                        continue
                
                logger.info(f"LLM extracted {len(claims)} structured claims")
                return claims
            else:
                # Fallback to regex-based extraction
                return self.extract_regex_claims(content)
                
        except Exception as e:
            logger.error(f"Claim extraction failed: {str(e)}")
            return self.extract_regex_claims(content)

    @sync_cached(ttl=300)
    def extract_regex_claims(self, content: str) -> List[FinancialClaim]:
        """
        Fallback regex-based claim extraction with caching
        """
        import re
        
        claims = []
        
        # Stock price patterns
        price_patterns = [
            r'(\w+)\s+(?:stock|shares?|price)\s+(?:is|are|was|were|traded?|closed?)\s+(?:at\s+)?\$?(\d+(?:\.\d{2})?)',
            r'\$?(\d+(?:\.\d{2})?)\s+(?:per\s+share|share price|stock price)\s+(?:for\s+)?(\w+)',
            r'(\w+)\s+\$(\d+(?:\.\d{2})?)',
        ]
        
        for pattern in price_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match.groups()) >= 2:
                        company = match.group(1)
                        price = float(match.group(2))
                        
                        claim = FinancialClaim(
                            text=match.group(0),
                            claim_type=ClaimType.STOCK_PRICE,
                            entities={'company': company},
                            values={'price': price},
                            confidence=0.7,
                            context=content[:100] + "...",
                            risk_level=RiskLevel.MEDIUM
                        )
                        claims.append(claim)
                except (ValueError, IndexError):
                    continue
        
        # Market cap patterns
        mcap_patterns = [
            r'(\w+)\s+(?:market\s+cap|market\s+capitalization)\s+(?:is|was|of)\s+\$?(\d+(?:\.\d+)?)\s*(billion|trillion|million)?',
            r'market\s+cap\s+(?:of\s+)?(\w+)\s+\$?(\d+(?:\.\d+)?)\s*(billion|trillion|million)?'
        ]
        
        for pattern in mcap_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    company = match.group(1)
                    value = float(match.group(2))
                    unit = match.group(3).lower() if match.group(3) else 'billion'
                    
                    # Convert to actual value
                    multipliers = {'million': 1e6, 'billion': 1e9, 'trillion': 1e12}
                    actual_value = value * multipliers.get(unit, 1e9)
                    
                    claim = FinancialClaim(
                        text=match.group(0),
                        claim_type=ClaimType.MARKET_CAP,
                        entities={'company': company},
                        values={'market_cap': actual_value},
                        confidence=0.7,
                        context=content[:100] + "...",
                        risk_level=RiskLevel.MEDIUM
                    )
                    claims.append(claim)
                except (ValueError, IndexError):
                    continue
        
        logger.info(f"Regex extracted {len(claims)} claims")
        return claims

    async def verify_claims_parallel(self, claims: List[FinancialClaim]) -> List[FactCheckResult]:
        """
        Verify multiple claims in parallel
        """
        # Group claims by type for batch processing
        price_claims = [c for c in claims if c.claim_type == ClaimType.STOCK_PRICE]
        mcap_claims = [c for c in claims if c.claim_type == ClaimType.MARKET_CAP]
        other_claims = [c for c in claims if c.claim_type not in [ClaimType.STOCK_PRICE, ClaimType.MARKET_CAP]]
        
        # Create parallel verification tasks
        tasks = []
        
        if price_claims:
            tasks.append(self.verify_stock_prices_batch(price_claims))
        
        if mcap_claims:
            tasks.append(self.verify_market_caps_batch(mcap_claims))
        
        # Handle other claims individually (can be parallelized further)
        for claim in other_claims:
            tasks.append(self.verify_single_claim(claim))
        
        # Execute all verifications in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Flatten results
            all_results = []
            for result in results:
                if isinstance(result, list):
                    all_results.extend(result)
                elif isinstance(result, FactCheckResult):
                    all_results.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Verification task failed: {str(result)}")
                    # Create error result
                    all_results.append({
                        'claim': 'Unknown',
                        'verified': False,
                        'confidence': 0.0,
                        'explanation': f"Verification failed: {str(result)}",
                        'error': True
                    })
            
            return all_results
        else:
            return []

    async def verify_stock_prices_batch(self, claims: List[FinancialClaim]) -> List[FactCheckResult]:
        """
        Verify multiple stock price claims in parallel
        """
        # Extract unique companies
        companies = list(set(claim.entities.get('company', '') for claim in claims))
        
        # Resolve tickers for all companies in parallel
        ticker_tasks = [self.resolve_ticker_async(company) for company in companies]
        ticker_results = await asyncio.gather(*ticker_tasks, return_exceptions=True)
        
        # Build company -> ticker mapping
        company_ticker_map = {}
        for company, ticker_result in zip(companies, ticker_results):
            if isinstance(ticker_result, str) and ticker_result:
                company_ticker_map[company] = ticker_result
        
        # Fetch stock data for all valid tickers
        valid_tickers = list(company_ticker_map.values())
        stock_data_map = {}
        
        if valid_tickers:
            stock_data_map = await self.fetch_stock_data_batch(valid_tickers)
        
        # Verify each claim
        results = []
        for claim in claims:
            company = claim.entities.get('company', '')
            claimed_price = claim.values.get('price', 0)
            
            ticker = company_ticker_map.get(company)
            if ticker and ticker in stock_data_map:
                stock_data = stock_data_map[ticker]
                result = self.verify_stock_price_with_data(claim, stock_data)
            else:
                result = FactCheckResult(
                    claim=claim,
                    verified=False,
                    confidence=0.1,
                    source="ticker_resolution_failed",
                    explanation=f"Could not resolve ticker for company: {company}",
                    actual_value=None,
                    discrepancy=None
                )
            
            results.append(result)
        
        return results

    async def verify_market_caps_batch(self, claims: List[FinancialClaim]) -> List[FactCheckResult]:
        """
        Verify multiple market cap claims in parallel
        """
        # Similar to stock prices but for market cap data
        companies = list(set(claim.entities.get('company', '') for claim in claims))
        
        # Resolve tickers
        ticker_tasks = [self.resolve_ticker_async(company) for company in companies]
        ticker_results = await asyncio.gather(*ticker_tasks, return_exceptions=True)
        
        company_ticker_map = {}
        for company, ticker_result in zip(companies, ticker_results):
            if isinstance(ticker_result, str) and ticker_result:
                company_ticker_map[company] = ticker_result
        
        # Fetch market cap data
        valid_tickers = list(company_ticker_map.values())
        mcap_data_map = {}
        
        if valid_tickers:
            mcap_data_map = await self.fetch_market_cap_data_batch(valid_tickers)
        
        # Verify each claim
        results = []
        for claim in claims:
            company = claim.entities.get('company', '')
            claimed_mcap = claim.values.get('market_cap', 0)
            
            ticker = company_ticker_map.get(company)
            if ticker and ticker in mcap_data_map:
                mcap_data = mcap_data_map[ticker]
                result = self.verify_market_cap_with_data(claim, mcap_data)
            else:
                result = FactCheckResult(
                    claim=claim,
                    verified=False,
                    confidence=0.1,
                    source="ticker_resolution_failed",
                    explanation=f"Could not resolve market cap for company: {company}",
                    actual_value=None,
                    discrepancy=None
                )
            
            results.append(result)
        
        return results

    @async_cached(ttl=300)
    async def resolve_ticker_async(self, company: str) -> Optional[str]:
        """
        Resolve company name to ticker symbol with caching
        """
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=4) as executor:
                future = loop.run_in_executor(
                    executor, 
                    self.ticker_resolver.resolve_ticker, 
                    company
                )
                return await future
        except Exception as e:
            logger.error(f"Ticker resolution failed for {company}: {str(e)}")
            return None

    @async_cached(ttl=60)  # Cache stock data for 1 minute
    async def fetch_stock_data_batch(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Fetch stock data for multiple tickers in parallel
        """
        stock_data = {}
        
        # Use ThreadPoolExecutor for yfinance calls (they're blocking)
        loop = asyncio.get_event_loop()
        
        async def fetch_single_stock(ticker: str) -> tuple:
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = loop.run_in_executor(
                        executor,
                        self._fetch_stock_data_sync,
                        ticker
                    )
                    data = await future
                    return ticker, data
            except Exception as e:
                logger.error(f"Failed to fetch data for {ticker}: {str(e)}")
                return ticker, None
        
        # Fetch all stock data in parallel
        tasks = [fetch_single_stock(ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                ticker, data = result
                if data:
                    stock_data[ticker] = data
        
        logger.info(f"Fetched stock data for {len(stock_data)}/{len(tickers)} tickers")
        return stock_data

    def _fetch_stock_data_sync(self, ticker: str) -> Optional[Dict]:
        """
        Synchronous stock data fetching for use in thread pool
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
                'market_cap': info.get('marketCap'),
                'symbol': ticker,
                'name': info.get('longName', ''),
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"yfinance fetch failed for {ticker}: {str(e)}")
            return None

    async def fetch_market_cap_data_batch(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Fetch market cap data for multiple tickers
        This can reuse the stock data fetching with different focus
        """
        return await self.fetch_stock_data_batch(tickers)

    async def verify_single_claim(self, claim: FinancialClaim) -> FactCheckResult:
        """
        Verify a single claim (for non-batchable claim types)
        """
        # Placeholder for other claim types
        return FactCheckResult(
            claim=claim,
            verified=False,
            confidence=0.5,
            source="not_implemented",
            explanation="Verification not implemented for this claim type",
            actual_value=None,
            discrepancy=None
        )

    def verify_stock_price_with_data(self, claim: FinancialClaim, stock_data: Dict) -> FactCheckResult:
        """
        Verify stock price claim against fetched data
        """
        try:
            claimed_price = claim.values.get('price', 0)
            actual_price = stock_data.get('current_price')
            
            if actual_price is None:
                return FactCheckResult(
                    claim=claim,
                    verified=False,
                    confidence=0.1,
                    source="yahoo_finance",
                    explanation="Current price data not available",
                    actual_value=None,
                    discrepancy=None
                )
            
            # Calculate discrepancy
            discrepancy = abs(actual_price - claimed_price) / actual_price if actual_price > 0 else 1.0
            
            # Determine verification status (allow 5% margin)
            verified = discrepancy <= 0.05
            confidence = max(0.1, 1.0 - discrepancy)
            
            explanation = f"Claimed: ${claimed_price:.2f}, Actual: ${actual_price:.2f}"
            if not verified:
                explanation += f" (Discrepancy: {discrepancy:.1%})"
            
            return FactCheckResult(
                claim=claim,
                verified=verified,
                confidence=confidence,
                source="yahoo_finance",
                explanation=explanation,
                actual_value=actual_price,
                discrepancy=discrepancy
            )
            
        except Exception as e:
            logger.error(f"Stock price verification failed: {str(e)}")
            return FactCheckResult(
                claim=claim,
                verified=False,
                confidence=0.1,
                source="verification_error",
                explanation=f"Verification failed: {str(e)}",
                actual_value=None,
                discrepancy=None
            )

    def verify_market_cap_with_data(self, claim: FinancialClaim, mcap_data: Dict) -> FactCheckResult:
        """
        Verify market cap claim against fetched data
        """
        try:
            claimed_mcap = claim.values.get('market_cap', 0)
            actual_mcap = mcap_data.get('market_cap')
            
            if actual_mcap is None:
                return FactCheckResult(
                    claim=claim,
                    verified=False,
                    confidence=0.1,
                    source="yahoo_finance",
                    explanation="Market cap data not available",
                    actual_value=None,
                    discrepancy=None
                )
            
            # Calculate discrepancy
            discrepancy = abs(actual_mcap - claimed_mcap) / actual_mcap if actual_mcap > 0 else 1.0
            
            # Allow 10% margin for market cap (more volatile)
            verified = discrepancy <= 0.10
            confidence = max(0.1, 1.0 - discrepancy)
            
            # Format values for display
            claimed_b = claimed_mcap / 1e9
            actual_b = actual_mcap / 1e9
            
            explanation = f"Claimed: ${claimed_b:.2f}B, Actual: ${actual_b:.2f}B"
            if not verified:
                explanation += f" (Discrepancy: {discrepancy:.1%})"
            
            return FactCheckResult(
                claim=claim,
                verified=verified,
                confidence=confidence,
                source="yahoo_finance",
                explanation=explanation,
                actual_value=actual_mcap,
                discrepancy=discrepancy
            )
            
        except Exception as e:
            logger.error(f"Market cap verification failed: {str(e)}")
            return FactCheckResult(
                claim=claim,
                verified=False,
                confidence=0.1,
                source="verification_error",
                explanation=f"Verification failed: {str(e)}",
                actual_value=None,
                discrepancy=None
            )
