"""
Configuration Management for FinSight
Centralized configuration for all components
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: str = "bedrock"  # "bedrock", "openai", "anthropic", or "regex"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    model: str = "gpt-4o-mini"  # Default OpenAI model
    anthropic_model: str = "claude-3-haiku-20240307"
    ollama_model: str = "llama3.1:8b"  # Default Ollama model
    bedrock_model: str = "anthropic.claude-3-haiku-20240307-v1:0"  # Default Bedrock model
    bedrock_fallback_model: str = "amazon.titan-text-express-v1"  # Cheaper fallback model
    bedrock_region: str = "us-east-1"
    temperature: float = 0.1
    max_tokens: int = 1000
    
    def get_provider_for_environment(self) -> str:
        """Determine appropriate provider based on environment"""
        # Check if we're in AWS Lambda
        if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
            return "bedrock"  # Use Bedrock in AWS Lambda
        
        # Check if we're in local development (Ollama available)
        if self._is_local_development():
            return "ollama"
        
        # Fall back to configured provider
        return self.provider
    
    def _is_local_development(self) -> bool:
        """Check if we're in a local development environment"""
        # Check for common local development indicators
        local_indicators = [
            os.getenv('FINSIGHT_ENVIRONMENT') == 'local',
            os.getenv('DEVELOPMENT') == 'true',
            not os.getenv('AWS_LAMBDA_FUNCTION_NAME'),
            not os.getenv('AWS_EXECUTION_ENV'),
            # Check if Ollama is available on localhost
            self._check_ollama_availability()
        ]
        return any(local_indicators)
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available on localhost"""
        try:
            import urllib.request
            import urllib.error
            request = urllib.request.Request('http://localhost:11434/api/tags')
            with urllib.request.urlopen(request, timeout=2) as response:
                return response.status == 200
        except:
            return False


@dataclass
class AWSConfig:
    """Configuration for AWS services"""
    s3_bucket: Optional[str] = None
    region: str = "us-east-1"
    lambda_timeout: int = 300
    lambda_memory: int = 1024


@dataclass
class DataConfig:
    """Configuration for data sources and caching"""
    cache_enabled: bool = True
    cache_duration_hours: int = 24
    max_retries: int = 3
    request_timeout: int = 30


@dataclass
class FinSightConfig:
    """Main configuration class for FinSight"""
    llm: LLMConfig
    aws: AWSConfig
    data: DataConfig
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> 'FinSightConfig':
        """Create configuration from environment variables"""
        llm_config = LLMConfig(
            provider=os.getenv('FINSIGHT_LLM_PROVIDER', 'bedrock'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            model=os.getenv('FINSIGHT_OPENAI_MODEL', 'gpt-4o-mini'),
            anthropic_model=os.getenv('FINSIGHT_ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
            ollama_model=os.getenv('OLLAMA_MODEL', 'llama3.1:8b'),
            bedrock_model=os.getenv('FINSIGHT_BEDROCK_MODEL', 'anthropic.claude-3-haiku-20240307-v1:0'),
            bedrock_fallback_model=os.getenv('FINSIGHT_BEDROCK_FALLBACK_MODEL', 'amazon.titan-text-express-v1'),
            bedrock_region=os.getenv('FINSIGHT_BEDROCK_REGION', 'us-east-1'),
            temperature=float(os.getenv('FINSIGHT_TEMPERATURE', '0.1')),
            max_tokens=int(os.getenv('FINSIGHT_MAX_TOKENS', '1000'))
        )
        
        # Override provider based on environment detection
        detected_provider = llm_config.get_provider_for_environment()
        if detected_provider != llm_config.provider:
            llm_config.provider = detected_provider
        
        return cls(
            llm=llm_config,
            aws=AWSConfig(
                s3_bucket=os.getenv('S3_BUCKET'),
                region=os.getenv('AWS_REGION', 'us-east-1'),
                lambda_timeout=int(os.getenv('LAMBDA_TIMEOUT', '300')),
                lambda_memory=int(os.getenv('LAMBDA_MEMORY', '1024'))
            ),
            data=DataConfig(
                cache_enabled=os.getenv('FINSIGHT_CACHE_ENABLED', 'true').lower() == 'true',
                cache_duration_hours=int(os.getenv('FINSIGHT_CACHE_HOURS', '24')),
                max_retries=int(os.getenv('FINSIGHT_MAX_RETRIES', '3')),
                request_timeout=int(os.getenv('FINSIGHT_REQUEST_TIMEOUT', '30'))
            ),
            debug=os.getenv('FINSIGHT_DEBUG', 'false').lower() == 'true'
        )


# Global configuration instance
config = FinSightConfig.from_env()
