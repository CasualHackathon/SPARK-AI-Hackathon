"""
Multi-Account Use Case - Turnkey SDK

Objective: Demonstrate how Trading AI Agent manages multiple wallets/accounts within the same organization:
1) Enumerate wallets & accounts  2) Build & sign transactions for each account  3) Optional broadcast
4) Per-account message signing  5) Query audit activities

Quick Start:
1) pip install -r requirements.txt
2) cp examples/turnkey/env.example .env and fill in TURNKEY_* values
3) Optional: Set WEB3_RPC_URL to enable per-account EIP-1559 transaction signing (signing only, no default broadcast)
4) Run: python -m examples.turnkey.multi_account_use_case

Safe Defaults:
- Transactions are not broadcasted by default. Set MULTI_ENABLE_BROADCAST=1 and TX_VALUE_WEI>0 to attempt broadcast.
"""

import os
import json
from typing import List, Dict, Optional

from dotenv import load_dotenv


def int_to_bytes(value: int) -> bytes:
    if value == 0:
        return b""
    return value.to_bytes((value.bit_length() + 7) // 8, byteorder="big")


def build_unsigned_eip1559_tx(w3, from_addr: str, to_addr: Optional[str], value_wei: int, data_hex: str = "0x",
                              priority_gwei: int = 1, gas_limit_override: Optional[int] = None) -> str:
    """Build minimal EIP-1559 unsigned transaction (transfer; gasLimit=21000 when data is empty)."""
    import rlp
    from web3 import Web3

    chain_id = w3.eth.chain_id
    nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(from_addr))
    latest = w3.eth.get_block("latest")
    base_fee = latest.get("baseFeePerGas", w3.to_wei(1, "gwei"))
    max_priority_fee_per_gas = w3.to_wei(priority_gwei, "gwei")
    max_fee_per_gas = base_fee * 2 + max_priority_fee_per_gas

    if gas_limit_override:
        gas_limit = gas_limit_override
    else:
        # Simple transfer fixed at 21000; for contract interaction, estimate first
        gas_limit = 21000 if (data_hex == "0x") else 100000

    fields = [
        int_to_bytes(chain_id),
        int_to_bytes(nonce),
        int_to_bytes(max_priority_fee_per_gas),
        int_to_bytes(max_fee_per_gas),
        int_to_bytes(gas_limit),
        bytes.fromhex(to_addr[2:]) if to_addr else b"",
        int_to_bytes(value_wei),
        bytes.fromhex(data_hex[2:]) if data_hex and data_hex != "0x" else b"",
        [],  # accessList empty
    ]

    encoded = rlp.encode(fields)
    return "0x02" + encoded.hex()


def list_all_accounts(tk) -> List[Dict]:
    """List all wallet accounts within organization, returns [{walletId, walletName, address}]."""
    accounts: List[Dict] = []
    try:
        wallets_resp = tk.list_wallets()
        for w in wallets_resp.get("wallets", []) or []:
            wallet_id = w.get("walletId")
            wallet_name = w.get("walletName", "")
            wa_resp = tk.list_wallet_accounts(wallet_id, limit="50")
            for acc in wa_resp.get("accounts", []) or []:
                address = acc.get("address")
                if address:
                    accounts.append({
                        "walletId": wallet_id,
                        "walletName": wallet_name,
                        "address": address,
                    })
    except Exception as e:
        print(f"❌ Failed to list wallets/accounts: {e}")
    return accounts


