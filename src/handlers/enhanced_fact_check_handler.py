"""
Enhanced Fact Check Handler with LLM-Powered Claim Extraction
Combines traditional regex patterns with AI-powered claim detection
"""

import json
import os
import boto3
import re
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

# Import our new models and utilities
try:
    from ..models.financial_models import FinancialClaim, FactCheckResult, ClaimType, RiskLevel
    from ..utils.llm_claim_extractor import extract_financial_claims, LLMClaimExtractor
    from ..utils.enhanced_ticker_resolver import EnhancedTickerResolver
except ImportError:
    from models.financial_models import FinancialClaim, FactCheckResult, ClaimType, RiskLevel
    from utils.llm_claim_extractor import extract_financial_claims, LLMClaimExtractor
    from utils.enhanced_ticker_resolver import EnhancedTickerResolver

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')
S3_BUCKET = os.environ.get('S3_BUCKET')

def lambda_handler(event, context):
    """
    Enhanced Lambda handler for fact-checking financial claims with LLM support
    """
    try:
        content = event.get('content', '')
        request_id = event.get('request_id', context.aws_request_id)
        use_llm = event.get('use_llm', True)  # Enable LLM by default

        logger.info(f"Processing enhanced fact check for request {request_id} (LLM: {use_llm})")

        fact_checker = EnhancedFinancialFactChecker(use_llm=use_llm)
        
        # Extract claims using LLM or fallback to regex
        claims = fact_checker.extract_financial_claims(content)
        logger.info(f"Extracted {len(claims)} claims for verification")

        # Verify each claim
        fact_check_results = []
        for claim in claims:
            fact_check = fact_checker.verify_claim(claim)
            fact_check_results.append(fact_check)

        # Convert results to serializable format
        serializable_results = []
        for result in fact_check_results:
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

        response_data = {
            'fact_checks': serializable_results,
            'claims_processed': len(claims),
            'request_id': request_id,
            'llm_enabled': use_llm
        }

        return response_data

    except Exception as e:
        logger.error(f"Enhanced fact checking failed: {str(e)}")
        return {
            'error': str(e),
            'fact_checks': [],
            'claims_processed': 0,
            'llm_enabled': False
        }


