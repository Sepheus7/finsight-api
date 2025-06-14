#!/usr/bin/env python3
"""
FinSight LLM-Enhanced Demo API Server
Uses the same logic as production AWS Lambda but with local Ollama fallback
Enhanced with Performance Optimizations
"""

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import json
import requests
import logging
import os
import re
from datetime import datetime
import yfinance as yf
import subprocess
import sys
import time
import asyncio

# Set up logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import boto3 for Bedrock support
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False

# Import performance optimization components
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    from optimizations.performance_monitor import PerformanceMonitor, AsyncPerformanceTracker
    from optimizations.rate_limiter import (
        AdaptiveRateLimiter, CircuitBreaker, RateLimitConfig, CircuitBreakerConfig,
        get_rate_limiter, get_circuit_breaker, get_adaptive_limiter
    )
    from optimizations.connection_pool import (
        HTTPConnectionPool, AWSConnectionPool, OptimizedHTTPClient, 
        ConnectionPoolConfig, AWSConnectionConfig
    )
    
    PERFORMANCE_OPTIMIZATIONS_AVAILABLE = True
    logger.info("Performance optimizations loaded successfully")
    
    # Initialize optimization components with proper configurations
    performance_monitor = PerformanceMonitor()
    
    # Create rate limit config for API endpoints
    api_rate_config = RateLimitConfig(
        requests_per_minute=60,
        burst_capacity=10,
        window_size_seconds=60
    )
    
    # Create circuit breaker config
    api_circuit_config = CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout_seconds=30
    )
    
    # Initialize global components
    global_rate_limiter = get_adaptive_limiter('api', api_rate_config)
    global_circuit_breaker = get_circuit_breaker('api', api_circuit_config)
    
    # Initialize connection pools with proper configurations
    http_pool_config = ConnectionPoolConfig(
        max_connections=100,
        max_connections_per_host=30,
        keepalive_timeout=30,
        timeout_seconds=30
    )
    
    aws_pool_config = AWSConnectionConfig(
        max_pool_connections=50,
        retries_max_attempts=3,
        session_timeout=30
    )
    
    http_pool = HTTPConnectionPool(http_pool_config)
    aws_pool = AWSConnectionPool(aws_pool_config)
    optimized_http_client = OptimizedHTTPClient()
    
except ImportError as e:
    PERFORMANCE_OPTIMIZATIONS_AVAILABLE = False
    logger.warning(f"Performance optimizations not available: {e}")

# Try to import enhanced multi-source components
try:
    # Import new enhanced multi-source fact checker
    from handlers.enhanced_multi_source_fact_checker import EnhancedMultiSourceFactChecker
    ENHANCED_MULTI_SOURCE_AVAILABLE = True
    logger.info("Enhanced multi-source fact checker loaded successfully")
except ImportError as e:
    ENHANCED_MULTI_SOURCE_AVAILABLE = False
    logger.warning(f"Enhanced multi-source fact checker not available: {e}")

# Fallback to original multi-source integration
try:
    from multi_source_integration import (
        get_multi_source_integration, 
        is_multi_source_available,
        MultiSourceIntegration
    )
    MULTI_SOURCE_AVAILABLE = is_multi_source_available()
    if MULTI_SOURCE_AVAILABLE:
        logger.info("Legacy multi-source integration loaded as fallback")
    else:
        logger.warning("Multi-source components available but not functional")
except ImportError as e:
    MULTI_SOURCE_AVAILABLE = False
    logger.warning(f"Multi-source components not available: {e}. Using legacy fact checker.")

