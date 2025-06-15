"""
Enhanced Ticker Resolution Service for FinSight
Provides dynamic company name to ticker mapping using multiple data sources
"""

import json
import logging
import re
import time
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TickerMatch:
    """Represents a company name to ticker match with confidence score"""
    company_name: str
    ticker: str
    confidence: float
    source: str
    market_cap: Optional[float] = None
    exchange: Optional[str] = None


class EnhancedTickerResolver:
    """
    Enhanced ticker resolution using multiple data sources and LLM assistance
    """
    
    def __init__(self):
        """Initialize the enhanced ticker resolver"""
        self.cache: Dict[str, TickerMatch] = {}
        self.cache_ttl_hours = 24
        self.last_cache_update: Dict[str, float] = {}
        
        # Core hardcoded mappings for major companies (fallback)
        self.core_mappings = {
            # Tech Giants
            'Apple': 'AAPL', 'Microsoft': 'MSFT', 'Google': 'GOOGL',
            'Alphabet': 'GOOGL', 'Amazon': 'AMZN', 'Meta': 'META',
            'Facebook': 'META', 'Tesla': 'TSLA', 'Netflix': 'NFLX',
            'Nvidia': 'NVDA', 'Advanced Micro Devices': 'AMD', 'AMD': 'AMD',
            'Intel': 'INTC', 'Oracle': 'ORCL', 'Salesforce': 'CRM',
            
            # Financial Services
            'JPMorgan Chase': 'JPM', 'Bank of America': 'BAC',
            'Wells Fargo': 'WFC', 'Goldman Sachs': 'GS',
            'Morgan Stanley': 'MS', 'Citigroup': 'C',
            'American Express': 'AXP', 'Visa': 'V', 'Mastercard': 'MA',
            
            # Healthcare & Pharma
            'Johnson & Johnson': 'JNJ', 'Pfizer': 'PFE', 'Merck': 'MRK',
            'AbbVie': 'ABBV', 'Bristol Myers Squibb': 'BMY',
            'UnitedHealth Group': 'UNH', 'Eli Lilly': 'LLY',
            
            # Consumer Goods
            'Procter & Gamble': 'PG', 'Coca-Cola': 'KO', 'PepsiCo': 'PEP',
            'Nike': 'NKE', 'McDonald\'s': 'MCD', 'Walmart': 'WMT',
            'Home Depot': 'HD', 'Disney': 'DIS',
            
            # Energy & Utilities
            'ExxonMobil': 'XOM', 'Chevron': 'CVX', 'ConocoPhillips': 'COP',
            'NextEra Energy': 'NEE',
            
            # Industrial
            'Boeing': 'BA', 'Caterpillar': 'CAT', '3M': 'MMM',
            'General Electric': 'GE', 'Honeywell': 'HON',
            
            # Telecommunications
            'Verizon': 'VZ', 'AT&T': 'T', 'T-Mobile': 'TMUS',
            
            # Real Estate & REITs
            'American Tower': 'AMT', 'Prologis': 'PLD',
        }
        
        # Common variations and aliases
        self.company_aliases = {
            'GOOGL': ['Google', 'Alphabet Inc', 'Alphabet', 'Google LLC'],
            'META': ['Meta', 'Facebook', 'Meta Platforms', 'Facebook Inc'],
            'TSLA': ['Tesla', 'Tesla Inc', 'Tesla Motors'],
            'MSFT': ['Microsoft', 'Microsoft Corp', 'Microsoft Corporation'],
            'AAPL': ['Apple', 'Apple Inc', 'Apple Computer'],
            'AMZN': ['Amazon', 'Amazon.com', 'Amazon Inc'],
            'NFLX': ['Netflix', 'Netflix Inc'],
            'NVDA': ['Nvidia', 'NVIDIA Corp', 'NVIDIA Corporation'],
        }
        
        # Build reverse lookup for aliases
        self.alias_to_ticker = {}
        for ticker, aliases in self.company_aliases.items():
            for alias in aliases:
                self.alias_to_ticker[alias.lower()] = ticker
                
        logger.info("Enhanced ticker resolver initialized with comprehensive mappings")

    def resolve_ticker(self, company_name: str) -> Optional[TickerMatch]:
        """
        Resolve company name to ticker with confidence scoring
        
        Args:
            company_name: Company name to resolve
            
        Returns:
            TickerMatch object if found, None otherwise
        """
        if not company_name or not company_name.strip():
            return None
            
        company_clean = company_name.strip()
        cache_key = company_clean.lower()
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for '{company_clean}'")
            return self.cache[cache_key]
            
        # Try multiple resolution strategies
        result = (
            self._resolve_exact_match(company_clean) or
            self._resolve_fuzzy_match(company_clean) or
            self._resolve_with_yfinance(company_clean) or
            self._resolve_with_search_api(company_clean)
        )
        
        # Cache the result
        if result:
            self.cache[cache_key] = result
            self.last_cache_update[cache_key] = time.time()
            logger.info(f"Resolved '{company_clean}' → {result.ticker} (confidence: {result.confidence:.2f})")
        else:
            logger.warning(f"Could not resolve ticker for '{company_clean}'")
            
        return result

    def resolve_multiple(self, company_names: List[str]) -> Dict[str, Optional[TickerMatch]]:
        """
        Resolve multiple company names concurrently
        
        Args:
            company_names: List of company names to resolve
            
        Returns:
            Dictionary mapping company names to TickerMatch objects
        """
        results = {}
        
        # Use ThreadPoolExecutor for concurrent resolution
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_company = {
                executor.submit(self.resolve_ticker, company): company 
                for company in company_names
            }
            
            for future in as_completed(future_to_company):
                company = future_to_company[future]
                try:
                    result = future.result()
                    results[company] = result
                except Exception as e:
                    logger.error(f"Error resolving '{company}': {e}")
                    results[company] = None
                    
        return results

    def get_ticker_suggestions(self, partial_name: str, limit: int = 5) -> List[TickerMatch]:
        """
        Get ticker suggestions for partial company names
        
        Args:
            partial_name: Partial company name
            limit: Maximum number of suggestions
            
        Returns:
            List of TickerMatch suggestions
        """
        suggestions = []
        partial_lower = partial_name.lower()
        
        # Search in core mappings
        for company, ticker in self.core_mappings.items():
            if partial_lower in company.lower():
                suggestions.append(TickerMatch(
                    company_name=company,
                    ticker=ticker,
                    confidence=0.8,
                    source="core_mapping"
                ))
                
        # Search in aliases
        for alias, ticker in self.alias_to_ticker.items():
            if partial_lower in alias:
                company_name = next(
                    (comp for comp, tick in self.core_mappings.items() if tick == ticker),
                    alias.title()
                )
                suggestions.append(TickerMatch(
                    company_name=company_name,
                    ticker=ticker,
                    confidence=0.7,
                    source="alias_mapping"
                ))
                
        # Remove duplicates and sort by confidence
        seen_tickers = set()
        unique_suggestions = []
        for suggestion in sorted(suggestions, key=lambda x: x.confidence, reverse=True):
            if suggestion.ticker not in seen_tickers:
                unique_suggestions.append(suggestion)
                seen_tickers.add(suggestion.ticker)
                
        return unique_suggestions[:limit]

    def validate_ticker(self, ticker: str) -> bool:
        """
        Validate if a ticker symbol exists and is active
        
        Args:
            ticker: Ticker symbol to validate
            
        Returns:
            True if ticker is valid, False otherwise
        """
        if not YFINANCE_AVAILABLE:
            # Basic validation without yfinance
            return bool(re.match(r'^[A-Z]{1,5}$', ticker.upper()))
            
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Check if we got valid data
            return bool(info.get('symbol') or info.get('longName'))
            
        except Exception as e:
            logger.debug(f"Ticker validation failed for {ticker}: {e}")
            return False

    def _resolve_exact_match(self, company_name: str) -> Optional[TickerMatch]:
        """Try exact match against core mappings and aliases"""
        company_lower = company_name.lower()
        
        # Check direct ticker symbols first (e.g., "AAPL", "MSFT")
        if company_name.upper() in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA', 'AMD', 'INTC']:
            return TickerMatch(
                company_name=company_name.upper(),
                ticker=company_name.upper(),
                confidence=1.0,
                source="direct_symbol"
            )
        
        # Check core mappings
        for company, ticker in self.core_mappings.items():
            if company_lower == company.lower():
                return TickerMatch(
                    company_name=company,
                    ticker=ticker,
                    confidence=1.0,
                    source="core_mapping"
                )
        
        # Check aliases
        if company_lower in self.alias_to_ticker:
            ticker = self.alias_to_ticker[company_lower]
            return TickerMatch(
                company_name=company_name,
                ticker=ticker,
                confidence=0.95,
                source="alias_mapping"
            )
        
        return None

    def _resolve_fuzzy_match(self, company_name: str) -> Optional[TickerMatch]:
        """Try fuzzy matching against known companies"""
        company_lower = company_name.lower()
        best_match = None
        best_score = 0.0
        
        # Check against core mappings with fuzzy matching
        for company, ticker in self.core_mappings.items():
            similarity = self._calculate_similarity(company_lower, company.lower())
            if similarity > 0.8 and similarity > best_score:
                best_score = similarity
                best_match = TickerMatch(
                    company_name=company,
                    ticker=ticker,
                    confidence=similarity * 0.9,  # Reduce confidence for fuzzy matches
                    source="fuzzy_mapping"
                )
        
        # Check against aliases with fuzzy matching
        for alias, ticker in self.alias_to_ticker.items():
            similarity = self._calculate_similarity(company_lower, alias)
            if similarity > 0.8 and similarity > best_score:
                best_score = similarity
                best_match = TickerMatch(
                    company_name=company_name,
                    ticker=ticker,
                    confidence=similarity * 0.85,
                    source="fuzzy_alias"
                )
        
        return best_match

    def _resolve_with_yfinance(self, company_name: str) -> Optional[TickerMatch]:
        """Resolve using yfinance search capabilities"""
        if not YFINANCE_AVAILABLE:
            return None
            
        try:
            # Try common ticker patterns first
            potential_tickers = self._generate_ticker_candidates(company_name)
            
            for ticker_candidate in potential_tickers:
                if self.validate_ticker(ticker_candidate):
                    stock = yf.Ticker(ticker_candidate)
                    info = stock.info
                    
                    # Check if company name matches
                    long_name = info.get('longName', '').lower()
                    short_name = info.get('shortName', '').lower()
                    
                    if (company_name.lower() in long_name or 
                        long_name in company_name.lower() or
                        company_name.lower() in short_name):
                        
                        return TickerMatch(
                            company_name=info.get('longName', company_name),
                            ticker=ticker_candidate,
                            confidence=0.85,
                            source="yfinance",
                            market_cap=info.get('marketCap'),
                            exchange=info.get('exchange')
                        )
                        
        except Exception as e:
            logger.debug(f"YFinance resolution failed for '{company_name}': {e}")
            
        return None

    def _resolve_with_search_api(self, company_name: str) -> Optional[TickerMatch]:
        """Resolve using external search APIs (placeholder for future implementation)"""
        # This would integrate with services like:
        # - Alpha Vantage Symbol Search
        # - Financial Modeling Prep
        # - IEX Cloud
        # - Polygon.io
        
        # For now, return None - can be implemented later
        logger.debug(f"External API resolution not implemented for '{company_name}'")
        return None

    def _generate_ticker_candidates(self, company_name: str) -> List[str]:
        """Generate potential ticker symbols from company name"""
        candidates = []
        clean_name = re.sub(r'[^\w\s]', '', company_name.upper())
        words = clean_name.split()
        
        if len(words) >= 1:
            # First letter of each word
            candidates.append(''.join(word[0] for word in words if word))
            
            # First few letters of first word
            first_word = words[0]
            if len(first_word) >= 3:
                candidates.append(first_word[:3])
                candidates.append(first_word[:4])
                
            # Common abbreviations
            if 'CORPORATION' in clean_name or 'CORP' in clean_name:
                base = clean_name.replace('CORPORATION', '').replace('CORP', '').strip()
                if base:
                    candidates.append(base[:4])
                    
        return candidates[:5]  # Limit to 5 candidates

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate simple string similarity score"""
        if str1 == str2:
            return 1.0
            
        # Simple Jaccard similarity using character n-grams
        def get_ngrams(s, n=2):
            return set(s[i:i+n] for i in range(len(s)-n+1))
            
        ngrams1 = get_ngrams(str1)
        ngrams2 = get_ngrams(str2)
        
        if not ngrams1 and not ngrams2:
            return 1.0
        if not ngrams1 or not ngrams2:
            return 0.0
            
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        
        return intersection / union if union > 0 else 0.0

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached entry is still valid"""
        if cache_key not in self.cache:
            return False
            
        last_update = self.last_cache_update.get(cache_key, 0)
        return (time.time() - last_update) < (self.cache_ttl_hours * 3600)

    def clear_cache(self) -> None:
        """Clear the ticker resolution cache"""
        self.cache.clear()
        self.last_cache_update.clear()
        logger.info("Ticker resolution cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "total_entries": len(self.cache),
            "valid_entries": sum(1 for key in self.cache if self._is_cache_valid(key)),
            "expired_entries": sum(1 for key in self.cache if not self._is_cache_valid(key))
        }


# Global instance for easy import
ticker_resolver = EnhancedTickerResolver()


def resolve_company_ticker(company_name: str) -> Optional[str]:
    """
    Convenient function to resolve company name to ticker
    
    Args:
        company_name: Company name to resolve
        
    Returns:
        Ticker symbol if found, None otherwise
    """
    result = ticker_resolver.resolve_ticker(company_name)
    return result.ticker if result else None


def get_ticker_with_confidence(company_name: str) -> Tuple[Optional[str], float]:
    """
    Get ticker with confidence score
    
    Args:
        company_name: Company name to resolve
        
    Returns:
        Tuple of (ticker, confidence_score)
    """
    result = ticker_resolver.resolve_ticker(company_name)
    return (result.ticker, result.confidence) if result else (None, 0.0)
