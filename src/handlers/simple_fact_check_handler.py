"""
Simple fact-check handler with LLM-powered claim extraction
Combines intelligent LLM extraction with reliable simple verification
"""

import json
import logging
import re
import asyncio
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import LLM claim extractor with fallback
try:
    from utils.llm_claim_extractor import LLMClaimExtractor
    LLM_AVAILABLE = True
except ImportError:
    LLMClaimExtractor = None
    LLM_AVAILABLE = False
    logger.warning("LLM claim extractor not available, falling back to regex")

async def lambda_handler(event, context):
    """
    Simple Lambda handler for fact-checking financial claims with LLM extraction
    """
    try:
        # Parse API Gateway event format
        if 'body' in event:
            # API Gateway event
            body = json.loads(event['body']) if event['body'] else {}
            content = body.get('advice', body.get('content', ''))
            use_llm = body.get('enable_llm', body.get('use_llm', True))
            request_id = body.get('request_id', getattr(context, 'aws_request_id', 'test-request-id'))
        else:
            # Direct Lambda invocation
            content = event.get('content', '')
            request_id = event.get('request_id', getattr(context, 'aws_request_id', 'test-request-id'))
            use_llm = event.get('use_llm', True)

        logger.info(f"Processing simple fact check for request {request_id} (LLM: {use_llm and LLM_AVAILABLE})")

        # Extract claims using LLM or fallback to regex
        if use_llm and LLM_AVAILABLE:
            claims = await extract_claims_with_llm(content)
        else:
            claims = extract_financial_claims_regex(content)
        
        logger.info(f"Extracted {len(claims)} claims")

        response_data = {
            'fact_checks': claims,
            'claims_processed': len(claims),
            'request_id': request_id,
            'llm_enabled': use_llm and LLM_AVAILABLE,
            'extraction_method': 'llm' if (use_llm and LLM_AVAILABLE) else 'regex',
            'note': 'LLM-powered extraction with simple verification' if (use_llm and LLM_AVAILABLE) else 'Regex-based extraction with simple verification'
        }

        # Return properly formatted API Gateway response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': json.dumps(response_data)
        }

    except Exception as e:
        logger.error(f"Simple fact checking failed: {str(e)}")
        # Return properly formatted error response
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'fact_checks': [],
                'claims_processed': 0,
                'llm_enabled': False,
                'extraction_method': 'error'
            })
        }


async def extract_claims_with_llm(content: str) -> List[Dict[str, Any]]:
    """
    Extract financial claims using LLM and convert to simple format
    """
    try:
        # Initialize LLM extractor
        if not LLM_AVAILABLE or LLMClaimExtractor is None:
            raise ImportError("LLM extractor not available")
        extractor = LLMClaimExtractor(provider="auto")
        
        # Extract claims using LLM
        financial_claims = await extractor.extract_claims(content)
        
        # Convert FinancialClaim objects to simple dictionary format
        claims = []
        processed_entities = set()
        
        for claim in financial_claims:
            # Get primary entity and value
            entity = claim.entities[0] if claim.entities else "Unknown"
            value = claim.values[0] if claim.values else ""
            
            # Create unique key to avoid duplicates
            entity_key = f"{entity.lower()}_{claim.claim_type.value}"
            
            if entity_key not in processed_entities:
                processed_entities.add(entity_key)
                
                # Determine verification status and confidence
                verified = False
                confidence = claim.confidence
                explanation = f"LLM extracted {claim.claim_type.value} claim for {entity}"
                warning = None
                
                # Add warnings for unverifiable claims
                if claim.claim_type.value in ['prediction', 'opinion']:
                    confidence = min(confidence, 0.3)
                    warning = "This appears to be a prediction or opinion rather than a verifiable fact."
                    explanation += " - Cannot be verified as it's speculative."
                elif 'guaranteed' in claim.text.lower() or 'definitely' in claim.text.lower():
                    confidence = min(confidence, 0.2)
                    warning = "Contains guarantee language which is typically not verifiable."
                
                claim_dict = {
                    'claim': claim.text,
                    'claim_type': claim.claim_type.value,
                    'entities': [entity],
                    'values': [value] if value else [],
                    'verified': verified,
                    'confidence': confidence,
                    'source': 'llm_extraction',
                    'explanation': explanation,
                    'actual_value': None,
                    'discrepancy': None
                }
                
                if warning:
                    claim_dict['warning'] = warning
                
                claims.append(claim_dict)
        
        logger.info(f"LLM extracted {len(claims)} unique claims")
        return claims
        
    except Exception as e:
        logger.error(f"LLM extraction failed: {str(e)}, falling back to regex")
        return extract_financial_claims_regex(content)