app = FastAPI(
    title="FinSight LLM-Enhanced API",
    description="LLM-powered financial fact-checking and enhancement API with Performance Optimizations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Performance Monitoring Middleware
if PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
    @app.middleware("http")
    async def performance_middleware(request: Request, call_next):
        """Middleware for performance monitoring and rate limiting"""
        request_id = f"{request.method}_{request.url.path}_{time.time()}"
        
        # Check rate limiter
        if not global_rate_limiter.allow_request():
            logger.warning(f"Rate limit exceeded for request {request_id}")
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
        
        # Check circuit breaker
        if global_circuit_breaker.state.value != "CLOSED":
            logger.warning(f"Circuit breaker open for request {request_id}")
            raise HTTPException(status_code=503, detail="Service temporarily unavailable. Please try again later.")
        
        # Start performance tracking
        async with AsyncPerformanceTracker(performance_monitor, request_id) as tracker:
            try:
                response = await call_next(request)
                
                # Record success for circuit breaker
                global_circuit_breaker._record_success()
                
                # Add performance headers
                performance_stats = performance_monitor.get_current_stats()
                response.headers["X-Processing-Time"] = str(tracker.duration_ms)
                response.headers["X-System-Health"] = performance_stats["status"]
                response.headers["X-Request-Count"] = str(performance_stats["recent_requests"])
                
                return response
                
            except Exception as e:
                # Record failure for circuit breaker
                global_circuit_breaker._record_failure()
                
                # Log performance impact of errors
                logger.error(f"Request {request_id} failed: {e}")
                raise

# Request/Response Models
class AIResponse(BaseModel):
    content: str
    agent_id: str
    timestamp: str

class EnrichmentRequest(BaseModel):
    ai_response: AIResponse
    enrichment_level: str = "comprehensive"
    fact_check: bool = True
    add_context: bool = True
    llm_provider: str = "auto"  # "ollama", "bedrock", or "auto"

class FactCheckResult(BaseModel):
    claim: str
    verified: bool
    confidence: float
    source: str
    explanation: str

class ContextEnrichment(BaseModel):
    type: str
    content: str
    relevance_score: float
    source: str

class EnhancedResponse(BaseModel):
    original_content: str
    enhanced_content: str
    fact_checks: List[FactCheckResult]
    context_additions: List[ContextEnrichment]
    quality_score: float
    compliance_flags: List[str]
    processing_time_ms: int
    provider_used: str

class MultiLLMClient:
    """Multi-provider LLM client supporting both Ollama and Bedrock"""
    
    def __init__(self, preferred_provider: str = "auto"):
        self.preferred_provider = preferred_provider
        self.ollama_client = LocalLLMClient()
        self.bedrock_client = BedrockLLMClient()
        self.current_provider = self._determine_provider()
    
    def _determine_provider(self) -> str:
        """Determine which provider to use based on availability and preference"""
        if self.preferred_provider == "ollama":
            return "ollama" if self.ollama_client.available else "regex_fallback"
        elif self.preferred_provider == "bedrock":
            return "bedrock" if self.bedrock_client.available else "regex_fallback"
        else:  # auto mode
            if self.ollama_client.available:
                return "ollama"
            elif self.bedrock_client.available:
                return "bedrock"
            else:
                return "regex_fallback"
    
    def extract_claims(self, text: str, provider: str = None) -> tuple:
        """Extract claims using specified or determined provider"""
        if provider:
            self.preferred_provider = provider
            self.current_provider = self._determine_provider()
        
        if self.current_provider == "ollama" and self.ollama_client.available:
            claims = self.ollama_client.extract_claims(text)
            return claims, "ollama_llm"
        elif self.current_provider == "bedrock" and self.bedrock_client.available:
            claims = self.bedrock_client.extract_claims(text)
            return claims, "bedrock_llm"
        else:
            claims = self._regex_fallback(text)
            return claims, "regex_fallback"
    
    def _regex_fallback(self, text: str) -> List[Dict[str, Any]]:
        """Enhanced fallback regex-based claim extraction"""
        return self.ollama_client._regex_fallback(text)

class LocalLLMClient:
    """Local LLM client using Ollama for development"""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "llama3.1:8b"
        self.available = self._check_ollama_availability()
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(model.get('name', '').startswith('llama3.1') for model in models)
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
        return False
    
    def extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """Extract financial claims using local LLM"""
        if not self.available:
            logger.warning("Ollama not available, falling back to regex")
            return self._regex_fallback(text)
        
        try:
            # Improved prompt for better local LLM extraction
            prompt = f"""Extract financial claims from this text. Focus on specific, verifiable facts.

Text: "{text}"

Find these types of claims:
1. Stock prices (e.g., "AAPL trading at $150")
2. Price predictions (e.g., "will increase by 50%") 
3. Market cap values
4. Revenue figures

Return JSON array format:
[
  {{
    "claim": "exact claim text from the input",
    "type": "stock_price",
    "symbol": "AAPL",
    "value": "150"
  }}
]

Extract ALL financial claims with numbers or percentages. Return empty array [] if none found."""

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                return self._parse_llm_response(response_text)
            else:
                logger.warning("LLM request failed, falling back to regex")
                return self._regex_fallback(text)
                
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}, falling back to regex")
            return self._regex_fallback(text)
    
    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse LLM response and extract JSON"""
        try:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                claims_data = json.loads(json_match.group())
                return claims_data if isinstance(claims_data, list) else []
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
        return []
    
    def _regex_fallback(self, text: str) -> List[Dict[str, Any]]:
        """Enhanced fallback regex-based claim extraction"""
        claims = []
        
        # Enhanced stock price patterns - more comprehensive
        stock_patterns = [
            # Original patterns (keep for backward compatibility)
            r'(?:[A-Za-z]+\s+)?\(([A-Z]{2,5})\)\s+(?:is|are)?\s*(?:currently\s+)?(?:trading|priced)\s+(?:at|around|near)\s+\$?(\d+(?:\.\d{2})?)',
            
            # NEW: Direct ticker patterns (most important for our sample)
            r'\b([A-Z]{2,5})\s+stock\s+is\s+currently\s+trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
            r'\b([A-Z]{2,5})\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
            
            # Company name to ticker mappings
            r'\b(Apple|AAPL)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
            r'\b(Microsoft|MSFT)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
            r'\b(Tesla|TSLA)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
            r'\b(Amazon|AMZN)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
            r'\b(Google|GOOGL)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
            r'\b(Meta|META)\s+(?:stock\s+)?(?:is\s+)?(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d{2})?)',
        ]
        
        # Company name to ticker mapping
        name_to_ticker = {
            'Apple': 'AAPL', 'Microsoft': 'MSFT', 'Tesla': 'TSLA',
            'Amazon': 'AMZN', 'Google': 'GOOGL', 'Meta': 'META'
        }
        
        for pattern in stock_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    symbol = match.group(1).upper()
                    value = match.group(2)
                    
                    # Convert company names to tickers
                    if symbol in name_to_ticker:
                        symbol = name_to_ticker[symbol]
                    
                    # Skip invalid symbols like "STOCK"
                    if symbol in ['STOCK', 'IS', 'AT', 'THE']:
                        continue
                    
                    claims.append({
                        "claim": f"{symbol} is currently trading at ${value}",
                        "type": "stock_price",
                        "symbol": symbol,
                        "value": value,
                        "timeframe": "current"
                    })
        
        # Add prediction/growth patterns
        prediction_patterns = [
            r'\b(Apple|AAPL|Microsoft|MSFT|Tesla|TSLA|Amazon|AMZN|Google|GOOGL|Meta|META)\s+stock\s+will\s+increase\s+by\s+(\d+(?:\.\d+)?%)',
            r'\b([A-Z]{2,5})\s+will\s+(?:increase|rise|grow)\s+(?:by\s+)?(\d+(?:\.\d+)?%)',
        ]
        
        for pattern in prediction_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    symbol = match.group(1).upper()
                    percentage = match.group(2)
                    
                    # Convert company names to tickers
                    if symbol in name_to_ticker:
                        symbol = name_to_ticker[symbol]
                    
                    claims.append({
                        "claim": f"{symbol} stock will increase by {percentage}",
                        "type": "prediction",
                        "symbol": symbol,
                        "value": percentage,
                        "timeframe": "future"
                    })
        
        # Filter out invalid symbols and remove duplicates
        invalid_symbols = {'STOCK', 'IS', 'AT', 'THE', 'AND', 'OR', 'BUT', 'FOR', 'WITH', 'BY'}
        seen_claims = set()
        valid_claims = []
        
        for claim in claims:
            if claim['symbol'] not in invalid_symbols:
                # Create a unique identifier for the claim
                claim_id = (claim['symbol'], claim['type'], str(claim['value']))
                if claim_id not in seen_claims:
                    seen_claims.add(claim_id)
                    valid_claims.append(claim)
        
        return valid_claims

class FinancialDataProvider:
    """Financial data provider using Yahoo Finance"""
    
    @staticmethod
    def get_stock_price(symbol: str) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                return {
                    "symbol": symbol,
                    "current_price": round(current_price, 2),
                    "company_name": info.get('longName', symbol),
                    "market_cap": info.get('marketCap'),
                    "pe_ratio": info.get('trailingPE'),
                    "last_updated": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
        
        return None

class ContextEnricher:
    """Simple context enrichment for demo"""
    
    def get_context_for_content(self, content: str) -> List[ContextEnrichment]:
        """Get relevant context for content"""
        context_additions = []
        content_lower = content.lower()
        
        # Stock market context
        if any(word in content_lower for word in ['stock', 'trading', 'shares', 'investment']):
            context_additions.append(ContextEnrichment(
                type="market_context",
                content="Stock market investments carry risks and past performance does not guarantee future results. Markets are open 9:30 AM - 4:00 PM ET, Monday-Friday.",
                relevance_score=0.85,
                source="Market Structure"
            ))
        
        # Apple/AAPL specific context
        if any(word in content_lower for word in ['aapl', 'apple']):
            context_additions.append(ContextEnrichment(
                type="company_context", 
                content="Apple Inc. (AAPL) is a technology company focused on consumer electronics, software, and services. It's one of the largest companies by market capitalization.",
                relevance_score=0.9,
                source="Company Information"
            ))
        
        # Investment advice context
        if any(word in content_lower for word in ['recommend', 'advice', 'should buy', 'should sell']):
            context_additions.append(ContextEnrichment(
                type="disclaimer",
                content="Investment recommendations should be evaluated carefully. Consider consulting with a financial advisor and conducting your own research before making investment decisions.",
                relevance_score=0.95,
                source="Investment Guidelines"
            ))
        
        # Risk/guarantee language context
        if any(word in content_lower for word in ['guaranteed', 'sure thing', 'can\'t lose']):
            context_additions.append(ContextEnrichment(
                type="risk_warning",
                content="No investment is guaranteed. All investments carry risk of loss, and past performance does not predict future results. Be wary of claims suggesting guaranteed returns.",
                relevance_score=0.98,
                source="SEC Investor Alerts"
            ))
        
        return context_additions

class EnhancedFactChecker:
    """Enhanced fact checker with LLM-powered claim extraction and enhanced multi-source support"""
    
    def __init__(self, enable_multi_source: bool = True):
        self.llm_client = LocalLLMClient()
        self.data_provider = FinancialDataProvider()
        self.context_enricher = ContextEnricher()
        self.enable_enhanced_multi_source = enable_multi_source and ENHANCED_MULTI_SOURCE_AVAILABLE
        self.enable_legacy_multi_source = enable_multi_source and MULTI_SOURCE_AVAILABLE
        
        # Initialize enhanced multi-source fact checker if available
        if self.enable_enhanced_multi_source:
            try:
                self.enhanced_fact_checker = EnhancedMultiSourceFactChecker(config={
                    'cross_validation_tolerance': 0.05,
                    'minimum_sources': 2,
                    'enable_fallback': True,
                    'enable_parallel': True
                })
                logger.info("Enhanced multi-source fact checker initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize enhanced multi-source fact checker: {e}")
                self.enable_enhanced_multi_source = False
                self.enhanced_fact_checker = None
        else:
            self.enhanced_fact_checker = None
        
        # Fallback to legacy multi-source integration if enhanced not available
        if not self.enable_enhanced_multi_source and self.enable_legacy_multi_source:
            try:
                self.multi_source_integration = get_multi_source_integration()
                if self.multi_source_integration and self.multi_source_integration.available:
                    logger.info("Legacy multi-source integration initialized as fallback")
                else:
                    logger.warning("Legacy multi-source integration not available")
                    self.enable_legacy_multi_source = False
                    self.multi_source_integration = None
            except Exception as e:
                logger.warning(f"Failed to initialize legacy multi-source integration: {e}")
                self.enable_legacy_multi_source = False
                self.multi_source_integration = None
        else:
            self.multi_source_integration = None
    
    async def process_content(self, content: str, provider: str = "auto") -> tuple:
        """Process content with enhanced multi-source capabilities"""
        start_time = datetime.now()
        
        logger.info(f"Processing content with enhanced multi-source enabled: {self.enable_enhanced_multi_source}")
        logger.info(f"Legacy multi-source available: {self.enable_legacy_multi_source}")
        
        # Try enhanced multi-source processing first if available
        if self.enable_enhanced_multi_source and self.enhanced_fact_checker:
            logger.info("Attempting enhanced multi-source processing...")
            try:
                # Extract claims using LLM
                claims = self.llm_client.extract_claims(content)
                logger.info(f"Extracted {len(claims)} claims for enhanced processing")
                
                # Process claims with enhanced fact checker
                enhanced_results = []
                for claim_info in claims:
                    claim_text = claim_info.get('claim', '')
                    if claim_text:
                        fact_check_result = await self.enhanced_fact_checker.fact_check(claim_text)
                        enhanced_results.append(fact_check_result)
                
                # Convert enhanced results to legacy format
                fact_checks = self._convert_enhanced_fact_check_results(enhanced_results)
                
                # Get context enrichments
                context_additions = self.context_enricher.get_context_for_content(content)
                
                # Add multi-source context from enhanced results
                for result in enhanced_results:
                    if result.sources_used:
                        sources_text = f"Verified using: {', '.join(result.sources_used)}"
                        if result.cross_validation_passed:
                            sources_text += f" (Cross-validation: ✓ {result.confidence_score:.1%} confidence)"
                        
                        context_additions.append(ContextEnrichment(
                            type="enhanced_multi_source_context",
                            content=sources_text,
                            relevance_score=result.confidence_score,
                            source="Enhanced Multi-source Validation"
                        ))
                
                # Create enhanced content with multi-source metadata
                enhanced_content = content
                if enhanced_results:
                    sources_used = set()
                    for result in enhanced_results:
                        sources_used.update(result.sources_used)
                    
                    if sources_used:
                        sources_text = f"\n\n🔍 Enhanced Data Sources: {', '.join(sorted(sources_used))}"
                        cross_validated_count = sum(1 for r in enhanced_results if r.cross_validation_passed)
                        if cross_validated_count > 0:
                            sources_text += f" | Cross-validated claims: {cross_validated_count}/{len(enhanced_results)}"
                        enhanced_content += sources_text
                
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                
                logger.info(f"Enhanced multi-source processing completed in {processing_time:.1f}ms")
                return fact_checks, context_additions, enhanced_content, processing_time
                
            except Exception as e:
                logger.warning(f"Enhanced multi-source processing failed: {e}. Falling back to legacy processing.")
        
        # Fallback to legacy multi-source processing if enhanced not available
        if self.enable_legacy_multi_source and self.multi_source_integration:
            logger.info("Attempting legacy multi-source processing...")
            try:
                result = await self.multi_source_integration.process_content(
                    content=content,
                    context={"provider": provider, "request_time": start_time.isoformat()}
                )
                
                # Convert legacy multi-source results
                fact_checks = self._convert_enhanced_results(result.get('fact_check_results', []))
                
                # Use enhanced content if available
                enhanced_content = result.get('enhanced_content', content)
                
                # Get context enrichments
                context_additions = self.context_enricher.get_context_for_content(content)
                
                # Add legacy multi-source context if available
                if result.get('context_enrichments'):
                    for ctx in result['context_enrichments']:
                        context_additions.append(ContextEnrichment(
                            type="legacy_multi_source_context",
                            content=ctx.get('content', ''),
                            relevance_score=ctx.get('relevance_score', 0.5),
                            source=ctx.get('source', 'Legacy Multi-source')
                        ))
                
                # Add processing metadata to enhanced content
                if result.get('data_sources_used'):
                    sources_text = f"\n\n🔍 Data Sources Consulted: {', '.join(result['data_sources_used'])}"
                    enhanced_content += sources_text
                
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                
                logger.info(f"Legacy multi-source processing completed in {processing_time:.1f}ms")
                return fact_checks, context_additions, enhanced_content, processing_time
                
            except Exception as e:
                logger.warning(f"Legacy multi-source processing failed: {e}. Falling back to basic processing.")
        
        # Fallback to basic processing
        return await self._legacy_process_content(content, provider, start_time)
    
    def _convert_enhanced_fact_check_results(self, enhanced_results) -> List[FactCheckResult]:
        """Convert enhanced multi-source fact check results to legacy format"""
        logger.info(f"Converting {len(enhanced_results)} enhanced fact check results")
        legacy_results = []
        
        for i, result in enumerate(enhanced_results):
            try:
                logger.info(f"Converting enhanced result {i+1}: confidence={result.confidence_score}, sources={result.sources_used}")
                
                # Create Pydantic model instance from enhanced result
                legacy_result = FactCheckResult(
                    claim=result.claim,
                    verified=result.is_factual,
                    confidence=result.confidence_score,
                    source=result.sources_used[0] if result.sources_used else 'Unknown',
                    explanation=result.verification_text
                )
                legacy_results.append(legacy_result)
                logger.info(f"Successfully converted enhanced result {i+1}")
            except Exception as e:
                logger.warning(f"Failed to convert enhanced result {i+1}: {e}")
        
        logger.info(f"Enhanced conversion complete: {len(legacy_results)} legacy results created")
        return legacy_results
    
    def _convert_enhanced_results(self, enhanced_results: List[Dict[str, Any]]) -> List[FactCheckResult]:
        """Convert enhanced fact check results to legacy format"""
        logger.info(f"Converting {len(enhanced_results)} enhanced results")
        legacy_results = []
        
        for i, result in enumerate(enhanced_results):
            try:
                logger.info(f"Converting result {i+1}: {list(result.keys())}")
                
                # Handle nested claim structure from multi-source integration
                claim_text = result.get('claim', '')
                if isinstance(claim_text, dict):
                    claim_text = claim_text.get('text', str(claim_text))
                    logger.info(f"Extracted claim text: {claim_text}")
                
                # Create Pydantic model instance (not dataclass)
                legacy_result = FactCheckResult(
                    claim=claim_text,
                    verified=result.get('verified', False),
                    confidence=result.get('confidence', 0.0),
                    source=result.get('sources', ['Unknown'])[0] if result.get('sources') else 'Unknown',
                    explanation=result.get('explanation', '')
                )
                legacy_results.append(legacy_result)
                logger.info(f"Successfully converted result {i+1} to Pydantic model")
            except Exception as e:
                logger.warning(f"Failed to convert enhanced result {i+1}: {e}")
        
        logger.info(f"Conversion complete: {len(legacy_results)} legacy results created")
        return legacy_results
    
    async def _legacy_process_content(self, content: str, provider: str, start_time: datetime) -> tuple:
        """Legacy processing method for backward compatibility"""
        # Extract claims using LLM
        claims_data = self.llm_client.extract_claims(content)
        logger.info(f"Extracted {len(claims_data)} claims using {'LLM' if self.llm_client.available else 'regex'}")
        
        fact_checks = []
        enhanced_content = content
        
        # Verify each claim
        for claim_info in claims_data:
            claim_text = claim_info.get('claim', '')
            symbol = claim_info.get('symbol', '')
            claim_type = claim_info.get('type', '')
            
            if symbol and claim_type == 'stock_price':
                fact_check = self._verify_stock_price_claim(claim_text, symbol, claim_info.get('value'))
                if fact_check:
                    fact_checks.append(fact_check)
            elif symbol and claim_type in ['prediction', 'price_prediction']:
                # Add fact check for prediction claims
                fact_check = self._verify_prediction_claim(claim_text, symbol, claim_info.get('value'))
                if fact_check:
                    fact_checks.append(fact_check)
        
        # Get context enrichments
        context_additions = self.context_enricher.get_context_for_content(content)
        logger.info(f"Generated {len(context_additions)} context enrichments")
        
        # Add context to enhanced content
        if context_additions:
            context_text = "\n\n📊 Additional Context:\n"
            for ctx in context_additions:
                context_text += f"• {ctx.content} (Source: {ctx.source})\n"
            enhanced_content += context_text
        
        # Add fact-check warnings to content
        failed_checks = [fc for fc in fact_checks if not fc.verified]
        if failed_checks:
            warning_text = "\n\n⚠️ Fact Check Alerts:\n"
            for fc in failed_checks:
                warning_text += f"• {fc.claim} - {fc.explanation}\n"
            enhanced_content += warning_text
        
        # Add verification confirmations
        verified_checks = [fc for fc in fact_checks if fc.verified]
        if verified_checks:
            verification_text = "\n\n✅ Verified Information:\n"
            for fc in verified_checks:
                verification_text += f"• {fc.claim} - {fc.explanation}\n"
            enhanced_content += verification_text
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return fact_checks, context_additions, enhanced_content, processing_time
    
    def _verify_stock_price_claim(self, claim: str, symbol: str, claimed_value: str) -> Optional[FactCheckResult]:
        """Verify a stock price claim"""
        try:
            # Clean the claimed value - remove currency symbols and whitespace
            cleaned_value = claimed_value.strip().replace('$', '').replace(',', '')
            claimed_price = float(cleaned_value)
            actual_data = self.data_provider.get_stock_price(symbol)
            
            if actual_data:
                actual_price = actual_data['current_price']
                price_diff = abs(actual_price - claimed_price) / actual_price
                
                if price_diff < 0.05:  # Within 5%
                    return FactCheckResult(
                        claim=claim,
                        verified=True,
                        confidence=0.95,
                        source="Yahoo Finance",
                        explanation=f"Current price ${actual_price:.2f} is within 5% of claimed ${claimed_price}"
                    )
                else:
                    return FactCheckResult(
                        claim=claim,
                        verified=False,
                        confidence=0.9,
                        source="Yahoo Finance",
                        explanation=f"Current price ${actual_price:.2f} differs significantly from claimed ${claimed_price} (difference: {price_diff*100:.1f}%)"
                    )
        except Exception as e:
            logger.error(f"Error verifying claim: {e}")
        
        return None
    
    def _verify_prediction_claim(self, claim: str, symbol: str, predicted_change: str) -> Optional[FactCheckResult]:
        """Verify a price prediction claim"""
        try:
            # Clean the predicted change value
            cleaned_value = predicted_change.strip().replace('%', '')
            predicted_percent = float(cleaned_value)
            
            # Get current stock data for context
            actual_data = self.data_provider.get_stock_price(symbol)
            
            if actual_data:
                current_price = actual_data['current_price']
                company_name = actual_data.get('company_name', symbol)
                
                # Prediction claims cannot be "verified" as true/false since they're future predictions
                # Instead, we provide context and flag as unverifiable prediction
                return FactCheckResult(
                    claim=claim,
                    verified=False,  # Predictions cannot be verified as they're about the future
                    confidence=0.0,  # No confidence since it's a future prediction
                    source="Market Data Context",
                    explanation=f"This is a prediction about {company_name} ({symbol}) future performance. Current price: ${current_price:.2f}. Predictions cannot be verified and should not be considered investment advice."
                )
        except Exception as e:
            logger.error(f"Error analyzing prediction claim: {e}")
        
        return None

class ComplianceChecker:
    """Compliance checking for financial content"""
    
    def check_compliance(self, text: str) -> List[str]:
        flags = []
        text_lower = text.lower()
        
        # High-risk investment language patterns
        high_risk_patterns = [
            r'(?:guaranteed|certain|sure|definitely)\s+(?:profit|return|money|gain)',
            r'can[\'t\s]*(?:lose|fail)',
            r'(?:all|entire)\s+(?:savings|money)',
            r'insider\s+information',
            r'(?:will|shall)\s+(?:definitely|certainly)\s+(?:make|earn|gain)'
        ]
        
        for pattern in high_risk_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                flags.append("HIGH RISK: Misleading investment guarantees detected")
                break
        
        # Investment advice patterns
        advice_patterns = [
            r'(?:should|must|need to)\s+(?:buy|sell|invest)',
            r'(?:recommend|suggest).*(?:buy|sell|invest)',
            r'(?:trust me|believe me)'
        ]
        
        for pattern in advice_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                flags.append("Investment advice without proper disclaimers")
                break
        
        # Risk disclosure check
        if any(word in text_lower for word in ['investment', 'portfolio', 'returns', 'trading']) and \
           'risk' not in text_lower and 'disclaimer' not in text_lower:
            flags.append("Investment discussion without risk disclosure")
        
        return flags

def calculate_enhanced_quality_score(fact_checks: List[FactCheckResult], 
                                   context_additions: List[Any], 
                                   compliance_flags: List[str]) -> float:
    """
    Calculate enhanced quality score based on multiple factors
    Returns score between 0.0 and 1.0 (displayed as percentage)
    """
    # Start with a higher base score for realistic content
    base_score = 0.85
    
    # Fact check scoring - more nuanced approach
    fact_check_score = 0.0
    if fact_checks:
        verified_count = sum(1 for fc in fact_checks if fc.verified)
        total_confidence = sum(fc.confidence for fc in fact_checks)
        avg_confidence = total_confidence / len(fact_checks)
        
        # Combine verification ratio with average confidence
        verified_ratio = verified_count / len(fact_checks)
        fact_check_score = 0.15 * (verified_ratio * 0.7 + avg_confidence * 0.3)
    
    # Context enrichment bonus - rewards comprehensive analysis
    context_bonus = min(0.1, len(context_additions) * 0.02)
    
    # Compliance scoring - more graduated penalties
    compliance_score = 0.0
    if compliance_flags:
        # Less severe penalties for minor issues
        high_severity = sum(1 for flag in compliance_flags if 'high' in flag.lower() or 'severe' in flag.lower())
        medium_severity = sum(1 for flag in compliance_flags if 'medium' in flag.lower())
        low_severity = len(compliance_flags) - high_severity - medium_severity
        
        compliance_penalty = (high_severity * 0.15) + (medium_severity * 0.08) + (low_severity * 0.03)
        compliance_score = -min(0.3, compliance_penalty)  # Cap maximum penalty
    
    # Content length bonus (if we have content)
    content_bonus = 0.02  # Small bonus for having content to analyze
    
    # Calculate final score
    final_score = base_score + fact_check_score + context_bonus + compliance_score + content_bonus
    
    # Ensure realistic range - most content should score 60-95%
    final_score = max(0.4, min(1.0, final_score))
    
    logger.info(f"Quality score breakdown - Base: {base_score:.2f}, Facts: {fact_check_score:.2f}, "
               f"Context: {context_bonus:.2f}, Compliance: {compliance_score:.2f}, Final: {final_score:.2f}")
    
    return round(final_score, 3)

# Initialize components
compliance_checker = ComplianceChecker()

class BedrockLLMClient:
    """AWS Bedrock LLM client for cloud-based claim extraction"""
    
    def __init__(self):
        self.available = False
        self.client = None
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        self.fallback_model_id = "amazon.titan-text-express-v1"
        
        if BEDROCK_AVAILABLE:
            self.available = self._check_bedrock_availability()
    
    def _check_bedrock_availability(self) -> bool:
        """Check if Bedrock is available and accessible"""
        try:
            self.client = boto3.client('bedrock-runtime', region_name='us-east-1')
            # Try a simple test call to verify access
            test_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}]
            }
            
            response = self.client.invoke_model(
                body=json.dumps(test_body),
                modelId=self.model_id,
                accept='application/json',
                contentType='application/json'
            )
            return True
        except Exception as e:
            logger.warning(f"Bedrock not available: {e}")
            return False
    
    def extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """Extract financial claims using Bedrock LLM"""
        if not self.available:
            logger.warning("Bedrock not available, falling back to regex")
            return self._regex_fallback(text)
        
        try:
            prompt = f"""Extract financial claims from this text. Focus on specific, verifiable facts.

