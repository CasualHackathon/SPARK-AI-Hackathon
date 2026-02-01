from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from eth_account import Account
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from web3 import Web3
from web3.exceptions import ContractLogicError


# Load .env automatically for local/demo usage, matching repository guidance.
load_dotenv(override=True)


# ----------------------------
# Configuration + Web3 helpers
# ----------------------------

_MINT_ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "gameId", "type": "uint256"},
            {"name": "claimId", "type": "bytes32"},
        ],
        "name": "mintTo",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": True, "name": "tokenId", "type": "uint256"},
            {"indexed": False, "name": "index", "type": "uint8"},
            {"indexed": True, "name": "gameId", "type": "uint256"},
            {"indexed": False, "name": "claimId", "type": "bytes32"},
        ],
        "name": "Minted",
        "type": "event",
    },
]

_web3: Optional[Web3] = None
_contract = None
_minter_account = None
_minter_private_key: Optional[str] = None
_contract_address: Optional[str] = None


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def _init_web3() -> None:
    global _web3, _contract, _minter_account, _minter_private_key, _contract_address
    if _web3 is not None:
        return

    rpc_url = _require_env("SEPOLIA_RPC_URL")
    _contract_address = _require_env("CONTRACT_ADDRESS")
    _minter_private_key = _require_env("MINTER_PRIVATE_KEY")

    _web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not _web3.is_connected():
        raise RuntimeError("Web3 provider not connected")

    _minter_account = Account.from_key(_minter_private_key)
    _contract = _web3.eth.contract(
        address=_web3.to_checksum_address(_contract_address),
        abi=_MINT_ABI,
    )


def _parse_minted_event(receipt: Dict[str, Any]) -> Dict[str, Any]:
    logs = _contract.events.Minted().process_receipt(receipt)  # type: ignore[union-attr]
    if not logs:
        raise RuntimeError("Minted event not found in receipt")
    return logs[0]["args"]


# ----------------------------
# FastAPI app
# ----------------------------

app = FastAPI(title="Spoon NFT Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# Models
# ----------------------------


class ClaimBadgeRequest(BaseModel):
    user_address: str = Field(alias="userAddress")

    model_config = {"populate_by_name": True}


class ClaimBadgeResponse(BaseModel):
    success: bool
    token_id: int = Field(alias="tokenId")
    contract_address: str = Field(alias="contractAddress")
    tx_hash: str = Field(alias="txHash")

    model_config = {"populate_by_name": True}


# ----------------------------
# Routes
# ----------------------------


@app.post("/claim-badge/7702", response_model=ClaimBadgeResponse)
def claim_badge_7702(req: ClaimBadgeRequest) -> ClaimBadgeResponse:
    return _claim_badge_for_game(req, game_id=7702)


@app.post("/claim-badge/8004", response_model=ClaimBadgeResponse)
def claim_badge_8004(req: ClaimBadgeRequest) -> ClaimBadgeResponse:
    return _claim_badge_for_game(req, game_id=8004)


@app.post("/claim-badge/1559", response_model=ClaimBadgeResponse)
def claim_badge_1559(req: ClaimBadgeRequest) -> ClaimBadgeResponse:
    return _claim_badge_for_game(req, game_id=1559)


def _claim_badge_for_game(req: ClaimBadgeRequest, game_id: int) -> ClaimBadgeResponse:
    try:
        _init_web3()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    assert _web3 is not None
    assert _contract is not None
    assert _minter_account is not None
    assert _minter_private_key is not None
    assert _contract_address is not None

    if not _web3.is_address(req.user_address):
        raise HTTPException(status_code=400, detail="invalid_user_address")

    to_address = _web3.to_checksum_address(req.user_address)
    claim_raw = f"{req.user_address.lower()}|{game_id}|{int(time.time() * 1000)}"
    claim_id_bytes = _web3.keccak(text=claim_raw)

    try:
        fn = _contract.functions.mintTo(to_address, game_id, claim_id_bytes)
        gas_estimate = fn.estimate_gas({"from": _minter_account.address})
        tx = fn.build_transaction(
            {
                "from": _minter_account.address,
                "nonce": _web3.eth.get_transaction_count(_minter_account.address),
                "chainId": _web3.eth.chain_id,
                "gas": gas_estimate,
                "gasPrice": _web3.eth.gas_price,
            }
        )
        signed = _web3.eth.account.sign_transaction(tx, _minter_private_key)
        tx_hash = _web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = _web3.eth.wait_for_transaction_receipt(tx_hash)
    except ContractLogicError as exc:
        message = str(exc)
        if "NotMinter" in message:
            raise HTTPException(status_code=403, detail="not_minter") from exc
        if "Paused" in message:
            raise HTTPException(status_code=423, detail="contract_paused") from exc
        if "ClaimAlreadyUsed" in message:
            raise HTTPException(status_code=409, detail="claim_already_used") from exc
        if "ZeroAddress" in message:
            raise HTTPException(status_code=400, detail="zero_address") from exc
        raise HTTPException(status_code=400, detail="contract_error") from exc
    except Exception as exc:  # noqa: BLE001 - keep demo flow simple
        raise HTTPException(status_code=500, detail="mint_failed") from exc

    if receipt.get("status") != 1:
        raise HTTPException(status_code=502, detail="transaction_failed")

    event = _parse_minted_event(receipt)
    token_id = int(event["tokenId"])

    return ClaimBadgeResponse(
        success=True,
        token_id=token_id,
        contract_address=_contract_address,
        tx_hash=tx_hash.hex(),
    )
