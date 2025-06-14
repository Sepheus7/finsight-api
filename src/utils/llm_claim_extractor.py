"""
LLM-Powered Claim Extraction for FinSight
Uses AI to intelligently extract and classify financial claims from text
"""

import json
import logging
import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import asdict

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

logger = logging.getLogger(__name__)


def get_bedrock_client():
    """Get configured Bedrock client instance with fallback model"""
    if not BEDROCK_AVAILABLE or BedrockLLMClient is None:
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
        
        # Initialize enhanced ticker resolver for dynamic company-to-ticker mapping
        self.ticker_resolver = EnhancedTickerResolver()
        
        if provider == "auto":
            # Try to use global config first
            try:
                from ..config import config
                provider = config.llm.get_provider_for_environment()
                logger.info(f"Using provider from global config: {provider}")
            except ImportError:
                try:
                    from src.config import config
                    provider = config.llm.get_provider_for_environment()
                    logger.info(f"Using provider from global config: {provider}")
                except ImportError:
                    # Fallback to auto-detection if config not available
                    # Priority: Local (Ollama) > Cloud (OpenAI/Anthropic) > AWS (Bedrock) > Fallback (Regex)
                    
                    # Check if we're in AWS Lambda - use Bedrock
                    if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
                        if BEDROCK_AVAILABLE:
                            provider = "bedrock"
                        elif OPENAI_AVAILABLE and os.environ.get('OPENAI_API_KEY'):
                            provider = "openai"
                        elif ANTHROPIC_AVAILABLE and os.environ.get('ANTHROPIC_API_KEY'):
                            provider = "anthropic"
                        else:
                            provider = "regex"
                    # Local development - prefer Ollama
                    else:
                        # Check if Ollama is available locally
                        if REQUESTS_AVAILABLE and self._check_ollama_availability():
                            provider = "ollama"
                        # Fallback to cloud providers
                        elif OPENAI_AVAILABLE and os.environ.get('OPENAI_API_KEY'):
                            provider = "openai"
                        elif ANTHROPIC_AVAILABLE and os.environ.get('ANTHROPIC_API_KEY'):
                            provider = "anthropic"
                        elif BEDROCK_AVAILABLE:
                            provider = "bedrock"
                        else:
                            provider = "regex"
            
            self.provider = provider
            logger.info(f"Auto-detected LLM provider: {provider} (environment: {'AWS Lambda' if os.environ.get('AWS_LAMBDA_FUNCTION_NAME') else 'Local'})")
        
        if provider == "bedrock" and BEDROCK_AVAILABLE:
            try:
                self.client = get_bedrock_client()
                logger.info(f"Initialized Bedrock client with model {self.client.model_id}")
            except Exception as e:
                logger.warning(f"Could not initialize Bedrock client: {e}, falling back to regex")
                self.provider = "regex"
                
        elif provider == "ollama" and REQUESTS_AVAILABLE and requests is not None:
            self.ollama_base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
            self.ollama_model = os.environ.get('OLLAMA_MODEL', 'llama3.1:8b')
            
            # Try to get model from config if available
            try:
                from ..config import config
                if hasattr(config.llm, 'ollama_model') and config.llm.ollama_model:
                    self.ollama_model = config.llm.ollama_model
            except (ImportError, AttributeError):
                try:
                    from src.config import config
                    if hasattr(config.llm, 'ollama_model') and config.llm.ollama_model:
                        self.ollama_model = config.llm.ollama_model
                except (ImportError, AttributeError):
                    pass
            try:
                # Test Ollama connection
                response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    self.client = "ollama"
                    logger.info(f"Initialized Ollama client with model {self.ollama_model}")
                else:
                    logger.warning("Ollama server not responding, falling back to regex")
                    self.provider = "regex"
            except Exception as e:
                logger.warning(f"Could not connect to Ollama: {e}, falling back to regex")
                self.provider = "regex"
                
        elif provider == "openai" and OPENAI_AVAILABLE and openai is not None:
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
                logger.info("Initialized OpenAI client for claim extraction")
            else:
                logger.warning("OpenAI API key not found, falling back to regex")
                self.provider = "regex"
                
        elif provider == "anthropic" and ANTHROPIC_AVAILABLE and anthropic is not None:
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

    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available on localhost"""
        try:
            import urllib.request
            import urllib.error
            request = urllib.request.Request('http://localhost:11434/api/tags')
            with urllib.request.urlopen(request, timeout=2) as response:
                return response.status == 200
        except:
            return False

    async def extract_claims(self, text: str) -> List[FinancialClaim]:
        """
        Extract financial claims from text using configured LLM provider
        Falls back to regex-based extraction if LLM fails
        """
        try:
            if self.provider == "regex":
                return self._extract_with_regex(text)
            else:
                return await self._extract_with_llm(text)
        except Exception as e:
            logger.error(f"Claim extraction failed: {e}")
            return self._extract_with_regex(text)

    async def _extract_with_llm(self, text: str) -> List[FinancialClaim]:
        """
        Extract claims using configured LLM provider
        """
        try:
            if self.provider == "bedrock" and self.client is not None and BedrockLLMClient is not None and isinstance(self.client, BedrockLLMClient):
                response = self.client.generate_text(
                    prompt=self._get_extraction_prompt(text),
                    max_tokens=1000,
                    temperature=0.1
                )
                return self._parse_llm_response(response, text)
            elif self.provider == "ollama" and self.client == "ollama" and requests is not None:
                response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": self._get_extraction_prompt(text),
                        "stream": False
                    }
                )
                if response.status_code == 200:
                    return self._parse_llm_response(response.json()["response"], text)
                else:
                    return self._extract_with_regex(text)
            elif self.provider == "openai" and openai is not None and isinstance(self.client, openai.OpenAI):
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a financial claim extractor."},
                        {"role": "user", "content": self._get_extraction_prompt(text)}
                    ],
                    temperature=0.1
                )
                content = response.choices[0].message.content
                if content:
                    return self._parse_llm_response(content, text)
                else:
                    return self._extract_with_regex(text)
            elif self.provider == "anthropic" and anthropic is not None and isinstance(self.client, anthropic.Anthropic):
                response = self.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    temperature=0.1,
                    system="You are a financial claim extractor.",
                    messages=[
                        {"role": "user", "content": self._get_extraction_prompt(text)}
                    ]
                )
                if response.content and len(response.content) > 0:
                    # Handle text content blocks
                    for content_block in response.content:
                        if hasattr(content_block, 'text'):
                            return self._parse_llm_response(getattr(content_block, 'text'), text)
                    # If no text content found, fallback to regex
                    return self._extract_with_regex(text)
                else:
                    return self._extract_with_regex(text)
            
            # Fallback to regex if LLM fails or is not configured
            logger.warning(f"LLM provider {self.provider} not properly configured, falling back to regex")
            return self._extract_with_regex(text)
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return self._extract_with_regex(text)

    def _get_extraction_prompt(self, text: str) -> str:
        """Get the prompt for claim extraction"""
        return f"""Extract all financial claims and company mentions from the following text. For each claim, identify:
