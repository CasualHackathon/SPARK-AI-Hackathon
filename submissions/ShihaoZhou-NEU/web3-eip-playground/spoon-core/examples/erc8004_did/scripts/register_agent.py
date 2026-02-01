"""
ERC-8004 Agent Registration Script
==================================

Complete workflow for registering an agent on the ERC-8004 IdentityRegistry:
1. Generate Agent Card JSON (with optional DID document)
2. Upload to NeoFS (or IPFS as fallback)
3. Register on-chain with metadata

Usage:
    # Dry-run (shows what would happen without uploading/registering):
    python -m examples.erc8004_did.scripts.register_agent \
        --name "MyAgent" \
        --description "A helpful AI agent" \
        --dry-run

    # Full registration:
    python -m examples.erc8004_did.scripts.register_agent \
        --name "MyAgent" \
        --description "A helpful AI agent" \
        --capabilities "search,chat,analysis" \
        --container-id CK44Vxzo21RED5LAZcBjQAGVQsPW5cLCxnr36vEBXvLG

Environment variables:
    PRIVATE_KEY               EOA private key for signing transactions (required)
    NEOX_RPC_URL              RPC endpoint (default: https://testnet.rpc.banelabs.org)
    NEOX_CHAIN_ID             Chain ID (default: 12227332)
    NEOX_IDENTITY_REGISTRY    IdentityRegistry address
    NEOX_REPUTATION_REGISTRY  ReputationRegistry address
    NEOX_VALIDATION_REGISTRY  ValidationRegistry address
    NEOFS_BASE_URL            NeoFS REST gateway URL
    NEOFS_OWNER_ADDRESS       NeoFS owner address
    NEOFS_PRIVATE_KEY_WIF     NeoFS private key (WIF format)

Deployed contracts (NeoX Testnet - open registration):
    IdentityRegistry:   0xaB5623F3DD66f2a52027FA06007C78c7b0E63508
    ReputationRegistry: 0x8bb086D12659D6e2c7220b07152255d10b2fB049
    ValidationRegistry: 0x18A9240c99c7283d9332B738f9C6972b5B59aEc2
"""

from __future__ import annotations

import argparse
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

os.environ.setdefault("WEB3_ENABLE_CKZG", "0")

try:
    from dotenv import load_dotenv
    core_dir = Path(__file__).resolve().parents[3]
    load_dotenv(core_dir / ".env", override=False)
except Exception:
    pass

import requests
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware


# ============================================================================
# Constants
# ============================================================================

DEFAULT_RPC_URL = "https://testnet.rpc.banelabs.org"
DEFAULT_CHAIN_ID = 12227332
DEFAULT_IDENTITY_REGISTRY = "0xaB5623F3DD66f2a52027FA06007C78c7b0E63508"
DEFAULT_REPUTATION_REGISTRY = "0x8bb086D12659D6e2c7220b07152255d10b2fB049"
DEFAULT_VALIDATION_REGISTRY = "0x18A9240c99c7283d9332B738f9C6972b5B59aEc2"
DEFAULT_NEOFS_BASE_URL = "https://rest.t5.fs.neo.org"

