# 🚀 SpoonOS MCP+ Tools Collection

Transform your SpoonOS tools into powerful MCP-compatible services that seamlessly integrate with Claude Desktop and other AI assistants!

## ✨ What is MCP?

The Model Context Protocol (MCP) enables AI models to interact with external tools and services. By wrapping your SpoonOS tools in an MCP interface, you can:

- Allow Claude and other AI assistants to directly use your financial tools
- Create powerful AI workflows with real-time market data
- Build sophisticated crypto trading and analysis systems

## 🛠️ Quick Setup

```bash
# Install FastMCP
pip install fastmcp

# Run the MCP tools server
python -m spoon_ai.tools.mcp_tools_collection
```

## 💻 Integration Examples

### Create Your Own MCP Tool

```python
from fastmcp import MCPService, Tool, ToolCall
from pydantic import BaseModel, Field
from spoon_ai.tools.your_original_tool import YourOriginalTool

# Define input schema
class TokenPriceInput(BaseModel):
    token_address: str = Field(..., description="Ethereum token address")
    chain_id: int = Field(1, description="Chain ID (1 for Ethereum mainnet)")

# Create MCP-compatible tool
class TokenPriceMCPTool(Tool):
    name = "token_price"
    description = "Get real-time token price from DEXs"
    input_schema = TokenPriceInput
    
    async def execute(self, input: TokenPriceInput, call: ToolCall) -> str:
        # Call your original SpoonAI tool
        price_tool = YourOriginalTool()
        result = price_tool.get_price(input.token_address, input.chain_id)
        return f"Current price: ${result}"

# Create MCP service
class SpoonAIMCPTools(MCPService):
    name = "SpoonAI Tools"
    description = "Crypto & DeFi analysis tools"
    
    def _setup_tools(self):
        self.add_tool(TokenPriceMCPTool())
        # Add more tools here...

# Run the service
mcp_tools = SpoonAIMCPTools()
mcp_tools.run()
```

## 🔌 Claude Desktop Integration

1. Install the tools:
   ```bash
   fastmcp install spoon_ai/tools/mcp_tools_collection.py --name "SpoonAI Tools"
   ```

2. Select "SpoonAI Tools" in Claude Desktop

3. Start asking Claude to analyze tokens, check prices, and perform complex DeFi operations!

## 🧪 Development Mode

Test your tools interactively:

```bash
fastmcp dev spoon_ai/tools/mcp_tools_collection.py
```

## 🧩 Available Tools

| Tool | Description |
|------|-------------|
| PredictPrice | Predicts future token prices using ML models |
| TokenHolders | Analyzes token holder distribution and whale activity |
| TradingHistory | Provides detailed trading history analytics |
| UniswapLiquidity | Monitors Uniswap liquidity pools |
| WalletAnalysis | Analyzes wallet transaction patterns |
| GetTokenPriceTool | Gets real-time token prices |
| Get24hStatsTool | Provides 24-hour market statistics |
| GetKlineDataTool | Retrieves candlestick chart data |
| PriceThresholdAlertTool | Sets up price threshold alerts |
| LpRangeCheckTool | Checks optimal LP ranges |
| SuddenPriceIncreaseTool | Detects sudden price movements |
| LendingRateMonitorTool | Monitors lending rates across protocols |
| LstArbitrageTool | Identifies LST arbitrage opportunities |
| TokenTransfer | Facilitates token transfers |
| Terminate | Gracefully terminates operations |

## 🔧 Advanced Configuration

```python
# Custom authentication
from fastmcp.security import APIKeyAuth

auth = APIKeyAuth(api_keys=["your-secret-key"])
mcp_tools.run(auth=auth)

# Custom transport
mcp_tools.run(
    transport="websocket",  # Options: "stdio", "sse", "websocket"
    host="0.0.0.0",
    port=8000
)

# Custom error handling
@mcp_tools.exception_handler(Exception)
async def handle_exception(exception: Exception, call: ToolCall):
    return f"Error executing tool: {str(exception)}"
```

## 🚀 Adding New Tools

To extend with new tools, simply add them to the `_setup_tools` method:

```python
def _setup_tools(self):
    self.add_tool(PredictPriceTool())
    self.add_tool(TokenHoldersTool())
    self.add_tool(YourNewAwesomeTool())  # Add your new tool here!
```

For more advanced configuration options, see the [FastMCP documentation](https://github.com/jlowin/fastmcp). 
