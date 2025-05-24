"""
Main Entry Point for FinSight
Provides CLI and API interfaces for financial fact-checking
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

# Import modules with fallback for different execution contexts
try:
    from config import config
    from models.financial_models import FinancialClaim, FactCheckResult
    from handlers.enhanced_fact_check_handler import EnhancedFinancialFactChecker
    from utils.llm_claim_extractor import LLMClaimExtractor
except ImportError:
    # Fallback for when run from different directory
    import importlib.util
    src_path = Path(__file__).parent
    
    # Load config
    spec = importlib.util.spec_from_file_location("config", src_path / "config.py")
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    config = config_module.config
    
    # Load other modules
    from models.financial_models import FinancialClaim, FactCheckResult
    from handlers.enhanced_fact_check_handler import EnhancedFinancialFactChecker  
    from utils.llm_claim_extractor import LLMClaimExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO if config.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinSightCLI:
    """Command-line interface for FinSight"""
    
    def __init__(self):
        self.fact_checker = EnhancedFinancialFactChecker(use_llm=True)
    
    def fact_check_text(self, text: str, use_llm: bool = True) -> Dict[str, Any]:
        """
        Fact-check financial claims in the provided text
        
        Args:
            text: Text to analyze for financial claims
            use_llm: Whether to use LLM for claim extraction
            
        Returns:
            Dictionary containing fact-check results
        """
        logger.info(f"Starting fact-check analysis (LLM: {use_llm})")
        
        # Extract claims
        if use_llm:
            claims = self.fact_checker.extract_financial_claims(text)
        else:
            extractor = LLMClaimExtractor(provider="regex")
            claims = extractor.extract_claims(text)
        
        logger.info(f"Extracted {len(claims)} claims for verification")
        
        # Verify each claim
        results = []
        for i, claim in enumerate(claims, 1):
            logger.info(f"Verifying claim {i}/{len(claims)}: {claim.claim_text[:50]}...")
            fact_check = self.fact_checker.verify_claim(claim)
            results.append({
                'claim': claim.claim_text,
                'entity': claim.entity,
                'claim_type': claim.claim_type.value,
                'value': claim.value,
                'is_accurate': fact_check.is_accurate,
                'confidence_score': fact_check.confidence_score,
                'explanation': fact_check.explanation,
                'sources': fact_check.sources,
                'risk_level': fact_check.risk_level.value
            })
        
        return {
            'total_claims': len(claims),
            'accurate_claims': sum(1 for r in results if r['is_accurate']),
            'results': results,
            'overall_accuracy': sum(r['confidence_score'] for r in results) / len(results) if results else 0,
            'high_risk_claims': sum(1 for r in results if r['risk_level'] in ['HIGH', 'CRITICAL'])
        }
    
    def fact_check_file(self, file_path: str, use_llm: bool = True) -> Dict[str, Any]:
        """
        Fact-check financial claims in a text file
        
        Args:
            file_path: Path to the text file
            use_llm: Whether to use LLM for claim extraction
            
        Returns:
            Dictionary containing fact-check results
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"Loaded {len(content)} characters from {file_path}")
            return self.fact_check_text(content, use_llm)
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return {'error': f'File not found: {file_path}'}
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return {'error': f'Error reading file: {str(e)}'}


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='FinSight - AI-Enhanced Financial Fact-Checking System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py -t "Microsoft's market cap is $3 trillion"
  python main.py -f earnings_report.txt
  python main.py -t "Apple revenue grew 15%" --no-llm
  python main.py --interactive
        """
    )
    
    parser.add_argument('-t', '--text', 
                       help='Text to fact-check')
    parser.add_argument('-f', '--file', 
                       help='File to fact-check')
    parser.add_argument('--no-llm', 
                       action='store_true',
                       help='Disable LLM and use regex-only extraction')
    parser.add_argument('--interactive', 
                       action='store_true',
                       help='Start interactive mode')
    parser.add_argument('--output', '-o',
                       help='Output file for results (JSON format)')
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    cli = FinSightCLI()
    use_llm = not args.no_llm
    
    if args.interactive:
        # Interactive mode
        print("🔍 FinSight Interactive Mode")
        print("Enter financial claims to fact-check (type 'quit' to exit):")
        
        while True:
            try:
                text = input("\n📝 Enter text: ").strip()
                if text.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not text:
                    continue
                
                print("🔄 Analyzing...")
                results = cli.fact_check_text(text, use_llm)
                
                print(f"\n📊 Results: {results['accurate_claims']}/{results['total_claims']} accurate")
                print(f"Overall confidence: {results['overall_accuracy']:.1%}")
                
                for i, result in enumerate(results['results'], 1):
                    status = "✅" if result['is_accurate'] else "❌"
                    print(f"{status} Claim {i}: {result['claim']}")
                    print(f"   Confidence: {result['confidence_score']:.1%}")
                    print(f"   Explanation: {result['explanation']}")
                
            except KeyboardInterrupt:
                break
        
        print("\n👋 Goodbye!")
        return
    
    # Process text or file
    results = None
    
    if args.text:
        results = cli.fact_check_text(args.text, use_llm)
    elif args.file:
        results = cli.fact_check_file(args.file, use_llm)
    else:
        parser.print_help()
        return
    
    # Output results
    if results:
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"✅ Results saved to {args.output}")
        else:
            print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
