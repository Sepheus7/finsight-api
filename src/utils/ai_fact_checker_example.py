"""
Enhanced fact-checking with AI models - Example implementation
"""

import openai
from typing import List, Dict, Any

class AIEnhancedFactChecker:
    def __init__(self, openai_api_key: str = None):
        if openai_api_key:
            openai.api_key = openai_api_key
        self.traditional_checker = FinancialFactChecker()
    
    async def extract_claims_with_ai(self, text: str) -> List[str]:
        """Use AI to extract more sophisticated financial claims"""
        
        prompt = f"""
        Extract all factual financial claims from this text that can be verified:
        
        Text: "{text}"
        
        Return only specific, verifiable claims like:
        - Stock prices and valuations
        - Financial ratios and metrics  
        - Economic indicators
        - Market performance data
        - Company financial data
        
        Format as a JSON list of strings.
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            import json
            claims = json.loads(response.choices[0].message.content)
            return claims
        except Exception as e:
            print(f"AI claim extraction failed: {e}")
            # Fallback to traditional method
            return self.traditional_checker.extract_financial_claims(text)
    
    async def verify_claim_with_ai(self, claim: str, market_data: Dict) -> FactCheckResult:
        """Use AI to verify complex financial claims"""
        
        prompt = f"""
        Verify this financial claim against the provided market data:
        
        Claim: "{claim}"
        Market Data: {market_data}
        
        Analyze:
        1. Is the claim factually accurate?
        2. What's your confidence level (0-1)?
        3. Provide explanation
        
        Return JSON format:
        {{
            "verified": true/false,
            "confidence": 0.0-1.0,
            "explanation": "detailed explanation"
        }}
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return FactCheckResult(
                claim=claim,
                verified=result["verified"],
                confidence=result["confidence"],
                source="AI + Market Data",
                explanation=result["explanation"]
            )
        except Exception as e:
            print(f"AI verification failed: {e}")
            # Fallback to traditional method
            return self.traditional_checker.verify_claim(claim)
