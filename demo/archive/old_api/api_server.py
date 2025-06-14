"""
Financial AI Quality Enhancement API - MVP
A service that enriches AI agent outputs with context and fact-checking for financial services
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import re
from datetime import datetime
import yfinance as yf
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
STOCK_PATTERNS = [
    r'(?:^|\s)([A-Z]{2,5})\s+(?:is|are)?\s*(?:currently\s+)?(?:trading|priced)\s+(?:at|around|near)\s+\$?(\d+(?:\.\d{2})?)',
    r'(?:[A-Za-z]+\s+)?\(([A-Z]{2,5})\)\s+(?:is|are)?\s*(?:currently\s+)?(?:trading|priced)\s+(?:at|around|near)\s+\$?(\d+(?:\.\d{2})?)',
    r'(?:^|\s)([A-Z]{2,5})\s+stock\s+(?:is|are)\s+(?:at|trading\s+at)\s+\$?(\d+(?:\.\d{2})?)'
]

PERCENTAGE_PATTERN = r'(\d+(?:\.\d+)?%)\s+(?:inflation|interest rate|return|yield)'

ADVICE_PATTERNS = [
    r'(?:should|must|need to)\s+(?:buy|sell|invest)',
    r'(?:guaranteed|certain|sure)\s+(?:return|profit)',
    r'(?:will|shall)\s+(?:increase|decrease|rise|fall)'
]

TOPIC_KEYWORDS = {
    "inflation": ["inflation", "cpi", "consumer price"],
    "interest_rates": ["interest rate", "fed rate", "federal funds"],
    "market_volatility": ["volatile", "volatility", "market risk"],
    "earnings": ["earnings", "eps", "quarterly results"]
}

MOCK_MARKET_CONTEXTS = {
    "inflation": [
        {
            "type": "economic_indicator",
            "content": "Current US inflation rate is approximately 3.2% (as of latest CPI data)",
            "relevance_score": 0.9,
            "source": "Federal Reserve Economic Data"
        }
    ],
    "interest_rates": [
        {
            "type": "monetary_policy",
            "content": "Federal funds rate is currently in the range of 5.25-5.50%",
            "relevance_score": 0.95,
            "source": "Federal Reserve"
        }
    ]
}

app = FastAPI(
    title="Financial AI Quality API",
    description="Enhance AI agent outputs with context enrichment and fact checking",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AIResponse(BaseModel):
    content: str
    agent_id: Optional[str] = None
    timestamp: Optional[datetime] = None

class EnrichmentRequest(BaseModel):
    ai_response: AIResponse
    enrichment_level: str = "standard"
    fact_check: bool = True
    add_context: bool = True

class FactCheckResult(BaseModel):
    claim: str
    verified: bool
    confidence: float
    source: Optional[str] = None
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

class FinancialDataProvider:
    """Mock financial data provider - replace with real APIs in production"""
    
    @staticmethod
    def get_stock_price(symbol: str) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"Fetching stock data for {symbol}")
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
    
    @staticmethod
    def get_market_context(topic: str) -> List[Dict[str, Any]]:
        """Mock market context - replace with real financial news/data APIs"""
        return MOCK_MARKET_CONTEXTS.get(topic.lower(), [])

class FinancialFactChecker:
    def __init__(self):
        self.data_provider = FinancialDataProvider()
    
    def extract_financial_claims(self, text: str) -> List[str]:
        """Extract potential financial claims from text"""
        claims = []
        
        for pattern in STOCK_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                claims.append(f"{match.group(1)} is priced at ${match.group(2)}")
        
        pct_matches = re.finditer(PERCENTAGE_PATTERN, text, re.IGNORECASE)
        for match in pct_matches:
            claims.append(match.group(0))
        
        return claims
    
    def verify_claim(self, claim: str) -> FactCheckResult:
        """Verify a financial claim"""
        stock_match = re.search(r'([A-Z]{1,5})\s+(?:is\s+)?(?:priced\s+)?at\s+\$?(\d+(?:\.\d{2})?)', claim, re.IGNORECASE)
        
        if stock_match:
            symbol = stock_match.group(1).upper()
            claimed_price = float(stock_match.group(2))
            
            actual_data = self.data_provider.get_stock_price(symbol)
            if actual_data:
                actual_price = actual_data['current_price']
                price_diff = abs(actual_price - claimed_price) / actual_price
                
                if price_diff < 0.05:
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
        
        return FactCheckResult(
            claim=claim,
            verified=False,
            confidence=0.5,
            source="Unable to verify",
            explanation="Claim could not be automatically verified"
        )

class ContextEnricher:
    def __init__(self):
        self.data_provider = FinancialDataProvider()
    
    def identify_topics(self, text: str) -> List[str]:
        """Identify financial topics that could benefit from context"""
        topics = []
        text_lower = text.lower()
        
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def get_context_for_topics(self, topics: List[str]) -> List[ContextEnrichment]:
        """Get relevant context for identified topics"""
        enrichments = []
        
        for topic in topics:
            contexts = self.data_provider.get_market_context(topic)
            for context in contexts:
                enrichments.append(ContextEnrichment(**context))
        
        return enrichments

class ComplianceChecker:
    def check_compliance(self, text: str) -> List[str]:
        """Check for potential compliance issues"""
        flags = []
        
        for pattern in ADVICE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                flags.append("Potential investment advice without proper disclaimers")
                break
        
        if any(word in text.lower() for word in ['investment', 'portfolio', 'returns']) and \
           'risk' not in text.lower():
            flags.append("Investment discussion without risk disclosure")
        
        return flags

fact_checker = FinancialFactChecker()
context_enricher = ContextEnricher()
compliance_checker = ComplianceChecker()

@app.post("/enhance", response_model=EnhancedResponse)
async def enhance_ai_response(request: EnrichmentRequest):
    """Main endpoint to enhance AI responses with fact-checking and context"""
    start_time = datetime.now()
    
    try:
        content = request.ai_response.content
        
        fact_checks = []
        if request.fact_check:
            claims = fact_checker.extract_financial_claims(content)
            for claim in claims:
                fact_check = fact_checker.verify_claim(claim)
                fact_checks.append(fact_check)
        
        context_additions = []
        if request.add_context:
            topics = context_enricher.identify_topics(content)
            context_additions = context_enricher.get_context_for_topics(topics)
        
        compliance_flags = compliance_checker.check_compliance(content)
        
        enhanced_content = content
        
        if context_additions:
            context_text = "\n\nAdditional Context:\n"
            for ctx in context_additions:
                context_text += f"• {ctx.content} (Source: {ctx.source})\n"
            enhanced_content += context_text
        
        failed_checks = [fc for fc in fact_checks if not fc.verified]
        if failed_checks:
            warning_text = "\n\n⚠️ Fact Check Alerts:\n"
            for fc in failed_checks:
                warning_text += f"• {fc.claim} - {fc.explanation}\n"
            enhanced_content += warning_text
        
        quality_score = 0.8
        if fact_checks:
            verified_ratio = sum(1 for fc in fact_checks if fc.verified) / len(fact_checks)
            quality_score = 0.6 + (0.4 * verified_ratio)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return EnhancedResponse(
            original_content=content,
            enhanced_content=enhanced_content,
            fact_checks=fact_checks,
            context_additions=context_additions,
            quality_score=quality_score,
            compliance_flags=compliance_flags,
            processing_time_ms=int(processing_time)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Financial AI Quality Enhancement API",
        "version": "1.0.0",
        "endpoints": {
            "enhance": "POST /enhance - Enhance AI responses with fact-checking and context",
            "health": "GET /health - Health check",
            "docs": "GET /docs - Interactive API documentation"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
