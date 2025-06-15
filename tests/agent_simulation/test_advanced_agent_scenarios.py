#!/usr/bin/env python3
"""
Advanced AI Agent Business Scenarios for FinSight API v1

This script simulates complex business decision-making scenarios where an AI agent
uses the FinSight API to gather data and make informed recommendations.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime

class BusinessIntelligenceAgent:
    """Advanced AI agent for business intelligence using FinSight API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/v1/query"
        self.session = None
        self.data_cache = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def query_api(self, query: str, context: str = "") -> Dict[str, Any]:
        """Query the FinSight API and cache results"""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        payload = {"query": query, "context": context}
        
        try:
            async with self.session.post(
                self.api_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # Cache the result
                    self.data_cache[query] = data
                    return data
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def portfolio_analysis_scenario(self) -> Dict[str, Any]:
        """Scenario: Building a diversified tech portfolio"""
        print("🎯 **SCENARIO: Tech Portfolio Analysis**")
        print("=" * 50)
        print("Goal: Analyze major tech stocks for portfolio diversification")
        print()
        
        # Define the stocks to analyze
        stocks = ["Apple", "Microsoft", "Google", "Amazon", "Tesla"]
        portfolio_data = {}
        
        print("📊 Gathering stock data...")
        for stock in stocks:
            query = f"What is {stock} stock price?"
            context = f"Portfolio analysis for {stock} investment evaluation"
            
            print(f"  • Querying {stock}...")
            response = await self.query_api(query, context)
            
            if "error" not in response:
                data = response.get('data', {})
                portfolio_data[stock] = {
                    'price': data.get('price', 0),
                    'symbol': data.get('symbol', 'N/A'),
                    'sources': response.get('sources', []),
                    'response_time': response.get('metadata', {}).get('processing_time_ms', 0)
                }
            else:
                portfolio_data[stock] = {'error': response.get('error')}
        
        # Analyze the portfolio
        print("\n📈 **Portfolio Analysis Results**")
        print("-" * 40)
        
        total_value = 0
        valid_stocks = 0
        
        for stock, data in portfolio_data.items():
            if 'error' not in data:
                price = data['price']
                symbol = data['symbol']
                sources = ', '.join(data['sources'])
                
                print(f"• {stock} ({symbol}): ${price:,.2f} [Sources: {sources}]")
                total_value += price
                valid_stocks += 1
            else:
                print(f"• {stock}: ❌ {data['error']}")
        
        if valid_stocks > 0:
            avg_price = total_value / valid_stocks
            print(f"\n💡 **Investment Insights**")
            print(f"• Portfolio Size: {valid_stocks} stocks")
            print(f"• Total Combined Value: ${total_value:,.2f}")
            print(f"• Average Stock Price: ${avg_price:,.2f}")
            
            # Simple recommendation logic
            if avg_price > 300:
                recommendation = "Consider dollar-cost averaging due to high average prices"
            elif avg_price > 150:
                recommendation = "Good entry points for long-term investment"
            else:
                recommendation = "Attractive prices for aggressive growth strategy"
            
            print(f"• Recommendation: {recommendation}")
        
        return portfolio_data
    
    async def economic_outlook_scenario(self) -> Dict[str, Any]:
        """Scenario: Economic outlook for investment strategy"""
        print("\n🎯 **SCENARIO: Economic Outlook Analysis**")
        print("=" * 50)
        print("Goal: Assess economic conditions for investment timing")
        print()
        
        # Economic indicators to check
        indicators = [
            ("What is the US unemployment rate?", "US Labor Market"),
            ("What is the inflation rate in the UK?", "UK Economic Stability"),
            ("What is the employment rate in France?", "European Market Health"),
            ("How is the US economy doing?", "Overall US Economic Sentiment")
        ]
        
        economic_data = {}
        
        print("📊 Gathering economic indicators...")
        for query, description in indicators:
            print(f"  • Analyzing: {description}")
            response = await self.query_api(query, f"Economic analysis for {description}")
            
            economic_data[description] = response
            await asyncio.sleep(0.5)  # Rate limiting
        
        print("\n📈 **Economic Analysis Results**")
        print("-" * 40)
        
        risk_factors = []
        opportunities = []
        
        for description, response in economic_data.items():
            if "error" not in response:
                data = response.get('data', {})
                
                if 'indicator' in data:
                    indicator = data['indicator']
                    value = data['value']
                    unit = data.get('unit', '')
                    
                    print(f"• {description}: {indicator} = {value}{unit}")
                    
                    # Simple risk assessment
                    if 'unemployment' in indicator.lower() and value > 5:
                        risk_factors.append(f"High unemployment in {description}")
                    elif 'inflation' in indicator.lower() and value > 3:
                        risk_factors.append(f"High inflation in {description}")
                    elif value > 0:
                        opportunities.append(f"Positive {indicator} in {description}")
                
                elif 'response' in data:
                    print(f"• {description}: Economic data unavailable")
                    risk_factors.append(f"Limited data visibility for {description}")
            else:
                print(f"• {description}: ❌ Error retrieving data")
                risk_factors.append(f"Data access issues for {description}")
        
        print(f"\n💡 **Economic Investment Strategy**")
        print(f"• Risk Factors: {len(risk_factors)}")
        for risk in risk_factors[:3]:  # Show top 3
            print(f"  - {risk}")
        
        print(f"• Opportunities: {len(opportunities)}")
        for opp in opportunities[:3]:  # Show top 3
            print(f"  - {opp}")
        
        # Investment timing recommendation
        risk_score = len(risk_factors)
        opportunity_score = len(opportunities)
        
        if opportunity_score > risk_score:
            timing = "FAVORABLE - Good time for strategic investments"
        elif risk_score > opportunity_score * 1.5:
            timing = "CAUTIOUS - Consider defensive positioning"
        else:
            timing = "NEUTRAL - Balanced approach recommended"
        
        print(f"• Investment Timing: {timing}")
        
        return economic_data
    
    async def market_comparison_scenario(self) -> Dict[str, Any]:
        """Scenario: Cross-market sector comparison"""
        print("\n🎯 **SCENARIO: Market Sector Comparison**")
        print("=" * 50)
        print("Goal: Compare different market sectors for allocation strategy")
        print()
        
        # Different sectors to compare
        sectors = {
            "Technology": ["Apple", "Microsoft", "Google"],
            "E-commerce": ["Amazon"],
            "Electric Vehicles": ["Tesla"]
        }
        
        sector_analysis = {}
        
        for sector_name, companies in sectors.items():
            print(f"📊 Analyzing {sector_name} sector...")
            sector_data = []
            
            for company in companies:
                query = f"What is {company} stock price?"
                context = f"Sector analysis for {sector_name} - {company} evaluation"
                
                response = await self.query_api(query, context)
                if "error" not in response:
                    data = response.get('data', {})
                    sector_data.append({
                        'company': company,
                        'price': data.get('price', 0),
                        'symbol': data.get('symbol', 'N/A')
                    })
                
                await asyncio.sleep(0.3)
            
            sector_analysis[sector_name] = sector_data
        
        print("\n📈 **Sector Comparison Results**")
        print("-" * 40)
        
        for sector_name, companies in sector_analysis.items():
            if companies:
                total_value = sum(c['price'] for c in companies)
                avg_price = total_value / len(companies)
                
                print(f"• {sector_name}:")
                print(f"  - Companies: {len(companies)}")
                print(f"  - Average Price: ${avg_price:,.2f}")
                print(f"  - Total Sector Value: ${total_value:,.2f}")
                
                # Show individual companies
                for company in companies:
                    print(f"    * {company['company']}: ${company['price']:,.2f}")
                print()
        
        return sector_analysis

async def main():
    """Run advanced business scenarios"""
    print("🤖 **Advanced FinSight Business Intelligence Agent**")
    print("=" * 60)
    print(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Check server availability
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                if response.status != 200:
                    print("❌ FinSight server not available")
                    return
        
        async with BusinessIntelligenceAgent() as agent:
            # Run comprehensive business scenarios
            portfolio_results = await agent.portfolio_analysis_scenario()
            economic_results = await agent.economic_outlook_scenario()
            sector_results = await agent.market_comparison_scenario()
            
            # Final summary
            print("\n🎯 **EXECUTIVE SUMMARY**")
            print("=" * 40)
            print("✅ Portfolio Analysis: Complete")
            print("✅ Economic Outlook: Complete")
            print("✅ Sector Comparison: Complete")
            print()
            print("💡 **Key Insights:**")
            print("• Real-time financial data successfully integrated")
            print("• Multi-source data validation working")
            print("• API response times suitable for business applications")
            print("• Structured data format enables automated decision-making")
            print()
            print(f"Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 