class EnhancedFinancialFactChecker:
    """Enhanced fact checker with LLM-powered claim extraction"""
    
    def __init__(self, use_llm: bool = True):
        """Initialize the enhanced fact checker"""
        self.use_llm = use_llm
        self.cache_ttl_minutes = 15
        
        # Initialize enhanced ticker resolver for dynamic company-to-ticker mapping
        self.ticker_resolver = EnhancedTickerResolver()
        
        # Initialize LLM extractor
        if use_llm:
            llm_provider = os.environ.get('FINSIGHT_LLM_PROVIDER', 'ollama')
            self.claim_extractor = LLMClaimExtractor(provider=llm_provider)
        else:
            self.claim_extractor = LLMClaimExtractor(provider='regex')

    def extract_financial_claims(self, text: str) -> List[FinancialClaim]:
        """Extract financial claims using LLM or regex fallback"""
        try:
            if self.use_llm:
                logger.info("Extracting claims using LLM-powered extraction")
                claims = self.claim_extractor.extract_claims(text)
            else:
                logger.info("Extracting claims using regex patterns")
                claims = self.claim_extractor._extract_with_regex(text)
            
            # Enhance entity resolution
            enhanced_claims = self.claim_extractor.enhance_entities(claims)
            
            logger.info(f"Extracted {len(enhanced_claims)} enhanced financial claims")
            return enhanced_claims
            
        except Exception as e:
            logger.error(f"Claim extraction failed: {str(e)}")
            # Fallback to basic regex extraction
            return self._fallback_extract_claims(text)

    def verify_claim(self, claim: FinancialClaim) -> FactCheckResult:
        """Verify a financial claim against real market data"""
        logger.info(f"Verifying {claim.claim_type.value} claim: {claim.text}")

        try:
            if claim.claim_type == ClaimType.STOCK_PRICE:
                return self._verify_stock_price_claim(claim)
            elif claim.claim_type == ClaimType.MARKET_CAP:
                return self._verify_market_cap_claim(claim)
            elif claim.claim_type == ClaimType.REVENUE:
                return self._verify_revenue_claim(claim)
            elif claim.claim_type == ClaimType.INTEREST_RATE:
                return self._verify_interest_rate_claim(claim)
            elif claim.claim_type in [ClaimType.OPINION, ClaimType.PREDICTION]:
                return self._verify_subjective_claim(claim)
            else:
                return self._verify_generic_claim(claim)
                
        except Exception as e:
            logger.error(f"Verification failed for claim: {str(e)}")
            return FactCheckResult(
                claim=claim,
                verified=False,
                confidence=0.3,
                source='Error',
                explanation=f"Error during verification: {str(e)}"
            )

    def _verify_stock_price_claim(self, claim: FinancialClaim) -> FactCheckResult:
        """Verify stock price claims"""
        try:
            # Extract ticker symbol from entities using enhanced resolver
            ticker = None
            for entity in claim.entities:
                if entity.upper() in ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META'] or len(entity) <= 5:
                    ticker = entity.upper()
                    break
                else:
                    # Use enhanced ticker resolver for dynamic company-to-ticker mapping
                    ticker_match = self.ticker_resolver.resolve_ticker(entity)
                    if ticker_match and ticker_match.confidence > 0.7:
                        ticker = ticker_match.ticker
                        logger.debug(f"Resolved '{entity}' to ticker '{ticker}' (confidence: {ticker_match.confidence:.2f})")
                        break
            
            if not ticker:
                return FactCheckResult(
                    claim=claim,
                    verified=False,
                    confidence=0.3,
                    source='Symbol extraction',
                    explanation='Could not identify stock ticker symbol'
                )
            
            # Extract claimed price
            claimed_price = None
            for value in claim.values:
                try:
                    price_str = value.replace('$', '').replace(',', '')
                    claimed_price = float(price_str)
                    break
                except ValueError:
                    continue
            
            if not claimed_price:
                return FactCheckResult(
                    claim=claim,
                    verified=False,
                    confidence=0.3,
                    source='Price extraction',
                    explanation='Could not extract price value from claim'
                )
            
            # Get actual stock data
            actual_data = self._get_stock_data(ticker)
            if actual_data:
                actual_price = actual_data['current_price']
                price_diff = abs(actual_price - claimed_price) / actual_price
                
                if price_diff < 0.05:  # Within 5%
                    return FactCheckResult(
                        claim=claim,
                        verified=True,
                        confidence=0.95 - price_diff,
                        source='Yahoo Finance',
                        explanation=f"Current price ${actual_price:.2f} is within 5% of claimed ${claimed_price:.2f}",
                        actual_value=f"${actual_price:.2f}",
                        discrepancy=price_diff
                    )
                else:
                    return FactCheckResult(
                        claim=claim,
                        verified=False,
                        confidence=0.9,
                        source='Yahoo Finance',
                        explanation=f"Current price ${actual_price:.2f} differs significantly from claimed ${claimed_price:.2f} ({price_diff:.1%} difference)",
                        actual_value=f"${actual_price:.2f}",
                        discrepancy=price_diff
                    )
            else:
                return FactCheckResult(
                    claim=claim,
                    verified=False,
                    confidence=0.5,
                    source='Yahoo Finance',
                    explanation=f"Could not retrieve current price data for {ticker}"
                )
                
        except Exception as e:
            logger.error(f"Error verifying stock price claim: {str(e)}")
            return FactCheckResult(
                claim=claim,
                verified=False,
                confidence=0.3,
                source='Error',
                explanation=f"Error retrieving stock data: {str(e)}"
            )

    def _verify_market_cap_claim(self, claim: FinancialClaim) -> FactCheckResult:
        """Verify market capitalization claims"""
        try:
            # Extract company/ticker
            entity = claim.entities[0] if claim.entities else None
            if not entity:
                return FactCheckResult(
                    claim=claim,
                    verified=False,
                    confidence=0.3,
                    source='Entity extraction',
                    explanation='Could not identify company or ticker'
                )
            
            # Map company name to ticker if needed using enhanced resolver
            ticker_match = self.ticker_resolver.resolve_ticker(entity)
            if ticker_match and ticker_match.confidence > 0.7:
                symbol = ticker_match.ticker
                logger.debug(f"Resolved '{entity}' to ticker '{symbol}' (confidence: {ticker_match.confidence:.2f})")
            else:
                symbol = entity.upper()
            
            # Extract claimed value and unit
            claimed_value = None
            unit = 'billion'  # default
            
            for value in claim.values:
                if 'trillion' in value.lower():
                    unit = 'trillion'
                    claimed_value = float(re.search(r'(\d+(?:\.\d+)?)', value).group(1))
                elif 'billion' in value.lower():
                    unit = 'billion'
                    claimed_value = float(re.search(r'(\d+(?:\.\d+)?)', value).group(1))
                elif value.replace('.', '').isdigit():
                    claimed_value = float(value)
                    
            if not claimed_value:
                # Look in claim text for numbers
                numbers = re.findall(r'\$?(\d+(?:\.\d+)?)', claim.text)
                if numbers:
                    claimed_value = float(numbers[0])
            
            if not claimed_value:
                return FactCheckResult(
                    claim=claim,
                    verified=False,
                    confidence=0.3,
                    source='Value extraction',
                    explanation='Could not extract market cap value'
                )
            
            # Convert to actual value
            multipliers = {'trillion': 1e12, 'billion': 1e9, 'million': 1e6}
            claimed_market_cap = claimed_value * multipliers.get(unit, 1e9)
            
            # Get actual market cap
            actual_data = self._get_stock_data(symbol)
            if actual_data and actual_data.get('market_cap'):
                actual_market_cap = actual_data['market_cap']
                cap_diff = abs(actual_market_cap - claimed_market_cap) / actual_market_cap
                
                if cap_diff < 0.15:  # Within 15%
                    return FactCheckResult(
                        claim=claim,
                        verified=True,
                        confidence=0.9 - cap_diff,
                        source='Yahoo Finance',
                        explanation=f"Market cap ${actual_market_cap/1e9:.1f}B is within 15% of claimed value",
                        actual_value=f"${actual_market_cap/1e9:.1f}B",
                        discrepancy=cap_diff
                    )
                else:
                    return FactCheckResult(
                        claim=claim,
                        verified=False,
                        confidence=0.8,
                        source='Yahoo Finance',
                        explanation=f"Market cap ${actual_market_cap/1e9:.1f}B differs significantly from claimed value",
                        actual_value=f"${actual_market_cap/1e9:.1f}B",
                        discrepancy=cap_diff
                    )
            else:
                return FactCheckResult(
                    claim=claim,
                    verified=False,
                    confidence=0.5,
                    source='Yahoo Finance',
                    explanation=f"Could not retrieve market cap data for {symbol}"
                )
                
        except Exception as e:
            logger.error(f"Error verifying market cap claim: {str(e)}")
            return FactCheckResult(
                claim=claim,
                verified=False,
                confidence=0.3,
                source='Error',
                explanation=f"Error retrieving market cap data: {str(e)}"
            )

    def _verify_revenue_claim(self, claim: FinancialClaim) -> FactCheckResult:
        """Verify revenue claims"""
        try:
            # Check if it's a percentage growth claim
            percentage_match = re.search(r'(\d+(?:\.\d+)?%)', claim.text)
            if percentage_match:
                percentage = float(percentage_match.group(1).replace('%', ''))
                if 0 <= percentage <= 100:  # Reasonable growth range
                    return FactCheckResult(
                        claim=claim,
                        verified=True,
                        confidence=0.7,
                        source='Range validation',
                        explanation=f"Revenue growth of {percentage}% is within reasonable range"
                    )
                else:
                    return FactCheckResult(
                        claim=claim,
                        verified=False,
                        confidence=0.6,
                        source='Range validation',
                        explanation=f"Revenue growth of {percentage}% appears unrealistic"
                    )
            
            # Handle absolute revenue claims
            value_match = re.search(r'\$?(\d+(?:\.\d+)?)\s*(billion|million|trillion)', claim.text, re.IGNORECASE)
            if value_match:
                value = float(value_match.group(1))
                unit = value_match.group(2).lower()
                
                multipliers = {'billion': 1e9, 'million': 1e6, 'trillion': 1e12}
                claimed_revenue = value * multipliers.get(unit, 1e9)
                
                if 1e6 <= claimed_revenue <= 1e12:  # $1M to $1T range
                    return FactCheckResult(
                        claim=claim,
                        verified=True,
                        confidence=0.7,
                        source='Range validation',
                        explanation=f"Revenue of ${claimed_revenue/1e9:.1f}B is within typical corporate range"
                    )
                else:
                    return FactCheckResult(
                        claim=claim,
                        verified=False,
                        confidence=0.8,
                        source='Range validation',
                        explanation=f"Revenue of ${claimed_revenue/1e9:.1f}B is outside typical range"
                    )
            
            return FactCheckResult(
                claim=claim,
                verified=False,
                confidence=0.4,
                source='Limited verification',
                explanation='Revenue claim requires specific data source for verification'
            )
            
        except Exception as e:
            logger.error(f"Error verifying revenue claim: {str(e)}")
            return FactCheckResult(
                claim=claim,
                verified=False,
                confidence=0.3,
                source='Error',
                explanation=f"Error verifying revenue claim: {str(e)}"
            )

    def _verify_interest_rate_claim(self, claim: FinancialClaim) -> FactCheckResult:
        """Verify interest rate claims"""
        try:
            percentage_match = re.search(r'(\d+(?:\.\d+)?%)', claim.text)
            if percentage_match:
                percentage = float(percentage_match.group(1).replace('%', ''))
                
                if 0 <= percentage <= 20:  # Typical range
                    return FactCheckResult(
                        claim=claim,
                        verified=True,
                        confidence=0.6,
                        source='Range validation',
                        explanation=f"Interest rate of {percentage}% is within typical range"
                    )
                else:
                    return FactCheckResult(
                        claim=claim,
                        verified=False,
                        confidence=0.8,
                        source='Range validation',
                        explanation=f"Interest rate of {percentage}% is outside typical range"
                    )
            
            return FactCheckResult(
                claim=claim,
                verified=False,
                confidence=0.4,
                source='Limited verification',
                explanation='Interest rate claim requires Fed data for verification'
            )
            
        except Exception as e:
            return FactCheckResult(
                claim=claim,
                verified=False,
                confidence=0.3,
                source='Error',
                explanation=f"Error verifying interest rate claim: {str(e)}"
            )

    def _verify_subjective_claim(self, claim: FinancialClaim) -> FactCheckResult:
        """Handle subjective claims (opinions, predictions)"""
        return FactCheckResult(
            claim=claim,
            verified=False,
            confidence=0.3,
            source='Subjective analysis',
            explanation='Claim represents opinion or prediction and cannot be objectively verified'
        )

    def _verify_generic_claim(self, claim: FinancialClaim) -> FactCheckResult:
        """Generic verification for unhandled claim types"""
        return FactCheckResult(
            claim=claim,
            verified=False,
            confidence=0.3,
            source='Generic verification',
            explanation='Claim type requires specialized verification method'
        )

    def _get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock data with caching"""
        try:
            # Check cache first
            cache_key = f"stock_data/{symbol}.json"
            cached_data = self._get_from_cache(cache_key)
            
            if cached_data:
                logger.info(f"Using cached data for {symbol}")
                return cached_data

            # Fetch fresh data
            logger.info(f"Fetching fresh data for {symbol}")
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                stock_data = {
                    "symbol": symbol,
                    "current_price": round(float(current_price), 2),
                    "company_name": info.get('longName', symbol),
                    "market_cap": info.get('marketCap'),
                    "pe_ratio": info.get('trailingPE'),
                    "last_updated": datetime.now().isoformat(),
                    "volume": int(hist['Volume'].iloc[-1]) if len(hist) > 0 else None
                }
                
                # Cache the data
                self._store_in_cache(cache_key, stock_data)
                return stock_data
            
            return None

        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
            return None

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from S3 cache"""
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
            data = json.loads(response['Body'].read())
            
            # Check if data is still fresh
            last_updated = datetime.fromisoformat(data['last_updated'])
            if datetime.now() - last_updated < timedelta(minutes=self.cache_ttl_minutes):
                return data
            
            # Data is stale, remove from cache
            s3_client.delete_object(Bucket=S3_BUCKET, Key=key)
            return None
            
        except Exception:
            return None

    def _store_in_cache(self, key: str, data: Dict[str, Any]) -> None:
        """Store data in S3 cache"""
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=key,
                Body=json.dumps(data, default=str),
                ContentType='application/json'
            )
        except Exception as e:
            logger.error(f"Failed to cache data: {str(e)}")

    def _fallback_extract_claims(self, text: str) -> List[FinancialClaim]:
        """Fallback extraction using basic regex when LLM fails"""
        claims = []
        
        # Simple patterns for fallback
        patterns = [
            (r'\b([A-Z]{2,5})\s+(?:is\s+)?(?:trading|at)\s+\$(\d+(?:\.\d{2})?)', ClaimType.STOCK_PRICE),
            (r'(Microsoft|Apple|Google|Tesla)\s+.*market\s+cap.*\$(\d+(?:\.\d+)?)\s*(trillion|billion)', ClaimType.MARKET_CAP),
            (r'revenue.*(\d+(?:\.\d+)?%)', ClaimType.REVENUE),
        ]
        
        for pattern, claim_type in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                claim = FinancialClaim(
                    text=match.group(0),
                    claim_type=claim_type,
                    entities=[],
                    values=[],
                    confidence=0.6,
                    source_text=text,
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                claims.append(claim)
        
        return claims
