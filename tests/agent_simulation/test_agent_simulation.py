#!/usr/bin/env python3
"""
AI Agent Simulation Test for FinSight API v1

This script simulates an external AI agent using the FinSight API to answer
various business queries. It demonstrates the API's capabilities and response formats.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List
from datetime import datetime

class FinSightAgentSimulator:
    """Simulates an AI agent using the FinSight API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/v1/query"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def query_api(self, query: str, context: str = "") -> Dict[str, Any]:
        """Send a query to the FinSight API"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
            
        payload = {
            "query": query,
            "context": context
        }
        
        start_time = time.time()
        
        try:
            async with self.session.post(
                self.api_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    data['_response_time_ms'] = response_time
                    return data
                else:
                    error_text = await response.text()
                    return {
                        "error": f"HTTP {response.status}",
                        "message": error_text,
                        "_response_time_ms": response_time
                    }
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "error": "Request failed",
                "message": str(e),
                "_response_time_ms": response_time
            }
    
    def format_response(self, query: str, response: Dict[str, Any]) -> str:
        """Format the API response for business presentation"""
        if "error" in response:
            return f"❌ Error: {response.get('message', 'Unknown error')}"
        
        data = response.get('data', {})
        sources = response.get('sources', [])
        cached = response.get('cached', False)
        response_time = response.get('_response_time_ms', 0)
        
        # Format based on data type
        if 'symbol' in data and 'price' in data:
            # Stock data
            symbol = data['symbol']
            price = data['price']
            currency = data.get('currency', 'USD')
            cache_status = "📋 Cached" if cached else "🔄 Live"
            
            return f"""
📈 **Stock Query Result**
• Symbol: {symbol}
• Price: {currency} {price:,.2f}
• Sources: {', '.join(sources)}
• Status: {cache_status}
• Response Time: {response_time:.0f}ms
"""
        
        elif 'indicator' in data and 'value' in data:
            # Economic indicator
            indicator = data['indicator'].replace('_', ' ').title()
            value = data['value']
            unit = data.get('unit', '')
            cache_status = "📋 Cached" if cached else "🔄 Live"
            
            return f"""
📊 **Economic Indicator Result**
• Indicator: {indicator}
• Value: {value}{unit}
• Sources: {', '.join(sources)}
• Status: {cache_status}
• Response Time: {response_time:.0f}ms
"""
        
        else:
            # Generic response
            response_text = data.get('response', str(data))
            cache_status = "📋 Cached" if cached else "🔄 Live"
            
            return f"""
💼 **General Query Result**
• Response: {response_text}
• Sources: {', '.join(sources)}
• Status: {cache_status}
• Response Time: {response_time:.0f}ms
"""

async def run_business_scenarios():
    """Run various business scenario tests"""
    
    print("🤖 FinSight AI Agent Simulation")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Business scenarios to test
    scenarios = [
        {
            "scenario": "Portfolio Analysis",
            "queries": [
                ("What is Apple stock price?", "Building a tech portfolio analysis"),
                ("What is Microsoft stock price?", "Comparing tech giants for investment"),
                ("What is Tesla stock price?", "Evaluating EV sector opportunities")
            ]
        },
        {
            "scenario": "Economic Research",
            "queries": [
                ("What is the US unemployment rate?", "Macroeconomic analysis for Q4 strategy"),
                ("What is the inflation rate in the UK?", "International market assessment"),
                ("What is the employment rate in France?", "European economic outlook")
            ]
        },
        {
            "scenario": "Market Intelligence",
            "queries": [
                ("How is the US economy doing?", "Overall market sentiment analysis"),
                ("What is Amazon stock price?", "E-commerce sector evaluation"),
                ("What is Google stock price?", "Tech sector diversification study")
            ]
        }
    ]
    
    async with FinSightAgentSimulator() as agent:
        total_queries = 0
        successful_queries = 0
        total_response_time = 0
        
        for scenario in scenarios:
            print(f"🎯 **{scenario['scenario']}**")
            print("-" * 30)
            
            for query, context in scenario['queries']:
                print(f"🔍 Query: {query}")
                print(f"📝 Context: {context}")
                
                response = await agent.query_api(query, context)
                formatted_result = agent.format_response(query, response)
                
                print(formatted_result)
                
                # Track metrics
                total_queries += 1
                if "error" not in response:
                    successful_queries += 1
                
                response_time = response.get('_response_time_ms', 0)
                total_response_time += response_time
                
                # Small delay between queries
                await asyncio.sleep(1)
            
            print()
        
        # Summary statistics
        success_rate = (successful_queries / total_queries) * 100 if total_queries > 0 else 0
        avg_response_time = total_response_time / total_queries if total_queries > 0 else 0
        
        print("📈 **Simulation Summary**")
        print("=" * 30)
        print(f"• Total Queries: {total_queries}")
        print(f"• Successful: {successful_queries}")
        print(f"• Success Rate: {success_rate:.1f}%")
        print(f"• Average Response Time: {avg_response_time:.0f}ms")
        print(f"• Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def run_single_query_demo():
    """Run a single query demonstration"""
    
    print("\n🔬 **Single Query Demonstration**")
    print("=" * 40)
    
    async with FinSightAgentSimulator() as agent:
        # Demonstrate detailed API response
        query = "What is Apple stock price?"
        context = "Investment decision for retirement portfolio"
        
        print(f"Query: {query}")
        print(f"Context: {context}")
        print("\nRaw API Response:")
        print("-" * 20)
        
        response = await agent.query_api(query, context)
        print(json.dumps(response, indent=2))
        
        print("\nFormatted Business Response:")
        print("-" * 30)
        formatted = agent.format_response(query, response)
        print(formatted)

async def main():
    """Main test runner"""
    try:
        # Check if server is running
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                if response.status != 200:
                    print("❌ FinSight server is not running on localhost:8000")
                    print("Please start the server with: python src/api_server.py")
                    return
        
        print("✅ FinSight server is running")
        print()
        
        # Run the simulation
        await run_business_scenarios()
        await run_single_query_demo()
        
    except aiohttp.ClientConnectorError:
        print("❌ Cannot connect to FinSight server on localhost:8000")
        print("Please start the server with: python src/api_server.py")
    except Exception as e:
        print(f"❌ Simulation failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 