Text: "{text}"

Find these types of claims:
1. Stock prices (e.g., "AAPL trading at $150")
2. Price predictions (e.g., "will increase by 50%") 
3. Market cap values
4. Revenue figures

Return JSON array format:
[
  {{
    "claim": "exact claim text from the input",
    "type": "stock_price",
    "symbol": "AAPL",
    "value": "150"
  }}
]

Extract ALL financial claims with numbers or percentages. Return empty array [] if none found."""

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = self.client.invoke_model(
                body=json.dumps(body),
                modelId=self.model_id,
                accept='application/json',
                contentType='application/json'
            )
            
            response_body = json.loads(response.get('body').read())
            response_text = response_body['content'][0]['text']
            
            return self._parse_llm_response(response_text)
                
        except Exception as e:
            logger.warning(f"Bedrock extraction failed: {e}, falling back to regex")
            return self._regex_fallback(text)
    
    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse LLM response and extract JSON"""
        try:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                claims_data = json.loads(json_match.group())
                return claims_data if isinstance(claims_data, list) else []
        except Exception as e:
            logger.warning(f"Failed to parse Bedrock response: {e}")
        return []
    
    def _regex_fallback(self, text: str) -> List[Dict[str, Any]]:
        """Fallback regex-based claim extraction using LocalLLMClient patterns"""
        # Delegate to the LocalLLMClient's regex implementation for consistency
        local_client = LocalLLMClient()
        return local_client._regex_fallback(text)

