# FinSight MCP Integration

This directory contains the Model Context Protocol (MCP) integration for FinSight, enabling AI agents and LLMs to access financial data through standardized protocols.

## Files

### Core MCP Servers
- **`mcp_server.py`** - Full-featured MCP server with all dependencies
- **`mcp_server_standalone.py`** - Standalone MCP server for system Python

### Configuration
- **`claude_desktop_config.json`** - Claude Desktop configuration template

## Quick Start

### For Claude Desktop

1. **Copy configuration** to Claude Desktop settings:
```json
{
  "mcpServers": {
    "finsight": {
      "command": "/usr/bin/python3",
      "args": ["/path/to/FinSight/integrations/mcp/mcp_server_standalone.py"],
      "env": {
        "PYTHONPATH": "/path/to/FinSight"
      }
    }
  }
}
```

2. **Start FinSight API server**:
```bash
cd /path/to/FinSight
python src/api_server.py
```

3. **Restart Claude Desktop**

### For Python Applications

```python
import asyncio
from integrations.mcp.mcp_server import FinSightMCPServer

async def main():
    server = FinSightMCPServer()
    await server.run_stdio()

if __name__ == "__main__":
    asyncio.run(main())
```

## Available Tools

- **`get_stock_price`** - Real-time stock prices
- **`get_economic_data`** - Economic indicators (unemployment, inflation, GDP)
- **`get_company_info`** - Company information and market cap
- **`analyze_market`** - Market analysis and sentiment

## Testing

```bash
# Test standalone server
python integrations/mcp/mcp_server_standalone.py test

# Test full server
python integrations/mcp/mcp_server.py test
```

## Protocol Compliance

Both servers implement:
- **MCP Protocol**: 2024-11-05
- **JSON-RPC**: 2.0
- **Transport**: stdio
- **Capabilities**: tools

## Dependencies

### Standalone Server
- Python 3.9+ (system Python)
- Standard library only
- Fallback HTTP client (urllib)

### Full Server  
- Python 3.9+
- aiohttp
- All FinSight dependencies

## Deployment Notes

For AWS deployment, use the standalone server for better compatibility with system Python environments. 