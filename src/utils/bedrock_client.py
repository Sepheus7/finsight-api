"""
AWS Bedrock LLM Client for FinSight
Provides integration with Amazon Bedrock for LLM operations with cost optimization and fallback models
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

logger = logging.getLogger(__name__)


class BedrockLLMClient:
    """Client for AWS Bedrock LLM operations with automatic fallback to cheaper models"""
    
    def __init__(self, region: str = "us-east-1", model_id: str = "anthropic.claude-3-haiku-20240307-v1:0", fallback_model_id: str = "amazon.titan-text-express-v1"):
        """
        Initialize Bedrock client
        
        Args:
            region: AWS region for Bedrock service
            model_id: Primary Bedrock model identifier
            fallback_model_id: Cheaper fallback model identifier
        """
        self.region = region
        self.model_id = model_id
        self.fallback_model_id = fallback_model_id
        self.client = None
        self.using_fallback = False
        
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for Bedrock integration. Install with: pip install boto3")
        
        try:
            # Initialize Bedrock Runtime client
            self.client = boto3.client(
                service_name='bedrock-runtime',
                region_name=region
            )
            
            # Test the connection by trying to list foundation models
            bedrock_client = boto3.client(
                service_name='bedrock',
                region_name=region
            )
            
            # Verify model availability
            try:
                response = bedrock_client.list_foundation_models()
                available_models = [model['modelId'] for model in response.get('modelSummaries', [])]
                
                if model_id not in available_models:
                    logger.warning(f"Primary model {model_id} not found in available models.")
                    if fallback_model_id in available_models:
                        logger.info(f"Using fallback model: {fallback_model_id}")
                        self.model_id = fallback_model_id
                        self.using_fallback = True
                    else:
                        # Find any Claude model as final fallback
                        claude_models = [m for m in available_models if 'claude' in m.lower()]
                        if claude_models:
                            self.model_id = claude_models[0]
                            logger.info(f"Using alternative Claude model: {self.model_id}")
                        else:
                            logger.warning(f"No suitable models found. Available: {available_models[:5]}...")
                
                logger.info(f"Initialized Bedrock client with model {self.model_id} in region {region}")
                if self.using_fallback:
                    logger.info(f"Using cost-optimized fallback model for reduced expenses")
                
            except Exception as e:
                logger.warning(f"Could not verify model availability: {e}. Proceeding with {model_id}")
                
        except NoCredentialsError:
            raise Exception("AWS credentials not found. Please configure AWS credentials.")
        except Exception as e:
            raise Exception(f"Failed to initialize Bedrock client: {e}")
    
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Generate text using Bedrock model with automatic fallback to cheaper model
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text response
        """
        try:
            return self._generate_with_model(self.model_id, prompt, system_prompt, **kwargs)
        except Exception as e:
            # Try fallback model if available and not already using it
            if not self.using_fallback and self.fallback_model_id != self.model_id:
                logger.warning(f"Primary model {self.model_id} failed: {e}. Trying fallback model {self.fallback_model_id}")
                try:
                    self.using_fallback = True
                    return self._generate_with_model(self.fallback_model_id, prompt, system_prompt, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {fallback_error}")
                    raise Exception(f"Both primary and fallback models failed. Primary: {e}, Fallback: {fallback_error}")
            else:
                raise e
    
    def _generate_with_model(self, model_id: str, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate text using specific model"""
        try:
            # Prepare the request based on model type
            if 'claude' in model_id.lower():
                return self._generate_claude(model_id, prompt, system_prompt, **kwargs)
            elif 'llama' in model_id.lower():
                return self._generate_llama(model_id, prompt, system_prompt, **kwargs)
            elif 'titan' in model_id.lower():
                return self._generate_titan(model_id, prompt, system_prompt, **kwargs)
            else:
                # Default to Claude format
                return self._generate_claude(model_id, prompt, system_prompt, **kwargs)
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ValidationException':
                raise Exception(f"Invalid request to Bedrock: {e.response['Error']['Message']}")
            elif error_code == 'AccessDeniedException':
                raise Exception(f"Access denied to Bedrock model {model_id}. Check IAM permissions.")
            elif error_code == 'ThrottlingException':
                raise Exception("Bedrock request throttled. Please retry later.")
            elif error_code == 'ModelNotReadyException':
                raise Exception(f"Model {model_id} is not ready. Please try again later.")
            else:
                raise Exception(f"Bedrock error: {e.response['Error']['Message']}")
        except Exception as e:
            raise Exception(f"Unexpected error calling Bedrock with model {model_id}: {e}")
    
    def _generate_claude(self, model_id: str, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate text using Claude models via Bedrock"""
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "user", "content": f"System: {system_prompt}\n\nUser: {prompt}"})
        else:
            messages.append({"role": "user", "content": prompt})
        
        # Prepare request body
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": kwargs.get('max_tokens', 1000),
            "temperature": kwargs.get('temperature', 0.1),
            "messages": messages
        }
        
        # Add system prompt if provided (Claude 3 format)
        if system_prompt and 'claude-3' in model_id:
            body["system"] = system_prompt
            body["messages"] = [{"role": "user", "content": prompt}]
        
        response = self.client.invoke_model(
            body=json.dumps(body),
            modelId=model_id,
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        
        # Extract text from Claude response
        if 'content' in response_body:
            return response_body['content'][0]['text']
        elif 'completion' in response_body:
            return response_body['completion']
        else:
            raise Exception(f"Unexpected Claude response format: {response_body}")
    
    def _generate_llama(self, model_id: str, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate text using Llama models via Bedrock"""
        
        # Format prompt for Llama
        if system_prompt:
            formatted_prompt = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{prompt} [/INST]"
        else:
            formatted_prompt = f"<s>[INST] {prompt} [/INST]"
        
        body = {
            "prompt": formatted_prompt,
            "max_gen_len": kwargs.get('max_tokens', 1000),
            "temperature": kwargs.get('temperature', 0.1),
            "top_p": kwargs.get('top_p', 0.9)
        }
        
        response = self.client.invoke_model(
            body=json.dumps(body),
            modelId=model_id,
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        return response_body.get('generation', '')
    
    def _generate_titan(self, model_id: str, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate text using Titan models via Bedrock"""
        
        # Format prompt for Titan
        if system_prompt:
            formatted_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        else:
            formatted_prompt = prompt
        
        body = {
            "inputText": formatted_prompt,
            "textGenerationConfig": {
                "maxTokenCount": kwargs.get('max_tokens', 1000),
                "temperature": kwargs.get('temperature', 0.1),
                "topP": kwargs.get('top_p', 0.9)
            }
        }
        
        response = self.client.invoke_model(
            body=json.dumps(body),
            modelId=model_id,
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        return response_body.get('results', [{}])[0].get('outputText', '')
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List available Bedrock models"""
        try:
            bedrock_client = boto3.client(
                service_name='bedrock',
                region_name=self.region
            )
            response = bedrock_client.list_foundation_models()
            return response.get('modelSummaries', [])
        except Exception as e:
            logger.error(f"Failed to list available models: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model"""
        return {
            "model_id": self.model_id,
            "region": self.region,
            "using_fallback": self.using_fallback,
            "fallback_model_id": self.fallback_model_id
        }
    
    def get_cost_estimate(self) -> Dict[str, Any]:
        """Get cost estimate for current model"""
        # This is a placeholder - actual costs would need to be calculated based on
        # AWS pricing and usage metrics
        return {
            "model": self.model_id,
            "estimated_cost_per_1k_tokens": 0.0,  # Would need actual pricing data
            "using_fallback": self.using_fallback
        }


def get_bedrock_client(region: Optional[str] = None, model_id: Optional[str] = None, fallback_model_id: Optional[str] = None) -> BedrockLLMClient:
    """Get or create Bedrock client instance"""
    return BedrockLLMClient(
        region=region or os.getenv('AWS_REGION', 'us-east-1'),
        model_id=model_id or os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0'),
        fallback_model_id=fallback_model_id or os.getenv('BEDROCK_FALLBACK_MODEL_ID', 'amazon.titan-text-express-v1')
    )