async def verify_financial_claim(claim_data: Dict[str, Any]) -> FactCheckResult:
    """
    Verify a financial claim from extracted claim data.
    
    Args:
        claim_data: Dictionary containing claim information with keys:
                   - 'claim': The claim text
                   - 'type': The claim type (stock_price, market_cap, etc.)
                   - 'symbol': Stock symbol (if applicable)
                   - 'value': The claimed value
    
    Returns:
        FactCheckResult: The verification result
    """
    try:
        claim_text = claim_data.get('claim', 'Unknown claim')
        claim_type = claim_data.get('type', 'unknown')
        symbol = claim_data.get('symbol', '').upper()
        value = claim_data.get('value', '')
        
        logger.info(f"Verifying {claim_type} claim: {claim_text}")
        
        if claim_type == 'stock_price' and symbol and value:
            return await _verify_stock_price_claim(claim_text, symbol, value)
        elif claim_type == 'market_cap' and symbol and value:
            return await _verify_market_cap_claim(claim_text, symbol, value)
        elif claim_type == 'prediction':
            return _create_prediction_result(claim_text, symbol)
        else:
            # Generic fallback for unhandled claim types
            return FactCheckResult(
                claim=claim_text,
                verified=False,
                confidence=0.3,
                source="Generic verification",
                explanation=f"Claim type '{claim_type}' requires specialized verification method"
            )
            
    except Exception as e:
        logger.error(f"Error verifying claim: {e}")
        return FactCheckResult(
            claim=claim_data.get('claim', 'Unknown claim'),
            verified=False,
            confidence=0.0,
            source="verification_error",
            explanation=f"Verification failed: {str(e)}"
        )

