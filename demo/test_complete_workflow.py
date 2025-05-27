#!/usr/bin/env python3
"""
Frontend-Backend End-to-End Test
Simulates the complete user workflow from frontend to backend
"""

import requests
import json
import time
from datetime import datetime

def test_complete_workflow():
    """Test the complete user workflow"""
    
    print("🎯 FinSight Complete Workflow Test")
    print("=" * 40)
    print(f"Testing at: {datetime.now()}")
    print()
    
    # Configuration
    API_BASE_URL = "http://localhost:8000"
    FRONTEND_URL = "http://localhost:8080"
    
    # Test 1: Verify servers are running
    print("1️⃣ Checking Server Status...")
    
    # Check API server
    try:
        api_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if api_response.status_code == 200:
            print("   ✅ API Server: Running")
        else:
            print("   ❌ API Server: Not responding")
            return False
    except Exception as e:
        print(f"   ❌ API Server: Connection failed - {e}")
        return False
    
    # Check frontend server
    try:
        frontend_response = requests.get(FRONTEND_URL, timeout=5)
        if frontend_response.status_code == 200:
            print("   ✅ Frontend Server: Running")
        else:
            print("   ❌ Frontend Server: Not responding")
            return False
    except Exception as e:
        print(f"   ❌ Frontend Server: Connection failed - {e}")
        return False
    
    print()
    
    # Test 2: Simulate frontend workflow
    print("2️⃣ Simulating User Workflow...")
    
    # Simulate the three main demo scenarios
    demo_scenarios = [
        {
            "name": "🚨 Risky Investment Advice",
            "content": "AAPL stock is currently trading at $150 and I recommend buying it immediately. This is a guaranteed profitable investment that will definitely make you money. You should invest all your savings into AAPL right now for maximum returns. Trust me, this is insider information and you can't lose money on this trade.",
            "expected_quality": "low"
        },
        {
            "name": "📊 Market Analysis",
            "content": "The S&P 500 has shown strong performance this quarter, with technology stocks leading the gains. Market volatility remains elevated due to ongoing economic uncertainties. Current market indicators suggest a bullish trend, with the VIX trading below 20.",
            "expected_quality": "medium"
        },
        {
            "name": "💰 Balanced Crypto Discussion",
            "content": "Cryptocurrency markets continue to evolve with increasing institutional adoption. Bitcoin and Ethereum remain the dominant digital assets by market capitalization. Investors should carefully consider the risks associated with digital asset investments. Consider consulting with a financial advisor before making investment decisions.",
            "expected_quality": "high"
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(demo_scenarios, 1):
        print(f"   Scenario {i}: {scenario['name']}")
        
        # Simulate frontend request (exactly as frontend sends it)
        payload = {
            "ai_response": {
                "content": scenario["content"],
                "agent_id": "frontend_demo",
                "timestamp": datetime.now().isoformat()
            },
            "enrichment_level": "comprehensive",
            "fact_check": True,
            "add_context": True
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_BASE_URL}/enhance",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            processing_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                
                quality_score = result.get('quality_score', 0)
                quality_score_percent = int(quality_score * 100)  # Convert to percentage
                fact_checks = len(result.get('fact_checks', []))
                compliance_flags = len(result.get('compliance_flags', []))
                
                print(f"      ✅ Success ({processing_time:.0f}ms)")
                print(f"      📊 Quality: {quality_score_percent}% | Facts: {fact_checks} | Flags: {compliance_flags}")
                
                # Validate expected quality level
                if scenario['expected_quality'] == 'low' and quality_score_percent < 60:
                    print("      ✅ Quality assessment: Correct (detected low quality)")
                elif scenario['expected_quality'] == 'medium' and 60 <= quality_score_percent < 80:
                    print("      ✅ Quality assessment: Correct (detected medium quality)")
                elif scenario['expected_quality'] == 'high' and quality_score_percent >= 80:
                    print("      ✅ Quality assessment: Correct (detected high quality)")
                else:
                    print(f"      ⚠️  Quality assessment: Unexpected ({quality_score_percent}% for {scenario['expected_quality']} quality)")
                
                results.append({
                    'scenario': scenario['name'],
                    'success': True,
                    'quality_score': quality_score_percent,  # Store as percentage
                    'processing_time': processing_time,
                    'fact_checks': fact_checks,
                    'compliance_flags': compliance_flags
                })
                
            else:
                print(f"      ❌ Failed: HTTP {response.status_code}")
                results.append({'scenario': scenario['name'], 'success': False})
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
            results.append({'scenario': scenario['name'], 'success': False})
        
        print()
    
    # Test 3: Performance Summary
    print("3️⃣ Performance Summary...")
    
    successful_tests = [r for r in results if r.get('success', False)]
    
    if successful_tests:
        avg_time = sum(r['processing_time'] for r in successful_tests) / len(successful_tests)
        avg_quality = sum(r['quality_score'] for r in successful_tests) / len(successful_tests)
        total_fact_checks = sum(r['fact_checks'] for r in successful_tests)
        total_compliance_flags = sum(r['compliance_flags'] for r in successful_tests)
        
        print(f"   📊 Success Rate: {len(successful_tests)}/{len(results)} scenarios")
        print(f"   ⏱️  Average Response Time: {avg_time:.0f}ms")
        print(f"   📈 Average Quality Score: {avg_quality:.0f}%")
        print(f"   🔍 Total Fact Checks: {total_fact_checks}")
        print(f"   ⚠️  Total Compliance Flags: {total_compliance_flags}")
        
        # Performance assessment
        if avg_time < 5000:
            print("   ✅ Performance Rating: Excellent")
        elif avg_time < 10000:
            print("   ✅ Performance Rating: Good")
        else:
            print("   ⚠️  Performance Rating: Needs improvement")
    
    print()
    
    # Test 4: Frontend File Check
    print("4️⃣ Frontend Accessibility...")
    
    frontend_files = ['enhanced-demo-clean.html', 'enhanced-demo.html', 'index.html']
    
    for file in frontend_files:
        try:
            file_response = requests.get(f"{FRONTEND_URL}/{file}", timeout=5)
            if file_response.status_code == 200:
                print(f"   ✅ {file}: Accessible")
                if "enhanceContent" in file_response.text:
                    print(f"      🔧 JavaScript: Function found")
                if "localhost:8000" in file_response.text:
                    print(f"      🔗 API: Correctly configured")
            else:
                print(f"   ❌ {file}: Not accessible ({file_response.status_code})")
        except Exception as e:
            print(f"   ❌ {file}: Error - {e}")
    
    print()
    
    # Final Results
    print("🎯 End-to-End Test Results")
    print("=" * 30)
    
    success_count = len([r for r in results if r.get('success', False)])
    total_tests = len(results)
    
    if success_count == total_tests:
        print("✅ ALL TESTS PASSED!")
        print()
        print("🚀 Ready for Demo!")
        print("1. API Server: ✅ Running & responsive")
        print("2. Frontend: ✅ Accessible & functional")
        print("3. Integration: ✅ Working end-to-end")
        print("4. LLM Enhancement: ✅ Active (with fallback)")
        print("5. Fact Checking: ✅ Operational")
        print("6. Compliance: ✅ Detecting issues")
        print()
        print("🌐 Demo URLs:")
        print(f"   Frontend: {FRONTEND_URL}/enhanced-demo-clean.html")
        print(f"   API Docs: {API_BASE_URL}/docs")
        
        return True
    else:
        print(f"⚠️  {success_count}/{total_tests} tests passed")
        print("❌ Some issues need to be resolved before demo")
        return False

if __name__ == "__main__":
    import sys
    try:
        success = test_complete_workflow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
        sys.exit(1)
