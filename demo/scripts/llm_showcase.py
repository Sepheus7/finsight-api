#!/usr/bin/env python3
"""
LLM Capabilities Showcase for FinSight
Demonstrates real LLM integration via API endpoints
"""

import sys
import os
import requests
import time
import json
from typing import Dict, Any

class LLMShowcase:
    """Demonstrates FinSight's LLM capabilities via API"""
    
    def __init__(self):
        self.api_base = "http://localhost:8000"
        
    def print_banner(self):
        """Print showcase banner"""
        print("🤖 FinSight LLM Capabilities Showcase")
        print("=" * 50)
        print("🎯 Demonstrating Real AI Integration:")
        print("   • LLM-powered claim extraction")
        print("   • AI-driven fact evaluation")
        print("   • Multi-provider LLM support")
        print("   • Enhanced content generation")
        print()
        
    def test_basic_enhancement(self, content: str) -> Dict[str, Any]:
        """Test basic API enhancement"""
        print("🔍 Basic Content Enhancement")
        print("-" * 30)
        print(f"📝 Input: {content[:100]}...")
        print()
        
        try:
            payload = {
                "ai_response": {
                    "content": content,
                    "agent_id": "llm_showcase"
                },
                "enrichment_level": "standard",
                "fact_check": True,
                "add_context": True
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/enhance",
                json=payload,
                timeout=30
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"⚡ Processing Time: {duration:.2f}s")
                print(f"📊 Quality Score: {result.get('quality_score', 0):.2f}")
                print(f"🔍 Fact Checks: {len(result.get('fact_checks', []))}")
                
                # Show fact check details
                for i, fact_check in enumerate(result.get('fact_checks', []), 1):
                    print(f"   {i}. {fact_check.get('claim', 'Unknown claim')}")
                    print(f"      Status: {fact_check.get('status', 'Unknown')}")
                    print(f"      Confidence: {fact_check.get('confidence', 0):.2f}")
                    print()
                
                return {
                    'result': result,
                    'processing_time': duration,
                    'success': True
                }
            else:
                print(f"❌ API Error: {response.status_code}")
                return {
                    'result': {},
                    'processing_time': duration,
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                'result': {},
                'processing_time': 0,
                'success': False,
                'error': str(e)
            }
    
    def test_comprehensive_enhancement(self, content: str) -> Dict[str, Any]:
        """Test comprehensive API enhancement with LLM"""
        print("🧠 Comprehensive LLM Enhancement")
        print("-" * 30)
        
        try:
            payload = {
                "ai_response": {
                    "content": content,
                    "agent_id": "llm_showcase_comprehensive"
                },
                "enrichment_level": "comprehensive",
                "fact_check": True,
                "add_context": True,
                "use_llm": True
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/enhance",
                json=payload,
                timeout=60
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"⚡ Processing Time: {duration:.2f}s")
                print(f"📊 Quality Score: {result.get('quality_score', 0):.2f}")
                print(f"🔍 Fact Checks: {len(result.get('fact_checks', []))}")
                print(f"🤖 LLM Enhanced: {'Yes' if result.get('llm_enhanced') else 'No'}")
                
                enhanced_content = result.get('enhanced_content', {})
                if enhanced_content:
                    print("✨ Content Enhanced Successfully")
                    print(f"   Original Length: {len(content)} chars")
                    
                    # Handle both string and dict enhanced content
                    if isinstance(enhanced_content, str):
                        enhanced_length = len(enhanced_content)
                        print(f"   Enhanced Length: {enhanced_length} chars")
                    elif isinstance(enhanced_content, dict):
                        enhanced_text = enhanced_content.get('content', '')
                        enhanced_length = len(enhanced_text)
                        print(f"   Enhanced Length: {enhanced_length} chars")
                        
                        # Show enhancement details
                        if enhanced_content.get('improvements'):
                            print("🔧 Improvements Applied:")
                            for improvement in enhanced_content.get('improvements', []):
                                print(f"   • {improvement}")
                    else:
                        print("   Enhanced content format: Unknown")
                
                compliance_flags = result.get('compliance_flags', [])
                if compliance_flags:
                    print(f"⚠️  Compliance Issues Detected: {len(compliance_flags)}")
                    for flag in compliance_flags:
                        print(f"   • {flag}")
                
                return {
                    'result': result,
                    'processing_time': duration,
                    'success': True
                }
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return {
                    'result': {},
                    'processing_time': duration,
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                'result': {},
                'processing_time': 0,
                'success': False,
                'error': str(e)
            }
    
    def run_showcase(self):
        """Run the complete LLM showcase"""
        self.print_banner()
        
        # Test content - problematic financial advice
        test_content = """
        Apple stock is currently trading at $150 per share and is guaranteed to reach $300 
        within the next month. This is based on insider information and you should 
        immediately invest all of your savings into AAPL. The company's AI division 
        will announce revolutionary products that will triple the stock price. 
        This is a risk-free investment opportunity that you cannot miss.
        """
        
        print("🎬 Testing Content:")
        print(f"   {test_content.strip()[:80]}...")
        print()
        
        # Test 1: Basic Enhancement
        basic_results = self.test_basic_enhancement(test_content)
        print("\n" + "="*50 + "\n")
        
        # Test 2: Comprehensive Enhancement with LLM
        comprehensive_results = self.test_comprehensive_enhancement(test_content)
        print("\n" + "="*50 + "\n")
        
        # Summary
        print("📋 LLM Showcase Summary")
        print("-" * 30)
        print(f"🔍 Basic Enhancement: {'✅' if basic_results['success'] else '❌'}")
        print(f"🧠 LLM Enhancement: {'✅' if comprehensive_results['success'] else '❌'}")
        
        total_time = (basic_results['processing_time'] + 
                     comprehensive_results['processing_time'])
        print(f"⚡ Total Processing: {total_time:.2f}s")
        
        if all([basic_results['success'], comprehensive_results['success']]):
            print("\n🎉 All LLM capabilities working perfectly!")
            print("🤖 FinSight is ready to demonstrate real AI integration")
            
            # Show some key metrics
            basic_quality = basic_results['result'].get('quality_score', 0)
            comprehensive_quality = comprehensive_results['result'].get('quality_score', 0)
            
            print(f"\n📊 Quality Improvement:")
            print(f"   Basic: {basic_quality:.2f}")
            print(f"   LLM Enhanced: {comprehensive_quality:.2f}")
            print(f"   Improvement: {((comprehensive_quality - basic_quality) * 100):.1f}%")
            
        else:
            print("\n⚠️  Some LLM features may need configuration")
            print("💡 Check API server and LLM provider settings")

def main():
    """Main showcase function"""
    try:
        showcase = LLMShowcase()
        showcase.run_showcase()
    except KeyboardInterrupt:
        print("\n🛑 Showcase interrupted")
    except Exception as e:
        print(f"\n❌ Showcase error: {e}")

if __name__ == "__main__":
    main()
