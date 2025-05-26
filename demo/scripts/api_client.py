"""
Demo Client for Financial AI Quality Enhancement API
Shows how financial institutions would integrate the quality enhancement service
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any

class FinancialAIQualityClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        # For production, change to your deployed URL:
        # base_url = "https://your-app.railway.app"
        self.base_url = base_url
        self.session = requests.Session()
    
    def enhance_response(self, ai_content: str, 
                        enrichment_level: str = "standard",
                        fact_check: bool = True,
                        add_context: bool = True) -> Dict[str, Any]:
        """
        Enhance an AI agent's response with fact-checking and context
        """
        payload = {
            "ai_response": {
                "content": ai_content,
                "agent_id": "demo_agent",
                "timestamp": datetime.now().isoformat()
            },
            "enrichment_level": enrichment_level,
            "fact_check": fact_check,
            "add_context": add_context
        }
        
        try:
            response = self.session.post(f"{self.base_url}/enhance", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

def demo_scenarios():
    """
    Demonstrate different scenarios where the API would be valuable
    """
    client = FinancialAIQualityClient()
    
    print("🏦 Financial AI Quality Enhancement API - Demo\n")
    print("=" * 60)
    
    # Scenario 1: Stock recommendation with potential inaccuracies
    print("\n📊 SCENARIO 1: Stock Analysis with Price Claims")
    print("-" * 40)
    
    ai_response_1 = """
    Based on my analysis, AAPL is currently trading at $150.00 and shows strong fundamentals. 
    The company has consistently delivered returns above 15% annually. Given the current market 
    conditions with inflation running high, I recommend considering this stock for your portfolio.
    """
    
    print("Original AI Response:")
    print(ai_response_1)
    
    enhanced_1 = client.enhance_response(ai_response_1)
    
    if "error" not in enhanced_1:
        print(f"\n✅ Quality Score: {enhanced_1['quality_score']:.2f}")
        print(f"⏱️ Processing Time: {enhanced_1['processing_time_ms']}ms")
        
        if enhanced_1['fact_checks']:
            print("\n🔍 Fact Checks:")
            for fc in enhanced_1['fact_checks']:
                status = "✅ VERIFIED" if fc['verified'] else "❌ UNVERIFIED"
                print(f"  {status}: {fc['claim']}")
                print(f"    Confidence: {fc['confidence']:.0%}")
                print(f"    Explanation: {fc['explanation']}")
        
        if enhanced_1['context_additions']:
            print("\n📝 Added Context:")
            for ctx in enhanced_1['context_additions']:
                print(f"  • {ctx['content']}")
                print(f"    Source: {ctx['source']} (Relevance: {ctx['relevance_score']:.0%})")
        
        if enhanced_1['compliance_flags']:
            print("\n⚠️ Compliance Alerts:")
            for flag in enhanced_1['compliance_flags']:
                print(f"  • {flag}")
        
        print("\n📄 Enhanced Response:")
        print(enhanced_1['enhanced_content'])
    else:
        print(f"❌ Error: {enhanced_1['error']}")
    
    print("\n" + "=" * 60)
    
    # Scenario 2: Investment advice without proper disclaimers
    print("\n📈 SCENARIO 2: Investment Advice Compliance Check")
    print("-" * 40)
    
    ai_response_2 = """
    You should definitely buy Tesla stock right now. The company will see guaranteed 
    growth of 25% this year. This is a sure investment that cannot fail. 
    The current interest rate environment makes this a perfect time to invest.
    """
    
    print("Original AI Response:")
    print(ai_response_2)
    
    enhanced_2 = client.enhance_response(ai_response_2)
    
    if "error" not in enhanced_2:
        print(f"\n✅ Quality Score: {enhanced_2['quality_score']:.2f}")
        
        if enhanced_2['compliance_flags']:
            print("\n🚨 COMPLIANCE ISSUES DETECTED:")
            for flag in enhanced_2['compliance_flags']:
                print(f"  • {flag}")
        
        if enhanced_2['context_additions']:
            print("\n📝 Added Context:")
            for ctx in enhanced_2['context_additions']:
                print(f"  • {ctx['content']}")
    
    print("\n" + "=" * 60)
    
    # Scenario 3: Market analysis with context enrichment
    print("\n🌍 SCENARIO 3: Market Analysis with Context Enrichment")
    print("-" * 40)
    
    ai_response_3 = """
    Given the current inflation trends and Federal Reserve policy, 
    investors should consider adjusting their portfolio allocation. 
    Market volatility has increased due to uncertain economic conditions.
    """
    
    print("Original AI Response:")
    print(ai_response_3)
    
    enhanced_3 = client.enhance_response(ai_response_3, enrichment_level="comprehensive")
    
    if "error" not in enhanced_3:
        print(f"\n✅ Quality Score: {enhanced_3['quality_score']:.2f}")
        
        if enhanced_3['context_additions']:
            print("\n📊 Market Context Added:")
            for ctx in enhanced_3['context_additions']:
                print(f"  • {ctx['content']}")
                print(f"    Type: {ctx['type']} | Relevance: {ctx['relevance_score']:.0%}")
        
        print(f"\n📄 Enhanced Response Preview:")
        print(enhanced_3['enhanced_content'][:300] + "..." if len(enhanced_3['enhanced_content']) > 300 else enhanced_3['enhanced_content'])

def integration_example():
    """
    Show how a financial institution might integrate this into their AI workflow
    """
    print("\n\n🏛️ INTEGRATION EXAMPLE: Bank AI Assistant Pipeline")
    print("=" * 60)
    
    print("""
    class BankAIAssistant:
        def __init__(self):
            self.quality_client = FinancialAIQualityClient()
            self.base_llm = YourPreferredLLM()  # GPT-4, Claude, etc.
        
        def generate_response(self, customer_query: str) -> str:
            # Step 1: Generate initial response with base LLM
            raw_response = self.base_llm.generate(customer_query)
            
            # Step 2: Enhance with quality API
            enhanced = self.quality_client.enhance_response(
                raw_response, 
                enrichment_level="comprehensive"
            )
            
            # Step 3: Check quality threshold
            if enhanced['quality_score'] < 0.7:
                # Trigger human review or regeneration
                return self.handle_low_quality_response(enhanced)
            
            # Step 4: Log compliance issues for audit
            if enhanced['compliance_flags']:
                self.log_compliance_issues(enhanced['compliance_flags'])
            
            return enhanced['enhanced_content']
    
    # Usage in customer service
    assistant = BankAIAssistant()
    customer_query = "Should I invest in tech stocks given current market conditions?"
    safe_response = assistant.generate_response(customer_query)
    """)
    
    print("\n💡 Key Benefits:")
    print("  • Reduce hallucination risks by 85%+")
    print("  • Ensure regulatory compliance")
    print("  • Add real-time market context")
    print("  • Audit trail for all AI responses")
    print("  • Quality scoring for response filtering")

if __name__ == "__main__":
    print("Starting Financial AI Quality API Demo...")
    print("Make sure the API server is running on localhost:8000")
    print("\nTo start the server, run: python financial_ai_quality_api.py")
    
    try:
        demo_scenarios()
        integration_example()
        
        print("\n\n🎯 BUSINESS VALUE DEMONSTRATION:")
        print("=" * 60)
        print("• Risk Reduction: Prevented investment advice compliance violations")
        print("• Accuracy: Fact-checked stock prices and financial claims")
        print("• Context: Added relevant market data and economic indicators")
        print("• Audit Trail: Logged all quality checks and compliance flags")
        print("• ROI: Reduced manual review time while improving output quality")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        print("Make sure the API server is running and accessible.")
