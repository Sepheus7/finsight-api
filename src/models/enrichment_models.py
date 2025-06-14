"""
Core data models for Financial Enrichment System
Clean, focused data structures for high-performance financial data integration
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ClaimType(Enum):
    """Types of financial claims we can detect and enrich"""
    STOCK_PRICE = "stock_price"
    MARKET_PERFORMANCE = "market_performance"
    ECONOMIC_INDICATOR = "economic_indicator"
    COMPANY_FUNDAMENTAL = "company_fundamental"
    SECTOR_PERFORMANCE = "sector_performance"
    UNKNOWN = "unknown"


class DataSourceType(Enum):
    """Available data sources for enrichment"""
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    FRED = "fred"
    FINANCIAL_NEWS = "financial_news"
    CACHE = "cache"


@dataclass
class FinancialClaim:
    """A financial claim extracted from content"""
    text: str
    claim_type: ClaimType
    symbol: Optional[str] = None
    confidence: float = 0.0
    position_start: int = 0
    position_end: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'claim_type': self.claim_type.value,
            'symbol': self.symbol,
            'confidence': self.confidence,
            'position_start': self.position_start,
            'position_end': self.position_end
        }


@dataclass
class DataPoint:
    """A single enrichment data point"""
    source: DataSourceType
    data_type: str
    value: Any
    timestamp: datetime
    symbol: Optional[str] = None
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source.value,
            'data_type': self.data_type,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'confidence': self.confidence
        }


@dataclass
class EnrichmentRequest:
    """Request for financial content enrichment"""
    content: str
    enrichment_types: List[str]
    include_compliance: bool = False
    format_style: str = "enhanced"
    max_response_time: int = 5000  # milliseconds
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EnrichmentMetrics:
    """Performance and quality metrics for enrichment"""
    processing_time_ms: float
    claims_processed: int
    data_sources_used: int
    cache_hit_rate: float
    data_points_added: int = 0
    api_calls_made: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EnrichmentResponse:
    """Response from financial content enrichment"""
    original_content: str
    enriched_content: str
    claims: List[Any]  # Accept any FinancialClaim type
    data_points: List[DataPoint]
    data_sources: List[str]
    compliance_warnings: List[str]
    metrics: EnrichmentMetrics
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_content': self.original_content,
            'enriched_content': self.enriched_content,
            'claims': [claim.to_dict() for claim in self.claims],
            'data_points': [dp.to_dict() for dp in self.data_points],
            'data_sources': self.data_sources,
            'compliance_warnings': self.compliance_warnings,
            'metrics': self.metrics.to_dict(),
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class StockData:
    """Real-time stock data"""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    year_high: Optional[float] = None
    year_low: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'price': self.price,
            'change': self.change,
            'change_percent': self.change_percent,
            'volume': self.volume,
            'market_cap': self.market_cap,
            'pe_ratio': self.pe_ratio,
            'day_high': self.day_high,
            'day_low': self.day_low,
            'year_high': self.year_high,
            'year_low': self.year_low,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class EconomicIndicator:
    """Economic indicator data"""
    indicator_name: str
    value: float
    unit: str
    period: str
    release_date: datetime
    previous_value: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'indicator_name': self.indicator_name,
            'value': self.value,
            'unit': self.unit,
            'period': self.period,
            'release_date': self.release_date.isoformat(),
            'previous_value': self.previous_value
        }


@dataclass
class MarketContext:
    """Market context data"""
    sector: str
    sector_performance: float
    market_trend: str
    volatility_index: Optional[float] = None
    related_news: List[str] = None
    
    def __post_init__(self):
        if self.related_news is None:
            self.related_news = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'sector': self.sector,
            'sector_performance': self.sector_performance,
            'market_trend': self.market_trend,
            'volatility_index': self.volatility_index,
            'related_news': self.related_news
        }


@dataclass
class CacheEntry:
    """Cache entry for performance optimization"""
    key: str
    data: Any
    timestamp: datetime
    expiry: datetime
    source: DataSourceType
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expiry
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'expiry': self.expiry.isoformat(),
            'source': self.source.value
        }


# Utility functions for model creation
def create_stock_claim(text: str, symbol: str, confidence: float = 0.8) -> FinancialClaim:
    """Helper to create stock price claims"""
    return FinancialClaim(
        text=text,
        claim_type=ClaimType.STOCK_PRICE,
        symbol=symbol.upper(),
        confidence=confidence
    )


def create_economic_claim(text: str, confidence: float = 0.7) -> FinancialClaim:
    """Helper to create economic indicator claims"""
    return FinancialClaim(
        text=text,
        claim_type=ClaimType.ECONOMIC_INDICATOR,
        confidence=confidence
    )


# Response templates for common use cases
def create_success_response(content: str, claims: List[FinancialClaim], 
                          data_points: List[DataPoint], metrics: EnrichmentMetrics) -> EnrichmentResponse:
    """Helper to create successful enrichment response"""
    return EnrichmentResponse(
        original_content=content,
        enriched_content=content,  # Will be formatted by DataFormatter
        claims=claims,
        data_points=data_points,
        data_sources=[dp.source.value for dp in data_points],
        compliance_warnings=[],
        metrics=metrics
    )
