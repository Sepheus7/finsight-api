"""
Demo Client for AWS Serverless Financial AI Quality Enhancement API
Tests the deployed serverless endpoints with real financial scenarios
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

class ServerlessFinAIDemoClient:
    def __init__(self, base_url: str):
        """
        Initialize demo client with the deployed API URL
        
        Args:
            base_url: The API Gateway URL (e.g., https://abc123.execute-api.us-east-1.amazonaws.com/dev/)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'FinAI-Demo-Client/1.0'
        })

    def test_health_check(self) -> Dict[str, Any]:
        """Test the health check endpoint"""
        print("🏥 Testing Health Check Endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health Check Passed")
                print(f"   Status: {health_data.get('status')}")
                print(f"   Timestamp: {health_data.get('timestamp')}")
                print(f"   Service: {health_data.get('service')}")
                print(f"   Version: {health_data.get('version')}")
                return health_data
            else:
                print(f"❌ Health Check Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Health Check Error: {str(e)}")
            return {"error": str(e)}

    def test_api_info(self) -> Dict[str, Any]:
        """Test the root API information endpoint"""
        print("\n📋 Testing API Information Endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                api_info = response.json()
                print(f"✅ API Info Retrieved")
                print(f"   Message: {api_info.get('message')}")
                print(f"   Architecture: {api_info.get('architecture')}")
                print(f"   Available Endpoints: {len(api_info.get('endpoints', {}))}")
                
                # Print feature list
                features = api_info.get('features', [])
                print(f"   Features ({len(features)}):")
                for feature in features[:3]:  # Show first 3
                    print(f"     • {feature}")
                if len(features) > 3:
                    print(f"     ... and {len(features) - 3} more")
                
                return api_info
            else:
                print(f"❌ API Info Failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ API Info Error: {str(e)}")
            return {"error": str(e)}

    def test_enhancement(self, scenario_name: str, content: str, 
                        fact_check: bool = True, add_context: bool = True, 
                        enrichment_level: str = "standard") -> Dict[str, Any]:
        """Test the main enhancement endpoint"""
        print(f"\n🧠 Testing Enhancement: {scenario_name}")
        print(f"   Content Preview: {content[:100]}{'...' if len(content) > 100 else ''}")
        
        request_data = {
            "ai_response": {
                "content": content,
                "agent_id": "demo_client",
                "timestamp": datetime.now().isoformat()
            },
            "enrichment_level": enrichment_level,
            "fact_check": fact_check,
            "add_context": add_context
        }
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/enhance", 
                json=request_data,
                timeout=60  # Longer timeout for complex processing
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Enhancement Completed")
                print(f"   Request Time: {(end_time - start_time)*1000:.1f}ms")
                print(f"   Server Processing Time: {result.get('processing_time_ms', 0):.1f}ms")
                print(f"   Quality Score: {result.get('quality_score', 0):.2f}")
                print(f"   Fact Checks: {len(result.get('fact_checks', []))}")
                print(f"   Context Additions: {len(result.get('context_additions', []))}")
                print(f"   Compliance Flags: {len(result.get('compliance_flags', []))}")
                
                # Show fact check results
                fact_checks = result.get('fact_checks', [])
                if fact_checks:
                    print(f"   📊 Fact Check Results:")
                    for i, fc in enumerate(fact_checks[:2]):  # Show first 2
                        status = "✅ Verified" if fc.get('verified') else "⚠️ Unverified"
                        print(f"     {i+1}. {status} - {fc.get('claim', '')[:60]}...")
                        print(f"        Confidence: {fc.get('confidence', 0):.2f}")
                
                # Show compliance flags
                compliance_flags = result.get('compliance_flags', [])
                if compliance_flags:
                    print(f"   ⚖️ Compliance Issues:")
                    for flag in compliance_flags[:2]:  # Show first 2
                        print(f"     • {flag}")
                
                return result
            else:
                print(f"❌ Enhancement Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return {"error": f"HTTP {response.status_code}", "response": response.text}
                
        except Exception as e:
            print(f"❌ Enhancement Error: {str(e)}")
            return {"error": str(e)}

    def run_comprehensive_demo(self):
        """Run a comprehensive demo of the serverless API"""
        print("=" * 70)
        print("🏦 FINANCIAL AI QUALITY ENHANCEMENT API - SERVERLESS DEMO")
        print("=" * 70)
        print(f"API URL: {self.base_url}")
        print(f"Demo Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # Test 1: Health Check
        health_result = self.test_health_check()
        
        # Test 2: API Information
        info_result = self.test_api_info()

        # Test 3: Investment Advisory Scenario
        investment_content = """
        I recommend buying AAPL stock immediately as it's currently trading at $180 per share. 
        This is a guaranteed investment that will provide 25% returns within 6 months. 
        Apple's market cap is $3 trillion and the company has strong fundamentals. 
        Everyone should invest their entire portfolio in AAPL regardless of their risk tolerance.
        This investment is completely risk-free and will definitely make you rich.
        """
        
        investment_result = self.test_enhancement(
            "Investment Advisory with Compliance Issues",
            investment_content,
            fact_check=True,
            add_context=True,
            enrichment_level="comprehensive"
        )

        # Test 4: Market Analysis Scenario
        market_content = """
        The current inflation rate is approximately 3.2% and the Federal Reserve has 
        maintained interest rates at 5.25-5.50%. This economic environment creates 
        volatility in equity markets. Bitcoin has shown strong performance this year,
        while traditional bonds face headwinds from rising rates. Gold prices have 
        been fluctuating based on economic uncertainty.
        """
        
        market_result = self.test_enhancement(
            "Market Analysis with Economic Context",
            market_content,
            fact_check=True,
            add_context=True,
            enrichment_level="standard"
        )

        # Test 5: Cryptocurrency Discussion
        crypto_content = """
        Cryptocurrency investments offer exciting opportunities for portfolio growth.
        Bitcoin and Ethereum have shown remarkable returns over the past decade.
        These digital assets provide diversification benefits and hedge against
        traditional currency devaluation. Consider allocating 5-10% of your portfolio
        to cryptocurrencies based on your risk tolerance and investment timeline.
        """
        
        crypto_result = self.test_enhancement(
            "Cryptocurrency Investment Discussion",
            crypto_content,
            fact_check=True,
            add_context=True,
            enrichment_level="standard"
        )

        # Summary
        print("\n" + "=" * 70)
        print("📊 DEMO SUMMARY")
        print("=" * 70)
        
        results = [
            ("Health Check", health_result),
            ("API Information", info_result),
            ("Investment Advisory", investment_result),
            ("Market Analysis", market_result),
            ("Cryptocurrency Discussion", crypto_result)
        ]
        
        for test_name, result in results:
            if "error" in result:
                print(f"❌ {test_name}: Failed - {result.get('error', 'Unknown error')}")
            else:
                print(f"✅ {test_name}: Passed")
                if 'quality_score' in result:
                    print(f"   Quality Score: {result['quality_score']:.2f}")
                if 'compliance_flags' in result and result['compliance_flags']:
                    print(f"   Compliance Issues: {len(result['compliance_flags'])}")

        print("\n🎯 Key Insights:")
        print("• Serverless architecture provides scalable, cost-effective deployment")
        print("• Each microservice (fact-check, context, compliance) operates independently")
        print("• Real-time processing with automatic scaling based on demand")
        print("• Comprehensive compliance checking helps ensure regulatory adherence")
        print("• Quality scoring enables continuous improvement of AI outputs")
        
        return results


def main():
    """Main demo function"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python serverless_demo_client.py <API_GATEWAY_URL>")
        print("Example: python serverless_demo_client.py https://abc123.execute-api.us-east-1.amazonaws.com/dev")
        sys.exit(1)
    
    api_url = sys.argv[1]
    
    # Initialize demo client
    demo_client = ServerlessFinAIDemoClient(api_url)
    
    # Run comprehensive demo
    results = demo_client.run_comprehensive_demo()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"serverless_demo_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            "demo_timestamp": datetime.now().isoformat(),
            "api_url": api_url,
            "results": results
        }, f, indent=2, default=str)
    
    print(f"\n💾 Demo results saved to: {results_file}")


if __name__ == "__main__":
    main()
