"""
Financial Data Models for FinSight
Defines the data structures used throughout the application
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class ClaimType(Enum):
    """Types of financial claims that can be extracted"""
    STOCK_PRICE = "stock_price"
    MARKET_CAP = "market_cap"
    REVENUE = "revenue"
    EARNINGS = "earnings"
    INTEREST_RATE = "interest_rate"
    INFLATION = "inflation"
    ECONOMIC_INDICATOR = "economic_indicator"
    OPINION = "opinion"
    PREDICTION = "prediction"
    HISTORICAL = "historical"


class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class FinancialClaim:
    """Represents a financial claim extracted from content"""
    text: str
    claim_type: ClaimType
    entities: List[str]  # Companies, tickers, etc.
    values: List[str]    # Prices, percentages, amounts
    confidence: float
    source_text: str
    start_pos: int = 0
    end_pos: int = 0
    
    # Backward compatibility properties
    @property
    def claim_text(self) -> str:
        """Backward compatibility for claim_text"""
        return self.text
    
    @property
    def entity(self) -> str:
        """Get primary entity (first in list)"""
        return self.entities[0] if self.entities else ""
    
    @property
    def value(self) -> str:
        """Get primary value (first in list)"""
        return self.values[0] if self.values else ""


@dataclass
class FactCheckResult:
    """Result of fact-checking a financial claim"""
    claim: FinancialClaim
    verified: bool
    confidence: float
    source: str
    explanation: str
    actual_value: Optional[str] = None
    discrepancy: Optional[float] = None
    
    # Additional properties for enhanced system
    risk_level: RiskLevel = RiskLevel.LOW
    sources: Optional[List[str]] = None
    
    # Backward compatibility properties
    @property
    def is_accurate(self) -> bool:
        """Backward compatibility for is_accurate"""
        return self.verified
    
    @property 
    def confidence_score(self) -> float:
        """Backward compatibility for confidence_score"""
        return self.confidence
    
    def __post_init__(self):
        """Initialize default values"""
        if self.sources is None:
            self.sources = [self.source] if self.source else []


@dataclass
class AIEvaluation:
    """AI evaluation of content quality"""
    explanation: str
    quality_assessment: str
    confidence_multiplier: float
    financial_risk: RiskLevel
    misinformation_risk: RiskLevel
    regulatory_flags: List[str] = None
    investment_advice_detected: bool = False


@dataclass
class EnhancedContent:
    """Enhanced content with fact-checking and AI evaluation"""
    original_content: str
    claims_extracted: List[FinancialClaim]
    fact_check_results: List[FactCheckResult]
    ai_evaluation: AIEvaluation
    original_confidence: float
    enhanced_confidence: float
    verification_status: str
    processing_time: float
    timestamp: str