def extract_financial_claims_regex(content: str) -> List[Dict[str, Any]]:
    """
    Fallback regex-based claim extraction
    """
    claims = []
    processed_entities = set()  # Track processed entities to avoid duplicates
    
    # Enhanced stock price patterns
    stock_patterns = [
        # Pattern 1: "Apple stock is trading at $150"
        r'\b(Apple|Microsoft|Google|Tesla|Amazon|AAPL|MSFT|GOOGL|TSLA|AMZN)\s+stock\s+is\s+(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d+)?)',
        # Pattern 2: "AAPL is trading at $150"  
        r'\b([A-Z]{2,5})\s+is\s+(?:currently\s+)?trading\s+at\s+\$?(\d+(?:\.\d+)?)',
        # Pattern 3: "Apple stock $150"
        r'\b(Apple|Microsoft|Google|Tesla|Amazon)\s+stock\s+\$?(\d+(?:\.\d+)?)',
        # Pattern 4: "AAPL at $150" or "Apple at $150"
        r'\b(Apple|Microsoft|Google|Tesla|Amazon|AAPL|MSFT|GOOGL|TSLA|AMZN)\s+(?:at|for)\s+\$?(\d+(?:\.\d+)?)',
        # Pattern 5: "$150 per share for Apple"
        r'\$?(\d+(?:\.\d+)?)\s+per\s+share\s+(?:for\s+)?(Apple|Microsoft|Google|Tesla|Amazon|AAPL|MSFT|GOOGL|TSLA|AMZN)',
    ]
    
    # Process stock price patterns
    for pattern in stock_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            if len(match.groups()) >= 2:
                # Handle different group orders
                if pattern.startswith(r'\$?(\d+'):  # Price first patterns
                    price = match.group(1)
                    entity = match.group(2)
                else:  # Entity first patterns
                    entity = match.group(1)
                    price = match.group(2)
                
                entity_key = entity.lower()
                if entity_key not in processed_entities:
                    processed_entities.add(entity_key)
                    
                    claims.append({
                        'claim': match.group(0),
                        'claim_type': 'stock_price',
                        'entities': [entity],
                        'values': [price],
                        'verified': False,
                        'confidence': 0.8,
                        'source': 'regex_extraction',
                        'explanation': f'Extracted stock price claim for {entity}: ${price}',
                        'actual_value': None,
                        'discrepancy': None
                    })
    
    # Market cap patterns
    mcap_patterns = [
        r'\b(Apple|Microsoft|Google|Tesla|Amazon|AAPL|MSFT|GOOGL|TSLA|AMZN)\s+(?:has\s+a\s+)?market\s+cap(?:italization)?\s+of\s+\$?(\d+(?:\.\d+)?)\s*(billion|trillion|million)?',
        r'market\s+cap(?:italization)?\s+(?:of\s+)?(Apple|Microsoft|Google|Tesla|Amazon|AAPL|MSFT|GOOGL|TSLA|AMZN)\s+is\s+\$?(\d+(?:\.\d+)?)\s*(billion|trillion|million)?'
    ]
    
    for pattern in mcap_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            groups = match.groups()
            if len(groups) >= 2:
                entity = groups[0] if groups[0] else groups[1]
                value = groups[1] if groups[0] else groups[2]
                unit = groups[2] if len(groups) > 2 and groups[2] else 'billion'
                
                entity_key = f"{entity.lower()}_mcap"
                if entity_key not in processed_entities:
                    processed_entities.add(entity_key)
                    
                    claims.append({
                        'claim': match.group(0),
                        'claim_type': 'market_cap',
                        'entities': [entity],
                        'values': [f"{value} {unit}"],
                        'verified': False,
                        'confidence': 0.7,
                        'source': 'regex_extraction',
                        'explanation': f'Extracted market cap claim for {entity}: ${value} {unit}',
                        'actual_value': None,
                        'discrepancy': None
                    })
    
    # Performance/prediction patterns (flagged as unverifiable)
    prediction_patterns = [
        r'\b(Apple|Microsoft|Google|Tesla|Amazon|AAPL|MSFT|GOOGL|TSLA|AMZN)\s+(?:stock\s+)?(?:will|is\s+guaranteed\s+to|definitely\s+will)\s+(?:increase|rise|go\s+up|double|triple)',
        r'\b(Apple|Microsoft|Google|Tesla|Amazon|AAPL|MSFT|GOOGL|TSLA|AMZN)\s+(?:is\s+)?guaranteed\s+to\s+(?:make\s+money|be\s+profitable)',
        r'(?:definitely|guaranteed|certain)\s+(?:that\s+)?(Apple|Microsoft|Google|Tesla|Amazon|AAPL|MSFT|GOOGL|TSLA|AMZN)'
    ]
    
    for pattern in prediction_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            entity = match.group(1)
            entity_key = f"{entity.lower()}_prediction"
            
            if entity_key not in processed_entities:
                processed_entities.add(entity_key)
                
                claims.append({
                    'claim': match.group(0),
                    'claim_type': 'prediction',
                    'entities': [entity],
                    'values': [],
                    'verified': False,
                    'confidence': 0.1,  # Low confidence for predictions
                    'source': 'regex_extraction',
                    'explanation': f'Detected unverifiable prediction about {entity}. Investment predictions cannot be fact-checked.',
                    'actual_value': None,
                    'discrepancy': None,
                    'warning': 'This appears to be a speculative prediction rather than a verifiable fact.'
                })
    
    return claims


# For local testing
if __name__ == "__main__":
    import asyncio
    
    async def test_handler():
        test_content = """
        Apple (AAPL) stock is trading at $195, up 2.3% today. Tesla (TSLA) is also performing well.
        Microsoft has a market cap of $2.8 trillion. Apple stock will definitely increase by 50% next month.
        Google's revenue grew significantly last quarter.
        """
        
        print("Testing LLM extraction:")
        if LLM_AVAILABLE:
            claims = await extract_claims_with_llm(test_content)
        else:
            print("LLM not available, using regex:")
            claims = extract_financial_claims_regex(test_content)
        
        print(f"Extracted {len(claims)} claims:")
        for i, claim in enumerate(claims, 1):
            print(f"{i}. {claim['claim_type']}: {claim['claim']}")
            print(f"   Entity: {claim['entities'][0] if claim['entities'] else 'N/A'}")
            print(f"   Values: {claim['values']}")
            print(f"   Confidence: {claim['confidence']}")
            print(f"   Source: {claim['source']}")
            if 'warning' in claim:
                print(f"   ⚠️  {claim['warning']}")
            print()
    
    asyncio.run(test_handler()) 