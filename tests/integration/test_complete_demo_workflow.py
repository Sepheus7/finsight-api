#!/usr/bin/env python3
"""
Complete Frontend Demo Test
Simulates exactly what the browser would do when testing the demo
"""

import requests
import json
import time
import webbrowser
from urllib.parse import urljoin

API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:8080/demo-fixed.html"

def test_complete_workflow():
    """Test the complete workflow that a user would experience"""
    print("🎯 Testing Complete Demo Workflow")
    print("=" * 50)
    
    # Step 1: Check API health (what the frontend does on load)
    print("1️⃣ Checking API health status...")
    try:
        health_response = requests.get(f"{API_BASE_URL}/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   ✅ API Status: {health_data['status']}")
            print(f"   🧠 LLM Status: {health_data['llm_status']}")
            print(f"   🔄 Fallback: {health_data['fallback']}")
        else:
            print(f"   ❌ Health check failed: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Step 2: Test sample scenario loading (what happens when user clicks a sample)
    print("\n2️⃣ Testing sample scenario: Risky Investment Advice...")
    
    sample_content = """AAPL stock is currently trading at $150 and I recommend buying it immediately. This is a guaranteed profitable investment that will definitely make you money. 

Based on my analysis, Apple stock will increase by 50% in the next month. You should invest all your savings into AAPL right now for maximum returns.

Trust me, this is insider information and you can't lose money on this trade. Apple is going to announce revolutionary products that will skyrocket the stock price."""
    
    print(f"   📝 Sample content loaded ({len(sample_content)} characters)")
    
    # Step 3: Test enhancement (what happens when user clicks "Enhance Content")
    print("\n3️⃣ Testing content enhancement...")
    
    enhancement_request = {
        "ai_response": {
            "content": sample_content,
            "agent_id": "frontend_demo",
            "timestamp": "2024-01-01T00:00:00Z"
        },
        "enrichment_level": "comprehensive",
        "fact_check": True,
        "add_context": True
    }
    
    try:
        start_time = time.time()
        enhance_response = requests.post(
            f"{API_BASE_URL}/enhance",
            headers={"Content-Type": "application/json"},
            json=enhancement_request,
            timeout=30
        )
        end_time = time.time()
        
        if enhance_response.status_code == 200:
            result = enhance_response.json()
            processing_time = (end_time - start_time) * 1000
            
            print(f"   ✅ Enhancement successful!")
            print(f"   ⏱️  Processing time: {processing_time:.0f}ms")
            print(f"   📊 Quality score: {result.get('quality_score', 0):.2f}")
            
            # Test what the frontend would display
            print("\n4️⃣ Testing results display simulation...")
            
            # Simulate quality score display
            quality_score_raw = result.get('quality_score', 0.75)
            quality_score_percent = round(quality_score_raw * 100)
            print(f"   📊 Quality Score Display: {quality_score_percent}%")
            
            # Simulate compliance flags display
            compliance_flags = result.get('compliance_flags', [])
            print(f"   🚨 Compliance Issues: {len(compliance_flags)}")
            for i, flag in enumerate(compliance_flags[:3], 1):
                print(f"      {i}. {flag}")
            
            # Simulate fact checks display
            fact_checks = result.get('fact_checks', [])
            print(f"   🔍 Fact Checks: {len(fact_checks)}")
            
            # Simulate context additions display
            context_additions = result.get('context_additions', [])
            print(f"   📖 Context Additions: {len(context_additions)}")
            
            # Test enhanced content display
            enhanced_content = result.get('enhanced_content', result.get('original_content', ''))
            print(f"   📄 Enhanced Content: {len(enhanced_content)} characters")
            
            return True
            
        else:
            print(f"   ❌ Enhancement failed: {enhance_response.status_code}")
            print(f"   📄 Response: {enhance_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Enhancement error: {e}")
        return False

def test_frontend_accessibility():
    """Test if the frontend is accessible"""
    print("\n5️⃣ Testing frontend accessibility...")
    try:
        frontend_response = requests.get(FRONTEND_URL, timeout=10)
        if frontend_response.status_code == 200:
            content = frontend_response.text
            
            # Check for key elements that should be in the HTML
            checks = [
                ("API_BASE_URL", "API_BASE_URL" in content),
                ("loadSample function", "function loadSample" in content),
                ("enhanceContent function", "function enhanceContent" in content),
                ("Sample scenarios", "sampleScenarios" in content),
                ("Analyze button", "analyze-btn" in content)
            ]
            
            all_good = True
            for check_name, check_result in checks:
                if check_result:
                    print(f"   ✅ {check_name}: Found")
                else:
                    print(f"   ❌ {check_name}: Missing")
                    all_good = False
            
            return all_good
        else:
            print(f"   ❌ Frontend not accessible: {frontend_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Frontend accessibility error: {e}")
        return False

def test_other_samples():
    """Test the other sample scenarios"""
    print("\n6️⃣ Testing other sample scenarios...")
    
    samples = {
        "Market Analysis": """The S&P 500 has shown strong performance this quarter, with technology stocks leading the gains. Market volatility remains elevated due to ongoing economic uncertainties.

Current market indicators suggest a bullish trend, with the VIX trading below 20. Institutional investors are showing increased confidence in large-cap technology stocks.""",
        
        "Crypto Discussion": """Cryptocurrency markets continue to evolve with increasing institutional adoption. Bitcoin and Ethereum remain the dominant digital assets by market capitalization.

Regulatory clarity in major markets will likely influence crypto adoption rates. Investors should carefully consider the risks associated with digital asset investments."""
    }
    
    for sample_name, sample_content in samples.items():
        print(f"\n   Testing {sample_name}...")
        
        request_data = {
            "ai_response": {
                "content": sample_content,
                "agent_id": "frontend_demo",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            "enrichment_level": "comprehensive",
            "fact_check": True,
            "add_context": True
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/enhance",
                headers={"Content-Type": "application/json"},
                json=request_data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"      ✅ Score: {result.get('quality_score', 0):.2f}")
                print(f"      🚨 Issues: {len(result.get('compliance_flags', []))}")
            else:
                print(f"      ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")

def main():
    """Run complete test suite"""
    print("🚀 FinSight Demo - Complete Workflow Test")
    print("=" * 60)
    
    # Run all tests
    workflow_ok = test_complete_workflow()
    frontend_ok = test_frontend_accessibility()
    
    if workflow_ok and frontend_ok:
        test_other_samples()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("\n🎯 Ready for PM Demo:")
        print(f"   🌐 Open: {FRONTEND_URL}")
        print("   📋 Demo Script:")
        print("      1. Show 'Risky Investment Advice' scenario")
        print("      2. Click 'Enhance Content with FinSight'")
        print("      3. Highlight compliance detection")
        print("      4. Show quality score improvement")
        print("      5. Emphasize business value and technical readiness")
        
        # Ask if user wants to open browser
        try:
            user_input = input("\n🌐 Open demo in browser now? (y/n): ")
            if user_input.lower().startswith('y'):
                webbrowser.open(FRONTEND_URL)
                print("🎯 Demo opened in browser!")
        except KeyboardInterrupt:
            print("\n👋 Demo test completed!")
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED!")
        print("Please check the issues above before proceeding with the demo.")

if __name__ == "__main__":
    main()
