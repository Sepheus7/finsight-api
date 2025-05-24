"""
AI Evaluator Handler for AWS Lambda
Uses local LLM to intelligently evaluate financial content quality and context relevance
"""

import json
import os
import boto3
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL', 'http://localhost:11434')
DEFAULT_MODEL = os.environ.get('LLM_MODEL', 'llama3.1:8b')  # or mistral, phi3, etc.

def lambda_handler(event, context):
    """
    Lambda handler for AI-powered content evaluation
    """
    try:
        content = event.get('content', '')
        fact_checks = event.get('fact_checks', [])
        context_additions = event.get('context_additions', [])
        compliance_flags = event.get('compliance_flags', [])
        request_id = event.get('request_id', context.aws_request_id)

        logger.info(f"Processing AI evaluation for request {request_id}")

        evaluator = AIContentEvaluator()
        
        # Perform intelligent evaluation
        evaluation_result = evaluator.evaluate_financial_content(
            content=content,
            fact_checks=fact_checks,
            context_additions=context_additions,
            compliance_flags=compliance_flags
        )

        response_data = {
            'ai_evaluation': evaluation_result,
            'request_id': request_id,
            'model_used': DEFAULT_MODEL,
            'evaluation_timestamp': datetime.utcnow().isoformat()
        }

        return response_data

    except Exception as e:
        logger.error(f"Error in AI evaluation: {str(e)}")
        return {
            'error': str(e),
            'ai_evaluation': {
                'overall_score': 0.5,
                'quality_assessment': 'Error occurred during AI evaluation',
                'improvement_suggestions': ['Unable to process due to technical error'],
                'confidence_adjustment': 1.0,
                'explanation': f'AI evaluation failed: {str(e)}'
            },
            'request_id': event.get('request_id', context.aws_request_id)
        }


