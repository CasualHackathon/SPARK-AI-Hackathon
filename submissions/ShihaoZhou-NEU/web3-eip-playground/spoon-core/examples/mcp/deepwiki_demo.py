#!/usr/bin/env python3
"""
MCP Tool Call Demo

This demo showcases agent successfully calling MCP tools.
It demonstrates how the agent uses MCP tools to process queries.
"""

import asyncio
from spoon_ai.agents.spoon_react_mcp import SpoonReactMCP
from spoon_ai.tools.mcp_tool import MCPTool
from spoon_ai.chat import ChatBot
import logging

# Configure logging - reduce output
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class MCPToolDemoAgent:
    """Agent for demonstrating MCP tool calls"""

    def __init__(self):
        self.agent = None
        self.chatbot = None

    async def initialize(self):
        """Initialize the agent with MCP tools"""
        try:
            # Initialize ChatBot with LLM provider
            # ChatBot will automatically create and manage LLMManager internally
            self.chatbot = ChatBot()

            # Create SSE MCP tool configuration
            sse_mcp_config = {
                "name": "deepwiki_sse",
                "type": "mcp",
                "description": "DeepWiki SSE MCP tool for repository analysis",
                "enabled": True,
                "mcp_server": {
                    "url": "https://mcp.deepwiki.com/sse",
                    "transport": "sse",
                    "timeout": 30,
                    "headers": {
                        "User-Agent": "SpoonOS-SSE-MCP/1.0",
                        "Accept": "text/event-stream"
                    }
                }
            }

            # Create HTTP MCP tool configuration using StreamableHttpTransport
            http_mcp_config = {
                "name": "deepwiki_http",
                "type": "mcp",
                "description": "DeepWiki HTTP MCP tool for repository analysis",
                "enabled": True,
                "mcp_server": {
                    "url": "https://mcp.deepwiki.com/mcp",
                    "transport": "http",
                    "timeout": 30,
                    "headers": {
                        "User-Agent": "SpoonOS-HTTP-MCP/1.0",
                        "Accept": "application/json, text/event-stream"
                    }
                }
            }

            # Create MCP tools (without pre-loading parameters)
            sse_tool = MCPTool(
                name=sse_mcp_config["name"],
                description=sse_mcp_config["description"],
                mcp_config=sse_mcp_config["mcp_server"]
            )
            http_tool = MCPTool(
                name=http_mcp_config["name"],
                description=http_mcp_config["description"],
                mcp_config=http_mcp_config["mcp_server"]
            )

            # Create agent with both MCP tools (tools will be loaded when needed)
            self.agent = SpoonReactMCP(
                name="mcp_demo_agent",
                llm=self.chatbot,
                tools=[sse_tool, http_tool]
            )

            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP Tool Demo Agent: {e}")
            return False

    async def query_agent(self, question: str):
        """Query the agent with a question (agent will call MCP tools as needed)"""
        try:
            result = await self.agent.run(question)
            if not isinstance(result, str):
                return f"❌ Agent returned non-string result: {type(result)}"
            return result
        except Exception as e:
            return f"❌ Agent execution failed: {str(e)}"



    async def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self.agent, 'cleanup'):
                await self.agent.cleanup()
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")



async def main():
    """Main demo function"""
    print("🚀 MCP Tool Call Demo")
    print("=" * 50)
    print("This demo showcases agent successfully calling MCP tools")
    print("to process queries and demonstrate tool integration.")
    print()

    # Create and initialize agent directly
    print("🤖 Creating MCP Tool Demo Agent...")
    agent = MCPToolDemoAgent()

    # Initialize agent
    if not await agent.initialize():
        print("❌ Agent initialization failed. Stopping demo.")
        return

    # Direct agent call demo
    print("\n🔧 Direct Agent Call Demo")
    print("Agent will call MCP tools automatically when processing queries...")

    query = "What is the XSpoonAi/spoon-core project?"

    print(f"\n🔍 Query: {query}")
    print("-" * 60)

    # Direct agent call
    print("\n🤖 Agent processing query (MCP tools will be called if needed)...")
    agent_result = await agent.query_agent(query)
    print(f"Agent Result:\n{agent_result}")

    print("\n" + "="*60)

    # Interactive demo
    print("\n💬 Interactive Agent Demo")
    print("Ask questions and agent will call MCP tools automatically (type 'quit' to exit):")
    print("Examples:")
    print("  'What is XSpoonAi/spoon-core?'")
    print("  'Analyze this GitHub repository'")
    print("  'quit' - Exit")

    while True:
        try:
            user_input = input("\n🤔 Ask a question: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                break

            if not user_input:
                continue

            print("🔄 Agent processing (will call MCP tools if needed)...")
            result = await agent.query_agent(user_input)
            print(f"\n📝 Agent Response:\n{result}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

    # Cleanup
    print("\n🧹 Cleaning up...")
    await agent.cleanup()
    print("✅ Demo completed!")

if __name__ == "__main__":
    asyncio.run(main())
