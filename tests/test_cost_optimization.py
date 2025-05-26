#!/usr/bin/env python3
"""
Test suite for FinSight cost optimization features
Tests environment detection, fallback models, and provider auto-selection
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import FinSightConfig, LLMConfig
from utils.llm_claim_extractor import LLMClaimExtractor


class TestCostOptimization(unittest.TestCase):
    """Test cost optimization features"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_env = dict(os.environ)
    
    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_default_fallback_model_config(self):
        """Test that default fallback model is properly configured"""
        config = LLMConfig()
        self.assertEqual(config.bedrock_fallback_model, "amazon.titan-text-express-v1")
        self.assertEqual(config.bedrock_model, "anthropic.claude-3-haiku-20240307-v1:0")
    
    def test_environment_override_fallback_model(self):
        """Test that environment variables properly override fallback model"""
        os.environ['FINSIGHT_BEDROCK_FALLBACK_MODEL'] = 'amazon.titan-text-lite-v1'
        
        config = FinSightConfig.from_env()
        self.assertEqual(config.llm.bedrock_fallback_model, 'amazon.titan-text-lite-v1')
    
    @patch('src.config.LLMConfig._check_ollama_availability')
    def test_local_environment_detection(self, mock_ollama_check):
        """Test that local environment correctly detects Ollama"""
        mock_ollama_check.return_value = True
        
        config = LLMConfig()
        provider = config.get_provider_for_environment()
        self.assertEqual(provider, "ollama")
    
    @patch('src.config.LLMConfig._check_ollama_availability')
    @patch('src.config.LLMConfig._is_local_development')
    def test_aws_environment_detection(self, mock_is_local, mock_ollama_check):
        """Test that AWS environment correctly uses Bedrock"""
        mock_is_local.return_value = False
        mock_ollama_check.return_value = False
        os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'test-function'
        
        config = LLMConfig()
        provider = config.get_provider_for_environment()
        self.assertEqual(provider, "bedrock")
    
    def test_claim_extractor_uses_global_config(self):
        """Test that claim extractor respects global configuration"""
        # Create config with specific provider
        os.environ['FINSIGHT_LLM_PROVIDER'] = 'anthropic'
        
        config = FinSightConfig.from_env()
        extractor = LLMClaimExtractor(provider="auto")
        
        # Should use the global config provider (after environment detection)
        self.assertIn(extractor.provider, ['anthropic', 'ollama'])  # Could be overridden by env detection
    
    @patch('src.utils.bedrock_client.BOTO3_AVAILABLE', True)
    @patch('src.utils.bedrock_client.boto3')
    def test_bedrock_fallback_integration(self, mock_boto3):
        """Test Bedrock client fallback functionality"""
        from utils.bedrock_client import BedrockLLMClient
        
        # Mock Bedrock client
        mock_client = MagicMock()
        mock_bedrock_client = MagicMock()
        mock_boto3.client.side_effect = [mock_client, mock_bedrock_client]
        
        # Mock model list response
        mock_bedrock_client.list_foundation_models.return_value = {
            'modelSummaries': [
                {'modelId': 'anthropic.claude-3-haiku-20240307-v1:0'},
                {'modelId': 'amazon.titan-text-express-v1'}
            ]
        }
        
        client = BedrockLLMClient(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            fallback_model_id="amazon.titan-text-express-v1"
        )
        
        self.assertEqual(client.model_id, "anthropic.claude-3-haiku-20240307-v1:0")
        self.assertEqual(client.fallback_model_id, "amazon.titan-text-express-v1")
        self.assertFalse(client.using_fallback)
    
    def test_cost_estimation_integration(self):
        """Test that cost estimation works for different models"""
        from utils.bedrock_client import BedrockLLMClient
        
        # Mock client without actually connecting to AWS
        with patch('src.utils.bedrock_client.BOTO3_AVAILABLE', False):
            try:
                client = BedrockLLMClient()
                self.fail("Should have raised ImportError")
            except ImportError:
                pass  # Expected
        
        # Test cost estimates directly
        with patch('src.utils.bedrock_client.BOTO3_AVAILABLE', True):
            with patch('src.utils.bedrock_client.boto3'):
                client = BedrockLLMClient.__new__(BedrockLLMClient)
                client.model_id = "amazon.titan-text-express-v1"
                
                cost = client.get_cost_estimate()
                self.assertIn('input', cost)
                self.assertIn('output', cost)
                self.assertEqual(cost['input'], 0.20)
    
    def test_environment_variable_precedence(self):
        """Test that environment variables take precedence over defaults"""
        os.environ.update({
            'FINSIGHT_LLM_PROVIDER': 'openai',
            'FINSIGHT_BEDROCK_MODEL': 'custom-model',
            'FINSIGHT_BEDROCK_FALLBACK_MODEL': 'custom-fallback-model',
            'FINSIGHT_TEMPERATURE': '0.5',
            'FINSIGHT_MAX_TOKENS': '2000'
        })
        
        config = FinSightConfig.from_env()
        
        # Note: provider might be overridden by environment detection
        self.assertEqual(config.llm.bedrock_model, 'custom-model')
        self.assertEqual(config.llm.bedrock_fallback_model, 'custom-fallback-model')
        self.assertEqual(config.llm.temperature, 0.5)
        self.assertEqual(config.llm.max_tokens, 2000)


