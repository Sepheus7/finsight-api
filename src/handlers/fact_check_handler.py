"""
Fact Check Handler for AWS Lambda
Verifies financial claims and statements using external data sources
"""

import json
import os
import boto3
import re
import yfinance as yf
from datetime import datetime, timedelta
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
    Lambda handler for fact-checking financial claims
    """
    try:
        content = event.get('content', '')
        request_id = event.get('request_id', context.aws_request_id)

        logger.info(f"Processing fact check for request {request_id}")

        fact_checker = FinancialFactChecker()
        
        # Extract claims from content
        claims = fact_checker.extract_financial_claims(content)
        logger.info(f"Extracted {len(claims)} claims for verification")

        # Verify each claim
        fact_checks = []
        for claim in claims:
            fact_check = fact_checker.verify_claim(claim)
            fact_checks.append(fact_check)

        response_data = {
            'fact_checks': fact_checks,
            'claims_processed': len(claims),
            'request_id': request_id
        }

        return response_data

    except Exception as e:
        logger.error(f"Fact checking failed: {str(e)}")
        return {
            'error': str(e),
            'fact_checks': [],
            'claims_processed': 0
        }


class FinancialFactChecker:
    def __init__(self):
        self.cache_ttl_minutes = 15  # Cache market data for 15 minutes
        
        # Company name to ticker symbol mapping
        self.company_to_ticker = {
            'Microsoft': 'MSFT',
            'Apple': 'AAPL', 
            'Google': 'GOOGL',
            'Alphabet': 'GOOGL',
            'Tesla': 'TSLA',
            'Amazon': 'AMZN',
            'Meta': 'META',
            'Netflix': 'NFLX',
            'Nvidia': 'NVDA',
            'AMD': 'AMD',
            'Intel': 'INTC'
        }

    def extract_financial_claims(self, text: str) -> List[str]:
        """Extract potential financial claims from text with improved pattern recognition"""
        claims = []
        
        # Enhanced stock price patterns - more precise and comprehensive
        stock_patterns = [
            # Company name with ticker: "Apple Inc. (AAPL) stock price is $185.50"
            r'(?:Apple Inc\.|Microsoft|Google|Tesla|Amazon|Meta)\s*\(([A-Z]{2,5})\)\s+stock\s+price\s+is\s+\$(\d+(?:\.\d{1,2})?)',
            # Direct ticker with price: "AAPL is trading at $150.50"
            r'\b([A-Z]{2,5})\s+(?:is\s+)?(?:currently\s+)?(?:trading|trades)\s+(?:at\s+)?\$(\d+(?:\.\d{1,2})?)',
            # Stock mention: "AAPL stock is $150"
            r'\b([A-Z]{2,5})\s+(?:stock|shares?)\s+(?:is|are|at)\s+\$(\d+(?:\.\d{1,2})?)',
            # Company with price: "Apple (AAPL) at $150"
            r'(?:Apple|Microsoft|Google|Tesla|Amazon|Meta)\s*\(([A-Z]{2,5})\)\s+(?:at\s+)?\$(\d+(?:\.\d{1,2})?)',
            # Reverse format: "$150 per share for AAPL"
            r'\$(\d+(?:\.\d{1,2})?)\s+per\s+share\s+(?:for\s+)?([A-Z]{2,5})'
        ]
        
        for pattern in stock_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    # Handle different capture group arrangements
                    if groups[0] and groups[1]:
                        # Check if we have a valid ticker symbol (2-5 chars)
                        if groups[0].replace('.', '').isdigit():
                            # First group is price, second is symbol
                            price, symbol = groups[0], groups[1]
                        else:
                            # First group is symbol, second is price
                            symbol, price = groups[0], groups[1]
                        
                        # Validate symbol length and format
                        if symbol and price and 2 <= len(symbol) <= 5 and symbol.isalpha():
                            claims.append(f"{symbol.upper()} is currently trading at ${price}")
        
        # Market cap claims - Enhanced with company name validation
        market_cap_patterns = [
            # Company with market cap: "Microsoft has a market capitalization of $2.8 trillion"
            r'(Microsoft|Apple|Google|Tesla|Amazon|Meta|Alphabet)\s+has\s+a\s+market\s+cap(?:italization)?\s+of\s+\$(\d+(?:\.\d+)?)\s*(trillion|billion|million)',
            # Market cap of company: "market capitalization of Microsoft is $2.8 trillion"
            r'market\s+cap(?:italization)?\s+of\s+(Microsoft|Apple|Google|Tesla|Amazon|Meta|Alphabet)\s+is\s+\$(\d+(?:\.\d+)?)\s*(trillion|billion|million)',
            # Ticker market cap: "MSFT has a market cap of $2.8T"
            r'\b([A-Z]{2,5})\s+has\s+a\s+market\s+cap(?:italization)?\s+of\s+\$(\d+(?:\.\d+)?)\s*([TMB]?)',
        ]
        
        for pattern in market_cap_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2 and groups[0] and groups[1]:
                    # Validate if it's a company name or ticker
                    entity = groups[0]
                    if entity in ['Microsoft', 'Apple', 'Google', 'Tesla', 'Amazon', 'Meta', 'Alphabet'] or (entity.isupper() and 2 <= len(entity) <= 5):
                        claims.append(match.group(0).strip())

        # Revenue/earnings claims - Enhanced with company validation
        revenue_patterns = [
            # "Tesla's revenue increased by 25% last quarter"
            r"(Tesla|Apple|Microsoft|Google|Amazon|Meta|Alphabet)'s\s+revenue\s+(?:increased|grew|rose)\s+by\s+(\d+(?:\.\d+)?%)\s+(?:last\s+)?quarter",
            # "Apple reported $90.1 billion in revenue"
            r'(Apple|Microsoft|Google|Tesla|Amazon|Meta|Alphabet)\s+reported\s+\$(\d+(?:\.\d+)?)\s*(billion|million|trillion)\s+in\s+revenue',
            # "Q4 revenue of $50.5 billion"
            r'Q\d\s+revenue\s+of\s+\$(\d+(?:\.\d+)?)\s*(billion|million|trillion)',
            # "Revenue increased to $90 billion"
            r'revenue\s+(?:increased|grew|rose)\s+to\s+\$(\d+(?:\.\d+)?)\s*(billion|million|trillion)',
            # Standalone percentage patterns
            r'revenue\s+(?:increased|grew|rose)\s+by\s+(\d+(?:\.\d+)?%)',
            r'(?:revenue|sales)\s+(?:growth|increase)\s+of\s+(\d+(?:\.\d+)?%)'
        ]
        
        for pattern in revenue_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                claims.append(match.group(0).strip())

        # Percentage and rate claims - Enhanced
        pct_patterns = [
            # Fed rate changes: "The Federal Reserve will raise interest rates by 0.75% next month"
            r'(?:Federal Reserve|Fed)\s+will\s+(?:raise|cut|set)\s+interest\s+rates?\s+(?:by\s+)?(\d+(?:\.\d+)?%)',
            # Interest rate mentions: "interest rates are at 5.25%"
            r'interest\s+rates?\s+(?:are|at)\s+(\d+(?:\.\d+)?%)',
            # Inflation mentions: "inflation is 3.2%"
            r'inflation\s+(?:is|at|reached)\s+(\d+(?:\.\d+)?%)',
            # Growth percentages: "revenue increased by 25%"
            r'(?:revenue|sales|profits?)\s+(?:increased|grew|rose)\s+by\s+(\d+(?:\.\d+)?%)'
        ]
        
        for pattern in pct_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                claims.append(match.group(0).strip())

        # Remove duplicates and filter out very short claims
        claims = list(set([claim for claim in claims if len(claim) > 15]))
        
        logger.info(f"Extracted {len(claims)} financial claims: {claims}")
        return claims

    def verify_claim(self, claim: str) -> Dict[str, Any]:
        """Verify a financial claim with enhanced pattern matching"""
        logger.info(f"Verifying claim: {claim}")

        # Enhanced stock price extraction with company name validation
        stock_patterns = [
            r'(?:Apple Inc\.|Microsoft|Google|Tesla|Amazon|Meta)\s*\(([A-Z]{2,5})\)\s+stock\s+price\s+is\s+\$(\d+(?:\.\d{1,2})?)',
            r'\b([A-Z]{2,5})\s+(?:is\s+)?(?:currently\s+)?(?:trading|trades)\s+(?:at\s+)?\$(\d+(?:\.\d{1,2})?)',
            r'\b([A-Z]{2,5})\s+(?:stock|shares?)\s+(?:is|are|at)\s+\$(\d+(?:\.\d{1,2})?)',
            r'(?:Apple|Microsoft|Google|Tesla|Amazon|Meta)\s*\(([A-Z]{2,5})\)\s+(?:at\s+)?\$(\d+(?:\.\d{1,2})?)'
        ]
        
        for pattern in stock_patterns:
            stock_match = re.search(pattern, claim, re.IGNORECASE)
            if stock_match:
                return self._verify_stock_price_claim(stock_match, claim)

        # Enhanced market cap extraction with company validation
        market_cap_patterns = [
            r'(Microsoft|Apple|Google|Tesla|Amazon|Meta|Alphabet)\s+has\s+a\s+market\s+cap(?:italization)?\s+of\s+\$(\d+(?:\.\d+)?)\s*(trillion|billion|million)',
            r'market\s+cap(?:italization)?\s+of\s+(Microsoft|Apple|Google|Tesla|Amazon|Meta|Alphabet)\s+is\s+\$(\d+(?:\.\d+)?)\s*(trillion|billion|million)',
            r'\b([A-Z]{2,5})\s+has\s+a\s+market\s+cap(?:italization)?\s+of\s+\$(\d+(?:\.\d+)?)\s*([TMB]?)'
        ]
        
        for pattern in market_cap_patterns:
            market_cap_match = re.search(pattern, claim, re.IGNORECASE)
            if market_cap_match:
                return self._verify_market_cap_claim(market_cap_match, claim)

        # Revenue claims with company validation
        revenue_patterns = [
            r"(Tesla|Apple|Microsoft|Google|Amazon|Meta|Alphabet)'s\s+revenue\s+(?:increased|grew|rose)\s+by\s+(\d+(?:\.\d+)?%)",
            r'(Apple|Microsoft|Google|Tesla|Amazon|Meta|Alphabet)\s+reported\s+\$(\d+(?:\.\d+)?)\s*(billion|million|trillion)\s+in\s+revenue',
            r'Q\d\s+revenue\s+of\s+\$(\d+(?:\.\d+)?)\s*(billion|million|trillion)',
            # Standalone percentage patterns
            r'revenue\s+(?:increased|grew|rose)\s+by\s+(\d+(?:\.\d+)?%)',
            r'(?:revenue|sales)\s+(?:growth|increase)\s+of\s+(\d+(?:\.\d+)?%)'
        ]
        
        for pattern in revenue_patterns:
            revenue_match = re.search(pattern, claim, re.IGNORECASE)
            if revenue_match:
                return self._verify_revenue_claim(revenue_match, claim)

        # Federal Reserve and interest rate claims
        fed_patterns = [
            r'(?:Federal Reserve|Fed)\s+will\s+(?:raise|cut|set)\s+interest\s+rates?\s+(?:by\s+)?(\d+(?:\.\d+)?%)',
            r'interest\s+rates?\s+(?:are|at)\s+(\d+(?:\.\d+)?%)'
        ]
        
        for pattern in fed_patterns:
            fed_match = re.search(pattern, claim, re.IGNORECASE)
            if fed_match:
                return self._verify_percentage_claim(fed_match, claim)

        # If we reach here, try to extract any valid stock symbols for basic validation
        symbol_match = re.search(r'\b([A-Z]{2,5})\b', claim)
        if symbol_match:
            symbol = symbol_match.group(1)
            # Validate it's a real symbol by checking against known companies or using basic validation
            if symbol in ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META'] or len(symbol) >= 2:
                stock_data = self._get_stock_data(symbol)
                if stock_data:
                    return {
                        'claim': claim,
                        'verified': True,
                        'confidence': 0.6,
                        'source': 'Yahoo Finance - Symbol validation',
                        'explanation': f'Found valid stock symbol {symbol} - {stock_data.get("company_name", "Unknown Company")}'
                    }

        # Default for unverifiable claims
        return {
            'claim': claim,
            'verified': False,
            'confidence': 0.3,
            'source': 'Unable to verify',
            'explanation': 'Claim could not be automatically verified with available data sources'
        }

    def _verify_stock_price_claim(self, match, claim: str) -> Dict[str, Any]:
        """Verify stock price claim"""
        try:
            symbol = match.group(1).upper()
            claimed_price = float(match.group(2))
            
            actual_data = self._get_stock_data(symbol)
            if actual_data:
                actual_price = actual_data['current_price']
                price_diff = abs(actual_price - claimed_price) / actual_price
                
                if price_diff < 0.05:  # Within 5%
                    return {
                        'claim': claim,
                        'verified': True,
                        'confidence': 0.95 - price_diff,
                        'source': 'Yahoo Finance',
                        'explanation': f"Current price ${actual_price:.2f} is within 5% of claimed ${claimed_price:.2f}"
                    }
                else:
                    return {
                        'claim': claim,
                        'verified': False,
                        'confidence': 0.9,
                        'source': 'Yahoo Finance',
                        'explanation': f"Current price ${actual_price:.2f} differs significantly from claimed ${claimed_price:.2f} ({price_diff:.1%} difference)"
                    }
            else:
                return {
                    'claim': claim,
                    'verified': False,
                    'confidence': 0.5,
                    'source': 'Yahoo Finance',
                    'explanation': f"Could not retrieve current price data for {symbol}"
                }
        except Exception as e:
            logger.error(f"Error verifying stock price claim: {str(e)}")
            return {
                'claim': claim,
                'verified': False,
                'confidence': 0.3,
                'source': 'Error',
                'explanation': f"Error retrieving stock data: {str(e)}"
            }

    def _verify_market_cap_claim(self, match, claim: str) -> Dict[str, Any]:
        """Verify market capitalization claim"""
        try:
            entity = match.group(1)
            claimed_value = float(match.group(2))
            unit = match.group(3).upper() if match.group(3) else ''
            
            # Map company name to ticker symbol if needed
            if entity in self.company_to_ticker:
                symbol = self.company_to_ticker[entity]
            else:
                symbol = entity.upper()
            
            # Convert to actual value
            multipliers = {'BILLION': 1e9, 'MILLION': 1e6, 'TRILLION': 1e12, 'B': 1e9, 'M': 1e6, 'T': 1e12}
            unit_lower = unit.lower()
            if unit_lower in ['billion', 'trillion', 'million']:
                claimed_market_cap = claimed_value * multipliers[unit_lower.upper()]
            elif unit in multipliers:
                claimed_market_cap = claimed_value * multipliers[unit]
            else:
                # Assume billions if no unit specified for large numbers
                if claimed_value >= 1000:
                    claimed_market_cap = claimed_value * 1e9
                else:
                    claimed_market_cap = claimed_value

            actual_data = self._get_stock_data(symbol)
            if actual_data and actual_data.get('market_cap'):
                actual_market_cap = actual_data['market_cap']
                cap_diff = abs(actual_market_cap - claimed_market_cap) / actual_market_cap
                
                if cap_diff < 0.1:  # Within 10%
                    return {
                        'claim': claim,
                        'verified': True,
                        'confidence': 0.9 - cap_diff,
                        'source': 'Yahoo Finance',
                        'explanation': f"Market cap ${actual_market_cap/1e9:.1f}B is within 10% of claimed value"
                    }
                else:
                    return {
                        'claim': claim,
                        'verified': False,
                        'confidence': 0.8,
                        'source': 'Yahoo Finance',
                        'explanation': f"Market cap ${actual_market_cap/1e9:.1f}B differs significantly from claimed value"
                    }
            else:
                return {
                    'claim': claim,
                    'verified': False,
                    'confidence': 0.5,
                    'source': 'Yahoo Finance',
                    'explanation': f"Could not retrieve market cap data for {symbol}"
                }
        except Exception as e:
            logger.error(f"Error verifying market cap claim: {str(e)}")
            return {
                'claim': claim,
                'verified': False,
                'confidence': 0.3,
                'source': 'Error',
                'explanation': f"Error retrieving market cap data: {str(e)}"
            }

    def _verify_revenue_claim(self, match, claim: str) -> Dict[str, Any]:
        """Verify revenue/earnings claim"""
        try:
            groups = match.groups()
            
            # Handle different group patterns for revenue claims
            if "increased by" in claim.lower() and "%" in claim:
                # Handle percentage growth claims like "Tesla's revenue increased by 25%"
                percentage_match = re.search(r'(\d+(?:\.\d+)?%)', claim)
                if percentage_match:
                    percentage = float(percentage_match.group(1).replace('%', ''))
                    if 0 <= percentage <= 100:  # Reasonable growth range
                        return {
                            'claim': claim,
                            'verified': True,
                            'confidence': 0.7,
                            'source': 'Range validation',
                            'explanation': f"Revenue growth of {percentage}% is within reasonable range"
                        }
                    else:
                        return {
                            'claim': claim,
                            'verified': False,
                            'confidence': 0.6,
                            'source': 'Range validation',
                            'explanation': f"Revenue growth of {percentage}% appears unrealistic"
                        }
            else:
                # Handle absolute revenue claims like "Apple reported $90.1 billion in revenue"
                # Find the numeric value and unit
                value_match = re.search(r'\$?(\d+(?:\.\d+)?)\s*(billion|million|trillion)', claim, re.IGNORECASE)
                if value_match:
                    value = float(value_match.group(1))
                    unit = value_match.group(2).lower()
                    
                    # Convert to actual value
                    multipliers = {'billion': 1e9, 'million': 1e6, 'trillion': 1e12}
                    claimed_revenue = value * multipliers.get(unit, 1e9)
                    
                    # Range validation (in production, you'd check against SEC filings)
                    if 1e6 <= claimed_revenue <= 1e12:  # $1M to $1T range
                        return {
                            'claim': claim,
                            'verified': True,
                            'confidence': 0.7,
                            'source': 'Range validation',
                            'explanation': f"Revenue of ${claimed_revenue/1e9:.1f}B is within typical corporate range"
                        }
                    else:
                        return {
                            'claim': claim,
                            'verified': False,
                            'confidence': 0.8,
                            'source': 'Range validation',
                            'explanation': f"Revenue of ${claimed_revenue/1e9:.1f}B is outside typical range"
                        }
            
            # Fallback for unrecognized revenue patterns
            return {
                'claim': claim,
                'verified': False,
                'confidence': 0.4,
                'source': 'Limited verification',
                'explanation': 'Revenue claim requires specific data source for verification'
            }
                
        except Exception as e:
            logger.error(f"Error verifying revenue claim: {str(e)}")
            return {
                'claim': claim,
                'verified': False,
                'confidence': 0.3,
                'source': 'Error',
                'explanation': f"Error verifying revenue claim: {str(e)}"
            }

    def _verify_percentage_claim(self, match, claim: str) -> Dict[str, Any]:
        """Verify percentage claims (inflation, interest rates, etc.)"""
        try:
            percentage = float(match.group(1).replace('%', ''))
            
            # This is a simplified verification - in production, you'd check against
            # Federal Reserve data, CPI data, etc.
            if 'inflation' in claim.lower():
                # Typical inflation range check
                if 0 <= percentage <= 10:
                    return {
                        'claim': claim,
                        'verified': True,
                        'confidence': 0.7,
                        'source': 'Range validation',
                        'explanation': f"Inflation rate of {percentage}% is within typical range"
                    }
                else:
                    return {
                        'claim': claim,
                        'verified': False,
                        'confidence': 0.8,
                        'source': 'Range validation',
                        'explanation': f"Inflation rate of {percentage}% is outside typical range (0-10%)"
                    }
            
            elif 'interest rate' in claim.lower():
                # Typical interest rate range check
                if 0 <= percentage <= 20:
                    return {
                        'claim': claim,
                        'verified': True,
                        'confidence': 0.6,
                        'source': 'Range validation',
                        'explanation': f"Interest rate of {percentage}% is within typical range"
                    }
                else:
                    return {
                        'claim': claim,
                        'verified': False,
                        'confidence': 0.8,
                        'source': 'Range validation',
                        'explanation': f"Interest rate of {percentage}% is outside typical range (0-20%)"
                    }

            return {
                'claim': claim,
                'verified': False,
                'confidence': 0.4,
                'source': 'Limited verification',
                'explanation': 'Percentage claim requires specific data source for verification'
            }

        except Exception as e:
            logger.error(f"Error verifying percentage claim: {str(e)}")
            return {
                'claim': claim,
                'verified': False,
                'confidence': 0.3,
                'source': 'Error',
                'explanation': f"Error verifying percentage claim: {str(e)}"
            }

    def _get_stock_data(self, symbol: str) -> Dict[str, Any]:
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

    def _get_from_cache(self, key: str) -> Dict[str, Any]:
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
