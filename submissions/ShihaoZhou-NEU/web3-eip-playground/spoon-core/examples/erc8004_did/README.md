# ERC-8004 DID Agent Demo

End-to-end demonstration of trustless AI agent identity on NeoX blockchain with NeoFS storage.

## Overview

This demo showcases the ERC-8004 Trustless Agent standard:

- **Server**: ReAct-style agent (`ERC8004SearchAgent`) with live web search via Tavily
- **Client**: Reads on-chain agent metadata from IdentityRegistry and queries the server
- **Storage**: Agent Card and DID documents stored on NeoFS (T5 testnet)
- **Registration**: Separate script for complete agent registration workflow

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   NeoFS (T5)    │     │  NeoX Testnet    │     │  Tavily API     │
│  ┌───────────┐  │     │  ┌────────────┐  │     │                 │
│  │Agent Card │  │     │  │ Identity   │  │     │  Web Search     │
│  │DID Doc    │  │     │  │ Registry   │  │     │                 │
│  └───────────┘  │     │  └────────────┘  │     └────────┬────────┘
└────────┬────────┘     └────────┬─────────┘              │
         │                       │                        │
         │    neofs://...        │  tokenURI/metadata     │
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        ERC8004 Demo                              │
│  ┌──────────────────┐              ┌──────────────────────────┐ │
│  │   Client Agent   │──── POST ───▶│     Server Agent         │ │
│  │                  │    /ask      │  (ERC8004SearchAgent)    │ │
│  │ - Fetch metadata │◀── JSON ────│  - ReAct + Tavily        │ │
│  │ - Ask questions  │              │  - Answer ERC-8004 Q&A   │ │
│  └──────────────────┘              └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Deployed Contracts (NeoX Testnet)

Open registration - anyone can register agents without special permissions.

| Contract | Address |
|----------|---------|
| IdentityRegistry | `0xaB5623F3DD66f2a52027FA06007C78c7b0E63508` |
| ReputationRegistry | `0x8bb086D12659D6e2c7220b07152255d10b2fB049` |
| ValidationRegistry | `0x18A9240c99c7283d9332B738f9C6972b5B59aEc2` |

- **RPC**: `https://testnet.rpc.banelabs.org`
- **Chain ID**: `12227332`
- **Explorer**: `https://xt4scan.ngd.network/`

## Pre-registered Resources

| Resource | Value |
|----------|-------|
| NeoFS Container | `CK44Vxzo21RED5LAZcBjQAGVQsPW5cLCxnr36vEBXvLG` |
| DID Document | `neofs://CK44Vxzo21RED5LAZcBjQAGVQsPW5cLCxnr36vEBXvLG/5r1VFgZi5Vnh4woLyYyTpSv67sNJ2E1MC75H21bpKwQE` |
| Agent Card | `neofs://CK44Vxzo21RED5LAZcBjQAGVQsPW5cLCxnr36vEBXvLG/QXxz1MnhzuU7sxDiBfUdbWUGtLNpgFBtQrA2mqowzKb` |
| Pre-registered Agent ID | `3` |

## Quick Start

### Prerequisites

1. Python 3.12+ with virtualenv
2. Install dependencies:
   ```bash
   cd core
   pip install -e .
   ```
3. API keys:
   ```bash
   export OPENAI_API_KEY=sk-...      # Required for ReAct agent
   export TAVILY_API_KEY=tvly-...    # Required for web search
   ```

### Run the Demo

```bash
# Use default pre-registered agent (ID=3)
python -m examples.erc8004_did.run_demo

# Use a specific agent ID
python -m examples.erc8004_did.run_demo --agent-id 7

# Custom question
python -m examples.erc8004_did.run_demo --question "How does ERC-8004 work?"
```

### Expected Output

```
============================================================
ERC-8004 DID Demo
============================================================
Agent ID: 3
Registry: 0xaB5623F3DD66f2a52027FA06007C78c7b0E63508
RPC: https://testnet.rpc.banelabs.org
Chain ID: 12227332
============================================================

Starting server: python -m examples.erc8004_did.server_agent --port 8004
Waiting for server to initialize...

Running client: python -m examples.erc8004_did.client_agent ...

Fetching agent 3 from IdentityRegistry 0xaB5623F3DD66f2a52027FA06007C78c7b0E63508 ...

Agent Info:
{
  "agent_id": 3,
  "token_uri": "neofs://CK44Vxzo21RED5LAZcBjQAGVQsPW5cLCxnr36vEBXvLG/QXxz1Mnhz...",
  "did_uri": "neofs://CK44Vxzo21RED5LAZcBjQAGVQsPW5cLCxnr36vEBXvLG/5r1VFgZi...",
  "card_uri": "neofs://CK44Vxzo21RED5LAZcBjQAGVQsPW5cLCxnr36vEBXvLG/QXxz1Mnhz..."
}

Asking server at http://127.0.0.1:8004 ...
Question: What is ERC-8004 and how do I register an agent?

Response:
{
  "agent": "ERC8004 Search Agent",
  "question": "What is ERC-8004 and how do I register an agent?",
  "answer": "ERC-8004 is a standard for trustless AI agents..."
}

Stopping server...
```

## Register a New Agent

Use the dedicated registration script for complete agent registration workflow.

### Dry Run (Preview)

