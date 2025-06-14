"""
Financial Claim Extractor
AI-powered extraction of financial claims from text content
Focus: High-precision detection using AWS Bedrock
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.financial_models import FinancialClaim, ClaimType
from utils.llm_claim_extractor import LLMClaimExtractor
from config import LLMConfig

logger = logging.getLogger(__name__)

class ClaimExtractor:
    """
    AI-powered financial claim extraction
    Uses AWS Bedrock for high-accuracy detection
    """
    
    def __init__(self):
        self.config = LLMConfig()
        self.llm_extractor = LLMClaimExtractor(provider=self.config.get_provider_for_environment())
        logger.info(f"Initialized claim extractor with provider: {self.llm_extractor.provider}")
    
    async def extract_claims(self, content: str) -> List[FinancialClaim]:
        """
        Extract all financial claims from content using AI
        Returns list of structured claims with confidence scores
        """
        try:
            # Use LLM extractor
            claims = await self.llm_extractor.extract_claims(content)
            logger.info(f"Extracted {len(claims)} unique financial claims")
            return claims
        except Exception as e:
            logger.error(f"LLM claim extraction failed: {e}")
            return []
    
    async def extract_symbols_from_text(self, content: str) -> List[str]:
        """
        Quick utility to extract just the stock symbols from text
        Uses LLM extractor with symbol-only mode
        """
        try:
            claims = await self.llm_extractor.extract_claims(content)
            symbols = []
            for claim in claims:
                if claim.entities:
                    symbols.extend(claim.entities)
            return symbols
        except Exception as e:
            logger.error(f"LLM symbol extraction failed: {e}")
            return []
    
    async def validate_symbol(self, symbol: str) -> bool:
        """Validate if a string is likely a valid stock symbol"""
        try:
            claims = await self.llm_extractor.extract_claims(f"Stock symbol: {symbol}")
            return any(symbol in claim.entities for claim in claims if claim.entities)
        except Exception as e:
            logger.error(f"LLM symbol validation failed: {e}")
            return False

async def extract_claims(content: str) -> List[Dict[str, Any]]:
    """Extract claims and return as dictionaries"""
    extractor = ClaimExtractor()
    claims = await extractor.extract_claims(content)
    return [claim.to_dict() for claim in claims]

# Utility functions for external use
async def quick_extract_symbols(content: str) -> List[str]:
    """Quick function to extract just stock symbols"""
    extractor = ClaimExtractor()
    return await extractor.extract_symbols_from_text(content)

async def extract_financial_claims(content: str) -> List[Dict[str, Any]]:
    """Extract claims and return as dictionaries"""
    extractor = ClaimExtractor()
    claims = await extractor.extract_claims(content)
    return [claim.to_dict() for claim in claims]