# Minimal ABI for SpoonIdentityRegistry
IDENTITY_ABI_MIN = [
    {
        "inputs": [{"internalType": "string", "name": "tokenURI_", "type": "string"}],
        "name": "register",
        "outputs": [{"internalType": "uint256", "name": "agentId", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "agentId", "type": "uint256"},
            {"internalType": "string", "name": "key", "type": "string"},
            {"internalType": "bytes", "name": "value", "type": "bytes"},
        ],
        "name": "setMetadata",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalAgents",
        "outputs": [{"internalType": "uint256", "name": "count", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]


# ============================================================================
# Agent Card / DID Generation
# ============================================================================

def generate_agent_card(
    name: str,
    description: str,
    capabilities: List[str],
    owner_address: str,
    version: str = "1.0.0",
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate an Agent Card JSON document following the ERC-8004 spec.

    Args:
        name: Agent display name
        description: Brief description of the agent
        capabilities: List of capability tags (e.g., ["search", "chat"])
        owner_address: Ethereum address of the agent owner
        version: Version string
        extra_metadata: Additional metadata fields

    Returns:
        Agent Card JSON object
    """
    agent_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    card = {
        "id": f"urn:spoon:agent:{agent_id}",
        "name": name,
        "description": description,
        "version": version,
        "capabilities": capabilities,
        "controller": [owner_address],
        "created": now,
        "updated": now,
    }

    if extra_metadata:
        card["metadata"] = extra_metadata

    return card


def generate_did_document(
    agent_card: Dict[str, Any],
    owner_address: str,
) -> Dict[str, Any]:
    """
    Generate a DID document for the agent.

    Args:
        agent_card: The agent card JSON
        owner_address: Ethereum address of the agent owner

    Returns:
        DID document JSON object
    """
    agent_id = agent_card["id"].split(":")[-1]
    did = f"did:spoon:agent:{agent_id}"

    return {
        "@context": [
            "https://www.w3.org/ns/did/v1",
            "https://w3id.org/security/suites/secp256k1-2019/v1",
        ],
        "id": did,
        "controller": [owner_address],
        "verificationMethod": [
            {
                "id": f"{did}#owner",
                "type": "EcdsaSecp256k1RecoveryMethod2020",
                "controller": did,
                "blockchainAccountId": f"eip155:12227332:{owner_address}",
            }
        ],
        "authentication": [f"{did}#owner"],
        "assertionMethod": [f"{did}#owner"],
    }


# ============================================================================
# NeoFS Upload
# ============================================================================

def upload_to_neofs(
    content: bytes,
    filename: str,
    container_id: str,
    base_url: str,
    owner_address: str,
    private_key_wif: str,
) -> str:
    """
    Upload content to NeoFS and return the neofs:// URI.

    Args:
        content: File content to upload
        filename: Filename for the object
        container_id: NeoFS container ID
        base_url: NeoFS REST gateway URL
        owner_address: NeoFS owner address
        private_key_wif: NeoFS private key in WIF format

    Returns:
        NeoFS URI (e.g., neofs://container/object)
    """
    url = f"{base_url}/v1/objects/{container_id}"

    headers = {
        "Content-Type": "application/json",
        "X-Neofs-Owner-Id": owner_address,
    }

    # Add auth header if private key provided
    if private_key_wif:
        headers["X-Neofs-Bearer-Token"] = private_key_wif

    # Upload as JSON payload with base64 content
    import base64
    payload = {
        "containerId": container_id,
        "fileName": filename,
        "payload": base64.b64encode(content).decode("ascii"),
    }

    response = requests.post(url, json=payload, headers=headers, timeout=60)

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"NeoFS upload failed: {response.status_code} - {response.text}"
        )

    result = response.json()
    object_id = result.get("objectId") or result.get("object_id")

    if not object_id:
        raise RuntimeError(f"NeoFS response missing objectId: {result}")

    return f"neofs://{container_id}/{object_id}"


# ============================================================================
# On-Chain Registration
# ============================================================================

def connect_web3(rpc_url: str, chain_id: int) -> Web3:
    """Connect to the EVM network with PoA middleware if needed."""
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if chain_id in (12227332, 97, 56, 11155111):  # PoA chains
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to {rpc_url}")
    return w3


def register_on_chain(
    w3: Web3,
    identity_registry: str,
    private_key: str,
    token_uri: str,
    metadata: Optional[List[Tuple[str, str]]] = None,
) -> int:
    """
    Register an agent on the IdentityRegistry.

    Args:
        w3: Web3 instance
        identity_registry: IdentityRegistry contract address
        private_key: EOA private key for signing
        token_uri: URI to the Agent Card (stored as tokenURI)
        metadata: List of (key, value) pairs to set as metadata

    Returns:
        The newly registered agent ID
    """
    account = w3.eth.account.from_key(private_key)
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(identity_registry),
        abi=IDENTITY_ABI_MIN,
    )

    # Get total agents before registration
    total_before = contract.functions.totalAgents().call()

    # Build and send register transaction
    nonce = w3.eth.get_transaction_count(account.address)
    tx = contract.functions.register(token_uri).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 500000,
        "gasPrice": w3.eth.gas_price,
    })

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    if receipt.status != 1:
        raise RuntimeError(f"Registration tx failed: {tx_hash.hex()}")

    # Get the new agent ID
    total_after = contract.functions.totalAgents().call()
    agent_id = total_after  # Agent IDs start at 1 and increment

    print(f"Registered agent ID: {agent_id}")
    print(f"Transaction hash: {tx_hash.hex()}")

    # Set metadata if provided
    if metadata:
        for key, value in metadata:
            nonce = w3.eth.get_transaction_count(account.address)
            meta_tx = contract.functions.setMetadata(
                agent_id, key, value.encode() if isinstance(value, str) else value
            ).build_transaction({
                "from": account.address,
                "nonce": nonce,
                "gas": 200000,
                "gasPrice": w3.eth.gas_price,
            })
            signed = account.sign_transaction(meta_tx)
            meta_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            w3.eth.wait_for_transaction_receipt(meta_hash, timeout=60)
            print(f"Set metadata '{key}': {meta_hash.hex()}")

    return agent_id


# ============================================================================
# Main CLI
# ============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register an agent on ERC-8004 IdentityRegistry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry-run to see generated Agent Card:
    python -m examples.erc8004_did.scripts.register_agent \\
        --name "MyAgent" --description "A helpful agent" --dry-run

    # Full registration with NeoFS upload:
    python -m examples.erc8004_did.scripts.register_agent \\
        --name "MyAgent" \\
        --description "A helpful AI agent" \\
        --capabilities "search,chat" \\
        --container-id CK44Vxzo21RED5LAZcBjQAGVQsPW5cLCxnr36vEBXvLG
        """,
    )

    # Agent info
    parser.add_argument("--name", required=True, help="Agent display name")
    parser.add_argument("--description", default="", help="Agent description")
    parser.add_argument(
        "--capabilities",
        default="",
        help="Comma-separated list of capabilities (e.g., 'search,chat')",
    )
    parser.add_argument("--version", default="1.0.0", help="Agent version")

    # NeoFS config
    parser.add_argument(
        "--container-id",
        default=os.getenv("NEOFS_DID_CONTAINER"),
        help="NeoFS container ID for storing Agent Card",
    )
    parser.add_argument(
        "--neofs-url",
        default=os.getenv("NEOFS_BASE_URL", DEFAULT_NEOFS_BASE_URL),
        help="NeoFS REST gateway URL",
    )
    parser.add_argument(
        "--neofs-owner",
        default=os.getenv("NEOFS_OWNER_ADDRESS"),
        help="NeoFS owner address",
    )
    parser.add_argument(
        "--neofs-key",
        default=os.getenv("NEOFS_PRIVATE_KEY_WIF"),
        help="NeoFS private key (WIF format)",
    )

    # Blockchain config
    parser.add_argument(
        "--rpc",
        default=os.getenv("NEOX_RPC_URL", DEFAULT_RPC_URL),
        help="RPC endpoint URL",
    )
    parser.add_argument(
        "--chain-id",
        type=int,
        default=int(os.getenv("NEOX_CHAIN_ID", str(DEFAULT_CHAIN_ID))),
        help="Chain ID",
    )
    parser.add_argument(
        "--registry",
        default=os.getenv("NEOX_IDENTITY_REGISTRY", DEFAULT_IDENTITY_REGISTRY),
        help="IdentityRegistry contract address",
    )
    parser.add_argument(
        "--private-key",
        default=os.getenv("PRIVATE_KEY"),
        help="EOA private key for signing transactions",
    )

    # Behavior flags
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate Agent Card and show what would happen, without uploading or registering",
    )
    parser.add_argument(
        "--skip-did",
        action="store_true",
        help="Skip DID document generation (only create Agent Card)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Save generated JSON files to this directory",
    )

    args = parser.parse_args()

    # Validate required args
    if not args.dry_run:
        if not args.private_key:
            parser.error("--private-key or PRIVATE_KEY env var is required")
        if not args.container_id:
            parser.error("--container-id or NEOFS_DID_CONTAINER env var is required")

    # Get owner address from private key
    if args.private_key:
        w3_temp = Web3()
        owner_address = w3_temp.eth.account.from_key(args.private_key).address
    else:
        owner_address = "0x0000000000000000000000000000000000000000"

    # Parse capabilities
    capabilities = [c.strip() for c in args.capabilities.split(",") if c.strip()]

    # Generate Agent Card
    print("\n=== Generating Agent Card ===")
    agent_card = generate_agent_card(
        name=args.name,
        description=args.description,
        capabilities=capabilities,
        owner_address=owner_address,
        version=args.version,
    )
    print(json.dumps(agent_card, indent=2))

    # Generate DID document
    did_doc = None
    if not args.skip_did:
        print("\n=== Generating DID Document ===")
        did_doc = generate_did_document(agent_card, owner_address)
        print(json.dumps(did_doc, indent=2))

    # Save to output directory if specified
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        card_path = args.output_dir / "agent_card.json"
        card_path.write_text(json.dumps(agent_card, indent=2))
        print(f"\nSaved Agent Card to: {card_path}")

        if did_doc:
            did_path = args.output_dir / "did_document.json"
            did_path.write_text(json.dumps(did_doc, indent=2))
            print(f"Saved DID Document to: {did_path}")

    # Dry-run stops here
    if args.dry_run:
        print("\n=== Dry Run Complete ===")
        print("No upload or registration performed.")
        print(f"\nTo register for real, add: --container-id {args.container_id or '<container-id>'}")
        return

    # Upload to NeoFS
    print("\n=== Uploading to NeoFS ===")
    card_content = json.dumps(agent_card, indent=2).encode()
    card_uri = upload_to_neofs(
        content=card_content,
        filename=f"agent_card_{agent_card['id'].split(':')[-1]}.json",
        container_id=args.container_id,
        base_url=args.neofs_url,
        owner_address=args.neofs_owner or "",
        private_key_wif=args.neofs_key or "",
    )
    print(f"Agent Card URI: {card_uri}")

    did_uri = ""
    if did_doc:
        did_content = json.dumps(did_doc, indent=2).encode()
        did_uri = upload_to_neofs(
            content=did_content,
            filename=f"did_{did_doc['id'].split(':')[-1]}.json",
            container_id=args.container_id,
            base_url=args.neofs_url,
            owner_address=args.neofs_owner or "",
            private_key_wif=args.neofs_key or "",
        )
        print(f"DID Document URI: {did_uri}")

    # Register on-chain
    print("\n=== Registering On-Chain ===")
    print(f"Registry: {args.registry}")
    print(f"RPC: {args.rpc}")
    print(f"Chain ID: {args.chain_id}")

    w3 = connect_web3(args.rpc, args.chain_id)

    metadata = [("card_uri", card_uri)]
    if did_uri:
        metadata.append(("did_uri", did_uri))
        metadata.append(("did_doc_uri", did_uri))  # Also set did_doc_uri for compatibility

    agent_id = register_on_chain(
        w3=w3,
        identity_registry=args.registry,
        private_key=args.private_key,
        token_uri=card_uri,
        metadata=metadata,
    )

    print("\n=== Registration Complete ===")
    print(f"Agent ID: {agent_id}")
    print(f"Token URI: {card_uri}")
    if did_uri:
        print(f"DID URI: {did_uri}")
    print(f"\nVerify with: python -m examples.erc8004_did.run_demo --agent-id {agent_id}")


if __name__ == "__main__":
    main()
