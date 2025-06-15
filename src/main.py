"""
Main Entry Point for FinSight
Provides CLI interface for financial content processing
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import modules with error handling
try:
    from config import config
except ImportError:
    # Create minimal config if not available
    class Config:
        debug = True
    config = Config()

from models.financial_models import FinancialClaim
from utils.claim_extractor import ClaimExtractor
from integrations.data_aggregator import DataAggregator
from handlers.financial_enrichment_handler import FinancialEnrichmentHandler
from models.enrichment_models import EnrichmentRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO if config.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinSightCLI:
    """Command-line interface for FinSight"""
    
    def __init__(self):
        """Initialize the CLI with required components"""
        self.claim_extractor = ClaimExtractor()
        self.data_aggregator = DataAggregator()
        self.enrichment_handler = FinancialEnrichmentHandler()
    
    async def process_text(self, text: str) -> Dict[str, Any]:
        """Process text and extract financial claims"""
        try:
            # Extract claims
            claims = await self.claim_extractor.extract_claims(text)
            logger.info(f"Extracted {len(claims)} claims")
        
            # Create enrichment request
            request = EnrichmentRequest(
                content=text,
                enrichment_types=['stock_data'],
                include_compliance=True
            )
            
            # Enrich content
            response = await self.enrichment_handler.enrich_content(request)
        
        return {
            'total_claims': len(claims),
                'claims': [{'text': claim.text, 'type': claim.claim_type.value, 'entities': claim.entities} for claim in claims],
                'enriched_content': response.enriched_content,
                'processing_time_ms': response.metrics.processing_time_ms,
                'compliance_warnings': response.compliance_warnings
            }
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            return {
                'error': str(e),
                'total_claims': 0,
                'claims': [],
                'enriched_content': text,
                'processing_time_ms': 0,
                'compliance_warnings': []
            }
    
    async def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process claims from a file"""
        try:
            with open(file_path, 'r') as f:
                text = f.read()
            return await self.process_text(text)
        except Exception as e:
            return {
                'total_claims': 0,
                'claims': [],
                'enriched_content': '',
                'processing_time_ms': 0,
                'compliance_warnings': [],
                'error': str(e)
            }

    async def extract_claims(self, text: str) -> List[FinancialClaim]:
        """Extract financial claims from text"""
        try:
            return await self.claim_extractor.extract_claims(text)
        except Exception as e:
            logger.error(f"Error extracting claims: {str(e)}")
            return []


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="FinSight Financial Content Processor")
    parser.add_argument("-t", "--text", help="Text to process")
    parser.add_argument("-f", "--file", help="File to process")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--extract-only", action="store_true", help="Only extract claims, don't enrich")
    args = parser.parse_args()
    
    cli = FinSightCLI()
    
    if args.interactive:
        print("🔍 FinSight Interactive Mode")
        print("Enter financial content to process (type 'quit' to exit):")
        while True:
            text = input("\n📝 Enter text: ")
            if text.lower() == 'quit':
                break
        
            if args.extract_only:
                claims = await cli.extract_claims(text)
                print(f"Extracted {len(claims)} claims:")
                for i, claim in enumerate(claims, 1):
                    print(f"  {i}. {claim.text} (Type: {claim.claim_type.value})")
            else:
                results = await cli.process_text(text)
                print(f"Total claims: {results['total_claims']}")
                print(f"Processing time: {results['processing_time_ms']:.1f}ms")
                if results['compliance_warnings']:
                    print(f"⚠️  Compliance warnings: {len(results['compliance_warnings'])}")
                print(f"Enriched content:\n{results['enriched_content']}")
                
    elif args.text:
        if args.extract_only:
            claims = await cli.extract_claims(args.text)
            print(f"Extracted {len(claims)} claims:")
            for i, claim in enumerate(claims, 1):
                print(f"  {i}. {claim.text} (Type: {claim.claim_type.value})")
        else:
            results = await cli.process_text(args.text)
            print(f"Total claims: {results['total_claims']}")
            print(f"Processing time: {results['processing_time_ms']:.1f}ms")
            if results['compliance_warnings']:
                print(f"⚠️  Compliance warnings: {len(results['compliance_warnings'])}")
            print(f"Enriched content:\n{results['enriched_content']}")
            
    elif args.file:
        results = await cli.process_file(args.file)
        print(f"Total claims: {results['total_claims']}")
        print(f"Processing time: {results['processing_time_ms']:.1f}ms")
        if results['compliance_warnings']:
            print(f"⚠️  Compliance warnings: {len(results['compliance_warnings'])}")
        print(f"Enriched content:\n{results['enriched_content']}")
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
