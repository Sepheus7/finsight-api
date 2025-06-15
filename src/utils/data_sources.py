"""
Data Source Abstraction Layer for FinSight
Provides a unified interface for accessing multiple data sources
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
import logging
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Types of data sources available"""
    MARKET_DATA = "market_data"
    ECONOMIC_INDICATORS = "economic_indicators" 
    COMPANY_FUNDAMENTALS = "company_fundamentals"
    GOVERNMENT_DATA = "government_data"
    GLOBAL_STATISTICS = "global_statistics"
    NEWS_SENTIMENT = "news_sentiment"


class DataSourceReliability(Enum):
    """Reliability levels for data sources"""
    VERY_HIGH = "very_high"  # Official government/regulatory sources
    HIGH = "high"           # Established financial data providers
    MEDIUM = "medium"       # Community-maintained APIs
    LOW = "low"            # Experimental or unverified sources


@dataclass
class DataSourceMetadata:
    """Metadata about a data source"""
    name: str
    description: str
    data_types: List[DataSourceType]
    reliability: DataSourceReliability
    rate_limit: Optional[int] = None  # requests per minute
    cost_per_request: Optional[float] = None  # USD
    requires_auth: bool = False
    base_url: Optional[str] = None
    documentation_url: Optional[str] = None


@dataclass
class DataQuery:
    """Represents a query to a data source"""
    query_type: str  # e.g., "stock_price", "gdp", "inflation_rate"
    parameters: Dict[str, Any]
    time_range: Optional[Tuple[datetime, datetime]] = None
    country_code: Optional[str] = None
    currency: Optional[str] = None


@dataclass
class DataResponse:
    """Response from a data source"""
    source_name: str
    query: DataQuery
    data: Any
    timestamp: datetime
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any]
    error: Optional[str] = None
    
    @property
    def is_successful(self) -> bool:
        """Check if the response was successful"""
        return self.error is None and self.data is not None


class DataSource(ABC):
    """Abstract base class for all data sources"""
    
    def __init__(self, metadata: DataSourceMetadata, config: Dict[str, Any] = None):
        self.metadata = metadata
        self.config = config or {}
        self._cache = {}
        self._rate_limiter = None
        self._last_request_time = None
        
    @abstractmethod
    async def query(self, query: DataQuery) -> DataResponse:
        """Execute a query against the data source"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the data source is available and responding"""
        pass
    
    @abstractmethod
    def supports_query_type(self, query_type: str) -> bool:
        """Check if this source supports a specific query type"""
        pass
    
    async def batch_query(self, queries: List[DataQuery]) -> List[DataResponse]:
        """Execute multiple queries (default implementation)"""
        tasks = [self.query(q) for q in queries]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def _should_cache(self, query: DataQuery) -> bool:
        """Determine if a query result should be cached"""
        # Cache by default, override in subclasses if needed
        return True
    
    def _get_cache_key(self, query: DataQuery) -> str:
        """Generate a cache key for a query"""
        return f"{self.metadata.name}:{query.query_type}:{hash(str(query.parameters))}"
    
    def _rate_limit_check(self) -> bool:
        """Check if we're within rate limits"""
        if not self.metadata.rate_limit:
            return True
            
        now = datetime.now()
        if self._last_request_time:
            time_since_last = (now - self._last_request_time).total_seconds()
            min_interval = 60.0 / self.metadata.rate_limit
            if time_since_last < min_interval:
                return False
        
        self._last_request_time = now
        return True


