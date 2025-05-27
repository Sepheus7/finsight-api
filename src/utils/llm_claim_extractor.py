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
                
        elif provider == "ollama" and REQUESTS_AVAILABLE:
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
                
        elif provider == "openai" and OPENAI_AVAILABLE:
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
                logger.info("Initialized OpenAI client for claim extraction")
            else:
                logger.warning("OpenAI API key not found, falling back to regex")
                self.provider = "regex"
                
        elif provider == "anthropic" and ANTHROPIC_AVAILABLE:
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

For each claim found, provide:
1. The exact claim text
2. Claim type (stock_price, market_cap, revenue, earnings, interest_rate, inflation, opinion, prediction, historical)
3. Entities involved (company names, tickers, institutions)
4. Numerical values mentioned
5. Confidence score (0.0-1.0)
6. Character positions in the original text

Focus on:
- Stock prices and valuations
- Market capitalizations
- Revenue and earnings figures
- Interest rates and economic indicators
- Future predictions and opinions
- Historical performance statements

Return a JSON array of claims."""

        user_prompt = f"""
Extract financial claims from this text:

"{text}"

Return JSON format:
[
  {{
    "text": "exact claim text",
    "claim_type": "stock_price|market_cap|revenue|earnings|interest_rate|inflation|opinion|prediction|historical",
    "entities": ["entity1", "entity2"],
    "values": ["value1", "value2"],
    "confidence": 0.95,
    "start_pos": 0,
    "end_pos": 50
  }}
]
"""

        try:
            content = ""
            
            if self.provider == "bedrock":
                # Bedrock API call
                content = self.client.generate_text(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    temperature=0.1,
                    max_tokens=2000
                )
                
            elif self.provider == "ollama":
                # Ollama API call
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
                
            elif self.provider == "openai":
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
                
            elif self.provider == "anthropic":
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
            # Try to extract JSON from response
            if response_content.startswith('['):
                claims_data = json.loads(response_content)
            else:
                # Look for JSON array in the response
                json_match = re.search(r'\[.*\]', response_content, re.DOTALL)
                if json_match:
                    claims_data = json.loads(json_match.group())
                else:
                    logger.warning("No JSON array found in LLM response")
                    return self._extract_with_regex(original_text)
            
            claims = []
            for claim_data in claims_data:
                try:
                    # Map string claim type to enum
                    claim_type_str = claim_data.get('claim_type', 'opinion')
                    claim_type = ClaimType(claim_type_str)
                    
                    # Create FinancialClaim object
                    claim = FinancialClaim(
                        text=claim_data.get('text', ''),
                        claim_type=claim_type,
                        entities=claim_data.get('entities', []),
                        values=claim_data.get('values', []),
                        confidence=float(claim_data.get('confidence', 0.5)),
                        source_text=original_text,
                        start_pos=int(claim_data.get('start_pos', 0)),
                        end_pos=int(claim_data.get('end_pos', len(original_text)))
                    )
                    claims.append(claim)
                    
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping malformed claim: {e}")
                    continue
            
            logger.info(f"Extracted {len(claims)} claims using LLM")
            return claims
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            return self._extract_with_regex(original_text)

    def _extract_with_regex(self, text: str) -> List[FinancialClaim]:
        """Fallback extraction using improved regex patterns"""
        claims = []
        
        # Stock price patterns
        stock_patterns = [
            (r'(?i)(apple inc\.|microsoft|google|tesla|amazon|meta)\s*\(([A-Z]{2,5})\)\s+stock\s+price\s+is\s+\$(\d+(?:\.\d{1,2})?)', ClaimType.STOCK_PRICE),
            (r'(?i)\b([A-Z]{2,5})\s+(?:is\s+)?(?:currently\s+)?(?:trading|trades)\s+(?:at\s+)?\$(\d+(?:\.\d{1,2})?)', ClaimType.STOCK_PRICE),
            (r'(?i)\b([A-Z]{2,5})\s+(?:stock|shares?)\s+(?:is|are|at)\s+\$(\d+(?:\.\d{1,2})?)', ClaimType.STOCK_PRICE),
        ]
        
        # Market cap patterns - made more flexible
        market_cap_patterns = [
            (r'(?i)(microsoft|apple|google|tesla|amazon|meta|alphabet)\s+(?:has\s+a\s+)?market\s+cap(?:italization)?\s+(?:of\s+|is\s+)?\$?(\d+(?:\.\d+)?)\s*(trillion|billion|million)', ClaimType.MARKET_CAP),
            (r'(?i)market\s+cap(?:italization)?\s+of\s+(microsoft|apple|google|tesla|amazon|meta|alphabet)\s+is\s+\$?(\d+(?:\.\d+)?)\s*(trillion|billion|million)', ClaimType.MARKET_CAP),
            (r"(?i)(microsoft|apple|google|tesla|amazon|meta|alphabet)(?:'s)?\s+market\s+cap(?:italization)?\s+(?:is|reached|hit)\s+\$?(\d+(?:\.\d+)?)\s*(trillion|billion|million)", ClaimType.MARKET_CAP),
        ]
        
        # Revenue patterns
        revenue_patterns = [
            (r"(?i)(tesla|apple|microsoft|google|amazon|meta|alphabet)'s\s+revenue\s+(?:increased|grew|rose)\s+by\s+(\d+(?:\.\d+)?%)", ClaimType.REVENUE),
            (r'(?i)(apple|microsoft|google|tesla|amazon|meta|alphabet)\s+reported\s+\$(\d+(?:\.\d+)?)\s*(billion|million|trillion)\s+in\s+revenue', ClaimType.REVENUE),
            (r'(?i)revenue\s+(?:increased|grew|rose)\s+by\s+(\d+(?:\.\d+)?%)', ClaimType.REVENUE),
        ]
        
        # Interest rate patterns
        rate_patterns = [
            (r'(?i)(?:federal reserve|fed)\s+will\s+(?:raise|cut|set)\s+interest\s+rates?\s+(?:by\s+)?(\d+(?:\.\d+)?%)', ClaimType.INTEREST_RATE),
            (r'(?i)interest\s+rates?\s+(?:are|at)\s+(\d+(?:\.\d+)?%)', ClaimType.INTEREST_RATE),
        ]
        
        all_patterns = stock_patterns + market_cap_patterns + revenue_patterns + rate_patterns
        
        for pattern, claim_type in all_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities = []
                values = []
                
                # Extract entities and values from match groups
                groups = match.groups()
                for group in groups:
                    if group and group.replace('.', '').replace('%', '').isdigit():
                        values.append(group)
                    elif group and group.isalpha() and len(group) > 1:
                        entities.append(group)
                
                claim = FinancialClaim(
                    text=match.group(0),
                    claim_type=claim_type,
                    entities=entities,
                    values=values,
                    confidence=0.8,  # High confidence for regex matches
                    source_text=text,
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                claims.append(claim)
        
        logger.info(f"Extracted {len(claims)} claims using regex patterns")
        return claims

    def enhance_entities(self, claims: List[FinancialClaim]) -> List[FinancialClaim]:
        """Enhance entity recognition by mapping company names to tickers"""
        for claim in claims:
            enhanced_entities = []
            for entity in claim.entities:
                # Use enhanced ticker resolver for dynamic company-to-ticker mapping
                ticker_match = self.ticker_resolver.resolve_ticker(entity)
                if ticker_match and ticker_match.confidence > 0.7:
                    enhanced_entities.extend([entity, ticker_match.ticker])
                    logger.debug(f"Enhanced entity '{entity}' with ticker '{ticker_match.ticker}' (confidence: {ticker_match.confidence:.2f})")
                else:
                    enhanced_entities.append(entity)
            claim.entities = list(set(enhanced_entities))  # Remove duplicates
        
        return claims


# Convenience function for easy usage
def extract_financial_claims(text: str, provider: str = "auto") -> List[FinancialClaim]:
    """
    Extract financial claims from text using the specified provider
    
    Args:
        text: Input text to analyze
        provider: "auto", "bedrock", "openai", "anthropic", "ollama", or "regex"
        
    Returns:
        List of FinancialClaim objects
    """
    extractor = LLMClaimExtractor(provider=provider)
    claims = extractor.extract_claims(text)
    return extractor.enhance_entities(claims)
