"""
Financial Data Enrichment Handler - Core FinSight Logic
Streamlined single handler for financial LLM content enrichment
Focus: Real-time data integration with high performance
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any


# Import data sources
from integrations.data_aggregator import DataAggregator
from utils.cache_manager import CacheManager
from utils.claim_extractor import ClaimExtractor
from utils.data_formatter import DataFormatter
from models.financial_models import FinancialClaim
from models.enrichment_models import (
    EnrichmentRequest, EnrichmentResponse, 
    DataSourceType, EnrichmentMetrics,
    DataPoint
)

logger = logging.getLogger(__name__)

class FinancialEnrichmentHandler:
    """
    Core handler for financial content enrichment
    Focuses on high-value real-time data integration
    """
    
    def __init__(self):
        self.data_aggregator = DataAggregator()
        self.cache_manager = CacheManager()
        self.claim_extractor = ClaimExtractor()
        self.data_formatter = DataFormatter()
        
    async def enrich_content(self, request: EnrichmentRequest) -> EnrichmentResponse:
        """
        Main enrichment method - adds real-time financial data to content
        """
        start_time = datetime.now()
        
        try:
            # 1. Extract financial claims from content
            claims = await self.claim_extractor.extract_claims(request.content)
            logger.info(f"Extracted {len(claims)} financial claims")
            
            # 2. Gather real-time data for claims
            enriched_data = await self._gather_financial_data(claims, request.enrichment_types)
            
            # 3. Format enriched content
            enriched_content = await self.data_formatter.format_response(
                original_content=request.content,
                claims=claims,
                data=enriched_data,
                format_style=request.format_style
            )
            
            # 4. Optional: Basic compliance check
            compliance_warnings = []
            if request.include_compliance:
                compliance_warnings = await self._basic_compliance_check(claims)
            
            # 5. Convert enriched_data to data_points
            data_points = []
            for key, value in enriched_data.items():
                if isinstance(value, dict):
                    # Handle cached data (dictionary format)
                    timestamp = datetime.now()
                    if 'timestamp' in value:
                        # Try to parse timestamp if it's a string
                        if isinstance(value['timestamp'], str):
                            try:
                                timestamp = datetime.fromisoformat(value['timestamp'].replace('Z', '+00:00'))
                            except:
                                timestamp = datetime.now()
                        elif isinstance(value['timestamp'], datetime):
                            timestamp = value['timestamp']
                    
                    data_points.append(DataPoint(
                        source=DataSourceType.YAHOO_FINANCE,
                        data_type='stock_price',
                        value=str(value.get('price', value.get('value', 'N/A'))),
                        timestamp=timestamp,
                        symbol=value.get('symbol', key)
                    ))
                elif hasattr(value, 'to_dict') and not isinstance(value, Exception):
                    # Handle StockData objects directly
                    stock_dict = value.to_dict()
                    timestamp = datetime.now()
                    if hasattr(value, 'timestamp') and value.timestamp:
                        timestamp = value.timestamp
                    
                    data_points.append(DataPoint(
                        source=DataSourceType.YAHOO_FINANCE,
                        data_type='stock_price',
                        value=str(stock_dict.get('price', 'N/A')),
                        timestamp=timestamp,
                        symbol=stock_dict.get('symbol', key)
                    ))
            
            # 6. Calculate metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            metrics = EnrichmentMetrics(
                processing_time_ms=processing_time,
                claims_processed=len(claims),
                data_sources_used=len(enriched_data.keys()),
                cache_hit_rate=self.cache_manager.get_hit_rate()
            )
            
            return EnrichmentResponse(
                original_content=request.content,
                enriched_content=enriched_content,
                claims=claims,
                data_points=data_points,
                data_sources=list(enriched_data.keys()),
                compliance_warnings=compliance_warnings,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Enrichment failed: {str(e)}")
            raise
    
    async def _gather_financial_data(self, claims: List[FinancialClaim], 
                                   enrichment_types: List[str]) -> Dict[str, Any]:
        """
        Parallel data gathering from multiple sources
        """
        data_tasks = []
        
        # Build data gathering tasks based on claims and requested types
        for claim in claims:
            logger.debug(f"Processing claim: {claim.text}, type: {claim.claim_type}, entities: {claim.entities}")
            
            if claim.claim_type.value == 'stock_price' and 'stock_data' in enrichment_types:
                if claim.entities:  # Check if entities list is not empty
                    logger.info(f"Adding stock data task for {claim.entities[0]}")
                data_tasks.append(
                        self.data_aggregator.get_stock_data(claim.entities[0])
                )
            
            if claim.claim_type.value == 'market_performance' and 'market_context' in enrichment_types:
                if claim.entities:  # Check if entities list is not empty
                    logger.info(f"Adding market data task for {claim.entities[0]}")
                data_tasks.append(
                        self.data_aggregator.get_market_data(claim.entities[0])
                )
        
        # Add general economic data if requested
        if 'economic_indicators' in enrichment_types:
            logger.info("Adding economic indicators task")
            data_tasks.append(
                self.data_aggregator.get_economic_indicators()
            )
        
        logger.info(f"Total data tasks to execute: {len(data_tasks)}")
        
        # Execute all data gathering in parallel
        results = await asyncio.gather(*data_tasks, return_exceptions=True)
        
        # Combine results into structured data
        enriched_data = {}
        for i, result in enumerate(results):
            logger.debug(f"Result {i}: {type(result)} - {result}")
            if isinstance(result, Exception):
                logger.error(f"Data gathering task {i} failed: {result}")
                continue
            elif isinstance(result, dict):
                enriched_data.update(result)
            elif result is not None and not isinstance(result, Exception):
                # Handle StockData objects with to_dict method
                try:
                    to_dict_method = getattr(result, 'to_dict', None)
                    if to_dict_method and callable(to_dict_method):
                        enriched_data[f"stock_{i}"] = to_dict_method()
                    else:
                        logger.debug(f"Result {i} has no to_dict method: {type(result)}")
                except (AttributeError, Exception) as e:
                    logger.warning(f"Failed to convert result {i} to dict: {type(result)} - {e}")
        
        logger.info(f"Final enriched data keys: {list(enriched_data.keys())}")
        return enriched_data
    
    async def _basic_compliance_check(self, claims: List[FinancialClaim]) -> List[str]:
        """
        Simple compliance warnings for obvious issues
        """
        warnings = []
        
        for claim in claims:
            # Check for guarantee language
            if any(word in claim.text.lower() for word in ['guaranteed', 'certain', 'definitely will']):
                warnings.append(f"Contains guarantee language: '{claim.text}'")
            
            # Check for investment advice without disclaimers
            if any(word in claim.text.lower() for word in ['should buy', 'recommended investment', 'buy now']):
                warnings.append("Investment advice without proper disclaimers detected")
        
        return warnings


def lambda_handler(event, context):
    """
    AWS Lambda entry point
    """
    try:
        # Parse request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        # Create request object
        request = EnrichmentRequest(
            content=body.get('content', ''),
            enrichment_types=body.get('enrichment_types', ['stock_data', 'economic_indicators']),
            include_compliance=body.get('include_compliance', False),
            format_style=body.get('format_style', 'enhanced')
        )
        
        if not request.content:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Content is required'})
            }
        
        # Process enrichment
        handler = FinancialEnrichmentHandler()
        
        # Run async enrichment
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(handler.enrich_content(request))
        finally:
            loop.close()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response.to_dict())
        }
        
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


# For local testing
async def test_enrichment():
    """Test function for local development"""
    handler = FinancialEnrichmentHandler()
    
    test_request = EnrichmentRequest(
        content="Apple (AAPL) is currently trading well and analysts expect good performance. The Fed's interest rate policy will impact tech stocks.",
        enrichment_types=['stock_data', 'economic_indicators'],
        include_compliance=True
    )
    
    response = await handler.enrich_content(test_request)
    print(json.dumps(response.to_dict(), indent=2))


if __name__ == "__main__":
    asyncio.run(test_enrichment())