class DataSourceRegistry:
    """Registry for managing multiple data sources"""
    
    def __init__(self):
        self._sources: Dict[str, DataSource] = {}
        self._source_rankings: Dict[DataSourceType, List[str]] = {}
        
    def register_source(self, source: DataSource, priority: int = 0):
        """Register a new data source"""
        self._sources[source.metadata.name] = source
        
        # Update rankings by data type
        for data_type in source.metadata.data_types:
            if data_type not in self._source_rankings:
                self._source_rankings[data_type] = []
            
            # Insert based on priority and reliability
            source_info = (source.metadata.name, priority, source.metadata.reliability.value)
            self._source_rankings[data_type].append(source_info)
            self._source_rankings[data_type].sort(key=lambda x: (x[1], x[2]), reverse=True)
    
    def get_source(self, name: str) -> Optional[DataSource]:
        """Get a specific data source by name"""
        return self._sources.get(name)
    
    def get_sources_for_type(self, data_type: DataSourceType) -> List[DataSource]:
        """Get all sources that support a specific data type, ordered by priority"""
        if data_type not in self._source_rankings:
            return []
        
        sources = []
        for source_name, _, _ in self._source_rankings[data_type]:
            source = self._sources.get(source_name)
            if source:
                sources.append(source)
        
        return sources
    
    def get_best_source_for_query(self, query: DataQuery) -> Optional[DataSource]:
        """Get the best available source for a specific query"""
        # Try to infer data type from query type
        data_type = self._infer_data_type(query.query_type)
        if not data_type:
            return None
        
        sources = self.get_sources_for_type(data_type)
        for source in sources:
            if source.supports_query_type(query.query_type):
                return source
        
        return None
    
    def _infer_data_type(self, query_type: str) -> Optional[DataSourceType]:
        """Infer data type from query type"""
        type_mapping = {
            "stock_price": DataSourceType.MARKET_DATA,
            "market_cap": DataSourceType.MARKET_DATA,
            "gdp": DataSourceType.ECONOMIC_INDICATORS,
            "inflation": DataSourceType.ECONOMIC_INDICATORS,
            "unemployment": DataSourceType.ECONOMIC_INDICATORS,
            "population": DataSourceType.GLOBAL_STATISTICS,
            "revenue": DataSourceType.COMPANY_FUNDAMENTALS,
            "earnings": DataSourceType.COMPANY_FUNDAMENTALS,
        }
        return type_mapping.get(query_type)
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all registered sources"""
        results = {}
        for name, source in self._sources.items():
            try:
                results[name] = await source.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = False
        return results


class MultiSourceQueryExecutor:
    """Executes queries across multiple sources with intelligent routing"""
    
    def __init__(self, registry: DataSourceRegistry):
        self.registry = registry
        
    async def execute_query(self, query: DataQuery, 
                          fallback: bool = True,
                          cross_verify: bool = False) -> Union[DataResponse, List[DataResponse]]:
        """
        Execute a query with optional fallback and cross-verification
        
        Args:
            query: The query to execute
            fallback: Whether to try fallback sources if primary fails
            cross_verify: Whether to query multiple sources for verification
            
        Returns:
            Single DataResponse or list of responses if cross_verify=True
        """
        if cross_verify:
            return await self._execute_cross_verification(query)
        else:
            return await self._execute_single_query(query, fallback)
    
    async def _execute_single_query(self, query: DataQuery, fallback: bool) -> DataResponse:
        """Execute query against the best available source"""
        best_source = self.registry.get_best_source_for_query(query)
        if not best_source:
            return DataResponse(
                source_name="unknown",
                query=query,
                data=None,
                timestamp=datetime.now(),
                confidence=0.0,
                metadata={},
                error="No suitable data source found"
            )
        
        try:
            response = await best_source.query(query)
            if response.is_successful:
                return response
            elif fallback:
                return await self._try_fallback_sources(query, best_source)
            else:
                return response
        except Exception as e:
            if fallback:
                return await self._try_fallback_sources(query, best_source)
            else:
                return DataResponse(
                    source_name=best_source.metadata.name,
                    query=query,
                    data=None,
                    timestamp=datetime.now(),
                    confidence=0.0,
                    metadata={},
                    error=str(e)
                )
    
    async def _execute_cross_verification(self, query: DataQuery) -> List[DataResponse]:
        """Execute query against multiple sources for cross-verification"""
        data_type = self.registry._infer_data_type(query.query_type)
        if not data_type:
            return []
        
        sources = self.registry.get_sources_for_type(data_type)
        suitable_sources = [s for s in sources if s.supports_query_type(query.query_type)]
        
        if not suitable_sources:
            return []
        
        # Limit to top 3 sources to avoid excessive API calls
        sources_to_query = suitable_sources[:3]
        
        tasks = [source.query(query) for source in sources_to_query]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and failed responses
        valid_responses = []
        for response in responses:
            if isinstance(response, DataResponse) and response.is_successful:
                valid_responses.append(response)
        
        return valid_responses
    
    async def _try_fallback_sources(self, query: DataQuery, failed_source: DataSource) -> DataResponse:
        """Try fallback sources when primary source fails"""
        data_type = self.registry._infer_data_type(query.query_type)
        if not data_type:
            return DataResponse(
                source_name="fallback",
                query=query,
                data=None,
                timestamp=datetime.now(),
                confidence=0.0,
                metadata={},
                error="No fallback sources available"
            )
        
        sources = self.registry.get_sources_for_type(data_type)
        for source in sources:
            if source.metadata.name != failed_source.metadata.name and source.supports_query_type(query.query_type):
                try:
                    response = await source.query(query)
                    if response.is_successful:
                        # Mark as fallback response
                        response.metadata["is_fallback"] = True
                        response.metadata["primary_source_failed"] = failed_source.metadata.name
                        return response
                except Exception as e:
                    logger.warning(f"Fallback source {source.metadata.name} also failed: {e}")
                    continue
        
        return DataResponse(
            source_name="fallback",
            query=query,
            data=None,
            timestamp=datetime.now(),
            confidence=0.0,
            metadata={},
            error="All fallback sources failed"
        )