```bash
python -m examples.erc8004_did.scripts.register_agent \
    --name "My AI Agent" \
    --description "A helpful AI assistant" \
    --capabilities "search,chat,analysis" \
    --dry-run
```

### Full Registration

```bash
# Set your private key (funded with NeoX testnet GAS)
export PRIVATE_KEY=0x...

# Register agent
python -m examples.erc8004_did.scripts.register_agent \
    --name "My AI Agent" \
    --description "A helpful AI assistant" \
    --capabilities "search,chat,analysis" \
    --container-id CK44Vxzo21RED5LAZcBjQAGVQsPW5cLCxnr36vEBXvLG
```

### Registration Workflow

1. **Generate Agent Card**: Creates JSON with agent metadata
2. **Generate DID Document**: Creates W3C DID document (optional)
3. **Upload to NeoFS**: Stores documents on decentralized storage
4. **Register On-Chain**: Calls `IdentityRegistry.register(tokenURI)`
5. **Set Metadata**: Stores `card_uri` and `did_uri` on-chain

### Registration Options

| Option | Description |
|--------|-------------|
| `--name` | Agent display name (required) |
| `--description` | Brief description |
| `--capabilities` | Comma-separated list (e.g., "search,chat") |
| `--version` | Version string (default: "1.0.0") |
| `--container-id` | NeoFS container for storage |
| `--dry-run` | Preview without uploading/registering |
| `--skip-did` | Skip DID document generation |
| `--output-dir` | Save generated JSON files locally |

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for the ReAct agent |
| `TAVILY_API_KEY` | Tavily API key for web search |

### Blockchain (Optional - has defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEOX_RPC_URL` | `https://testnet.rpc.banelabs.org` | RPC endpoint |
| `NEOX_CHAIN_ID` | `12227332` | Chain ID |
| `NEOX_IDENTITY_REGISTRY` | `0xaB5623F3DD66f2a52027FA06007C78c7b0E63508` | IdentityRegistry address |
| `NEOX_REPUTATION_REGISTRY` | `0x8bb086D12659D6e2c7220b07152255d10b2fB049` | ReputationRegistry address |
| `NEOX_VALIDATION_REGISTRY` | `0x18A9240c99c7283d9332B738f9C6972b5B59aEc2` | ValidationRegistry address |
| `PRIVATE_KEY` | - | EOA private key for registration |
| `ERC8004_AGENT_ID` | `3` | Default agent ID to query |

### NeoFS (For registration)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEOFS_BASE_URL` | `https://rest.t5.fs.neo.org` | NeoFS REST gateway |
| `NEOFS_DID_CONTAINER` | - | Container ID for DID storage |
| `NEOFS_OWNER_ADDRESS` | - | NeoFS owner address |
| `NEOFS_PRIVATE_KEY_WIF` | - | NeoFS private key (WIF format) |

## Project Structure

```
examples/erc8004_did/
├── README.md              # This file
├── __init__.py
├── run_demo.py            # One-shot demo launcher
├── server_agent.py        # ReAct agent server with Tavily search
├── client_agent.py        # Client that fetches on-chain data
└── scripts/
    ├── __init__.py
    └── register_agent.py  # Complete registration workflow
```

## Component Details

### run_demo.py

Orchestrates the demo by:
1. Starting the server in a subprocess
2. Waiting for initialization
3. Running the client
4. Stopping the server

```bash
python -m examples.erc8004_did.run_demo --help
```

### server_agent.py

HTTP server exposing `/ask` endpoint:
- Uses `SpoonReactMCP` base agent
- Integrates Tavily MCP tool for live search
- Returns JSON responses

```bash
# Run standalone
python -m examples.erc8004_did.server_agent --port 8004

# Test with curl
curl -X POST http://127.0.0.1:8004/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "What is ERC-8004?"}'
```

### client_agent.py

Fetches agent metadata and queries the server:
- Reads `tokenURI` and metadata from IdentityRegistry
- Resolves NeoFS URIs
- Posts questions to the server

```bash
python -m examples.erc8004_did.client_agent --agent-id 3 --help
```

### scripts/register_agent.py

Complete registration workflow:
- Generates Agent Card JSON
- Generates DID document
- Uploads to NeoFS
- Registers on-chain

```bash
python -m examples.erc8004_did.scripts.register_agent --help
```

## Troubleshooting

### "TAVILY_API_KEY is missing"

Set the environment variable:
```bash
export TAVILY_API_KEY=tvly-...
```

### "Cannot connect to RPC"

Check your network connection. The default RPC (`https://testnet.rpc.banelabs.org`) should be accessible.

### "Registry has no agents"

The registry might be newly deployed or empty. Register a new agent using the registration script.

### "Agent ID exceeds totalAgents"

The specified agent ID doesn't exist. Check available agents:
```python
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://testnet.rpc.banelabs.org"))
contract = w3.eth.contract(address="0xaB5623F3DD66f2a52027FA06007C78c7b0E63508", abi=[...])
print(contract.functions.totalAgents().call())
```

### "Connection refused to /ask"

The server might not be ready. Wait a few more seconds or check server logs.

### NeoFS upload fails

- Verify `NEOFS_BASE_URL` is accessible
- Check container permissions
- Ensure valid `NEOFS_PRIVATE_KEY_WIF`
