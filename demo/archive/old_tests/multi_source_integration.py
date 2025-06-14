"""
Multi-Source Integration Module
Provides a simplified interface to multi-source capabilities for the demo API server
"""

import sys
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class BasicFactChecker:
    """Basic fallback fact checker when no advanced components are available"""
    
    def __init__(self):
        self.available = True
    
    def fact_check_content(self, content: str) -> Dict[str, Any]:
        """Basic fact check implementation"""
        return {
            'original_content': content,
            'enhanced_content': content,
            'fact_check_results': [],
            'overall_confidence': 0.5,
            'sources_used': [],
            'verification_timestamp': datetime.now().isoformat(),
            'multi_source_available': False
        }
    
    async def process_content(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Async wrapper for basic fact checking"""
        return self.fact_check_content(content)

class MultiSourceIntegration:
    """Multi-source integration with graceful fallback"""
    
    def __init__(self):
        self.available = False
        self.world_bank_available = False
        self.bedrock_agents_available = False
        self.fact_checker = None
        self.implementation_type = "none"
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize multi-source components with multiple fallback levels"""
        # Try advanced components first
        if self._try_advanced_components():
            return
        
        # Try simplified components
        if self._try_simple_components():
            return
        
        # Fall back to basic components
        self._initialize_basic_components()
    
    def _try_advanced_components(self) -> bool:
        """Try to initialize advanced multi-source components"""
        try:
            logger.info("Attempting to load advanced multi-source components...")
            
            from handlers.multi_source_fact_checker import MultiSourceFactChecker
            from utils.data_sources import DataSourceRegistry
            from integrations.world_bank_client import WorldBankDataSource
            from agents.bedrock_orchestrator import BedrockAgentOrchestrator
            
            # Initialize components
            self.fact_checker = MultiSourceFactChecker(
                use_llm=True,
                use_bedrock_agents=True
            )
            
            # Check component availability
            registry = DataSourceRegistry()
            world_bank = WorldBankDataSource()
            registry.register_source('world_bank', world_bank)
            
            self.world_bank_available = True
            self.bedrock_agents_available = True
            self.available = True
            self.implementation_type = "advanced"
            
            logger.info("Advanced multi-source components initialized successfully")
            return True
            
        except ImportError as e:
            logger.warning(f"Advanced components not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize advanced components: {e}")
            return False
    
    def _try_simple_components(self) -> bool:
        """Try to initialize simplified multi-source components with Alpha Vantage"""
        try:
            logger.info("Attempting to load simplified multi-source components...")
            
            from simple_multi_source import get_simple_multi_source_fact_checker
            
            # Use the simplified fact checker implementation with Yahoo Finance, Alpha Vantage, and World Bank
            self.fact_checker = get_simple_multi_source_fact_checker(
                enable_world_bank=True, 
                enable_yahoo_finance=True,
                enable_alpha_vantage=True
            )
            self.world_bank_available = True
            self.bedrock_agents_available = False  # Not available in simple version
            self.available = True
            self.implementation_type = "simple_with_alpha_vantage"
            
            logger.info("Simple multi-source components initialized with Yahoo Finance, Alpha Vantage, and World Bank")
            logger.info(f"Available data sources: {self.fact_checker.data_registry.available_sources}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to initialize simple components: {e}")
            return False
    
    def _initialize_basic_components(self):
        """Initialize basic fallback components"""
        try:
            logger.info("Initializing basic fallback components...")
            
            # Use a minimal fact checker implementation
            self.fact_checker = BasicFactChecker()
            self.world_bank_available = False
            self.bedrock_agents_available = False
            self.available = True
            self.implementation_type = "basic"
            
            logger.info("Basic fallback components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize any components: {e}")
            self.available = False
            self.implementation_type = "none"
    
    async def process_content(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process content using available fact checking implementation"""
        if not self.available or not self.fact_checker:
            raise RuntimeError("No fact checker available")
        
        try:
            if hasattr(self.fact_checker, 'process_content'):
                # Advanced implementation
                result = await self.fact_checker.process_content(content, context or {})
            elif hasattr(self.fact_checker, 'fact_check_content'):
                # Simple implementation
                result = self.fact_checker.fact_check_content(content)
            else:
                # Basic implementation
                result = {
                    'original_content': content,
                    'enhanced_content': content,
                    'fact_check_results': [],
                    'overall_confidence': 0.5,
                    'sources_used': [],
                    'verification_timestamp': datetime.now().isoformat(),
                    'multi_source_available': self.available
                }
            
            # Add implementation type to result
            result['implementation_type'] = self.implementation_type
            return result
            
        except Exception as e:
            logger.error(f"Multi-source processing failed: {e}")
            # Return basic result on error
            return {
                'original_content': content,
                'enhanced_content': content,
                'fact_check_results': [],
                'overall_confidence': 0.3,
                'sources_used': [],
                'verification_timestamp': datetime.now().isoformat(),
                'multi_source_available': False,
                'error': str(e),
                'implementation_type': self.implementation_type
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of multi-source components"""
        return {
            "available": self.available,
            "implementation_type": self.implementation_type,
            "world_bank": self.world_bank_available,
            "bedrock_agents": self.bedrock_agents_available,
            "data_sources": self.get_available_sources()
        }
    
    def get_available_sources(self) -> List[str]:
        """Get list of available data sources"""
        if not self.available or not self.fact_checker:
            return []
        
        sources = []
        
        try:
            # Try advanced implementation
            if hasattr(self.fact_checker, 'data_registry') and hasattr(self.fact_checker.data_registry, 'get_all_sources'):
                sources = list(self.fact_checker.data_registry.get_all_sources().keys())
            # Try simple implementation
            elif hasattr(self.fact_checker, 'data_registry') and hasattr(self.fact_checker.data_registry, 'available_sources'):
                sources = self.fact_checker.data_registry.available_sources
            # World Bank available in simple implementation
            elif self.world_bank_available:
                sources = ['world_bank']
        except Exception as e:
            logger.warning(f"Error getting available sources: {e}")
        
        return sources

# Global instance
_multi_source_integration = None

def get_multi_source_integration() -> Optional[MultiSourceIntegration]:
    """Get singleton multi-source integration instance"""
    global _multi_source_integration
    
    if _multi_source_integration is None:
        try:
            _multi_source_integration = MultiSourceIntegration()
            logger.info(f"Created multi-source integration: available={_multi_source_integration.available}, type={_multi_source_integration.implementation_type}")
        except Exception as e:
            logger.warning(f"Failed to create multi-source integration: {e}")
            return None
    
    return _multi_source_integration if _multi_source_integration.available else None

def is_multi_source_available() -> bool:
    """Check if multi-source capabilities are available"""
    integration = get_multi_source_integration()
    return integration is not None and integration.available

# Test the simplified components on import
def test_simple_components():
    """Test simplified components availability"""
    try:
        from simple_multi_source import test_simple_multi_source
        result = test_simple_multi_source()
        logger.info("Simple multi-source test completed successfully")
        return True
    except Exception as e:
        logger.warning(f"Simple multi-source test failed: {e}")
        return False

# Initialize on import for early error detection
try:
    _test_integration = get_multi_source_integration()
    if _test_integration:
        logger.info(f"Multi-source integration module loaded successfully: {_test_integration.implementation_type}")
        
        # Test simple components if available
        if _test_integration.implementation_type == "simple":
            test_simple_components()
    else:
        logger.warning("Multi-source integration module loaded but not functional")
except Exception as e:
    logger.warning(f"Error during multi-source integration initialization: {e}")
