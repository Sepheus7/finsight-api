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
    provider: str = "openai"  # "openai", "anthropic", or "regex"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    model: str = "gpt-4o-mini"  # Default OpenAI model
    anthropic_model: str = "claude-3-haiku-20240307"
    temperature: float = 0.1
    max_tokens: int = 1000


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
        return cls(
            llm=LLMConfig(
                provider=os.getenv('FINSIGHT_LLM_PROVIDER', 'openai'),
                openai_api_key=os.getenv('OPENAI_API_KEY'),
                anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
                model=os.getenv('FINSIGHT_OPENAI_MODEL', 'gpt-4o-mini'),
                anthropic_model=os.getenv('FINSIGHT_ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
                temperature=float(os.getenv('FINSIGHT_TEMPERATURE', '0.1')),
                max_tokens=int(os.getenv('FINSIGHT_MAX_TOKENS', '1000'))
            ),
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
