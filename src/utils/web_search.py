"""
Web Search Utility for Entity Validation and Economic Data
Real web search functionality with structured data extraction
"""

import asyncio
import aiohttp
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSearchClient:
    """Enhanced web search client with multiple strategies"""
    
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform web search using multiple strategies
        """
        logger.info(f"Performing web search for: {query}")
        
        # Strategy 1: Try Searx (open source search)
        try:
            results = await self._search_searx(query, max_results)
            if results:
                return results
        except Exception as e:
            logger.warning(f"Searx search failed: {e}")
        
        # Strategy 2: Economic data patterns (for economic queries)
        if any(term in query.lower() for term in ['economy', 'economic', 'inflation', 'unemployment', 'employment', 'gdp']):
            return await self._search_economic_fallback(query, max_results)
        
        # Strategy 3: Generic fallback with helpful guidance
        return await self._search_generic_fallback(query, max_results)

    async def _search_searx(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Try Searx public instances for web search"""
        if not self.session:
            return []
            
        searx_instances = [
            "https://searx.be",
            "https://search.sapti.me", 
            "https://searx.xyz"
        ]
        
        for instance in searx_instances:
            try:
                url = f"{instance}/search"
                params = {
                    'q': query,
                    'format': 'json',
                    'categories': 'general'
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        for item in data.get('results', [])[:max_results]:
                            results.append({
                                'title': item.get('title', ''),
                                'snippet': item.get('content', ''),
                                'url': item.get('url', ''),
                                'confidence': 0.7,
                                'source': 'searx'
                            })
                        
                        if results:
                            logger.info(f"Searx search successful with {len(results)} results")
                            return results
                            
            except Exception as e:
                logger.warning(f"Searx instance {instance} failed: {e}")
                continue
        
        return []

    async def _search_economic_fallback(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Provide guidance for economic data queries instead of fake data"""
        
        query_lower = query.lower()
        
        # Economic data guidance with official sources
        if any(term in query_lower for term in ['france', 'french']):
            return [{
                'title': 'Economic Data Not Available - France',
                'snippet': 'Real-time economic data for France is currently unavailable due to API limitations. For accurate and current French economic statistics, please visit INSEE (French National Institute of Statistics) at https://www.insee.fr/en/statistiques directly.',
                'url': 'https://www.insee.fr/en/statistiques',
                'confidence': 0.9,
                'source': 'guidance',
                'data_limitation': True
            }]
        
        elif any(term in query_lower for term in ['uk', 'united kingdom', 'britain', 'british']):
            return [{
                'title': 'Economic Data Not Available - United Kingdom',
                'snippet': 'Real-time economic data for the UK is currently unavailable due to API limitations. For accurate and current UK economic statistics, please visit ONS (UK Office for National Statistics) at https://www.ons.gov.uk/ directly.',
                'url': 'https://www.ons.gov.uk/',
                'confidence': 0.9,
                'source': 'guidance',
                'data_limitation': True
            }]
        
        elif any(term in query_lower for term in ['us', 'usa', 'united states', 'america', 'american']):
            return [{
                'title': 'Economic Data Not Available - United States',
                'snippet': 'Real-time economic data for the US is currently unavailable due to API limitations. For accurate and current US economic statistics, please visit BLS (Bureau of Labor Statistics) at https://www.bls.gov/ and BEA (Bureau of Economic Analysis) at https://www.bea.gov/ directly.',
                'url': 'https://www.bls.gov/',
                'confidence': 0.9,
                'source': 'guidance',
                'data_limitation': True
            }]
        
        else:
            return [{
                'title': 'Economic Data Not Available',
                'snippet': 'Real-time economic data is currently unavailable due to API limitations. For accurate economic statistics, please visit the official statistical agencies of the relevant countries directly.',
                'url': 'https://www.imf.org/en/Data',
                'confidence': 0.8,
                'source': 'guidance',
                'data_limitation': True
            }]

    async def _search_generic_fallback(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Generic fallback for non-economic queries"""
        return [{
            'title': 'Web Search Not Available',
            'snippet': f'Web search for "{query}" is currently unavailable due to API limitations. Please try searching directly on your preferred search engine.',
            'url': f'https://www.google.com/search?q={query.replace(" ", "+")}',
            'confidence': 0.5,
            'source': 'fallback',
            'search_limitation': True
        }]


async def search_economic_indicators(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search for economic indicators with enhanced error handling
    """
    async with WebSearchClient() as client:
        results = await client.search(query, max_results)
        
        extracted_data = {
            'indicators': [],
            'sources': [],
            'search_query': query,
            'timestamp': datetime.now().isoformat(),
            'data_available': False
        }
        
        # Check if we have data limitations
        has_limitations = any(result.get('data_limitation') or result.get('search_limitation') for result in results)
        
        if has_limitations:
            extracted_data['data_limitation'] = True
            extracted_data['message'] = 'Real-time data unavailable - please check official sources'
        
        # Add source information
        for result in results:
            source_info = {
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'confidence': result.get('confidence', 0.5),
                'source_type': result.get('source', 'unknown')
            }
            
            extracted_data['sources'].append(source_info)
        
        return extracted_data


async def perform_web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    General web search function
    """
    async with WebSearchClient() as client:
        results = await client.search(query, max_results)
        
        return {
            'query': query,
            'results': results,
            'total_results': len(results),
            'timestamp': datetime.now().isoformat(),
            'search_successful': len(results) > 0
        }


# Utility functions for specific use cases
async def validate_company_ticker(company_name: str) -> Dict[str, Any]:
    """Validate if a company name corresponds to a stock ticker"""
    query = f"{company_name} stock ticker symbol"
    results = await perform_web_search(query, max_results=3)
    
    # Look for ticker symbols in results
    ticker_pattern = r'\b[A-Z]{1,5}\b'
    found_tickers = []
    
    for result in results['results']:
        snippet = result.get('snippet', '')
        tickers = re.findall(ticker_pattern, snippet)
        found_tickers.extend(tickers)
    
    return {
        'company_name': company_name,
        'potential_tickers': list(set(found_tickers)),
        'search_results': results['results'],
        'is_public_company': len(found_tickers) > 0
    }


async def get_latest_economic_news(country: str = "US") -> List[Dict[str, Any]]:
    """Get latest economic news for a specific country"""
    query = f"{country} economy latest news economic indicators"
    search_result = await perform_web_search(query, max_results=5)
    return search_result['results'] 