1. The type of claim (stock price, market performance, economic indicator, etc.)
2. The specific stock symbol or company name mentioned
3. The confidence level (0.0 to 1.0) in the extraction
4. The exact text of the claim

Important: Extract company names even from questions like "What's Apple's stock price?" or "How is Microsoft performing?"

Text: {text}

Format the response as a JSON array of objects with the following structure:
[
  {{
    "text": "exact claim text or company mention",
    "claim_type": "stock_price|market_performance|economic_indicator|company_fundamental|sector_performance|company_mention|unknown",
    "symbol": "stock symbol or company name if applicable",
    "confidence": 0.0 to 1.0
  }}
]"""

    def _parse_llm_response(self, response_content: str, original_text: str) -> List[FinancialClaim]:
        """Parse LLM response into structured claims"""
        try:
            # Extract JSON from response
            json_str = re.search(r'\[.*\]', response_content, re.DOTALL)
            if not json_str:
                logger.warning("No valid JSON found in LLM response")
                return []
            
            claims_data = json.loads(json_str.group())
            claims = []
            
            for claim_data in claims_data:
                try:
                    entities = []
                    if "symbol" in claim_data and claim_data["symbol"]:
                        entities.append(claim_data["symbol"])
                    claim = FinancialClaim(
                        text=claim_data["text"],
                        claim_type=ClaimType(claim_data["claim_type"]),
                        entities=entities,
                        values=[],
                        confidence=float(claim_data["confidence"]),
                        source_text=original_text
                    )
                    claims.append(claim)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse claim: {e}")
                    continue
            
            return self.enhance_entities(claims)
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return []

    def _extract_with_regex(self, text: str) -> List[FinancialClaim]:
        """Fallback regex-based claim extraction"""
        claims = []
        
        # Direct stock symbols (AAPL, MSFT, etc.)
        symbol_pattern = r'\b([A-Z]{2,5})\b'
        for match in re.finditer(symbol_pattern, text):
            symbol = match.group(1)
            # Only include if it looks like a stock symbol
            if len(symbol) <= 5 and symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA', 'AMD', 'INTC', 'ORCL', 'CRM', 'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'V', 'MA']:
                claims.append(FinancialClaim(
                    text=match.group(0),
                    claim_type=ClaimType.STOCK_PRICE,
                    entities=[symbol],
                    values=[],
                    confidence=0.9,
                    source_text=text
                ))
        
        # Company names in questions
        company_patterns = [
            r'\b(Apple|Microsoft|Google|Amazon|Tesla|Meta|Facebook|Netflix|Nvidia|AMD|Intel|Oracle|Salesforce)\b',
            r'\b(JPMorgan|Bank of America|Wells Fargo|Goldman Sachs|Morgan Stanley|Citigroup|American Express|Visa|Mastercard)\b',
            r'\b(Johnson & Johnson|Pfizer|Merck|AbbVie|Bristol Myers|UnitedHealth|Eli Lilly)\b'
        ]
        
        for pattern in company_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                company = match.group(1)
                claims.append(FinancialClaim(
                    text=f"{company} stock",
                    claim_type=ClaimType.STOCK_PRICE,
                    entities=[company],
                    values=[],
                    confidence=0.8,
                    source_text=text
                ))
        
        # Stock price patterns
        stock_pattern = r'\b([A-Z]{1,5})\s*(?:stock|shares?)?\s*(?:is|are|trading|at|currently)?\s*\$?\s*(\d+(?:\.\d+)?)'
        for match in re.finditer(stock_pattern, text, re.IGNORECASE):
            symbol = match.group(1)
            price = float(match.group(2))
            claims.append(FinancialClaim(
                text=match.group(0),
                claim_type=ClaimType.STOCK_PRICE,
                entities=[symbol],
                values=[],
                confidence=0.7,
                source_text=text
            ))
        
        # Market performance patterns
        market_pattern = r'\b(market|S&P 500|Dow Jones|Nasdaq)\s*(?:is|was|has|have)?\s*(up|down|gained|lost)\s*(\d+(?:\.\d+)?%?)'
        for match in re.finditer(market_pattern, text, re.IGNORECASE):
            claims.append(FinancialClaim(
                text=match.group(0),
                claim_type=ClaimType.STOCK_PRICE,  # Use existing enum value
                entities=[],
                values=[],
                confidence=0.6,
                source_text=text
            ))
        
        return claims

    def enhance_entities(self, claims: List[FinancialClaim]) -> List[FinancialClaim]:
        """Enhance claims with additional entity information"""
        enhanced_claims = []
        for claim in claims:
            if claim.entities:
                # Resolve company names to symbols for each entity
                enhanced_entities = []
                for entity in claim.entities:
                    ticker_match = self.ticker_resolver.resolve_ticker(entity)
                    if ticker_match:
                        enhanced_entities.append(ticker_match.ticker)
                    else:
                        enhanced_entities.append(entity)
                claim.entities = enhanced_entities
            enhanced_claims.append(claim)
        return enhanced_claims


# Convenience function for easy usage
async def extract_financial_claims(text: str, provider: str = "auto") -> List[FinancialClaim]:
    """
    Extract financial claims from text using the specified provider
    
    Args:
        text: Input text to analyze
        provider: "auto", "bedrock", "openai", "anthropic", "ollama", or "regex"
        
    Returns:
        List of FinancialClaim objects
    """
    extractor = LLMClaimExtractor(provider=provider)
    claims = await extractor.extract_claims(text)
    return extractor.enhance_entities(claims)
