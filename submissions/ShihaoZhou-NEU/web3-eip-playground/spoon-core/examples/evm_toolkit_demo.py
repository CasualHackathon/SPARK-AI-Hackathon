"""
EVM Toolkit Agent Demo - Comprehensive demonstration using spoon_ai framework

This example demonstrates EVM blockchain tools using spoon_ai agents, showcasing:
- Agent-based tool interaction
- Comprehensive EVM toolkit coverage (6 tools)
- Real-world usage scenarios
- Error handling and validation

Uses testnet for all demonstrations with embedded test data.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import spoon_ai framework
from spoon_ai.agents.toolcall import ToolCallAgent
from spoon_ai.tools import ToolManager
from spoon_ai.chat import ChatBot
from spoon_ai.llm.manager import get_llm_manager
from pydantic import Field

# Import EVM tools for agent
from spoon_toolkits.crypto.evm import (
    EvmBalanceTool,
    EvmTransferTool,
    EvmErc20TransferTool,
)

# Load environment variables
load_dotenv()


class EvmToolkitAgentDemo:
    """EVM Toolkit Agent-based comprehensive demonstration"""

    TEST_DATA = {
        "network": "sepolia",
        "basic_test_data": {
            "addresses": [
                "0x1234567890123456789012345678901234567890",
                "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb2"
            ],
            "chain_ids": {
                "sepolia": 11155111,
                "mumbai": 80001,
                "arbitrum_sepolia": 421614,
            },
            "transfer_amount": "0.001",
            "transfer_to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb2",
            
        },
        "test_tokens": {
            "sepolia": {
                "USDC": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
                "WETH": "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
            },
            "mumbai": {
                "USDC": "0x0FA8781a83E46826621b3BC094Ea2A0212e71B23",
                "WMATIC": "0x9c3C9283D3E44854697Cd22D3Faa240Cfb032889",
            },
        },
    }

    def __init__(self):
        """Initialize the demo with embedded test data"""
        self.load_test_data()
        self.agents = {}

    def load_test_data(self):
        """Load test data from embedded TEST_DATA configuration"""
        try:
            data = self.TEST_DATA
            
            # Load basic configuration
            self.network = data.get("network", "sepolia")

            # Load basic test data
            basic_data = data.get("basic_test_data", {})
            self.demo_address = basic_data.get("addresses", [])[0] if basic_data.get("addresses") else "default_address"
            self.demo_addresses = basic_data.get("addresses", [])
            self.chain_ids = basic_data.get("chain_ids", {})
            self.sepolia_chain_id = self.chain_ids.get("sepolia", 11155111)
            self.mumbai_chain_id = self.chain_ids.get("mumbai", 80001)
            self.transfer_amount = basic_data.get("transfer_amount", "0.001") 
            self.transfer_to_address = basic_data.get("transfer_to_address", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb2")
            # Load token data
            self.test_tokens = data.get("test_tokens", {})
            self.sepolia_usdc = self.test_tokens.get("sepolia", {}).get("USDC", "")
            self.sepolia_weth = self.test_tokens.get("sepolia", {}).get("WETH", "")
            
            print(f"✅ Loaded test data from embedded configuration")
            print(f"   Network: {self.network}")
            print(f"   Addresses: {len(self.demo_addresses)} available")
            print(f"   Chain IDs: Sepolia={self.sepolia_chain_id}, Mumbai={self.mumbai_chain_id}")

        except Exception as e:
            print(f"❌ Failed to load test data: {e}")
            # Set minimal defaults
            self.network = "sepolia"
            self.demo_address = ""
            self.demo_addresses = []
            self.sepolia_chain_id = 11155111
            self.mumbai_chain_id = 80001
            self.sepolia_usdc = ""
            self.sepolia_weth = ""

    def create_agent(self, name: str, tools: List, description: str) -> ToolCallAgent:
        """Create a specialized agent with specific tools"""
        network = self.network

        class EvmSpecializedAgent(ToolCallAgent):
            agent_name: str = name
            agent_description: str = description
            system_prompt: str = f"""
            You are an EVM blockchain specialist focused on {description}.
            Use the available tools to analyze EVM blockchain data and provide comprehensive insights.

            **CRITICAL - RPC URL Configuration:**
            - You MUST provide a valid RPC URL when calling tools
            - For Ethereum Sepolia testnet, try these public RPC URLs in order:
              1. "https://ethereum-sepolia-rpc.publicnode.com" (recommended)
              2. "https://sepolia.gateway.tenderly.co"
              3. "https://rpc.sepolia.org"
            - NEVER use network names like "sepolia" as RPC URLs - always use full HTTP/HTTPS URLs
            - If environment variable EVM_PROVIDER_URL or RPC_URL is set, the tool will use it automatically
            - Example valid RPC URLs:
              * Sepolia: "https://ethereum-sepolia-rpc.publicnode.com"
              * Sepolia (Infura): "https://sepolia.infura.io/v3/YOUR_API_KEY"
              * Mumbai: "https://rpc-mumbai.maticvigil.com"

            **Important Notes:**
            - All addresses must be 0x-prefixed hex strings (42 characters total)
            - Token amounts should be provided as decimal strings (e.g., "1.5" for 1.5 tokens)
            - For native token transfers, use address "0x0000000000000000000000000000000000000000"
            - Gas prices are in gwei
            - Slippage is typically specified as a decimal (e.g., 0.005 for 0.5%)

            **Tool Usage:**
            - When calling evm_get_balance, always provide rpc_url parameter with a valid HTTP/HTTPS URL
            - Example: evm_get_balance(address="0x...", rpc_url="https://rpc.sepolia.org")
            - When calling evm_swap_quote, always provide rpc_url parameter with a valid HTTP/HTTPS URL
            - Example: evm_swap_quote(from_token="0x0000000000000000000000000000000000000000", to_token="0x...", amount="0.1", rpc_url="https://ethereum-sepolia-rpc.publicnode.com")
            - For native ETH, use "0x0000000000000000000000000000000000000000" as from_token address

            Provide clear, informative responses based on the tool results.
            
            IMPORTANT: After calling tools and receiving results, you MUST provide a comprehensive summary and analysis. 
            Do not just return the raw tool output. Instead, analyze the data, extract key insights, and present a 
            well-structured response that answers the user's question completely.
            """
            max_steps: int = 10
            available_tools: ToolManager = Field(default_factory=lambda: ToolManager(tools))

        agent = EvmSpecializedAgent(
            llm=ChatBot(
                llm_provider="openrouter",
                model_name="anthropic/claude-3.5-sonnet"
            )
        )
        return agent

    def create_transfer_agent(self, name: str, tools: List, description: str) -> ToolCallAgent:
        """Create a transfer agent that can execute transfers"""
        network = self.network

        class EvmTransferAgent(ToolCallAgent):
            agent_name: str = name
            agent_description: str = description
            system_prompt: str = f"""
            You are an EVM blockchain transfer specialist focused on {description}.
            You can execute actual transfers using the available tools.

            **CRITICAL - RPC URL Configuration:**
            - You MUST provide a valid RPC URL when calling tools
            - For Ethereum Sepolia testnet, use: "https://ethereum-sepolia-rpc.publicnode.com"
            - NEVER use network names like "sepolia" as RPC URLs - always use full HTTP/HTTPS URLs

            **Transfer Execution Guidelines:**
            1. Before executing any transfer, ALWAYS check the sender's balance first using evm_get_balance
            2. Verify sufficient balance (amount + gas fees) before proceeding
            3. For native transfers, use evm_transfer tool with:
               - to_address: recipient address
               - amount_ether: amount in ETH (as decimal string, e.g., "0.001")
               - rpc_url: full RPC URL
               - Private key will be automatically used from EVM_PRIVATE_KEY env or Turnkey from TURNKEY_SIGN_WITH env
            4. For ERC20 transfers, use evm_erc20_transfer tool with:
               - token_address: ERC20 token contract address
               - to_address: recipient address
               - amount: amount in human-readable units (as decimal string, e.g., "1.0")
               - rpc_url: full RPC URL
               - Private key will be automatically used from EVM_PRIVATE_KEY env or Turnkey from TURNKEY_SIGN_WITH env
            5. After execution, provide the transaction hash and wait for confirmation
            6. Report any errors clearly

            **Important Notes:**
            - All addresses must be 0x-prefixed hex strings (42 characters total)
            - Token amounts should be provided as decimal strings (e.g., "0.001" for 0.001 ETH, "1.5" for 1.5 tokens)
            - Gas prices are automatically estimated, but you can override with gas_price_gwei if needed
            - The signer address is automatically determined from the private key or Turnkey configuration

            **Tool Usage Examples:**
            - Native transfer: evm_transfer(to_address="0x...", amount_ether="0.001", rpc_url="https://ethereum-sepolia-rpc.publicnode.com")
            - ERC20 transfer: evm_erc20_transfer(token_address="0x...", to_address="0x...", amount="1.0", rpc_url="https://ethereum-sepolia-rpc.publicnode.com")
            - Balance check: evm_get_balance(address="0x...", rpc_url="https://ethereum-sepolia-rpc.publicnode.com")

            Provide clear, informative responses with transaction details after execution.
            """
            max_steps: int = 10
            available_tools: ToolManager = Field(default_factory=lambda: ToolManager(tools))

        agent = EvmTransferAgent(
            llm=ChatBot(
                llm_provider="openrouter",
                model_name="anthropic/claude-3.5-sonnet"
            )
        )
        return agent

    def setup_agents(self):
        """Setup specialized agents for different EVM toolkit categories"""

        # Balance Analyst Agent
        balance_tools = [
            EvmBalanceTool(),
        ]
        self.agents['balance'] = self.create_agent(
            "Balance Analyst",
            balance_tools,
            "Expert in EVM address balance queries and portfolio analysis"
        )

        # Transfer Specialist Agent
        transfer_tools = [
            EvmTransferTool(),
            EvmErc20TransferTool(),
        ]
        self.agents['transfer'] = self.create_transfer_agent(
            "Transfer Specialist",
            transfer_tools,
            "Specialist in native and ERC20 token transfers on EVM chains"
        )


    def print_section_header(self, title: str):
        """Print formatted section header"""
        print(f"\n{'='*80}")
        print(f" {title}")
        print(f"{'='*80}")

    async def run_agent_scenario(self, agent_name: str, scenario_title: str, user_message: str):
        """Run a specific scenario with an agent"""
        print(f"\n{'-'*60}")
        print(f" Agent: {self.agents[agent_name].agent_name}")
        print(f" Scenario: {scenario_title}")
        print(f" Query: {user_message}")
        print(f"{'-'*60}")

        try:
            # Clear agent state before running
            self.agents[agent_name].clear()

            # Run the agent with the user message
            response = await self.agents[agent_name].run(user_message)

            # Display response with better formatting
            print(f"\n{'='*60}")
            print(f"✅ AI Agent Response:")
            print(f"{'='*60}")
            print(response)
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

    async def demo_balance_analysis(self):
        """Demonstrate balance analysis capabilities"""
        self.print_section_header("1. Balance Analysis with AI Agent")

        # Scenario 1: Native Balance Query
        await self.run_agent_scenario(
            'balance',
            "Native Balance Query",
            f"Get the native token balance (ETH) for address {self.demo_address} on Ethereum Sepolia testnet. "
            f"Use RPC URL: https://ethereum-sepolia-rpc.publicnode.com"
        )

        # Scenario 2: ERC20 Balance Query
        if self.sepolia_usdc:
            await self.run_agent_scenario(
                'balance',
                "ERC20 Balance Query",
                f"Get the USDC token balance for address {self.demo_address} on Ethereum Sepolia. "
                f"USDC token address: {self.sepolia_usdc}. "
                f"Use RPC URL: https://ethereum-sepolia-rpc.publicnode.com"
            )

        # Scenario 3: Multi-Address Portfolio Analysis
        if len(self.demo_addresses) >= 2:
            await self.run_agent_scenario(
                'balance',
                "Multi-Address Portfolio Analysis",
                f"Analyze the balances for these addresses on Sepolia: {self.demo_addresses[0]} and {self.demo_addresses[1]}. "
                f"Use RPC URL: https://ethereum-sepolia-rpc.publicnode.com for all queries. "
                f"Provide a comprehensive portfolio summary including native ETH balances."
            )

    async def demo_transfer_operations(self):
        """Demonstrate transfer operation capabilities - executes actual transfers"""
        self.print_section_header("2. Transfer Operations with AI Agent")
        
        # Check if private key is configured (must be non-empty)
        private_key = os.getenv("EVM_PRIVATE_KEY")
        turnkey_sign_with = os.getenv("TURNKEY_SIGN_WITH")
        
        # Validate private key format if present
        if private_key:
            private_key = private_key.strip()
            if not private_key or len(private_key) < 64:
                print("\n⚠️  WARNING: EVM_PRIVATE_KEY is set but invalid!")
                print("   Private key must be at least 64 hex characters (with or without 0x prefix).")
                print("   Transfer operations will be skipped.\n")
                return
        
        # Validate turnkey config if present
        if turnkey_sign_with:
            turnkey_sign_with = turnkey_sign_with.strip()
            if not turnkey_sign_with:
                turnkey_sign_with = None
        
        if not private_key and not turnkey_sign_with:
            print("\n⚠️  WARNING: No private key or Turnkey credentials found!")
            print("   Set EVM_PRIVATE_KEY or TURNKEY_SIGN_WITH environment variable to enable transfers.")
            print("   Transfer operations will be skipped.\n")
            return
        
        signer_type = "local" if private_key else "turnkey"
        print(f"✅ Signer configured: {signer_type}")
        if signer_type == "local":
            print(f"   Using private key from EVM_PRIVATE_KEY environment variable")
        else:
            print(f"   Using Turnkey signing with TURNKEY_SIGN_WITH")
        print()

        # Scenario 1: Native Token Transfer

        await self.run_agent_scenario(
            'transfer',
            "Native Token Transfer",
            f"Execute a native token transfer of 0.001 ETH from the configured signer address to {self.transfer_to_address} on Sepolia testnet. "
            f"Use RPC URL: https://ethereum-sepolia-rpc.publicnode.com. "
            f"First check the sender's balance to ensure sufficient funds, then execute the transfer. "
            f"Provide the transaction hash and confirmation details."
        )

        # Scenario 2: ERC20 Token Transfer

        await self.run_agent_scenario(
            'transfer',
            "ERC20 Token Transfer",
            f"Execute an ERC20 token transfer: 0.01 USDC from the configured signer address to {self.transfer_to_address} on Sepolia testnet. "
            f"Token address: {self.sepolia_usdc}. "
            f"Use RPC URL: https://ethereum-sepolia-rpc.publicnode.com. "
            f"First check the sender's USDC balance to ensure sufficient funds, then execute the transfer. "
            f"Provide the transaction hash and confirmation details."
        )


    async def run_comprehensive_demo(self):
        """Run the complete agent-based demonstration"""
        print("🚀 EVM Blockchain Toolkit - AI Agent Demonstration")
        print("=" * 80)
        print("This demo showcases EVM blockchain tools through specialized AI agents")
        print("Each agent is an expert in specific aspects of the EVM ecosystem")
        print("=" * 80)
        print(f" Network: {self.network}")
        print(f" Demo Address: {self.demo_address}")
        print(f"  Test Data Available:")
        print(f"   - Addresses: {len(self.demo_addresses)}")
        print(f"   - Chain IDs: Sepolia={self.sepolia_chain_id}, Mumbai={self.mumbai_chain_id}")

        try:
            # Setup all specialized agents
            print("\n🔧 Setting up specialized agents...")
            self.setup_agents()
            print(f"✅ Created {len(self.agents)} specialized agents")

            # Run comprehensive demonstrations
            await self.demo_balance_analysis()
            await self.demo_transfer_operations()

            # Final summary
            self.print_section_header("Demo Completed Successfully")
            for agent_name, agent in self.agents.items():
                tool_count = len(agent.available_tools.tools)
                print(f"  ✅ {agent.agent_name}: {tool_count} specialized tools")

            total_tools = sum(len(agent.available_tools.tools) for agent in self.agents.values())
            print(f"\n🔧 Total Tools Demonstrated: {total_tools} EVM tools")
            print("   All demonstrations powered by AI agents with domain expertise")
            print("   Each agent provides intelligent analysis and workflow orchestration")
            print("\nAgent Capabilities:")
            print("   1. Balance Analyst: Query native and ERC20 token balances")
            print("   2. Transfer Specialist: Native and ERC20 token transfers")
            print("\nKey Features Demonstrated:")
            print("   ✅ Multi-chain support (Sepolia, Mumbai)")
            print("   ✅ Native and ERC20 token operations")

        except Exception as e:
            print(f"\n❌ Demo error: {str(e)}")
            print("Please check your environment setup and network connectivity")


async def main():
    """Main demonstration function"""
    print("\n EVM Blockchain Toolkit - AI Agent Demonstration")
    print("=" * 80)
    print("Showcasing comprehensive EVM blockchain analysis through specialized AI agents")
    print("Each agent is equipped with domain-specific tools and expertise")
    print("=" * 80)

    demo = EvmToolkitAgentDemo()
    await demo.run_comprehensive_demo()


if __name__ == "__main__":
    asyncio.run(main())
