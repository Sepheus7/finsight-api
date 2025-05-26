"""
LLM-Powered Claim Extraction for FinSight
Uses AI to intelligently extract and classify financial claims from text
"""

import json
import logging
import os
import re
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict

# Import models - handle both relative and absolute imports
try:
    from ..models.financial_models import FinancialClaim, ClaimType
    from ..utils.enhanced_ticker_resolver import EnhancedTickerResolver
    from ..config import LLMConfig
except ImportError:
    try:
        from models.financial_models import FinancialClaim, ClaimType
        from utils.enhanced_ticker_resolver import EnhancedTickerResolver
        from config import LLMConfig
    except ImportError:
        from src.models.financial_models import FinancialClaim, ClaimType
        from src.utils.enhanced_ticker_resolver import EnhancedTickerResolver
        from src.config import LLMConfig

# Optional imports with proper fallbacks
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None
    ANTHROPIC_AVAILABLE = False

try:
    from .bedrock_client import BedrockLLMClient
    BEDROCK_AVAILABLE = True
except ImportError:
    try:
        from bedrock_client import BedrockLLMClient
        BEDROCK_AVAILABLE = True
    except ImportError:
        BedrockLLMClient = None
        BEDROCK_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


def get_bedrock_client():
    """Get configured Bedrock client instance with fallback model"""
    if not BEDROCK_AVAILABLE:
        raise ImportError("Bedrock client not available")
    config = LLMConfig()
    return BedrockLLMClient(
        region=config.bedrock_region,
        model_id=config.bedrock_model,
        fallback_model_id=config.bedrock_fallback_model
    )


class LLMClaimExtractor:
    """LLM-powered financial claim extraction with fallback to regex patterns"""
    
    def __init__(self, provider: str = "auto"):
        """
        Initialize the LLM claim extractor
        
        Args:
            provider: LLM provider to use ("auto", "bedrock", "ollama", "openai", "anthropic", "regex")
        """
        self.provider = provider
        self.client = None
        self.ollama_base_url = None
        self.ollama_model = None
        
        # Initialize enhanced ticker resolver for dynamic company-to-ticker mapping
        self.ticker_resolver = EnhancedTickerResolver()
        
        if provider == "auto":
            self.provider = self._auto_detect_provider()
        
        self._initialize_client()

    def _auto_detect_provider(self) -> str:
        """Auto-detect best available provider with environment awareness"""
        # Priority: Local (Ollama) > Cloud (OpenAI/Anthropic) > AWS (Bedrock) > Fallback (Regex)
        
        # Check if we're in AWS Lambda - use Bedrock
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            if BEDROCK_AVAILABLE:
                return "bedrock"
            elif OPENAI_AVAILABLE and os.environ.get('OPENAI_API_KEY'):
                return "openai"
            elif ANTHROPIC_AVAILABLE and os.environ.get('ANTHROPIC_API_KEY'):
                return "anthropic"
            else:
                return "regex"
        
        # Local development - prefer Ollama
        else:
            # Check if Ollama is available locally
            if REQUESTS_AVAILABLE and self._check_ollama_availability():
                return "ollama"
            # Fallback to cloud providers
            elif OPENAI_AVAILABLE and os.environ.get('OPENAI_API_KEY'):
                return "openai"
            elif ANTHROPIC_AVAILABLE and os.environ.get('ANTHROPIC_API_KEY'):
                return "anthropic"
            elif BEDROCK_AVAILABLE:
                return "bedrock"
            else:
                return "regex"

    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available on localhost"""
        try:
            request = urllib.request.Request('http://localhost:11434/api/tags')
            with urllib.request.urlopen(request, timeout=2) as response:
                return response.status == 200
        except Exception:
            return False

    def _initialize_client(self):
        """Initialize the appropriate client based on provider"""
        logger.info(f"Initializing LLM provider: {self.provider}")
        
        if self.provider == "bedrock" and BEDROCK_AVAILABLE:
            try:
                self.client = get_bedrock_client()
                logger.info(f"Initialized Bedrock client with model {self.client.model_id}")
            except Exception as e:
                logger.warning(f"Could not initialize Bedrock client: {e}, falling back to regex")
                self.provider = "regex"
                
        elif self.provider == "ollama" and REQUESTS_AVAILABLE:
            self.ollama_base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
            self.ollama_model = os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')
            try:
                # Test Ollama connection
                if requests:
                    response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                    if response.status_code == 200:
                        self.client = "ollama"  # Use string identifier for Ollama
                        logger.info(f"Initialized Ollama client with model {self.ollama_model}")
                    else:
                        logger.warning("Ollama server not responding, falling back to regex")
                        self.provider = "regex"
                else:
                    raise ImportError("requests not available")
            except Exception as e:
                logger.warning(f"Could not connect to Ollama: {e}, falling back to regex")
                self.provider = "regex"
                
        elif self.provider == "openai" and OPENAI_AVAILABLE and openai:
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
                logger.info("Initialized OpenAI client for claim extraction")
            else:
                logger.warning("OpenAI API key not found, falling back to regex")
                self.provider = "regex"
                
        elif self.provider == "anthropic" and ANTHROPIC_AVAILABLE and anthropic:
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if api_key:
                self.client = anthropic.Anthropic(api_key=api_key)
                logger.info("Initialized Anthropic client for claim extraction")
            else:
                logger.warning("Anthropic API key not found, falling back to regex")
                self.provider = "regex"
        else:
            logger.info("Using regex-based claim extraction")
            self.provider = "regex"

    def extract_claims(self, text: str) -> List[FinancialClaim]:
        """
        Extract financial claims from text using LLM or regex fallback
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of FinancialClaim objects
        """
        if self.provider in ["bedrock", "ollama", "openai", "anthropic"] and self.client:
            try:
                return self._extract_with_llm(text)
            except Exception as e:
                logger.error(f"LLM extraction failed: {e}, falling back to regex")
                return self._extract_with_regex(text)
        else:
            return self._extract_with_regex(text)

    def _extract_with_llm(self, text: str) -> List[FinancialClaim]:
        """Extract claims using LLM (Bedrock, OpenAI, Anthropic, or Ollama)"""
        system_prompt = """You are a financial claim extraction expert. Analyze the provided text and extract ALL financial claims with high precision.

