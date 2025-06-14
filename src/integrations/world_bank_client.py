"""
World Bank Open Data API Client
Provides access to World Bank economic and development indicators
"""

import aiohttp
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

from ..utils.data_sources import (
    DataSource, DataSourceMetadata, DataSourceType, DataSourceReliability,
    DataQuery, DataResponse
)

logger = logging.getLogger(__name__)


@dataclass
class WorldBankIndicator:
    """World Bank indicator metadata"""
    id: str
    name: str
    unit: str
    source: str
    topics: List[str]
    frequency: str  # Annual, Monthly, Quarterly


class WorldBankDataSource(DataSource):
    """World Bank Open Data API client"""
    
    BASE_URL = "https://api.worldbank.org/v2"
    
    # Key economic indicators relevant to financial fact-checking
    ECONOMIC_INDICATORS = {
        "gdp": "NY.GDP.MKTP.CD",                    # GDP (current US$)
        "gdp_growth": "NY.GDP.MKTP.KD.ZG",          # GDP growth (annual %)
        "gdp_per_capita": "NY.GDP.PCAP.CD",         # GDP per capita (current US$)
        "inflation": "FP.CPI.TOTL.ZG",              # Inflation, consumer prices (annual %)
        "unemployment": "SL.UEM.TOTL.ZS",           # Unemployment, total (% of total labor force)
        "interest_rate": "FR.INR.RINR",             # Real interest rate (%)
        "debt_to_gdp": "GC.DOD.TOTL.GD.ZS",        # Central government debt, total (% of GDP)
        "exports": "NE.EXP.GNFS.CD",                # Exports of goods and services (current US$)
        "imports": "NE.IMP.GNFS.CD",                # Imports of goods and services (current US$)
        "population": "SP.POP.TOTL",                # Population, total
        "exchange_rate": "PA.NUS.FCRF",             # Official exchange rate (LCU per US$)
        "fdi": "BX.KLT.DINV.CD.WD",                 # Foreign direct investment, net inflows
        "market_cap": "CM.MKT.LCAP.CD",             # Market capitalization of listed companies
        "stock_traded": "CM.MKT.TRAD.CD"            # Stocks traded, total value
    }
    
    COUNTRY_CODES = {
        # Major economies
        "united_states": "US", "usa": "US", "us": "US",
        "china": "CN", "cn": "CN",
        "japan": "JP", "jp": "JP",
        "germany": "DE", "de": "DE",
        "united_kingdom": "GB", "uk": "GB", "gb": "GB",
        "france": "FR", "fr": "FR",
        "india": "IN", "in": "IN",
        "italy": "IT", "it": "IT",
        "brazil": "BR", "br": "BR",
        "canada": "CA", "ca": "CA",
        "russia": "RU", "ru": "RU",
        "south_korea": "KR", "korea": "KR", "kr": "KR",
        "spain": "ES", "es": "ES",
        "australia": "AU", "au": "AU",
        "mexico": "MX", "mx": "MX",
        "indonesia": "ID", "id": "ID",
        "netherlands": "NL", "nl": "NL",
        "saudi_arabia": "SA", "sa": "SA",
        "turkey": "TR", "tr": "TR",
        "taiwan": "TW", "tw": "TW",
        # Regional aggregates
        "world": "WLD",
        "high_income": "HIC",
        "upper_middle_income": "UMC",
        "lower_middle_income": "LMC",
        "low_income": "LIC",
        "oecd": "OED",
        "euro_area": "EMU",
        "european_union": "EUU",
        "east_asia_pacific": "EAS",
        "latin_america_caribbean": "LCN",
        "middle_east_north_africa": "MEA",
        "north_america": "NAC",
        "south_asia": "SAS",
        "sub_saharan_africa": "SSF"
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        metadata = DataSourceMetadata(
            name="world_bank",
            description="World Bank Open Data - Economic and development indicators",
            data_types=[
                DataSourceType.ECONOMIC_INDICATORS,
                DataSourceType.GLOBAL_STATISTICS,
                DataSourceType.GOVERNMENT_DATA
            ],
            reliability=DataSourceReliability.VERY_HIGH,
            rate_limit=120,  # Conservative rate limit
            cost_per_request=0.0,  # Free API
            requires_auth=False,
            base_url=self.BASE_URL,
            documentation_url="https://datahelpdesk.worldbank.org/knowledgebase/articles/889392"
        )
        super().__init__(metadata, config)
        self._session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": "FinSight/1.0 (+https://github.com/your-repo/finsight)",
                    "Accept": "application/json"
                }
            )
        return self._session
    
    async def query(self, query: DataQuery) -> DataResponse:
        """Execute query against World Bank API"""
        try:
            if not self.supports_query_type(query.query_type):
                return DataResponse(
                    source_name=self.metadata.name,
                    query=query,
                    data=None,
                    timestamp=datetime.now(),
                    confidence=0.0,
                    metadata={},
                    error=f"Unsupported query type: {query.query_type}"
                )
            
            # Check rate limiting
            if not self._rate_limit_check():
                return DataResponse(
                    source_name=self.metadata.name,
                    query=query,
                    data=None,
                    timestamp=datetime.now(),
                    confidence=0.0,
                    metadata={},
                    error="Rate limit exceeded"
                )
            
            # Build API request
            indicator_code = self.ECONOMIC_INDICATORS.get(query.query_type)
            if not indicator_code:
                return DataResponse(
                    source_name=self.metadata.name,
                    query=query,
                    data=None,
                    timestamp=datetime.now(),
                    confidence=0.0,
                    metadata={},
                    error=f"No indicator mapping for query type: {query.query_type}"
                )
            
            country_code = self._resolve_country_code(query.country_code or "US")
            
            # Determine date range
            if query.time_range:
                start_year = query.time_range[0].year
                end_year = query.time_range[1].year
            else:
                # Default to last 5 years
                end_year = datetime.now().year
                start_year = end_year - 4
            
            date_range = f"{start_year}:{end_year}"
            
            # Build URL
            url = f"{self.BASE_URL}/country/{country_code}/indicator/{indicator_code}"
            params = {
                "format": "json",
                "date": date_range,
                "per_page": 100,
                "page": 1
            }
            
            session = await self._get_session()
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return DataResponse(
                        source_name=self.metadata.name,
                        query=query,
                        data=None,
                        timestamp=datetime.now(),
                        confidence=0.0,
                        metadata={"http_status": response.status},
                        error=f"API request failed: {response.status} - {error_text}"
                    )
                
                data = await response.json()
                
                # World Bank API returns [metadata, data] array
                if not isinstance(data, list) or len(data) < 2:
                    return DataResponse(
                        source_name=self.metadata.name,
                        query=query,
                        data=None,
                        timestamp=datetime.now(),
                        confidence=0.0,
                        metadata={},
                        error="Unexpected API response format"
                    )
                
                metadata_info = data[0]
                indicator_data = data[1]
                
                if not indicator_data:
                    return DataResponse(
                        source_name=self.metadata.name,
                        query=query,
                        data=None,
                        timestamp=datetime.now(),
                        confidence=0.5,  # Low confidence for no data
                        metadata={"total_records": 0},
                        error="No data available for the specified criteria"
                    )
                
                # Process and format the data
                processed_data = self._process_indicator_data(indicator_data, query.query_type)
                
                # Calculate confidence based on data recency and completeness
                confidence = self._calculate_confidence(processed_data)
                
                return DataResponse(
                    source_name=self.metadata.name,
                    query=query,
                    data=processed_data,
                    timestamp=datetime.now(),
                    confidence=confidence,
                    metadata={
                        "total_records": len(indicator_data),
                        "indicator_code": indicator_code,
                        "country_code": country_code,
                        "source_organization": metadata_info.get("source", {}).get("value", "World Bank"),
                        "last_updated": metadata_info.get("lastupdated")
                    }
                )
                
        except asyncio.TimeoutError:
            return DataResponse(
                source_name=self.metadata.name,
                query=query,
                data=None,
                timestamp=datetime.now(),
                confidence=0.0,
                metadata={},
                error="Request timeout"
            )
        except Exception as e:
            logger.error(f"World Bank API error: {e}")
            return DataResponse(
                source_name=self.metadata.name,
                query=query,
                data=None,
                timestamp=datetime.now(),
                confidence=0.0,
                metadata={},
                error=str(e)
            )
    
    def _resolve_country_code(self, country_input: str) -> str:
        """Resolve country name or code to World Bank country code"""
        if not country_input:
            return "US"  # Default to US
        
        country_input = country_input.lower().strip()
        
        # Direct lookup
        if country_input in self.COUNTRY_CODES:
            return self.COUNTRY_CODES[country_input]
        
        # Try 2-letter code directly (might already be valid)
        if len(country_input) == 2:
            return country_input.upper()
        
        # Try 3-letter code to 2-letter mapping (common ones)
        three_to_two = {
            "usa": "US", "gbr": "GB", "deu": "DE", "fra": "FR",
            "jpn": "JP", "chn": "CN", "ind": "IN", "bra": "BR",
            "can": "CA", "aus": "AU", "kor": "KR", "ita": "IT"
        }
        
        if country_input in three_to_two:
            return three_to_two[country_input]
        
        # Default fallback
        logger.warning(f"Could not resolve country code for: {country_input}, using US")
        return "US"
    
    def _process_indicator_data(self, data: List[Dict], query_type: str) -> Dict[str, Any]:
        """Process and format World Bank indicator data"""
        if not data:
            return {}
        
        # Sort by year descending to get most recent first
        sorted_data = sorted(data, key=lambda x: x.get("date", "0"), reverse=True)
        
        # Get most recent non-null value
        latest_value = None
        latest_year = None
        
        for record in sorted_data:
            if record.get("value") is not None:
                latest_value = record["value"]
                latest_year = record.get("date")
                break
        
        # Create time series
        time_series = []
        for record in sorted_data:
            if record.get("value") is not None:
                time_series.append({
                    "year": record.get("date"),
                    "value": record["value"],
                    "country": record.get("country", {}).get("value"),
                    "country_code": record.get("countryiso3code")
                })
        
        # Calculate trends if we have multiple data points
        trend = None
        if len(time_series) >= 2:
            recent_val = time_series[0]["value"]
            older_val = time_series[1]["value"]
            if older_val != 0:
                trend = ((recent_val - older_val) / older_val) * 100
        
        return {
            "latest_value": latest_value,
            "latest_year": latest_year,
            "trend_percent": trend,
            "time_series": time_series[:10],  # Limit to last 10 years
            "unit": self._get_unit_for_indicator(query_type),
            "data_points": len(time_series)
        }
    
    def _get_unit_for_indicator(self, query_type: str) -> str:
        """Get the unit for a specific indicator"""
        units = {
            "gdp": "USD",
            "gdp_growth": "% annual",
            "gdp_per_capita": "USD",
            "inflation": "% annual",
            "unemployment": "% of labor force",
            "interest_rate": "%",
            "debt_to_gdp": "% of GDP",
            "exports": "USD",
            "imports": "USD",
            "population": "people",
            "exchange_rate": "local currency per USD",
            "fdi": "USD",
            "market_cap": "USD",
            "stock_traded": "USD"
        }
        return units.get(query_type, "")
    
    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on data quality"""
        if not data or data.get("latest_value") is None:
            return 0.0
        
        base_confidence = 0.9  # High base confidence for World Bank data
        
        # Reduce confidence based on data age
        latest_year = data.get("latest_year")
        if latest_year:
            try:
                year_age = datetime.now().year - int(latest_year)
                if year_age > 3:
                    base_confidence *= 0.8  # Older data is less reliable
                elif year_age > 1:
                    base_confidence *= 0.9
            except (ValueError, TypeError):
                base_confidence *= 0.7
        
        # Reduce confidence if we have limited data points
        data_points = data.get("data_points", 0)
        if data_points < 3:
            base_confidence *= 0.8
        
        return min(1.0, base_confidence)
    
    async def health_check(self) -> bool:
        """Check if World Bank API is available"""
        try:
            session = await self._get_session()
            # Simple check: get countries list
            url = f"{self.BASE_URL}/country"
            params = {"format": "json", "per_page": 1}
            
            async with session.get(url, params=params) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"World Bank health check failed: {e}")
            return False
    
    def supports_query_type(self, query_type: str) -> bool:
        """Check if this source supports a specific query type"""
        return query_type in self.ECONOMIC_INDICATORS
    
    async def get_available_countries(self) -> List[Dict[str, str]]:
        """Get list of available countries from World Bank API"""
        try:
            session = await self._get_session()
            url = f"{self.BASE_URL}/country"
            params = {"format": "json", "per_page": 500}
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                if isinstance(data, list) and len(data) >= 2:
                    countries = data[1]
                    return [
                        {
                            "code": country.get("id"),
                            "name": country.get("name"),
                            "region": country.get("region", {}).get("value"),
                            "income_level": country.get("incomeLevel", {}).get("value")
                        }
                        for country in countries
                        if country.get("id") and country.get("name")
                    ]
        except Exception as e:
            logger.error(f"Failed to get countries list: {e}")
        return []
    
    async def get_available_indicators(self) -> List[Dict[str, str]]:
        """Get list of available indicators"""
        indicators = []
        for key, code in self.ECONOMIC_INDICATORS.items():
            indicators.append({
                "key": key,
                "code": code,
                "name": key.replace("_", " ").title(),
                "unit": self._get_unit_for_indicator(key)
            })
        return indicators
    
    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, '_session') and self._session and not self._session.closed:
            # Note: This won't work in async context, better to call close() explicitly
            pass


# Example usage and testing functions
async def test_world_bank_integration():
    """Test function for World Bank integration"""
    wb_source = WorldBankDataSource()
    
    try:
        # Test health check
        health = await wb_source.health_check()
        print(f"World Bank API Health: {'✅ OK' if health else '❌ Failed'}")
        
        # Test GDP query for US
        gdp_query = DataQuery(
            query_type="gdp",
            parameters={"country": "US"},
            country_code="US"
        )
        
        gdp_response = await wb_source.query(gdp_query)
        if gdp_response.is_successful:
            print(f"✅ US GDP Query Success:")
            print(f"   Latest Value: ${gdp_response.data['latest_value']:,.0f}")
            print(f"   Latest Year: {gdp_response.data['latest_year']}")
            print(f"   Confidence: {gdp_response.confidence:.2f}")
        else:
            print(f"❌ GDP Query Failed: {gdp_response.error}")
        
        # Test inflation query
        inflation_query = DataQuery(
            query_type="inflation",
            parameters={"country": "US"},
            country_code="US"
        )
        
        inflation_response = await wb_source.query(inflation_query)
        if inflation_response.is_successful:
            print(f"✅ US Inflation Query Success:")
            print(f"   Latest Value: {inflation_response.data['latest_value']:.2f}%")
            print(f"   Latest Year: {inflation_response.data['latest_year']}")
            if inflation_response.data.get('trend_percent'):
                print(f"   Trend: {inflation_response.data['trend_percent']:+.2f}%")
        else:
            print(f"❌ Inflation Query Failed: {inflation_response.error}")
    
    finally:
        await wb_source.close()


if __name__ == "__main__":
    asyncio.run(test_world_bank_integration())