async def _verify_stock_price_claim(claim: str, symbol: str, claimed_value: str) -> FactCheckResult:
    """Verify a stock price claim using real market data"""
    try:
        # Clean the claimed value
        cleaned_value = claimed_value.strip().replace('$', '').replace(',', '')
        claimed_price = float(cleaned_value)
        
        # Get actual stock data
        data_provider = FinancialDataProvider()
        actual_data = data_provider.get_stock_price(symbol)
        
        if actual_data:
            actual_price = actual_data['current_price']
            price_diff = abs(actual_price - claimed_price) / actual_price
            
            if price_diff < 0.05:  # Within 5%
                return FactCheckResult(
                    claim=claim,
                    verified=True,
                    confidence=round(0.95 - price_diff, 3),
                    source="Yahoo Finance",
                    explanation=f"Current price ${actual_price:.2f} is within 5% of claimed ${claimed_price:.2f}"
                )
            else:
                return FactCheckResult(
                    claim=claim,
                    verified=False,
                    confidence=0.9,
                    source="Yahoo Finance",
                    explanation=f"Current price ${actual_price:.2f} differs significantly from claimed ${claimed_price:.2f} (difference: {price_diff*100:.1f}%)"
                )
        else:
            return FactCheckResult(
                claim=claim,
                verified=False,
                confidence=0.5,
                source="Data retrieval",
                explanation=f"Could not retrieve current price data for {symbol}"
            )
            
    except ValueError:
        return FactCheckResult(
            claim=claim,
            verified=False,
            confidence=0.3,
            source="Value parsing",
            explanation=f"Could not parse claimed price value: {claimed_value}"
        )
    except Exception as e:
        logger.error(f"Error verifying stock price: {e}")
        return FactCheckResult(
            claim=claim,
            verified=False,
            confidence=0.2,
            source="verification_error",
            explanation=f"Error retrieving stock data: {str(e)}"
        )

