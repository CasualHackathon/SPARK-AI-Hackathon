"""
ERC-8004 DID Search Agent (Server)
==================================

A ReAct-style agent powered by spoon_ai that:
- Uses Tavily MCP tool for live web search
- Focuses on answering questions about ERC-8004 agents/standard
- Exposes a simple HTTP JSON API on /ask for demo purposes

Usage:
    python -m examples.erc8004_did.server_agent --port 8004

Environment variables:
    TAVILY_API_KEY       Tavily API key (required for search)
    OPENAI_API_KEY       OpenAI API key (required for LLM)
    ERC8004_AGENT_PORT   Server port (default: 8004)
    ERC8004_AGENT_NAME   Agent display name (optional)

Deployed contracts (NeoX Testnet - open registration):
    IdentityRegistry:   0xaB5623F3DD66f2a52027FA06007C78c7b0E63508
    ReputationRegistry: 0x8bb086D12659D6e2c7220b07152255d10b2fB049
    ValidationRegistry: 0x18A9240c99c7283d9332B738f9C6972b5B59aEc2

To register a new agent, use the separate registration script:
    python -m examples.erc8004_did.scripts.register_agent --help
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os

os.environ.setdefault("WEB3_ENABLE_CKZG", "0")

from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from typing import Any, Optional
import threading

from spoon_ai.agents.spoon_react_mcp import SpoonReactMCP
from spoon_ai.chat import ChatBot
from spoon_ai.tools.mcp_tool import MCPTool
from spoon_ai.tools.tool_manager import ToolManager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("erc8004.server")


class ERC8004SearchAgent(SpoonReactMCP):
    """ReAct agent specialized for ERC-8004 Q&A with live web search."""

    name: str = "ERC8004SearchAgent"
    system_prompt: str = (
        "You are an on-chain ERC-8004 agent.\n"
        "- Use tavily-search to fetch recent info about ERC-8004, agent registries, and ecosystem projects.\n"
        "- Explain concisely, cite key projects (Identity, Reputation, Validation registries), "
        "and highlight how to register/resolve agents.\n"
        "- Prefer actionable steps. Keep answers under 8 sentences."
    )

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.available_tools = ToolManager([])

    async def initialize(self) -> None:
        tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
        if not tavily_key or "your-tavily-api-key" in tavily_key:
            raise ValueError("TAVILY_API_KEY is missing; tavily-search cannot run.")

        tavily_tool = MCPTool(
            name="tavily-search",
            description="Web search via Tavily MCP server",
            mcp_config={
                "command": "npx",
                "args": ["--yes", "tavily-mcp"],
                "env": {"TAVILY_API_KEY": tavily_key},
            },
        )
        self.available_tools = ToolManager([tavily_tool])
        logger.info("Loaded tools: %s", list(self.available_tools.tool_map.keys()))


class _RequestHandler(BaseHTTPRequestHandler):
    agent: Optional[ERC8004SearchAgent] = None
    loop: Optional[asyncio.AbstractEventLoop] = None
    agent_name: str = "ERC8004 Search Agent"
    # Lock to serialize agent.run() calls for thread safety
    _agent_lock: threading.Lock = threading.Lock()

    def _send_json(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/ask":
            self._send_json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length) or b"{}")
            question = str(data.get("question", "")).strip()
        except Exception as exc:
            logger.exception("Malformed request: %s", exc)
            self._send_json(400, {"error": "bad request"})
            return

        if not question:
            self._send_json(400, {"error": "question is required"})
            return

        assert self.agent and self.loop
        # Serialize agent.run() calls to prevent concurrent execution issues
        # The agent's internal _run_lock provides additional protection, but
        # this ensures requests are handled one at a time at the HTTP level
        with self._agent_lock:
            fut = asyncio.run_coroutine_threadsafe(self.agent.run(question), self.loop)
            try:
                answer = fut.result(timeout=120)
            except Exception as exc:
                logger.exception("Agent failed: %s", exc)
                self._send_json(500, {"error": "agent_error", "detail": str(exc)})
                return

        self._send_json(
            200,
            {
                "agent": self.agent_name,
                "question": question,
                "answer": answer,
            },
        )

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.info("%s - %s", self.address_string(), fmt % args)


async def _prepare_agent(agent_name: str) -> ERC8004SearchAgent:
    agent = ERC8004SearchAgent(llm=ChatBot(llm_provider="openai"))
    await agent.initialize()
    logger.info("Agent ready: %s", agent_name)
    return agent


def run_server(port: int, agent_name: str) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    agent = loop.run_until_complete(_prepare_agent(agent_name))

    _RequestHandler.agent = agent
    _RequestHandler.loop = loop
    _RequestHandler.agent_name = agent_name

    # Use ThreadingHTTPServer to handle concurrent requests safely
    # The agent's internal locks and the request-level lock ensure thread safety
    server = ThreadingHTTPServer(("0.0.0.0", port), _RequestHandler)
    logger.info("HTTP server listening on http://127.0.0.1:%d/ask (threading enabled)", port)

    try:
        loop.run_in_executor(None, server.serve_forever)
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        server.shutdown()
        loop.stop()
        loop.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ERC-8004 DID Search Agent server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This server exposes a single endpoint:
    POST /ask
    Body: {"question": "your question here"}
    Response: {"agent": "...", "question": "...", "answer": "..."}

Example:
    curl -X POST http://127.0.0.1:8004/ask \\
         -H "Content-Type: application/json" \\
         -d '{"question": "What is ERC-8004?"}'
        """,
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("ERC8004_AGENT_PORT", "8004")),
        help="Server port (default: 8004)",
    )
    parser.add_argument(
        "--agent-name",
        default=os.getenv("ERC8004_AGENT_NAME", "ERC8004 Search Agent"),
        help="Agent display name",
    )
    args = parser.parse_args()

    run_server(args.port, args.agent_name)


if __name__ == "__main__":
    main()