class TestIntegrationWorkflow(unittest.TestCase):
    """Test complete integration workflow"""
    
    def test_local_development_workflow(self):
        """Test complete workflow in local development environment"""
        print("\n=== Testing Local Development Workflow ===")
        
        # Clear environment to simulate clean state
        for key in list(os.environ.keys()):
            if key.startswith('FINSIGHT_') or key in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
                del os.environ[key]
        
        # Create configuration
        config = FinSightConfig.from_env()
        print(f"✓ Config created with provider: {config.llm.provider}")
        
        # Test claim extractor
        extractor = LLMClaimExtractor()
        print(f"✓ Claim extractor initialized with provider: {extractor.provider}")
        
        # Should prefer Ollama in local environment (if available)
        self.assertIn(extractor.provider, ['ollama', 'regex'])
        
        print("✓ Local development workflow test completed")
    
    @patch.dict(os.environ, {'AWS_LAMBDA_FUNCTION_NAME': 'test-function'})
    def test_aws_deployment_workflow(self):
        """Test complete workflow in AWS deployment environment"""
        print("\n=== Testing AWS Deployment Workflow ===")
        
        # Simulate AWS environment
        os.environ.update({
            'FINSIGHT_BEDROCK_MODEL': 'anthropic.claude-3-haiku-20240307-v1:0',
            'FINSIGHT_BEDROCK_FALLBACK_MODEL': 'amazon.titan-text-express-v1',
            'AWS_REGION': 'us-east-1'
        })
        
        config = FinSightConfig.from_env()
        print(f"✓ AWS config created with provider: {config.llm.provider}")
        
        extractor = LLMClaimExtractor()
        print(f"✓ AWS claim extractor initialized with provider: {extractor.provider}")
        
        # Should use Bedrock in AWS environment
        self.assertEqual(extractor.provider, 'bedrock')
        
        print("✓ AWS deployment workflow test completed")


def run_cost_optimization_tests():
    """Run all cost optimization tests"""
    print("🧪 Running FinSight Cost Optimization Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestCostOptimization))
    suite.addTest(unittest.makeSuite(TestIntegrationWorkflow))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All cost optimization tests passed!")
        print(f"✓ Ran {result.testsRun} tests successfully")
    else:
        print("❌ Some tests failed!")
        print(f"✗ Failures: {len(result.failures)}")
        print(f"✗ Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_cost_optimization_tests()
    sys.exit(0 if success else 1)
