#!/usr/bin/env python3
"""
Lightweight Financial Fact Checker for AWS Lambda
Uses direct Yahoo Finance API calls and Bedrock LLM for enhanced claim extraction
"""

import json
import logging
import os
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
import re
import boto3

logger = logging.getLogger(__name__)


class BedrockLLMClient:
    """Lightweight Bedrock client for claim extraction"""
    
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.primary_model = "anthropic.claude-3-haiku-20240307-v1:0"
        self.fallback_model = "amazon.titan-text-express-v1"
    
    def extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """Extract financial claims using Bedrock LLM"""
        try:
            prompt = f"""You are a financial fact-checking AI. Extract specific, verifiable financial claims from this text.

Text: "{text}"

Extract claims in this JSON format:
[
  {{
    "claim": "exact text of the claim",
    "type": "stock_price|market_cap|performance|valuation",
    "symbol": "stock symbol if mentioned",
    "value": "specific number/percentage if mentioned",
    "timeframe": "time period if mentioned"
  }}
]

Only extract factual claims that can be verified with financial data. Return empty array if no verifiable claims found."""

            # Try primary model first
            try:
                response = self._invoke_model(self.primary_model, prompt)
                return self._parse_llm_response(response)
            except Exception as e:
                logger.warning(f"Primary model failed: {e}, trying fallback")
                response = self._invoke_model(self.fallback_model, prompt)
                return self._parse_llm_response(response)
                
        except Exception as e:
            logger.error(f"Bedrock extraction failed: {e}, falling back to regex")
            return []
    
    def _invoke_model(self, model_id: str, prompt: str) -> str:
        """Invoke a Bedrock model"""
        if "claude" in model_id:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
        else:  # Titan
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 1000,
                    "temperature": 0.1
                }
            }
        
        response = self.bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(body)
        )
        
        result = json.loads(response['body'].read())
        
        if "claude" in model_id:
            return result['content'][0]['text']
        else:
            return result['results'][0]['outputText']
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract claims"""
        try:
            # Look for JSON array in the response
            import re
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                claims_data = json.loads(json_match.group())
                return claims_data
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
        
        return []


class LightweightFinancialChecker:
    """Lightweight financial fact checker for Lambda"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # Initialize Bedrock client if in AWS environment
        self.bedrock_client = None
        try:
            if os.environ.get('AWS_EXECUTION_ENV'):  # Running in Lambda
                self.bedrock_client = BedrockLLMClient()
                logger.info("Bedrock LLM client initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Bedrock client: {e}")
    
    def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current stock price using Yahoo Finance API directly"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                chart = data.get('chart', {})
                result = chart.get('result', [])
                
                if result:
                    meta = result[0].get('meta', {})
                    return {
                        'symbol': symbol,
                        'price': meta.get('regularMarketPrice'),
                        'currency': meta.get('currency', 'USD'),
                        'market_cap': meta.get('marketCap'),
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
        
        return None
    
    def extract_financial_claims(self, text: str) -> List[Dict[str, Any]]:
        """Extract financial claims using Bedrock LLM or regex fallback"""
        
        # Try Bedrock first if available
        if self.bedrock_client:
            try:
                bedrock_claims = self.bedrock_client.extract_claims(text)
                if bedrock_claims:
                    logger.info(f"Extracted {len(bedrock_claims)} claims using Bedrock")
                    return bedrock_claims
            except Exception as e:
                logger.error(f"Bedrock claim extraction failed: {e}")
        
        # Fallback to regex extraction
        logger.info("Using regex fallback for claim extraction")
        return self._extract_claims_regex(text)
    
    def _extract_claims_regex(self, text: str) -> List[Dict[str, Any]]:
        """Extract financial claims using regex patterns"""
        claims = []
        
        # Price patterns
        price_pattern = r'(\$[\d,]+\.?\d*)\s*(?:trillion|billion|million|thousand|k|b|t)?'
        stock_pattern = r'([A-Z]{1,5})\s+(?:stock|shares?|price)'
        market_cap_pattern = r'market\s+cap(?:italization)?\s+(?:is|of)?\s*(\$[\d,]+\.?\d*)\s*(trillion|billion|million)'
        
        # Find market cap claims
        for match in re.finditer(market_cap_pattern, text, re.IGNORECASE):
            amount = match.group(1)
            unit = match.group(2)
            claims.append({
                'claim': match.group(0),
                'type': 'market_cap',
                'value': amount,
                'unit': unit,
                'symbol': None
            })
        
        # Find stock mentions
        for match in re.finditer(stock_pattern, text, re.IGNORECASE):
            symbol = match.group(1)
            claims.append({
                'claim': match.group(0),
                'type': 'stock_price',
                'symbol': symbol,
                'value': None
            })
        
        return claims
    
    def verify_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a financial claim"""
        result = {
            'claim': claim.get('claim', ''),
            'type': claim.get('type', 'unknown'),
            'status': 'unknown',
            'confidence': 0.0,
            'details': {}
        }
        
        if claim['type'] == 'stock_price':
            symbol = claim.get('symbol')
            if symbol:
                stock_data = self.get_stock_price(symbol)
                if stock_data:
                    result['status'] = 'verified'
                    result['confidence'] = 0.95
                    result['details'] = {
                        'current_price': stock_data['price'],
                        'currency': stock_data['currency'],
                        'symbol': symbol
                    }
                else:
                    result['status'] = 'unverifiable'
                    result['confidence'] = 0.0
        
        elif claim['type'] == 'market_cap':
            # For market cap, we'd need to identify the company first
            result['status'] = 'partial'
            result['confidence'] = 0.5
            result['details'] = {
                'note': 'Market cap claims require company identification'
            }
        
        return result


def lambda_handler(event, context):
    """AWS Lambda handler for lightweight fact checking"""
    try:
        # Parse request body
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        
        text = body.get('text', '')
        if not text:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Text parameter is required'
                })
            }
        
        # Initialize checker
        checker = LightweightFinancialChecker()
        
        # Extract and verify claims
        start_time = datetime.now()
        claims = checker.extract_financial_claims(text)
        verified_claims = []
        
        for claim in claims:
            verified_claim = checker.verify_claim(claim)
            verified_claims.append(verified_claim)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Determine provider used
        provider = "bedrock_llm" if checker.bedrock_client else "lightweight_regex"
        
        # Prepare response
        response_data = {
            'text': text,
            'claims': verified_claims,
            'total_claims': len(verified_claims),
            'provider_used': provider,
            'processing_time_ms': round(processing_time, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }


if __name__ == "__main__":
    # Test locally
    test_event = {
        'body': json.dumps({
            'text': "Apple's market cap is $3 trillion. AAPL stock is trading well. Tesla shares have increased 200% this year."
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))
