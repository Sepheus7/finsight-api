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

# Try to import boto3 for Bedrock support
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False

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
    """Enhanced fact checker with LLM-powered claim extraction"""
    
    def __init__(self):
        self.llm_client = LocalLLMClient()
        self.data_provider = FinancialDataProvider()
        self.context_enricher = ContextEnricher()
    
    def process_content(self, content: str) -> tuple:
        """Process content and return fact checks, context enrichments, and enhanced content"""
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
    """Enhanced endpoint with multi-provider LLM-powered claim extraction"""
    start_time = datetime.now()
    
    try:
        content = request.ai_response.content
        
        # Initialize multi-provider LLM client with user preference
        multi_llm_client = MultiLLMClient(preferred_provider=request.llm_provider)
        
        # Extract claims using preferred provider
        claims, provider_used = multi_llm_client.extract_claims(content)
        
        # Process each claim for fact-checking
        fact_checks = []
        for claim_data in claims:
            try:
                fact_check = await verify_financial_claim(claim_data)
                fact_checks.append(fact_check)
            except Exception as e:
                logger.warning(f"Fact check failed for claim: {claim_data.get('claim', '')}: {e}")
                # Add failed fact check with low confidence
                fact_checks.append(FactCheckResult(
                    claim=claim_data.get('claim', 'Unknown claim'),
                    verified=False,
                    confidence=0.0,
                    source="verification_failed",
                    explanation=f"Could not verify: {str(e)[:100]}"
                ))
        
        # Enhanced content generation using LLM-powered rewriting
        enhanced_content = await generate_enhanced_content(content, fact_checks, multi_llm_client)
        
        # Context enrichment
        context_additions = []
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
        
        # Reduce score for compliance issues
        if compliance_flags:
            quality_score = max(0.3, quality_score - (len(compliance_flags) * 0.05))
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
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
    """Health check with multi-provider LLM status"""
    # Check provider availability
    multi_llm = MultiLLMClient()
    ollama_status = "available" if multi_llm.ollama_client.available else "unavailable"
    bedrock_status = "available" if multi_llm.bedrock_client.available else "unavailable"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
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
        "current_provider": multi_llm.current_provider,
        "fallback": "regex" if multi_llm.current_provider == "regex_fallback" else None
    }

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
    
    print(f"Starting FinSight LLM-Enhanced API Server on {host}:{port}")
    print(f"Supported LLM providers: Ollama (Available: {LocalLLMClient().available}), Bedrock (Available: {BedrockLLMClient().available})")
    print(f"Provider auto-select will use: {MultiLLMClient().current_provider}")
    print(f"Documentation available at: http://localhost:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)