class AIContentEvaluator:
    """AI-powered financial content evaluator using local LLM"""
    
    def __init__(self):
        self.model = DEFAULT_MODEL
        self.api_url = OLLAMA_API_URL
        
    def evaluate_financial_content(self, content: str, fact_checks: List[Dict], 
                                 context_additions: List[Dict], 
                                 compliance_flags: List[str]) -> Dict[str, Any]:
        """
        Comprehensive AI evaluation of financial content
        """
        try:
            # Prepare evaluation prompt
            evaluation_prompt = self._create_evaluation_prompt(
                content, fact_checks, context_additions, compliance_flags
            )
            
            # Get AI evaluation
            ai_response = self._query_llm(evaluation_prompt)
            
            # Parse and structure the response
            evaluation = self._parse_ai_evaluation(ai_response)
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error in AI evaluation: {str(e)}")
            return self._fallback_evaluation()
    
    def _create_evaluation_prompt(self, content: str, fact_checks: List[Dict], 
                                context_additions: List[Dict], 
                                compliance_flags: List[str]) -> str:
        """Create comprehensive evaluation prompt for the LLM"""
        
        prompt = f"""
You are a financial content quality expert. Evaluate the following financial AI-generated content and its enhancements.

ORIGINAL CONTENT:
{content}

FACT CHECK RESULTS:
{json.dumps(fact_checks, indent=2) if fact_checks else "No fact checks performed"}

CONTEXT ADDITIONS:
{json.dumps(context_additions, indent=2) if context_additions else "No context added"}

COMPLIANCE FLAGS:
{json.dumps(compliance_flags, indent=2) if compliance_flags else "No compliance issues"}

Please provide a comprehensive evaluation in the following JSON format:

{{
  "overall_score": <float 0.0-1.0>,
  "quality_assessment": "<detailed assessment of content quality>",
  "improvement_suggestions": [
    "<specific suggestion 1>",
    "<specific suggestion 2>",
    "<specific suggestion 3>"
  ],
  "confidence_adjustments": {{
    "fact_check_confidence": <float 0.5-2.0>,
    "context_relevance": <float 0.0-1.0>,
    "compliance_severity": <float 0.0-1.0>
  }},
  "strengths": [
    "<strength 1>",
    "<strength 2>"
  ],
  "weaknesses": [
    "<weakness 1>",
    "<weakness 2>"
  ],
  "risk_assessment": {{
    "financial_risk": "<low|medium|high>",
    "regulatory_risk": "<low|medium|high>",
    "misinformation_risk": "<low|medium|high>"
  }},
  "explanation": "<detailed explanation of the evaluation reasoning>"
}}

Evaluation Criteria:
1. Accuracy of financial information
2. Appropriateness of investment advice
3. Regulatory compliance
4. Clarity and usefulness of context
5. Overall trustworthiness for end users
6. Risk of financial harm

Respond only with valid JSON.
"""
        return prompt
    
    def _query_llm(self, prompt: str) -> str:
        """Query the local LLM API (Ollama)"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent, factual evaluation
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": 1000  # Allow detailed responses
                }
            }
            
            response = requests.post(
                f"{self.api_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                logger.error(f"LLM API error: {response.status_code} - {response.text}")
                raise Exception(f"LLM API returned status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error querying LLM: {str(e)}")
            raise Exception(f"Failed to connect to LLM API: {str(e)}")
    
    def _parse_ai_evaluation(self, ai_response: str) -> Dict[str, Any]:
        """Parse and validate AI evaluation response"""
        try:
            # Try to extract JSON from the response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                evaluation = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['overall_score', 'quality_assessment', 'improvement_suggestions']
                for field in required_fields:
                    if field not in evaluation:
                        logger.warning(f"Missing required field: {field}")
                        evaluation[field] = self._get_default_value(field)
                
                # Ensure score is in valid range
                evaluation['overall_score'] = max(0.0, min(1.0, float(evaluation['overall_score'])))
                
                return evaluation
            else:
                logger.error("No valid JSON found in AI response")
                return self._fallback_evaluation()
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return self._fallback_evaluation()
        except Exception as e:
            logger.error(f"Error parsing AI evaluation: {str(e)}")
            return self._fallback_evaluation()
    
    def _get_default_value(self, field: str) -> Any:
        """Get default values for missing fields"""
        defaults = {
            'overall_score': 0.5,
            'quality_assessment': 'AI evaluation incomplete',
            'improvement_suggestions': ['Unable to generate specific suggestions'],
            'confidence_adjustments': {
                'fact_check_confidence': 1.0,
                'context_relevance': 0.5,
                'compliance_severity': 0.5
            },
            'strengths': ['Content evaluation incomplete'],
            'weaknesses': ['Unable to identify specific weaknesses'],
            'risk_assessment': {
                'financial_risk': 'medium',
                'regulatory_risk': 'medium',
                'misinformation_risk': 'medium'
            },
            'explanation': 'AI evaluation was incomplete or failed'
        }
        return defaults.get(field, 'N/A')
    
    def _fallback_evaluation(self) -> Dict[str, Any]:
        """Fallback evaluation when AI evaluation fails"""
        return {
            'overall_score': 0.5,
            'quality_assessment': 'AI evaluation unavailable - using fallback assessment',
            'improvement_suggestions': [
                'Enable AI evaluation service for detailed analysis',
                'Review content manually for quality assurance',
                'Verify all financial claims independently'
            ],
            'confidence_adjustments': {
                'fact_check_confidence': 1.0,
                'context_relevance': 0.5,
                'compliance_severity': 0.8
            },
            'strengths': ['Content provided for evaluation'],
            'weaknesses': ['Unable to perform detailed AI analysis'],
            'risk_assessment': {
                'financial_risk': 'medium',
                'regulatory_risk': 'medium',
                'misinformation_risk': 'medium'
            },
            'explanation': 'AI evaluation service unavailable, using conservative fallback assessment'
        }


def test_ai_evaluator():
    """Test function for local development"""
    test_event = {
        'content': 'AAPL stock is currently trading at $150 and I recommend buying it now for guaranteed returns.',
        'fact_checks': [
            {
                'claim': 'AAPL stock is currently trading at $150',
                'verified': False,
                'confidence': 0.3,
                'source': 'Unable to verify'
            }
        ],
        'context_additions': [
            {
                'type': 'market_context',
                'content': 'Technology stocks have shown volatility recently',
                'relevance_score': 0.8
            }
        ],
        'compliance_flags': [
            'Investment advice provided without proper disclaimers',
            'Claims of guaranteed returns are prohibited'
        ]
    }
    
    # Mock context
    class MockContext:
        aws_request_id = 'test-request-123'
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    test_ai_evaluator()
