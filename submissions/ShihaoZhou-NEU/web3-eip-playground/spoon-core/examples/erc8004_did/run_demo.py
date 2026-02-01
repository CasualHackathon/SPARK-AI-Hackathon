"""
ERC-8004 DID Demo Launcher
==========================

End-to-end demo that:
1. Starts the ERC8004SearchAgent server (ReAct agent with Tavily search)
2. Runs the client to fetch on-chain agent data and ask a question
3. Stops the server

Usage:
    # Use default pre-registered agent (ID=3):
    python -m examples.erc8004_did.run_demo

    # Specify a different agent ID:
    python -m examples.erc8004_did.run_demo --agent-id 7

    # Custom registry address:
    python -m examples.erc8004_did.run_demo --registry 0x...

Environment variables:
    TAVILY_API_KEY            Required for live web search
    OPENAI_API_KEY            Required for the ReAct agent
    NEOX_IDENTITY_REGISTRY    IdentityRegistry address (default: 0xaB5623F3DD66f2a52027FA06007C78c7b0E63508)
    ERC8004_AGENT_ID          Agent token ID to query (default: 3)
    NEOX_RPC_URL              RPC endpoint (default: https://testnet.rpc.banelabs.org)
    NEOX_CHAIN_ID             Chain ID (default: 12227332)

Deployed contracts (NeoX Testnet - open registration):
    IdentityRegistry:   0xaB5623F3DD66f2a52027FA06007C78c7b0E63508
    ReputationRegistry: 0x8bb086D12659D6e2c7220b07152255d10b2fB049
    ValidationRegistry: 0x18A9240c99c7283d9332B738f9C6972b5B59aEc2

To register a new agent, use the separate registration script:
    python -m examples.erc8004_did.scripts.register_agent --help
"""

from __future__ import annotations

import os
from pathlib import Path
import argparse
import subprocess
import sys
import time

try:
    from dotenv import load_dotenv
    core_dir = Path(__file__).resolve().parents[2]
    load_dotenv(core_dir / ".env", override=False)
except Exception:
    pass


# Default contract addresses (NeoX Testnet)
DEFAULT_IDENTITY_REGISTRY = "0xaB5623F3DD66f2a52027FA06007C78c7b0E63508"
DEFAULT_RPC_URL = "https://testnet.rpc.banelabs.org"
DEFAULT_CHAIN_ID = "12227332"
DEFAULT_AGENT_ID = "3"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run ERC-8004 server + client demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with default pre-registered agent:
    python -m examples.erc8004_did.run_demo

    # Run with a specific agent ID:
    python -m examples.erc8004_did.run_demo --agent-id 7

    # Custom question:
    python -m examples.erc8004_did.run_demo --question "What is ERC-8004?"
        """,
    )

    parser.add_argument(
        "--agent-id",
        type=int,
        default=int(os.getenv("ERC8004_AGENT_ID", DEFAULT_AGENT_ID)),
        help=f"Agent token ID to query (default: {DEFAULT_AGENT_ID})",
    )
    parser.add_argument(
        "--registry",
        default=os.getenv("NEOX_IDENTITY_REGISTRY", DEFAULT_IDENTITY_REGISTRY),
        help="IdentityRegistry contract address",
    )
    parser.add_argument(
        "--rpc",
        default=os.getenv("NEOX_RPC_URL", DEFAULT_RPC_URL),
        help="RPC endpoint URL",
    )
    parser.add_argument(
        "--chain-id",
        default=os.getenv("NEOX_CHAIN_ID", DEFAULT_CHAIN_ID),
        help="Chain ID",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("ERC8004_AGENT_PORT", "8004")),
        help="Server port (default: 8004)",
    )
    parser.add_argument(
        "--question",
        default="What is ERC-8004 and how do I register an agent?",
        help="Question to ask the agent",
    )

    args = parser.parse_args()

    # Prepare environment
    env = os.environ.copy()
    core_dir = Path(__file__).resolve().parents[2]
    env["PYTHONPATH"] = f"{core_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"

    # Start server
    server_cmd = [
        sys.executable,
        "-m",
        "examples.erc8004_did.server_agent",
        "--port",
        str(args.port),
    ]

    print("=" * 60)
    print("ERC-8004 DID Demo")
    print("=" * 60)
    print(f"Agent ID: {args.agent_id}")
    print(f"Registry: {args.registry}")
    print(f"RPC: {args.rpc}")
    print(f"Chain ID: {args.chain_id}")
    print("=" * 60)
    print()

    print("Starting server:", " ".join(server_cmd))
    server = subprocess.Popen(server_cmd, env=env)

    # Wait for server to start
    print("Waiting for server to initialize...")
    time.sleep(10)

    # Run client
    client_cmd = [
        sys.executable,
        "-m",
        "examples.erc8004_did.client_agent",
        "--server",
        f"http://127.0.0.1:{args.port}",
        "--agent-id",
        str(args.agent_id),
        "--registry",
        args.registry,
        "--rpc",
        args.rpc,
        "--chain-id",
        str(args.chain_id),
        "--question",
        args.question,
    ]

    print("\nRunning client:", " ".join(client_cmd[:6]), "...")
    print()

    try:
        subprocess.check_call(client_cmd, env=env)
    finally:
        print("\nStopping server...")
        server.terminate()
        try:
            server.wait(timeout=5)
        except Exception:
            server.kill()


if __name__ == "__main__":
    main()