async def _verify_market_cap_claim(claim: str, symbol: str, claimed_value: str) -> FactCheckResult:
    """Verify a market cap claim using real market data"""
    try:
        # Parse claimed market cap value
        value_str = claimed_value.strip().replace('$', '').replace(',', '')
        
        # Handle different units (trillion, billion, million)
        multiplier = 1
        if 'trillion' in claimed_value.lower() or 'T' in claimed_value:
            multiplier = 1e12
        elif 'billion' in claimed_value.lower() or 'B' in claimed_value:
            multiplier = 1e9
        elif 'million' in claimed_value.lower() or 'M' in claimed_value:
            multiplier = 1e6
        
        # Extract numeric value
        import re
        num_match = re.search(r'(\d+(?:\.\d+)?)', value_str)
        if not num_match:
            return FactCheckResult(
                claim=claim,
                verified=False,
                confidence=0.3,
                source="Value parsing",
                explanation=f"Could not parse market cap value: {claimed_value}"
            )
        
        claimed_market_cap = float(num_match.group(1)) * multiplier
        
        # Get actual market cap
        data_provider = FinancialDataProvider()
        actual_data = data_provider.get_stock_price(symbol)
        
        if actual_data and actual_data.get('market_cap'):
            actual_market_cap = actual_data['market_cap']
            cap_diff = abs(actual_market_cap - claimed_market_cap) / actual_market_cap
            
            if cap_diff < 0.15:  # Within 15%
                return FactCheckResult(
                    claim=claim,
                    verified=True,
                    confidence=round(0.9 - cap_diff, 3),
                    source="Yahoo Finance",
                    explanation=f"Market cap ${actual_market_cap/1e9:.1f}B is within 15% of claimed value"
                )
            else:
                return FactCheckResult(
                    claim=claim,
                    verified=False,
                    confidence=0.8,
                    source="Yahoo Finance",
                    explanation=f"Market cap ${actual_market_cap/1e9:.1f}B differs significantly from claimed value"
                )
        else:
            return FactCheckResult(
                claim=claim,
                verified=False,
                confidence=0.5,
                source="Data retrieval",
                explanation=f"Could not retrieve market cap data for {symbol}"
            )
            
    except Exception as e:
        logger.error(f"Error verifying market cap: {e}")
        return FactCheckResult(
            claim=claim,
            verified=False,
            confidence=0.2,
            source="verification_error",
            explanation=f"Error verifying market cap: {str(e)}"
        )

def _create_prediction_result(claim: str, symbol: str) -> FactCheckResult:
    """Create a fact check result for prediction claims"""
    return FactCheckResult(
        claim=claim,
        verified=False,  # Predictions cannot be verified as they're about the future
        confidence=0.0,  # No confidence since it's a future prediction
        source="Prediction Analysis",
        explanation="This is a prediction about future performance and cannot be verified. Predictions should not be considered investment advice."
    )

