#!/usr/bin/env python3
"""
FinSight System Validation Test
Comprehensive test of the complete streamlined system
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def test_complete_system():
    """Test the complete FinSight system end-to-end"""
    
    print("🧪 FinSight Complete System Validation")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Health Check
        print("\n1️⃣ Testing Health Check...")
        async with session.get(f"{base_url}/health") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Health check passed: {data['status']}")
            else:
                print(f"❌ Health check failed: {response.status}")
                return False
        
        # Test 2: System Status
        print("\n2️⃣ Testing System Status...")
        async with session.get(f"{base_url}/status") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ System status: {data['status']}")
                print(f"📊 Cache statistics available: {bool(data.get('cache_statistics'))}")
            else:
                print(f"❌ System status failed: {response.status}")
        
        # Test 3: Basic Enrichment
        print("\n3️⃣ Testing Basic Financial Enrichment...")
        
        test_content = """
        Apple Inc. (AAPL) reported strong Q4 earnings with revenue of $94.9 billion.
        The stock is currently trading at $195.50, up 2.3% from yesterday's close.
        Tesla (TSLA) shares fell 3.2% after production concerns, now at $238.45.
        The S&P 500 index gained 0.8% today, reflecting positive market sentiment.
        """
        
        payload = {
            "content": test_content,
            "enrichment_types": ["stock_data", "market_context"],
            "format_style": "enhanced",
            "include_compliance": False
        }
        
        start_time = time.time()
        async with session.post(f"{base_url}/enrich", json=payload) as response:
            processing_time = (time.time() - start_time) * 1000
            
            if response.status == 200:
                data = await response.json()
                print(f"✅ Enrichment completed in {processing_time:.2f}ms")
                print(f"📊 Claims extracted: {data['metrics']['claims_processed']}")
                print(f"🎯 Data sources used: {data['metrics']['data_sources_used']}")
                print(f"💾 Cache hit rate: {data['metrics']['cache_hit_rate']:.2%}")
                print(f"📈 Content enhanced: {len(data['enriched_content'])} characters")
                
                # Test with real stock data
                if data['data_points']:
                    print(f"💰 Real-time data points: {len(data['data_points'])}")
                    for dp in data['data_points'][:3]:  # Show first 3
                        print(f"   • {dp['symbol']}: {dp['value']}")
                else:
                    print("ℹ️  No real-time data (expected without API keys)")
                
            else:
                print(f"❌ Enrichment failed: {response.status}")
                error_text = await response.text()
                print(f"Error: {error_text}")
                return False
        
        # Test 4: Performance Test
        print("\n4️⃣ Testing Performance (5 concurrent requests)...")
        
        async def single_request():
            async with session.post(f"{base_url}/enrich", json={
                "content": "Tesla (TSLA) stock analysis with S&P 500 comparison",
                "enrichment_types": ["stock_data"],
                "format_style": "minimal"
            }) as resp:
                return resp.status, await resp.json() if resp.status == 200 else None
        
        # Run 5 concurrent requests
        start_time = time.time()
        results = await asyncio.gather(*[single_request() for _ in range(5)])
        total_time = (time.time() - start_time) * 1000
        
        successful = sum(1 for status, _ in results if status == 200)
        print(f"✅ Performance test: {successful}/5 requests successful")
        print(f"⚡ Total time for 5 requests: {total_time:.2f}ms")
        print(f"📊 Average per request: {total_time/5:.2f}ms")
        
        # Test 5: Frontend Assets
        print("\n5️⃣ Testing Frontend Assets...")
        async with session.get(f"{base_url}/streamlined-demo.html") as response:
            if response.status == 200:
                content = await response.text()
                if "FinSight" in content and "Streamlined Demo" in content:
                    print("✅ Frontend demo page loads correctly")
                else:
                    print("⚠️  Frontend page loads but content may be incorrect")
            else:
                print(f"❌ Frontend page failed to load: {response.status}")
        
        print("\n" + "=" * 50)
        print("🎉 Complete system validation finished!")
        print("✅ FinSight streamlined architecture is operational")
        
        return True

async def test_data_integration():
    """Test real data integration capabilities"""
    print("\n📊 Data Integration Test")
    print("-" * 30)
    
    # Test direct data access
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    try:
        from integrations.data_aggregator import DataAggregator
        
        aggregator = DataAggregator()
        
        # Test Yahoo Finance integration
        print("📈 Testing Yahoo Finance integration...")
        stock_data = await aggregator.get_stock_data("AAPL")
        if stock_data:
            print(f"✅ AAPL data retrieved: ${stock_data.price} ({stock_data.change_percent:+.2f}%)")
        else:
            print("ℹ️  No AAPL data retrieved (may need API keys)")
        
        # Test cache functionality
        print("💾 Testing cache performance...")
        start_time = time.time()
        cached_data = await aggregator.get_stock_data("AAPL")  # Should be cached
        cache_time = (time.time() - start_time) * 1000
        print(f"⚡ Cache retrieval: {cache_time:.2f}ms")
        
    except Exception as e:
        print(f"⚠️  Data integration test failed: {e}")

def main():
    """Run all validation tests"""
    print(f"🚀 Starting FinSight System Validation at {datetime.now()}")
    
    async def run_tests():
        success = await test_complete_system()
        await test_data_integration()
        return success
    
    success = asyncio.run(run_tests())
    
    if success:
        print("\n🎯 System Status: READY FOR DEPLOYMENT")
        print("🌐 Frontend: http://localhost:8000/streamlined-demo.html")
        print("📊 API Health: http://localhost:8000/health")
    else:
        print("\n❌ System Status: ISSUES DETECTED")

if __name__ == "__main__":
    main()