def main():
    load_dotenv()

    print("🔐 Turnkey SDK · Multi-Wallet/Multi-Account Use Case")
    print("=" * 50)

    # Initialize Turnkey client
    try:
        from spoon_ai.turnkey import Turnkey
        tk = Turnkey()
        print("✅ Turnkey client initialized successfully")
    except Exception as e:
        print(f"❌ Turnkey initialization failed: {e}")
        print("💡 Please check TURNKEY_API_PUBLIC_KEY / TURNKEY_API_PRIVATE_KEY / TURNKEY_ORG_ID in .env")
        return

    # Read environment parameters
    rpc_url = os.getenv("WEB3_RPC_URL")
    tx_to = os.getenv("TX_TO_ADDRESS")  # If not set, defaults to self-address signing (broadcast not recommended)
    tx_value_wei = int(os.getenv("TX_VALUE_WEI", "0"))
    priority_gwei = int(os.getenv("TX_PRIORITY_FEE_GWEI", "1"))
    enable_broadcast = os.getenv("MULTI_ENABLE_BROADCAST", "0") == "1"
    max_accounts = int(os.getenv("MULTI_MAX_ACCOUNTS", "3"))

    # Optional: RPC client
    w3 = None
    if rpc_url:
        try:
            from web3 import Web3
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                print(f"🌐 Connected to RPC, chainId={w3.eth.chain_id}")
            else:
                print("⚠️  Cannot connect to RPC, will skip transaction signing and broadcasting")
                w3 = None
        except Exception as e:
            print(f"⚠️  Cannot initialize web3: {e}, will skip transaction signing and broadcasting")

    # 1) Account discovery
    print("\n🧭 Step 1/5 · Enumerate wallets and accounts")
    accounts = list_all_accounts(tk)
    if not accounts:
        print("ℹ️  No wallet accounts found.")
        sw = os.getenv("TURNKEY_SIGN_WITH")
        if sw:
            print("   → Can still use TURNKEY_SIGN_WITH for message/EIP-712 signing demo")
        else:
            print("   → Please create wallet and accounts in Turnkey console, or configure TURNKEY_SIGN_WITH")
    else:
        for i, acc in enumerate(accounts[:max_accounts], 1):
            print(f"  {i}. {acc['walletName']} · {acc['address']}")

    # 2) Per-account transaction signing (only executed when RPC is available)
    print("\n🧩 Step 2/5 · Per-account EVM transaction signing")
    if w3 and accounts:
        for acc in accounts[:max_accounts]:
            from_addr = acc["address"]
            to_addr = tx_to or from_addr  # Default self-to-self, for signing demo only
            try:
                unsigned = build_unsigned_eip1559_tx(
                    w3=w3,
                    from_addr=from_addr,
                    to_addr=to_addr,
                    value_wei=tx_value_wei,
                    data_hex="0x",
                    priority_gwei=priority_gwei,
                )
                print(f"   • {from_addr[:10]}… unsigned: {unsigned[:16]}…")
                resp = tk.sign_evm_transaction(sign_with=from_addr, unsigned_tx=unsigned)
                signed = (
                    resp.get("activity", {})
                    .get("result", {})
                    .get("signTransactionResult", {})
                    .get("signedTransaction")
                )
                ok = bool(signed)
                print(f"     ↳ Signing result: {'✅' if ok else '❌'}")
                if not ok:
                    print("       Hint: Check policy restrictions, chain ID, or unsignedTx format")

                # Optional broadcast (default off; requires funds and TX_VALUE_WEI>0)
                if ok and enable_broadcast and tx_value_wei > 0:
                    try:
                        from eth_utils import to_bytes
                        tx_hash = w3.eth.send_raw_transaction(to_bytes(hexstr=signed))
                        print(f"       🚀 Broadcasted: {tx_hash.hex()}")
                    except Exception as e:
                        print(f"       ❌ Broadcast failed: {e}")
                        print("       Hint: Confirm account balance is sufficient and RPC is available")
                elif ok and not enable_broadcast:
                    print("       ℹ️  Skip broadcast (set MULTI_ENABLE_BROADCAST=1 to enable)")
                elif ok and enable_broadcast and tx_value_wei == 0:
                    print("       ℹ️  TX_VALUE_WEI=0, skip broadcast to avoid gas consumption failure")
            except Exception as e:
                print(f"   • {from_addr[:10]}… ❌ Build/sign failed: {e}")
    else:
        if not w3:
            print("ℹ️  RPC not configured or cannot connect, skip transaction signing. Set WEB3_RPC_URL to enable.")
        if not accounts:
            print("ℹ️  No available accounts, skip transaction signing.")

    # 3) Per-account message signing (no chain dependency, strongly recommended to demonstrate)
    print("\n🧩 Step 3/5 · Per-account message signing")
    message_template = os.getenv("TURNKEY_SIGN_MESSAGE") or "hello from multi-account demo"
    if accounts:
        for acc in accounts[:max_accounts]:
            addr = acc["address"]
            msg = f"{message_template} | {addr}"
            try:
                msg_resp = tk.sign_message(sign_with=addr, message=msg, use_keccak256=True)
                status = msg_resp.get("activity", {}).get("status")
                print(f"   • {addr[:10]}… Signing status: {status}")
            except Exception as e:
                print(f"   • {addr[:10]}… ❌ Message signing failed: {e}")
    else:
        # Fallback: use TURNKEY_SIGN_WITH demo
        sw = os.getenv("TURNKEY_SIGN_WITH")
        if sw:
            try:
                msg_resp = tk.sign_message(sign_with=sw, message=message_template, use_keccak256=True)
                status = msg_resp.get("activity", {}).get("status")
                print(f"   • Fallback account({sw[:10]}…) signing status: {status}")
            except Exception as e:
                print(f"   • Fallback account ❌ Message signing failed: {e}")
        else:
            print("ℹ️  No accounts available and TURNKEY_SIGN_WITH not configured, cannot demo message signing")

    # 4) Single account EIP-712 structured data signing (example)
    print("\n🧩 Step 4/5 · EIP-712 structured data signing (example)")
    target_addr = (accounts[0]["address"] if accounts else os.getenv("TURNKEY_SIGN_WITH"))
    if target_addr:
        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                ],
                "Mail": [
                    {"name": "contents", "type": "string"}
                ],
            },
            "primaryType": "Mail",
            "domain": {"name": "Turnkey", "version": "1", "chainId": 1},
            "message": {"contents": f"multi-account demo: {target_addr}"},
        }
        try:
            typed_resp = tk.sign_typed_data(sign_with=target_addr, typed_data=typed_data)
            status = typed_resp.get("activity", {}).get("status")
            print(f"   • {target_addr[:10]}… EIP-712 signing status: {status}")
        except Exception as e:
            print(f"   • {target_addr[:10]}… ❌ EIP-712 signing failed: {e}")
    else:
        print("ℹ️  No available address, skip EIP-712 signing")

    # 5) Audit and history
    print("\n🧩 Step 5/5 · Signing activity audit")
    try:
        acts = tk.list_activities(limit="10")
        print("✅ Recent activities:")
        for i, a in enumerate((acts.get("activities") or [])[:5], 1):
            print(f"  {i}. Type: {a.get('type','?')} | Status: {a.get('status','?')} | Time: {a.get('createdAt','?')}")
        if not acts.get("activities"):
            print("  (No activities)")
    except Exception as e:
        print(f"❌ Query activities failed: {e}")

    print("\n📊 Demo Summary")
    print("=" * 50)
    if not accounts:
        print("• No organization accounts found: fell back to TURNKEY_SIGN_WITH demo (if configured)")
    else:
        print(f"• Number of accounts traversed this time: {min(max_accounts, len(accounts))}")
        if not w3:
            print("• RPC not connected: skip transaction signing/broadcasting (configure WEB3_RPC_URL to enable)")
        else:
            print("• Completed: per-account unsignedTx building and signing (broadcast default off)")
    if enable_broadcast:
        print("• Broadcast enabled: ensure TX_VALUE_WEI>0 and account balance is sufficient")
    else:
        print("• Broadcast disabled: set MULTI_ENABLE_BROADCAST=1 to enable")
    print("\n🎉 Complete. This use case demonstrates multi-account signing and audit processes, meeting the core needs of Trading Agents.")


if __name__ == "__main__":
    main()



