#!/usr/bin/env python3
"""
Enhanced Agentic Capabilities Demo
Demonstrates the improved Bedrock-powered orchestrator with function calling
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.bedrock_orchestrator import (
    BedrockAgentOrchestrator, 
    AgentCapability, 
    AnalysisRequest,
    ToolRecommendation,
    AgentDecision
)


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🤖 {title}")
    print(f"{'='*60}")


def print_section(title: str):
    """Print a formatted section"""
    print(f"\n📋 {title}")
    print("-" * 40)


async def demo_enhanced_agentic_capabilities():
    """Demonstrate enhanced agentic capabilities"""
    
    print_header("FinSight Enhanced Agentic Framework Demo")
    
    # Initialize orchestrator
    orchestrator = BedrockAgentOrchestrator(
        aws_region='us-east-1',
        model_id='anthropic.claude-3-haiku-20240307-v1:0'
    )
    
    print_section("Orchestrator Capabilities")
    metrics = orchestrator.get_performance_metrics()
    for key, value in metrics.items():
        print(f"   • {key}: {value}")
    
    print_section("Available Tools & Enhanced Features")
    for tool_name, tool_info in orchestrator.available_tools.items():
        capabilities = [cap.value for cap in tool_info['capabilities']]
        print(f"   🔧 {tool_name}:")
        print(f"      • Capabilities: {', '.join(capabilities)}")
        print(f"      • Reliability: {tool_info['reliability']}")
        print(f"      • Rate Limit: {tool_info['rate_limit']}")
        print(f"      • Strengths: {', '.join(tool_info['strengths'])}")
    
    print_section("Function Calling Definitions")
    for func_def in orchestrator.function_definitions:
        print(f"   🎯 {func_def['name']}:")
        print(f"      • Description: {func_def['description']}")
        required_params = func_def['input_schema']['properties'].keys()
        print(f"      • Parameters: {', '.join(required_params)}")
    
    print_section("Test Financial Analysis Scenarios")
    
    # Test Scenario 1: Multi-source stock analysis
    print("\n🧪 Scenario 1: Complex Market Analysis")
    test_request_1 = AnalysisRequest(
        content="Apple's stock (AAPL) is trading at $175, up 5% this quarter. The company reported record iPhone sales and expanded into AI services. With a market cap of $2.8 trillion, Apple remains the world's most valuable company.",
        claims=[
            {
                "claim_type": "stock_price",
                "text": "AAPL trading at $175",
                "confidence": 0.9,
                "ticker": "AAPL",
                "entities": ["AAPL", "$175"]
            },
            {
                "claim_type": "market_cap", 
                "text": "market cap of $2.8 trillion",
                "confidence": 0.85,
                "ticker": "AAPL",
                "entities": ["$2.8 trillion", "market cap"]
            },
            {
                "claim_type": "earnings",
                "text": "record iPhone sales",
                "confidence": 0.7,
                "ticker": "AAPL",
                "entities": ["iPhone sales", "record"]
            }
        ],
        context={"sector": "technology", "market_conditions": "bullish"},
        requested_capabilities=[
            AgentCapability.FACT_VERIFICATION,
            AgentCapability.MARKET_DATA_ANALYSIS,
            AgentCapability.TREND_ANALYSIS
        ],
        target_audience="professional",
        risk_tolerance="moderate"
    )
    
    # Demonstrate fallback routing (since Bedrock isn't available locally)
    print("   📊 Analyzing complex market scenario...")
    decision_1 = await orchestrator.analyze_and_route(test_request_1)
    
    print(f"   • Strategy: {decision_1.analysis_strategy}")
    print(f"   • Confidence Threshold: {decision_1.confidence_threshold}")
    print(f"   • Reasoning: {decision_1.reasoning}")
    print(f"   • Recommended Tools: {len(decision_1.recommended_tools)}")
    
    for i, tool_rec in enumerate(decision_1.recommended_tools, 1):
        print(f"      {i}. {tool_rec.tool_name} (confidence: {tool_rec.confidence:.2f}, priority: {tool_rec.priority})")
        print(f"         └─ {tool_rec.reasoning}")
    
    # Test cost estimation
    cost_estimate = orchestrator.get_cost_estimation(test_request_1, decision_1)
    print(f"   💰 Cost Estimation:")
    print(f"      • Total Cost: ${cost_estimate['total_estimated_cost']:.6f}")
    print(f"      • Cost per Claim: ${cost_estimate['cost_per_claim']:.6f}")
    print(f"      • Model Used: {cost_estimate['model_used']}")
    
    # Test Scenario 2: Economic indicator analysis
    print("\n🧪 Scenario 2: Economic Analysis")
    test_request_2 = AnalysisRequest(
        content="The US economy shows strong fundamentals with GDP growth at 2.3% annually and unemployment at a historic low of 3.5%. However, inflation remains elevated at 3.8%, prompting concerns about Fed policy.",
        claims=[
            {
                "claim_type": "gdp",
                "text": "GDP growth at 2.3%",
                "confidence": 0.8,
                "parameters": {"country": "US", "growth_rate": 2.3}
            },
            {
                "claim_type": "unemployment", 
                "text": "unemployment at 3.5%",
                "confidence": 0.9,
                "parameters": {"country": "US", "rate": 3.5}
            },
            {
                "claim_type": "inflation",
                "text": "inflation at 3.8%", 
                "confidence": 0.85,
                "parameters": {"country": "US", "rate": 3.8}
            }
        ],
        context={"analysis_type": "macroeconomic", "time_horizon": "current"},
        requested_capabilities=[
            AgentCapability.ECONOMIC_ANALYSIS,
            AgentCapability.FACT_VERIFICATION,
            AgentCapability.CONTEXT_ENRICHMENT
        ],
        target_audience="regulatory",
        risk_tolerance="low"
    )
    
    print("   📈 Analyzing economic indicators...")
    decision_2 = await orchestrator.analyze_and_route(test_request_2)
    
    print(f"   • Strategy: {decision_2.analysis_strategy}")
    print(f"   • Tools Recommended: {[t.tool_name for t in decision_2.recommended_tools]}")
    print(f"   • Routing Method: {decision_2.metadata.get('routing_method', 'standard')}")
    
    cost_estimate_2 = orchestrator.get_cost_estimation(test_request_2, decision_2)
    print(f"   💰 Economic Analysis Cost: ${cost_estimate_2['total_estimated_cost']:.6f}")
    
    print_section("Enhanced Features Summary")
    print("   ✅ Function Calling Support: Enable structured agent decisions")
    print("   ✅ Multi-source Intelligence: Yahoo Finance + Alpha Vantage + World Bank")
    print("   ✅ Cost Optimization: Real-time cost estimation and model selection")
    print("   ✅ Enhanced Error Handling: Exponential backoff, detailed error codes")
    print("   ✅ Adaptive Routing: Risk-aware tool selection based on audience")
    print("   ✅ Performance Metrics: Comprehensive monitoring and analytics")
    
    print_section("Bedrock Integration Benefits")
    print("   🧠 Intelligent Tool Selection: AI-driven source prioritization")
    print("   ⚡ Function Calling: Structured responses for reliable parsing") 
    print("   🔄 Adaptive Fallbacks: Graceful degradation when services unavailable")
    print("   💰 Cost-Aware Routing: Optimize for both accuracy and expense")
    print("   📊 Risk-Based Analysis: Adjust verification depth by risk tolerance")
    print("   🌐 Multi-region Support: Flexible AWS region configuration")
    
    print_header("Demo Complete - Enhanced Agentic Capabilities Ready")
    print("🚀 The system is now significantly more 'Bedrock-friendly' with:")
    print("   • Advanced function calling for structured agent interactions")
    print("   • Enhanced error handling with exponential backoff")  
    print("   • Real-time cost optimization and estimation")
    print("   • Intelligent multi-source data routing")
    print("   • Alpha Vantage integration for premium market data")
    print("   • Risk-aware analysis based on audience and tolerance")


async def test_function_calling_mock():
    """Test function calling behavior with mock responses"""
    print_section("Function Calling Mock Test")
    
    orchestrator = BedrockAgentOrchestrator()
    
    # Mock a function call response
    mock_response = {
        'content': [
            {
                'type': 'tool_use',
                'name': 'select_data_sources',
                'input': {
                    'primary_sources': ['yahoo_finance', 'alpha_vantage'],
                    'fallback_sources': ['world_bank'],
                    'analysis_strategy': 'multi_source_verification',
                    'confidence_threshold': 0.85,
                    'reasoning': 'Stock data requires real-time accuracy, using both Yahoo Finance and Alpha Vantage for cross-verification'
                }
            },
            {
                'type': 'tool_use', 
                'name': 'estimate_cost_and_time',
                'input': {
                    'selected_sources': ['yahoo_finance', 'alpha_vantage'],
                    'query_complexity': 'moderate',
                    'estimated_total_cost': 0.001,
                    'estimated_total_time': 5.0
                }
            }
        ]
    }
    
    # Test parsing function call response
    test_request = AnalysisRequest(
        content="Test content",
        claims=[{"claim_type": "stock_price", "ticker": "AAPL"}],
        context={},
        requested_capabilities=[AgentCapability.FACT_VERIFICATION]
    )
    
    try:
        decision = await orchestrator._parse_function_call_response(mock_response, test_request)
        print("   ✅ Function call parsing successful")
        print(f"   • Tools selected: {[t.tool_name for t in decision.recommended_tools]}")
        print(f"   • Strategy: {decision.analysis_strategy}")
        print(f"   • Reasoning: {decision.reasoning}")
        print(f"   • Metadata: {decision.metadata.get('function_calls_used', [])}")
    except Exception as e:
        print(f"   ❌ Function call parsing failed: {e}")


if __name__ == "__main__":
    asyncio.run(demo_enhanced_agentic_capabilities())
    asyncio.run(test_function_calling_mock())
