# 🤖 Real LLM Integration Guide

## Overview
This guide shows how to replace the simulated AI evaluation with actual LLM integration in the FinSight system.

## Current State vs. Target State

### **Current (Simulated AI)**
```python
def simulate_ai_evaluation(content, fact_checks):
    """Simulated AI evaluation for demo purposes"""
    return {
        'explanation': 'Simulated AI analysis...',
        'quality_assessment': 'Content quality assessment...',
        'confidence_multiplier': 1.2,
        'financial_risk': 'medium',
        'misinformation_risk': 'low'
    }
```

### **Target (Real LLM Integration)**
```python
import openai  # or anthropic

def call_real_llm(content, fact_checks):
    """Real LLM evaluation using OpenAI or Anthropic"""
    client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    
    prompt = build_financial_analysis_prompt(content, fact_checks)
    
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": FINANCIAL_ANALYST_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1000
    )
    
    return parse_llm_response(response.choices[0].message.content)
```

## Implementation Steps

### Step 1: Update Dependencies
```bash
cd /Users/romainboluda/Documents/PersonalProjects/FinSight/aws-serverless
pip install openai==1.35.0  # or anthropic==0.25.0
```

### Step 2: Environment Configuration
```bash
# Add to your environment variables
export OPENAI_API_KEY="your-openai-api-key"
# OR
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### Step 3: Update ai_evaluator_handler.py

Replace the simulation function with:

```python
import openai
import json
from typing import Dict, Any, List

class RealAIEvaluator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.system_prompt = """You are a financial fact-checking expert specializing in accuracy assessment.
        
        Analyze the provided content and fact-checking results to provide:
        1. Detailed explanation of accuracy and reliability
        2. Overall quality assessment 
        3. Confidence multiplier (0.5-2.0)
        4. Financial risk level (low/medium/high)
        5. Misinformation risk level (low/medium/high)
        
        Focus on financial accuracy, regulatory compliance, and potential market impact."""
    
    def evaluate_content(self, content: str, fact_checks: List[Dict]) -> Dict[str, Any]:
        """Evaluate content using real LLM"""
        try:
            prompt = self._build_evaluation_prompt(content, fact_checks)
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            return self._parse_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"LLM evaluation failed: {str(e)}")
            return self._fallback_evaluation(content, fact_checks)
    
    def _build_evaluation_prompt(self, content: str, fact_checks: List[Dict]) -> str:
        """Build structured prompt for LLM evaluation"""
        fact_check_summary = "\n".join([
            f"- {fc.get('claim', '')}: {fc.get('explanation', '')} (Confidence: {fc.get('confidence', 0):.1f})"
            for fc in fact_checks
        ])
        
        return f"""
        Please analyze this financial content and provide a JSON response:
        
        **Content to Analyze:**
        {content}
        
        **Fact-Checking Results:**
        {fact_check_summary}
        
        **Required JSON Response Format:**
        {{
            "explanation": "Detailed analysis of content accuracy and reliability",
            "quality_assessment": "Overall assessment of content quality and trustworthiness", 
            "confidence_multiplier": 1.2,
            "financial_risk": "low|medium|high",
            "misinformation_risk": "low|medium|high"
        }}
        """
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM JSON response"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            return self._extract_from_text(response_text)
    
    def _fallback_evaluation(self, content: str, fact_checks: List[Dict]) -> Dict[str, Any]:
        """Fallback evaluation if LLM fails"""
        avg_confidence = sum(fc.get('confidence', 0) for fc in fact_checks) / max(len(fact_checks), 1)
        
        return {
            'explanation': 'LLM evaluation unavailable. Based on fact-checking results only.',
            'quality_assessment': f'Content has {len(fact_checks)} fact-checked claims with average confidence {avg_confidence:.1f}',
            'confidence_multiplier': min(max(avg_confidence * 2, 0.5), 2.0),
            'financial_risk': 'medium' if avg_confidence < 0.7 else 'low',
            'misinformation_risk': 'high' if avg_confidence < 0.5 else 'medium'
        }
```

### Step 4: Update Lambda Environment Variables

In your AWS Lambda configuration:
```bash
# Environment Variables
OPENAI_API_KEY=your-key-here
# OR
ANTHROPIC_API_KEY=your-key-here
```

### Step 5: Update requirements.txt
```
openai==1.35.0
# OR
anthropic==0.25.0
```

## Alternative: Anthropic Claude Integration

If you prefer Claude over GPT-4:

```python
import anthropic

class ClaudeEvaluator:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
    
    def evaluate_content(self, content: str, fact_checks: List[Dict]) -> Dict[str, Any]:
        prompt = self._build_evaluation_prompt(content, fact_checks)
        
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return self._parse_response(response.content[0].text)
```

## Testing the Integration

### Test Script
```python
# test_real_llm.py
from src.ai_evaluator_handler import RealAIEvaluator

def test_real_llm():
    evaluator = RealAIEvaluator()
    
    content = "Apple Inc. (AAPL) stock price is $185.50"
    fact_checks = [
        {
            'claim': 'AAPL is currently trading at $185.50',
            'verified': False,
            'confidence': 0.9,
            'explanation': 'Current price $195.27 differs from claimed $185.50'
        }
    ]
    
    result = evaluator.evaluate_content(content, fact_checks)
    print(f"LLM Evaluation: {result}")

if __name__ == "__main__":
    test_real_llm()
```

## Cost Considerations

### OpenAI GPT-4 Turbo Pricing (as of 2024)
- **Input**: $0.01 per 1K tokens
- **Output**: $0.03 per 1K tokens
- **Estimated Cost per Evaluation**: ~$0.001-0.005
- **Monthly Cost (1000 evaluations)**: ~$1-5

### Anthropic Claude Pricing
- **Input**: $0.015 per 1K tokens  
- **Output**: $0.075 per 1K tokens
- **Estimated Cost per Evaluation**: ~$0.002-0.008
- **Monthly Cost (1000 evaluations)**: ~$2-8

## Performance Expectations

### With Real LLM Integration:
- **Processing Time**: +2-4 seconds for LLM call
- **Total Time**: ~18-20 seconds (vs current 16.5s)
- **Accuracy**: Significantly improved content analysis
- **Consistency**: More reliable quality assessments

### Optimization Options:
1. **Async Processing**: Call LLM in parallel with fact-checking
2. **Response Caching**: Cache similar content evaluations
3. **Model Selection**: Use faster models for less critical evaluations

## Deployment Steps

1. **Test Locally**: Verify LLM integration works with your API keys
2. **Update Lambda**: Deploy updated code with LLM dependencies
3. **Environment Variables**: Set API keys in Lambda configuration
4. **Monitor**: Watch for API rate limits and costs
5. **Gradual Rollout**: Start with subset of traffic

## Monitoring & Alerts

```python
# Add monitoring for LLM usage
import boto3
cloudwatch = boto3.client('cloudwatch')

def log_llm_metrics(response_time, token_usage, cost):
    cloudwatch.put_metric_data(
        Namespace='FinSight/LLM',
        MetricData=[
            {
                'MetricName': 'ResponseTime',
                'Value': response_time,
                'Unit': 'Seconds'
            },
            {
                'MetricName': 'TokenUsage', 
                'Value': token_usage,
                'Unit': 'Count'
            },
            {
                'MetricName': 'Cost',
                'Value': cost,
                'Unit': 'None'
            }
        ]
    )
```

This integration will transform your system from a sophisticated demo into a production-ready AI-powered financial fact-checking service!
