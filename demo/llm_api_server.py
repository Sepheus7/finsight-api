#!/usr/bin/env python3
"""
FinSight LLM-Enhanced Demo API Server
Uses the same logic as production AWS Lambda but with local Ollama fallback
"""

from fastapi import FastAPI, HTTPException
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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FinSight LLM-Enhanced API",
    description="LLM-powered financial fact-checking and enhancement API",
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

class LocalLLMClient:
    """Local LLM client using Ollama for development"""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "llama3.2:3b"
        self.available = self._check_ollama_availability()
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(model.get('name', '').startswith('llama3.2') for model in models)
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
        return False
    
    def extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """Extract financial claims using local LLM"""
        if not self.available:
            logger.warning("Ollama not available, falling back to regex")
            return self._regex_fallback(text)
        
        try:
            prompt = f"""You are a financial fact-checking AI. Extract specific, verifiable financial claims from this text.

Text: "{text}"

Extract claims in this JSON format:
[
  {{
    "claim": "exact text of the claim",
    "type": "stock_price|market_cap|performance|valuation",
    "symbol": "stock symbol if mentioned",
    "value": "specific number/percentage if mentioned",
    "timeframe": "time period if mentioned"
  }}
]

Only extract factual claims that can be verified with financial data. Return empty array if no verifiable claims found."""

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
        """Fallback regex-based claim extraction"""
        claims = []
        
        # Stock price patterns
        stock_patterns = [
            r'(?:[A-Za-z]+\s+)?\(([A-Z]{2,5})\)\s+(?:is|are)?\s*(?:currently\s+)?(?:trading|priced)\s+(?:at|around|near)\s+\$?(\d+(?:\.\d{2})?)',
            r'(?:^|\s)([A-Z]{2,5})\s+(?:is|are)?\s*(?:currently\s+)?(?:trading|priced)\s+(?:at|around|near)\s+\$?(\d+(?:\.\d{2})?)',
        ]
        
        for pattern in stock_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                claims.append({
                    "claim": f"{match.group(1)} is priced at ${match.group(2)}",
                    "type": "stock_price",
                    "symbol": match.group(1).upper(),
                    "value": match.group(2),
                    "timeframe": "current"
                })
        
        return claims

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

class EnhancedFactChecker:
    """Enhanced fact checker with LLM-powered claim extraction"""
    
    def __init__(self):
        self.llm_client = LocalLLMClient()
        self.data_provider = FinancialDataProvider()
    
    def process_content(self, content: str) -> tuple:
        """Process content and return fact checks and enhanced content"""
        start_time = datetime.now()
        
        # Extract claims using LLM
        claims_data = self.llm_client.extract_claims(content)
        logger.info(f"Extracted {len(claims_data)} claims using {'LLM' if self.llm_client.available else 'regex'}")
        
        fact_checks = []
        enhanced_content = content
        
        # Verify each claim
        for claim_info in claims_data:
            claim_text = claim_info.get('claim', '')
            symbol = claim_info.get('symbol', '')
            
            if symbol and claim_info.get('type') == 'stock_price':
                fact_check = self._verify_stock_price_claim(claim_text, symbol, claim_info.get('value'))
                if fact_check:
                    fact_checks.append(fact_check)
        
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
        
        return fact_checks, enhanced_content, processing_time
    
    def _verify_stock_price_claim(self, claim: str, symbol: str, claimed_value: str) -> Optional[FactCheckResult]:
        """Verify a stock price claim"""
        try:
            claimed_price = float(claimed_value)
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

class ComplianceChecker:
    """Compliance checking for financial content"""
    
    def check_compliance(self, text: str) -> List[str]:
        flags = []
        
        # Investment advice patterns
        advice_patterns = [
            r'(?:should|must|need to)\s+(?:buy|sell|invest)',
            r'(?:guaranteed|certain|sure)\s+(?:return|profit)',
            r'(?:will|shall)\s+(?:increase|decrease|rise|fall)'
        ]
        
        for pattern in advice_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                flags.append("Potential investment advice without proper disclaimers")
                break
        
        # Risk disclosure check
        if any(word in text.lower() for word in ['investment', 'portfolio', 'returns']) and \
           'risk' not in text.lower():
            flags.append("Investment discussion without risk disclosure")
        
        return flags

# Initialize components
fact_checker = EnhancedFactChecker()
compliance_checker = ComplianceChecker()

@app.post("/enhance", response_model=EnhancedResponse)
async def enhance_ai_response(request: EnrichmentRequest):
    """Enhanced endpoint with LLM-powered claim extraction"""
    start_time = datetime.now()
    
    try:
        content = request.ai_response.content
        
        # Enhanced fact checking with LLM
        fact_checks, enhanced_content, fact_check_time = fact_checker.process_content(content)
        
        # Context enrichment (simplified for demo)
        context_additions = []
        
        # Compliance checking
        compliance_flags = compliance_checker.check_compliance(content)
        
        # Calculate quality score
        quality_score = 0.8  # Base score
        if fact_checks:
            verified_ratio = sum(1 for fc in fact_checks if fc.verified) / len(fact_checks)
            quality_score = 0.6 + (0.4 * verified_ratio)
        
        # Reduce score for compliance issues
        if compliance_flags:
            quality_score = max(0.3, quality_score - (len(compliance_flags) * 0.1))
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        provider_used = "local_llm" if fact_checker.llm_client.available else "regex_fallback"
        
        return EnhancedResponse(
            original_content=content,
            enhanced_content=enhanced_content,
            fact_checks=fact_checks,
            context_additions=context_additions,
            quality_score=quality_score,
            compliance_flags=compliance_flags,
            processing_time_ms=int(processing_time),
            provider_used=provider_used
        )
    
    except Exception as e:
        logger.error(f"Enhancement failed: {e}")
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check with LLM status"""
    llm_status = "available" if fact_checker.llm_client.available else "unavailable"
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "llm_provider": "ollama",
        "llm_status": llm_status,
        "fallback": "regex" if not fact_checker.llm_client.available else None
    }

@app.get("/")
async def root():
    """Root endpoint with enhanced API information"""
    return {
        "message": "FinSight LLM-Enhanced API",
        "version": "1.0.0",
        "provider": "local_llm" if fact_checker.llm_client.available else "regex_fallback",
        "endpoints": {
            "enhance": "POST /enhance - LLM-powered financial content enhancement",
            "health": "GET /health - Health check with LLM status",
            "docs": "GET /docs - Interactive API documentation"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