RESPONSE FORMAT: Return ONLY valid JSON in this exact structure:
{
  "claims": [
    {
      "claim_text": "exact text containing the claim",
      "company": "company name or ticker symbol",
      "claim_type": "one of: earnings, revenue, growth, merger, acquisition, dividend, guidance, market_share, product_launch, partnership, regulatory, lawsuit, rating_change, price_target, analyst_recommendation, insider_trading, ipo, bankruptcy, restructuring, other",
      "context": "surrounding context that makes this claim meaningful"
    }
  ]
}

EXTRACTION RULES:
1. Extract ONLY factual financial claims, NOT opinions or speculation
2. Each claim must reference a specific company (name or ticker)
3. Include numerical values, percentages, timeframes when present
4. Capture both explicit and implicit financial implications
5. Be precise - extract the exact claim text, not a summary
6. If no financial claims exist, return empty claims array

TEXT TO ANALYZE:"""

        user_prompt = f"{text[:4000]}"  # Limit text length
        
        try:
            content = ""
            
            if self.provider == "bedrock":
                content = self.client.generate_text(
                    user_prompt=user_prompt,
                    system_prompt=system_prompt,
                    max_tokens=2000
                )
                
            elif self.provider == "ollama":
                if requests:
                    payload = {
                        "model": self.ollama_model,
                        "prompt": f"{system_prompt}\n\n{user_prompt}",
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 2000
                        }
                    }
                    
                    response = requests.post(
                        f"{self.ollama_base_url}/api/generate",
                        json=payload,
                        timeout=30
                    )
                    response.raise_for_status()
                    content = response.json().get("response", "")
                
            elif self.provider == "openai" and hasattr(self.client, 'chat'):
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                content = response.choices[0].message.content
                
            elif self.provider == "anthropic" and hasattr(self.client, 'messages'):
                response = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2000,
                    temperature=0.1,
                    messages=[
                        {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}
                    ]
                )
                content = response.content[0].text
                
            return self._parse_llm_response(content, text)
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise

    def _parse_llm_response(self, response_content: str, original_text: str) -> List[FinancialClaim]:
        """Parse LLM JSON response into FinancialClaim objects"""
        try:
            # Extract JSON from response (handle cases where LLM adds extra text)
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning("No JSON found in LLM response")
                return []
                
            json_content = response_content[json_start:json_end]
            parsed_response = json.loads(json_content)
            
            claims = []
            for claim_data in parsed_response.get("claims", []):
                # Resolve company name to ticker
                company = claim_data.get("company", "")
                ticker = self.ticker_resolver.resolve_ticker(company)
                
                # Determine claim type - map to available enum values
                claim_type_str = claim_data.get("claim_type", "opinion").lower()
                claim_type_mapping = {
                    "earnings": ClaimType.EARNINGS,
                    "revenue": ClaimType.REVENUE,
                    "growth": ClaimType.REVENUE,  # Map growth to revenue
                    "stock_price": ClaimType.STOCK_PRICE,
                    "market_cap": ClaimType.MARKET_CAP,
                    "dividend": ClaimType.EARNINGS,  # Map dividend to earnings
                    "merger": ClaimType.PREDICTION,  # Map merger to prediction
                    "acquisition": ClaimType.PREDICTION,  # Map acquisition to prediction
                    "guidance": ClaimType.PREDICTION,
                    "market_share": ClaimType.ECONOMIC_INDICATOR,
                    "product_launch": ClaimType.PREDICTION,
                    "partnership": ClaimType.PREDICTION,
                    "regulatory": ClaimType.ECONOMIC_INDICATOR,
                    "lawsuit": ClaimType.PREDICTION,
                    "rating_change": ClaimType.OPINION,
                    "price_target": ClaimType.PREDICTION,
                    "analyst_recommendation": ClaimType.OPINION,
                    "insider_trading": ClaimType.HISTORICAL,
                    "ipo": ClaimType.PREDICTION,
                    "bankruptcy": ClaimType.PREDICTION,
                    "restructuring": ClaimType.PREDICTION,
                    "interest_rate": ClaimType.INTEREST_RATE,
                    "inflation": ClaimType.INFLATION
                }
                
                claim_type = claim_type_mapping.get(claim_type_str, ClaimType.OPINION)
                
                # Extract entities and values
                entities = [company]
                if ticker and ticker != company:
                    entities.append(ticker)
                
                # Try to extract numerical values from the claim text
                values = []
                import re
                value_patterns = [
                    r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|trillion))?',
                    r'\d+(?:\.\d+)?%',
                    r'\d+(?:\.\d+)?(?:\s*(?:million|billion|trillion))?'
                ]
                for pattern in value_patterns:
                    matches = re.findall(pattern, claim_data.get("claim_text", ""), re.IGNORECASE)
                    values.extend(matches)
                
                # Create claim object with correct structure
                claim = FinancialClaim(
                    text=claim_data.get("claim_text", ""),
                    claim_type=claim_type,
                    entities=entities,
                    values=values,
                    confidence=0.9,  # High confidence for LLM extraction
                    source_text=original_text
                )
                
                if claim.text and claim.entities:
                    claims.append(claim)
            
            logger.info(f"Extracted {len(claims)} claims using {self.provider}")
            return claims
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Response content: {response_content}")
            return []
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return []

    def _extract_with_regex(self, text: str) -> List[FinancialClaim]:
        """Fallback regex-based extraction for when LLM is not available"""
        claims = []
        
        # Define regex patterns for common financial claims - mapped to available ClaimType values
        patterns = [
            # Earnings patterns
            (r'(\w+)\s+(?:reported|posted|announced)\s+(?:earnings|profit|income)\s+of\s+\$?([\d.,]+\s*(?:million|billion)?)', ClaimType.EARNINGS),
            (r'(\w+)(?:\'s)?\s+(?:Q\d+|quarterly|annual)\s+earnings\s+(?:were|was|of)\s+\$?([\d.,]+\s*(?:million|billion)?)', ClaimType.EARNINGS),
            
            # Revenue patterns
            (r'(\w+)\s+(?:reported|generated|posted)\s+(?:revenue|sales)\s+of\s+\$?([\d.,]+\s*(?:million|billion)?)', ClaimType.REVENUE),
            (r'(\w+)(?:\'s)?\s+revenue\s+(?:increased|decreased|rose|fell)\s+(?:by\s+)?(\d+(?:\.\d+)?%)', ClaimType.REVENUE),
            
            # Growth patterns (mapped to REVENUE)
            (r'(\w+)\s+(?:grew|increased|expanded)\s+(?:by\s+)?(\d+(?:\.\d+)?%)', ClaimType.REVENUE),
            (r'(\w+)(?:\'s)?\s+(?:growth|expansion)\s+of\s+(\d+(?:\.\d+)?%)', ClaimType.REVENUE),
            
            # Stock price patterns
            (r'(\w+)\s+(?:stock|shares|price)\s+(?:rose|fell|increased|decreased)\s+(?:by\s+)?(\d+(?:\.\d+)?%)', ClaimType.STOCK_PRICE),
            
            # Market cap patterns
            (r'(\w+)(?:\'s)?\s+market\s+cap\s+(?:is|was|reached)\s+\$?([\d.,]+\s*(?:million|billion|trillion)?)', ClaimType.MARKET_CAP),
            
            # Dividend patterns (mapped to EARNINGS)
            (r'(\w+)\s+(?:declared|announced|paid)\s+(?:a\s+)?dividend\s+of\s+\$?([\d.]+)', ClaimType.EARNINGS),
            
            # Merger/Acquisition patterns (mapped to PREDICTION)
            (r'(\w+)\s+(?:acquired|purchased|bought)\s+(\w+)', ClaimType.PREDICTION),
            (r'(\w+)\s+(?:to\s+)?(?:merge|combine)\s+with\s+(\w+)', ClaimType.PREDICTION),
        ]
        
        for pattern, claim_type in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                company = match.group(1)
                ticker = self.ticker_resolver.resolve_ticker(company)
                
                # Extract entities and values
                entities = [company]
                if ticker and ticker != company:
                    entities.append(ticker)
                
                # Extract values from the match
                values = []
                for i in range(2, len(match.groups()) + 1):
                    try:
                        value = match.group(i)
                        if value:
                            values.append(value)
                    except IndexError:
                        break
                
                claim = FinancialClaim(
                    text=match.group(0),
                    claim_type=claim_type,
                    entities=entities,
                    values=values,
                    confidence=0.6,  # Lower confidence for regex extraction
                    source_text=text,
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                claims.append(claim)
        
        logger.info(f"Extracted {len(claims)} claims using regex patterns")
        return claims

    def _extract_context(self, text: str, start: int, end: int, context_window: int = 100) -> str:
        """Extract surrounding context for a claim"""
        context_start = max(0, start - context_window)
        context_end = min(len(text), end + context_window)
        return text[context_start:context_end].strip()

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider and its capabilities"""
        return {
            "provider": self.provider,
            "client_type": type(self.client).__name__ if self.client else None,
            "capabilities": {
                "llm_extraction": self.provider != "regex",
                "high_confidence": self.provider in ["bedrock", "openai", "anthropic"],
                "cost_optimized": self.provider in ["ollama", "regex"],
                "offline_capable": self.provider in ["ollama", "regex"]
            },
            "model_info": {
                "bedrock": getattr(self.client, 'model_id', None) if self.provider == "bedrock" else None,
                "ollama": self.ollama_model if self.provider == "ollama" else None,
                "openai": "gpt-4-turbo" if self.provider == "openai" else None,
                "anthropic": "claude-3-sonnet-20240229" if self.provider == "anthropic" else None
            }
        }
