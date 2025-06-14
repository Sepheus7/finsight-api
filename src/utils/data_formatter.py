"""
Data Formatter for Financial Content Enrichment
Intelligent formatting of enriched content with financial data integration
Focus: Clean, readable output that enhances the original content
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from models.financial_models import FinancialClaim, ClaimType
from models.enrichment_models import DataPoint

logger = logging.getLogger(__name__)

class DataFormatter:
    """
    Formats enriched financial content with real-time data
    Provides multiple output styles for different use cases
    """
    
    def __init__(self):
        self.formatting_styles = {
            'enhanced': self._format_enhanced,
            'inline': self._format_inline,
            'appendix': self._format_appendix,
            'minimal': self._format_minimal
        }
    
    async def format_response(self, original_content: str, claims: List[FinancialClaim], 
                            data: Dict[str, Any], format_style: str = 'enhanced') -> str:
        """
        Format the enriched content based on the specified style
        """
        formatter = self.formatting_styles.get(format_style, self._format_enhanced)
        
        try:
            formatted_content = await formatter(original_content, claims, data)
            logger.info(f"Content formatted using '{format_style}' style")
            return formatted_content
        except Exception as e:
            logger.error(f"Formatting failed: {e}")
            return original_content  # Fallback to original
    
    async def _format_enhanced(self, content: str, claims: List[FinancialClaim], 
                             data: Dict[str, Any]) -> str:
        """
        Enhanced formatting with inline data integration and appendix
        """
        enhanced_content = content
        enrichment_notes = []
        
        # Process each claim and add inline enhancements
        for claim in claims:
            if claim.claim_type == ClaimType.STOCK_PRICE and claim.entities:
                symbol = claim.entities[0]  # Get first entity as symbol
                stock_data = self._find_stock_data(symbol, data)
                if stock_data:
                    inline_info = self._format_stock_inline(symbol, stock_data)
                    enhanced_content = self._insert_inline_data(
                        enhanced_content, claim, inline_info
                    )
                    
                    # Add detailed info to appendix
                    detailed_info = self._format_stock_detailed(symbol, stock_data)
                    enrichment_notes.append(detailed_info)
        
        # Add economic context if available
        economic_data = self._find_economic_data(data)
        if economic_data:
            econ_summary = self._format_economic_summary(economic_data)
            enrichment_notes.append(econ_summary)
        
        # Combine content with enrichment appendix
        if enrichment_notes:
            enhanced_content += "\n\n---\n**FinSight Real-Time Data:**\n"
            for note in enrichment_notes:
                enhanced_content += f"\n{note}"
            
            enhanced_content += f"\n\n*Data updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*"
        
        return enhanced_content
    
    async def _format_inline(self, content: str, claims: List[FinancialClaim], 
                           data: Dict[str, Any]) -> str:
        """
        Inline formatting with data integrated directly into the text
        """
        enhanced_content = content
        
        for claim in claims:
            if claim.claim_type == ClaimType.STOCK_PRICE and claim.symbol:
                stock_data = self._find_stock_data(claim.symbol, data)
                if stock_data:
                    inline_enhancement = self._format_inline_stock_data(claim.symbol, stock_data)
                    enhanced_content = self._insert_inline_data(
                        enhanced_content, claim, inline_enhancement
                    )
        
        return enhanced_content
    
    async def _format_appendix(self, content: str, claims: List[FinancialClaim], 
                             data: Dict[str, Any]) -> str:
        """
        Appendix formatting with all data at the end
        """
        appendix_sections = []
        
        # Stock data section
        stock_info = []
        for claim in claims:
            if claim.claim_type == ClaimType.STOCK_PRICE and claim.symbol:
                stock_data = self._find_stock_data(claim.symbol, data)
                if stock_data:
                    stock_summary = self._format_stock_appendix(claim.symbol, stock_data)
                    stock_info.append(stock_summary)
        
        if stock_info:
            appendix_sections.append("**Stock Information:**\n" + "\n".join(stock_info))
        
        # Economic data section
        economic_data = self._find_economic_data(data)
        if economic_data:
            econ_section = "**Economic Context:**\n" + self._format_economic_summary(economic_data)
            appendix_sections.append(econ_section)
        
        # Combine with original content
        if appendix_sections:
            return content + "\n\n---\n" + "\n\n".join(appendix_sections)
        
        return content
    
    async def _format_minimal(self, content: str, claims: List[FinancialClaim], 
                            data: Dict[str, Any]) -> str:
        """
        Minimal formatting with just key price updates
        """
        updates = []
        
        for claim in claims:
            if claim.claim_type == ClaimType.STOCK_PRICE and claim.symbol:
                stock_data = self._find_stock_data(claim.symbol, data)
                if stock_data:
                    price_update = f"{claim.symbol}: ${stock_data.get('price', 'N/A')}"
                    change = stock_data.get('change_percent', 0)
                    if change > 0:
                        price_update += f" (+{change}%)"
                    elif change < 0:
                        price_update += f" ({change}%)"
                    updates.append(price_update)
        
        if updates:
            return content + f"\n\n*Current prices: {', '.join(updates)}*"
        
        return content
    
    def _find_stock_data(self, symbol: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find stock data for a specific symbol in the data dict"""
        # Look for stock data with various key formats
        possible_keys = [
            f"{symbol}_stock_data",
            f"{symbol.lower()}_stock_data",
            f"stock_data_{symbol}",
            f"stock_data_{symbol.lower()}"
        ]
        
        for key in possible_keys:
            if key in data:
                return data[key]
        
        # Check if data is nested
        for key, value in data.items():
            if isinstance(value, dict) and 'symbol' in value:
                if value['symbol'].upper() == symbol.upper():
                    return value
        
        return None
    
    def _find_economic_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract economic indicators from data"""
        economic_keys = ['economic_indicators', 'fed_funds_rate', 'unemployment_rate', 'inflation_rate']
        
        economic_data = {}
        for key in economic_keys:
            if key in data:
                economic_data[key] = data[key]
        
        return economic_data if economic_data else None
    
    def _format_stock_inline(self, symbol: str, stock_data: Dict[str, Any]) -> str:
        """Format stock data for inline insertion"""
        price = stock_data.get('price', 'N/A')
        change = stock_data.get('change', 0)
        change_percent = stock_data.get('change_percent', 0)
        
        if change > 0:
            trend = f"↗ +{change_percent}%"
        elif change < 0:
            trend = f"↘ {change_percent}%"
        else:
            trend = "→ 0%"
        
        return f" [${price} {trend}]"
    
    def _format_stock_detailed(self, symbol: str, stock_data: Dict[str, Any]) -> str:
        """Format detailed stock information"""
        price = stock_data.get('price', 'N/A')
        change = stock_data.get('change', 0)
        change_percent = stock_data.get('change_percent', 0)
        volume = stock_data.get('volume', 'N/A')
        market_cap = stock_data.get('market_cap', None)
        
        details = f"**{symbol}**: ${price}"
        
        if change != 0:
            sign = "+" if change > 0 else ""
            details += f" ({sign}{change} / {sign}{change_percent}%)"
        
        if volume != 'N/A':
            details += f" | Volume: {volume:,}"
        
        if market_cap:
            cap_billions = market_cap / 1e9
            details += f" | Market Cap: ${cap_billions:.1f}B"
        
        return details
    
    def _format_stock_appendix(self, symbol: str, stock_data: Dict[str, Any]) -> str:
        """Format stock data for appendix section"""
        return f"• {self._format_stock_detailed(symbol, stock_data)}"
    
    def _format_inline_stock_data(self, symbol: str, stock_data: Dict[str, Any]) -> str:
        """Format stock data for direct inline integration"""
        price = stock_data.get('price', 'N/A')
        change_percent = stock_data.get('change_percent', 0)
        
        if abs(change_percent) < 0.01:
            return f" (currently ${price})"
        elif change_percent > 0:
            return f" (currently ${price}, +{change_percent}% today)"
        else:
            return f" (currently ${price}, {change_percent}% today)"
    
    def _format_economic_summary(self, economic_data: Dict[str, Any]) -> str:
        """Format economic indicators summary"""
        summary_parts = []
        
        for key, value in economic_data.items():
            if isinstance(value, dict):
                indicator_name = value.get('indicator_name', key.replace('_', ' ').title())
                indicator_value = value.get('value', 'N/A')
                unit = value.get('unit', '')
                summary_parts.append(f"{indicator_name}: {indicator_value}{unit}")
        
        if summary_parts:
            return "**Economic Context:** " + " | ".join(summary_parts)
        
        return ""
    
    def _insert_inline_data(self, content: str, claim: FinancialClaim, 
                          inline_data: str) -> str:
        """Insert inline data after the claim in the content"""
        # Find the end position of the claim
        end_pos = claim.position_end
        
        # Insert the inline data
        if end_pos < len(content):
            return content[:end_pos] + inline_data + content[end_pos:]
        else:
            return content + inline_data
    
    def get_available_styles(self) -> List[str]:
        """Get list of available formatting styles"""
        return list(self.formatting_styles.keys())
    
    def format_data_summary(self, data: Dict[str, Any]) -> str:
        """Create a summary of all available data"""
        summary_parts = []
        
        # Count different types of data
        stock_count = sum(1 for key in data.keys() if 'stock_data' in key)
        has_economic = any('economic' in key for key in data.keys())
        has_market = any('market' in key for key in data.keys())
        
        if stock_count > 0:
            summary_parts.append(f"{stock_count} stock ticker(s)")
        
        if has_economic:
            summary_parts.append("economic indicators")
        
        if has_market:
            summary_parts.append("market context")
        
        if summary_parts:
            return f"Real-time data: {', '.join(summary_parts)}"
        
        return "No real-time data available"


# Utility functions for external use
def format_price(price: float) -> str:
    """Format price with appropriate decimal places"""
    if price >= 1000:
        return f"${price:,.2f}"
    else:
        return f"${price:.2f}"

def format_percentage(percentage: float) -> str:
    """Format percentage with appropriate sign and precision"""
    if percentage > 0:
        return f"+{percentage:.2f}%"
    else:
        return f"{percentage:.2f}%"

def format_volume(volume: int) -> str:
    """Format trading volume in readable format"""
    if volume >= 1_000_000:
        return f"{volume/1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"{volume/1_000:.1f}K"
    else:
        return str(volume)