@app.post("/enhance", response_model=EnhancedResponse)
async def enhance_ai_response(request: EnrichmentRequest):
    """Enhanced endpoint with multi-provider LLM-powered claim extraction and multi-source fact checking"""
    start_time = datetime.now()
    
    try:
        content = request.ai_response.content
        
        # Validate request before processing
        if not content or len(content.strip()) == 0:
            raise HTTPException(status_code=400, detail="Empty content provided")
        
        # Use optimized HTTP client for external requests if available
        if PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
            # Check system health before processing
            stats = performance_monitor.get_stats()
            if stats["system_health"] == "critical":
                logger.warning("System health critical, rejecting request")
                raise HTTPException(status_code=503, detail="System overloaded, please try again later")
        
        # Initialize enhanced fact checker with multi-source support
        enhanced_fact_checker = EnhancedFactChecker(enable_multi_source=True)
        
        # Initialize multi-provider LLM client with user preference
        multi_llm_client = MultiLLMClient(preferred_provider=request.llm_provider)
        provider_used = multi_llm_client.current_provider
        
        # Process content with enhanced multi-source fact checking and performance tracking
        if PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
            async with AsyncPerformanceTracker(performance_monitor, f"fact_check_{time.time()}") as fact_check_tracker:
                fact_checks, context_additions, enhanced_content, fact_check_time = await enhanced_fact_checker.process_content(
                    content, provider=request.llm_provider
                )
        else:
            fact_checks, context_additions, enhanced_content, fact_check_time = await enhanced_fact_checker.process_content(
                content, provider=request.llm_provider
            )
        
        logger.info(f"Fact checking completed: {len(fact_checks)} claims verified in {fact_check_time:.1f}ms")
        
        # Enhanced content generation using LLM-powered rewriting
        try:
            llm_enhanced_content = await generate_enhanced_content(enhanced_content, fact_checks, multi_llm_client)
            if llm_enhanced_content and len(llm_enhanced_content.strip()) > len(enhanced_content) / 2:
                enhanced_content = llm_enhanced_content
                logger.info("Used LLM-enhanced content generation")
            else:
                logger.info("Used template-based content enhancement")
        except Exception as e:
            logger.warning(f"LLM content enhancement failed: {e}")
        
        # Additional context enrichment for verified facts
        for fact_check in fact_checks:
            if fact_check.verified and fact_check.confidence > 0.7:
                context_additions.append(ContextEnrichment(
                    type="fact_verification",
                    content=f"✓ Verified: {fact_check.explanation}",
                    relevance_score=fact_check.confidence,
                    source=fact_check.source
                ))
        
        # Compliance checking
        compliance_flags = compliance_checker.check_compliance(content)
        
        # Calculate quality score based on verification and enhancement
        quality_score = calculate_enhanced_quality_score(fact_checks, context_additions, compliance_flags)
        
        # Add multi-source processing bonus
        if (enhanced_fact_checker.enable_enhanced_multi_source or enhanced_fact_checker.enable_legacy_multi_source) and enhanced_fact_checker.multi_source_integration:
            quality_score = min(1.0, quality_score + 0.05)  # 5% bonus for multi-source processing
        
        # Reduce score for compliance issues
        if compliance_flags:
            quality_score = max(0.3, quality_score - (len(compliance_flags) * 0.05))
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"About to create response with {len(fact_checks)} fact checks")
        for i, fc in enumerate(fact_checks):
            logger.info(f"Fact check {i+1}: type={type(fc)}, claim='{fc.claim}', verified={fc.verified}")
        
        response = EnhancedResponse(
            original_content=content,
            enhanced_content=enhanced_content,
            fact_checks=fact_checks,
            context_additions=context_additions,
            quality_score=quality_score,
            compliance_flags=compliance_flags,
            processing_time_ms=int(processing_time),
            provider_used=f"{provider_used}" + ("_with_multi_source" if (enhanced_fact_checker.enable_enhanced_multi_source or enhanced_fact_checker.enable_legacy_multi_source) else "")
        )
        
        logger.info(f"API Response created with {len(response.fact_checks)} fact checks")
        if response.fact_checks:
            logger.info(f"First fact check in response: {response.fact_checks[0].claim}")
        
        return response
    
    except Exception as e:
        logger.error(f"Enhancement failed: {e}")
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check with multi-provider LLM status, enhanced multi-source capabilities, and performance metrics"""
    # Check provider availability
    multi_llm = MultiLLMClient()
    ollama_status = "available" if multi_llm.ollama_client.available else "unavailable"
    bedrock_status = "available" if multi_llm.bedrock_client.available else "unavailable"
    
    # Performance monitoring status
    performance_status = {}
    if PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
        stats = performance_monitor.get_current_stats()
        performance_status = {
            "system_health": stats["status"],
            "total_requests": stats["recent_requests"],
            "avg_response_time_ms": stats["avg_response_time_ms"],
            "rate_limiter_status": global_rate_limiter.rate_limiter.get_stats(),
            "circuit_breaker_state": global_circuit_breaker.state.value,
            "connection_pools": {
                "http_pool_active": len(http_pool._session._connector._conns) if hasattr(http_pool, '_session') else 0,
                "aws_pool_sessions": len(aws_pool.session_cache) if hasattr(aws_pool, 'session_cache') else 0
            }
        }
    
    # Check enhanced multi-source fact checker
    enhanced_multi_source_status = "unavailable"
    enhanced_source_health = {}
    
    if ENHANCED_MULTI_SOURCE_AVAILABLE:
        try:
            test_fact_checker = EnhancedMultiSourceFactChecker()
            source_health = await test_fact_checker.check_source_health()
            enhanced_multi_source_status = "available"
            enhanced_source_health = {
                "yahoo_finance": source_health.yahoo_finance,
                "world_bank": source_health.world_bank,
                "alpha_vantage": source_health.alpha_vantage,
                "last_check": source_health.last_check
            }
        except Exception as e:
            enhanced_multi_source_status = f"error: {str(e)[:50]}"
    
    # Check legacy multi-source components
    legacy_multi_source_status = "unavailable"
    legacy_data_sources = []
    
    if MULTI_SOURCE_AVAILABLE:
        try:
            test_integration = get_multi_source_integration()
            if test_integration and test_integration.available:
                legacy_multi_source_status = "available"
                legacy_data_sources = test_integration.get_available_sources()
            else:
                legacy_multi_source_status = "initialized_but_not_functional"
        except Exception as e:
            legacy_multi_source_status = f"error: {str(e)[:50]}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "performance": performance_status if PERFORMANCE_OPTIMIZATIONS_AVAILABLE else {"status": "optimizations_disabled"},
        "providers": {
            "ollama": {
                "status": ollama_status,
                "model": multi_llm.ollama_client.model if multi_llm.ollama_client.available else None
            },
            "bedrock": {
                "status": bedrock_status,
                "model": multi_llm.bedrock_client.model_id if multi_llm.bedrock_client.available else None
            }
        },
        "enhanced_multi_source": {
            "status": enhanced_multi_source_status,
            "source_health": enhanced_source_health,
            "cross_validation": "enabled" if enhanced_multi_source_status == "available" else "unavailable",
            "confidence_scoring": "enabled" if enhanced_multi_source_status == "available" else "unavailable"
        },
        "legacy_multi_source": {
            "status": legacy_multi_source_status,
            "available_sources": legacy_data_sources,
            "bedrock_agents": "available" if bedrock_status == "available" and legacy_multi_source_status == "available" else "unavailable"
        },
        "current_provider": multi_llm.current_provider,
        "fallback": "regex" if multi_llm.current_provider == "regex_fallback" else None,
        "enhanced_features": {
            "enhanced_multi_source_fact_checking": ENHANCED_MULTI_SOURCE_AVAILABLE,
            "legacy_multi_source_fact_checking": MULTI_SOURCE_AVAILABLE,
            "world_bank_integration": enhanced_multi_source_status == "available" or legacy_multi_source_status == "available",
            "alpha_vantage_integration": enhanced_multi_source_status == "available",
            "bedrock_agent_orchestration": bedrock_status == "available" and MULTI_SOURCE_AVAILABLE,
            "cross_validation": enhanced_multi_source_status == "available",
            "confidence_scoring": enhanced_multi_source_status == "available",
            "performance_optimizations": PERFORMANCE_OPTIMIZATIONS_AVAILABLE
        }
    }    @app.get("/performance-stats")
    async def get_performance_stats():
        """Get detailed performance statistics"""
        stats = performance_monitor.get_current_stats()
        rate_limiter_stats = global_rate_limiter.rate_limiter.get_stats()
        circuit_breaker_stats = global_circuit_breaker.get_state()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "performance": stats,
            "rate_limiter": rate_limiter_stats,
            "circuit_breaker": circuit_breaker_stats,
            "connection_pools": {
                "http_pool": {
                    "active_connections": len(http_pool._session._connector._conns) if hasattr(http_pool, '_session') and hasattr(http_pool._session, '_connector') else 0,
                    "status": "healthy" if hasattr(http_pool, '_session') else "not_initialized"
                },
                "aws_pool": {
                    "cached_sessions": len(aws_pool.session_cache) if hasattr(aws_pool, 'session_cache') else 0,
                    "status": "healthy" if hasattr(aws_pool, 'session_cache') else "not_initialized"
                }
            }
        }    @app.post("/reset-circuit-breaker")
    async def reset_circuit_breaker():
        """Manually reset the circuit breaker"""
        global_circuit_breaker.state = global_circuit_breaker.state.__class__.CLOSED
        global_circuit_breaker.failure_count = 0
        global_circuit_breaker.success_count = 0
        return {
            "message": "Circuit breaker reset successfully",
            "timestamp": datetime.now().isoformat(),
            "new_state": global_circuit_breaker.state.value
        }    @app.get("/system-health")
    async def get_system_health():
        """Get comprehensive system health information"""
        stats = performance_monitor.get_current_stats()
        
        # Determine overall system status
        overall_status = "healthy"
        if stats["status"] in ["degraded", "critical"]:
            overall_status = stats["status"]
        elif global_circuit_breaker.state.value == "OPEN":
            overall_status = "degraded"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "performance_monitor": {
                    "status": stats["status"],
                    "avg_response_time": stats["avg_response_time_ms"],
                    "total_requests": stats["recent_requests"]
                },
                "rate_limiter": {
                    "status": "healthy" if global_rate_limiter.rate_limiter.bucket.tokens > 0 else "throttling",
                    "available_tokens": int(global_rate_limiter.rate_limiter.bucket.tokens),
                    "requests_per_minute": global_rate_limiter.current_limit
                },
                "circuit_breaker": {
                    "status": "healthy" if global_circuit_breaker.state.value == "CLOSED" else global_circuit_breaker.state.value.lower(),
                    "state": global_circuit_breaker.state.value,
                    "failure_count": global_circuit_breaker.failure_count
                }
            },
            "recommendations": _get_health_recommendations(stats, global_circuit_breaker, global_rate_limiter)
        }

def _get_health_recommendations(stats: Dict, circuit_breaker, rate_limiter) -> List[str]:
    """Generate health recommendations based on current system state"""
    recommendations = []
    
    if stats["avg_response_time_ms"] > 10000:
        recommendations.append("High response times detected. Consider scaling up resources.")
    
    if circuit_breaker.state.value == "OPEN":
        recommendations.append("Circuit breaker is open. Check downstream services.")
    
    if rate_limiter.rate_limiter.bucket.tokens < rate_limiter.rate_limiter.bucket.capacity * 0.1:
        recommendations.append("Rate limiter tokens low. Consider implementing backpressure.")
    
    if stats["status"] == "critical":
        recommendations.append("System health is critical. Immediate attention required.")
    
    if not recommendations:
        recommendations.append("System is operating normally.")
    
    return recommendations

@app.get("/")
async def root():
    """Root endpoint with multi-provider API information"""
    multi_llm = MultiLLMClient()
    return {
        "message": "FinSight Multi-Provider LLM-Enhanced API",
        "version": "1.0.0",
        "current_provider": multi_llm.current_provider,
        "supported_providers": ["ollama", "bedrock", "auto"],
        "endpoints": {
            "enhance": "POST /enhance - Multi-provider LLM-powered financial content enhancement",
            "health": "GET /health - Health check with all provider status",
            "docs": "GET /docs - Interactive API documentation"
        }
    }

async def generate_enhanced_content(original_content: str, fact_checks: List[FactCheckResult], multi_llm_client: MultiLLMClient) -> str:
    """Generate enhanced content using LLM that integrates fact-checks naturally"""
    try:
        # Prepare context from fact-checks
        verified_facts = [fc for fc in fact_checks if fc.verified and fc.confidence > 0.7]
        flagged_claims = [fc for fc in fact_checks if not fc.verified or fc.confidence < 0.5]
        
        # Create enhancement prompt
        prompt = f"""Rewrite the following financial content to be more professional, compliant, and accurate. 

