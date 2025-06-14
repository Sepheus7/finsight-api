"""
Bedrock Router Agent - Intelligent Financial Query Orchestrator
Uses Bedrock's function calling capability to route user queries to the best tool.
"""

import json
import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.bedrock_client import BedrockLLMClient
from utils.cache_manager import CacheManager
from handlers.agent_tools import AGENT_TOOLS, TOOL_EXECUTOR_MAP

logger = logging.getLogger(__name__)

class BedrockRouterAgent:
    """
    An intelligent agent that uses Bedrock's function calling (tool use)
    feature to answer financial queries.
    """

    def __init__(self, system_prompt: Optional[str] = None):
        """Initialize the router agent"""
        try:
            self.bedrock_client = BedrockLLMClient()
            self.cache_manager = CacheManager()
            self.system_prompt = system_prompt or self._get_default_system_prompt()
            logger.info("BedrockRouterAgent with function calling initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock Router Agent: {e}")
            raise

    def _get_default_system_prompt(self) -> str:
        """Returns the default system prompt for the agent."""
        return """You are a highly intelligent financial assistant named FinSight.
        Your goal is to provide accurate and timely financial information to users.
        You have access to a variety of tools to get stock data, company information,
        economic indicators, and perform web searches.

        When you receive a user query, first think about what you know and what tools
        you need to use. Then, use the tools to find the information.
        If a user asks a question that requires multiple steps or information from
        multiple sources, break it down and use the tools sequentially.

        Once you have gathered all the necessary information, synthesize it into a
        clear, concise, and helpful answer for the user. Always cite your sources
        by mentioning which tool you used to get the information.

        If a stock symbol or company seems invalid or you can't find information,
        use the web_search tool to validate it or find the correct ticker symbol.
        Do not make up information. If you cannot answer a question, say so.
        """

    async def route_query(self, query: str) -> Dict[str, Any]:
        """
        Routes a financial query using Bedrock's function calling.

        Args:
            query: Natural language financial query.

        Returns:
            A dictionary containing the agent's response and metadata.
        """
        start_time = datetime.now()
        request_id = f"router_{int(start_time.timestamp())}"
        logger.info(f"[{request_id}] Routing query with function calling: {query[:100]}...")

        messages = [{"role": "user", "content": [{"text": query}]}]
        
        try:
            # First call to Bedrock to determine tool usage
            response = self.bedrock_client.converse(
                messages=messages,
                tools=AGENT_TOOLS,
                system_prompt=self.system_prompt
            )

            messages.append(response['output']['message'])

            # Enter conversation loop to handle tool calls
            while response['stopReason'] == 'tool_use':
                tool_requests = [
                    content for content in response['output']['message']['content']
                    if 'toolUse' in content
                ]

                tool_results = await self._execute_tools(tool_requests)

                # Add tool results to the conversation history
                messages.append({
                    "role": "user",
                    "content": [{"toolResult": result} for result in tool_results]
                })

                # Call Bedrock again with the tool results
                response = self.bedrock_client.converse(
                    messages=messages,
                    tools=AGENT_TOOLS,
                    system_prompt=self.system_prompt
                )
                messages.append(response['output']['message'])

            # Extract final response from the agent
            final_answer_parts = [
                content['text'] for content in response['output']['message']['content']
                if 'text' in content
            ]
            final_answer = " ".join(final_answer_parts)

            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(f"[{request_id}] Query routed successfully in {processing_time:.2f}ms")
            
            return {
                'response': final_answer,
                'routing_metadata': {
                    'request_id': request_id,
                    'processing_time_ms': round(processing_time, 2),
                    'llm_stop_reason': response['stopReason'],
                    'input_token_count': response['usage']['inputTokens'],
                    'output_token_count': response['usage']['outputTokens'],
                    'timestamp': datetime.now().isoformat(),
                    'router_version': '3.0.0-function-calling'
                }
            }

        except Exception as e:
            logger.error(f"[{request_id}] Query routing with function calling failed: {str(e)}")
            return {
                'error': f"Query routing failed: {str(e)}",
                'request_id': request_id,
                'timestamp': datetime.now().isoformat()
            }

    async def _execute_tools(self, tool_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Executes the tool calls requested by the model."""
        tasks = []
        for tool_request in tool_requests:
            tool_use = tool_request['toolUse']
            tool_name = tool_use['name']
            tool_input = tool_use['input'] or {}
            tool_use_id = tool_use['toolUseId']

            if tool_name in TOOL_EXECUTOR_MAP:
                executor = TOOL_EXECUTOR_MAP[tool_name]
                task = self._run_tool(executor, tool_input, tool_use_id, tool_name)
                tasks.append(task)
            else:
                logger.warning(f"Unknown tool requested: {tool_name}")
                # Return an error result for the unknown tool
                tasks.append(asyncio.create_task(
                    self._create_tool_result(
                        {"error": f"Tool '{tool_name}' is not available."},
                        tool_use_id,
                        was_successful=False
                    )
                ))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Filter out exceptions and ensure we return proper Dict objects
        valid_results = []
        for res in results:
            if not isinstance(res, Exception) and isinstance(res, dict):
                valid_results.append(res)
        return valid_results

    async def _run_tool(self, executor, tool_input, tool_use_id, tool_name):
        """Helper to run a single tool and handle exceptions."""
        try:
            logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
            result = await executor(**tool_input)
            return await self._create_tool_result(result, tool_use_id)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return await self._create_tool_result(
                {"error": str(e)},
                tool_use_id,
                was_successful=False
            )

    async def _create_tool_result(self, result: Any, tool_use_id: str, was_successful: bool = True) -> Dict[str, Any]:
        """Formats the result of a tool execution for the Bedrock API."""
        return {
            "toolUseId": tool_use_id,
            "content": [{"json": result}],
            "status": "success" if was_successful else "error"
        }


# Test function
async def test_bedrock_router():
    """Test the Bedrock Router Agent with function calling."""
    print("🤖 Testing Bedrock Router Agent (Function Calling)")
    print("=" * 50)

    try:
        router = BedrockRouterAgent()

        test_queries = [
            "What is Apple's current stock price?",
            "What is the market cap of Microsoft?",
            "How is the US economy doing? Check some indicators.",
            "What is the stock ticker for the company that makes Photoshop?", # Requires web search
            "Compare the stock price of TSLA and F."
        ]

        for query in test_queries:
            print(f"\n📊 Query: {query}")
            print("-" * 30)

            result = await router.route_query(query)

            if 'error' in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"✅ Response: {result.get('response', 'No response')}")
                metadata = result.get('routing_metadata', {})
                print(f"⚡ Processing time: {metadata.get('processing_time_ms', 0):.1f}ms")
                print(f"🔧 LLM Stop Reason: {metadata.get('llm_stop_reason', 'unknown')}")

        print(f"\n🎉 Bedrock Router (Function Calling) testing completed!")

    except Exception as e:
        print(f"❌ Failed to test Bedrock Router: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    asyncio.run(test_bedrock_router())