Original content: "{original_content}"

Verified facts to integrate naturally:
{chr(10).join([f"- {fc.claim}: {fc.explanation}" for fc in verified_facts])}

Claims that need disclaimers or corrections:
{chr(10).join([f"- {fc.claim}: {fc.explanation}" for fc in flagged_claims])}

Guidelines:
1. Maintain the original meaning and intent
2. Integrate verified facts seamlessly into the text
3. Add appropriate disclaimers for unverified claims
4. Use professional financial language
5. Ensure compliance with financial advisory regulations
6. Keep the tone informative but not promotional

Return only the enhanced content, no additional commentary."""

        # Try to use LLM for content enhancement
        if multi_llm_client.current_provider in ["ollama", "bedrock"]:
            if multi_llm_client.current_provider == "ollama" and multi_llm_client.ollama_client.available:
                response = await generate_with_ollama(prompt, multi_llm_client.ollama_client)
                if response:
                    return response
            elif multi_llm_client.current_provider == "bedrock" and multi_llm_client.bedrock_client.available:
                response = await generate_with_bedrock(prompt, multi_llm_client.bedrock_client)
                if response:
                    return response
        
        # Fallback to template-based enhancement
        return generate_template_enhanced_content(original_content, verified_facts, flagged_claims)
        
    except Exception as e:
        logger.warning(f"Enhanced content generation failed: {e}, using template fallback")
        return generate_template_enhanced_content(original_content, verified_facts or [], flagged_claims or [])

async def generate_with_ollama(prompt: str, ollama_client: LocalLLMClient) -> Optional[str]:
    """Generate enhanced content using Ollama"""
    try:
        response = requests.post(
            f"{ollama_client.base_url}/api/generate",
            json={
                "model": ollama_client.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3}
            },
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '').strip()
    except Exception as e:
        logger.warning(f"Ollama content generation failed: {e}")
    return None

async def generate_with_bedrock(prompt: str, bedrock_client: BedrockLLMClient) -> Optional[str]:
    """Generate enhanced content using Bedrock"""
    try:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = bedrock_client.client.invoke_model(
            body=json.dumps(body),
            modelId=bedrock_client.model_id,
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        return response_body['content'][0]['text'].strip()
        
    except Exception as e:
        logger.warning(f"Bedrock content generation failed: {e}")
    return None

def generate_template_enhanced_content(original_content: str, verified_facts: List[FactCheckResult], flagged_claims: List[FactCheckResult]) -> str:
    """Template-based content enhancement as fallback"""
    enhanced = original_content
    
    # Add verified fact context
    if verified_facts:
        fact_context = " ".join([f"According to {fc.source}, {fc.explanation.lower()}" for fc in verified_facts[:2]])
        enhanced += f"\n\nAdditional Context: {fact_context}"
    
    # Add disclaimers for flagged claims
    if flagged_claims:
        enhanced += "\n\nPlease note: Some claims in this content could not be independently verified. Always conduct your own research and consult with financial professionals before making investment decisions."
    
    # Add standard compliance disclaimer
    enhanced += "\n\nDisclaimer: This content is for informational purposes only and should not be considered as financial advice."
    
    return enhanced

# Run the application if executed directly
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"🚀 Starting FinSight Enhanced Multi-Source API Server on {host}:{port}")
    print(f"📊 LLM Providers: Ollama (Available: {LocalLLMClient().available}), Bedrock (Available: {BedrockLLMClient().available})")
    print(f"🎯 Current Provider: {MultiLLMClient().current_provider}")
    
    if MULTI_SOURCE_AVAILABLE:
        print(f"🔍 Multi-Source Fact Checking: ✅ Available")
        print(f"🌍 World Bank Integration: ✅ Available")
        print(f"🤖 Bedrock Agent Orchestration: {'✅ Available' if BEDROCK_AVAILABLE else '❌ Requires AWS credentials'}")
    else:
        print(f"🔍 Multi-Source Fact Checking: ❌ Using legacy fact checker")
    
    print(f"📖 Documentation: http://localhost:{port}/docs")
    print(f"💡 Health Check: http://localhost:{port}/health")
    print(f"---")
    
    uvicorn.run(app, host=host, port=port)
