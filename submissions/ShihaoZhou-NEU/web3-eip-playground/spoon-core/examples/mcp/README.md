# Turnkey Examples

Sample workflows for the Turnkey SDK in three scripts:
- `turnkey_trading_use_case.py`: guided demo for single-identity signing (txn, message, EIP-712) plus optional broadcast and activity audit.
- `multi_account_use_case.py`: enumerates wallets/accounts, builds unsigned EIP-1559 tx per account, signs, optionally broadcasts, signs messages and typed data, and lists audit history.
- `build_unsigned_eip1559_tx.py`: helper to build an unsigned EIP-1559 transaction hex that can be fed into the other scripts.

## Prerequisites
- Python 3.10+ (recommended inside a virtual environment).
- Install repo dependencies from the project root: `pip install -e .` or `pip install -r requirements.txt`.
- Extra deps if missing: `pip install web3 rlp eth-utils`.
- Turnkey credentials in a `.env` file (copy `env.example`): `TURNKEY_API_PUBLIC_KEY`, `TURNKEY_API_PRIVATE_KEY`, `TURNKEY_ORG_ID`, `TURNKEY_SIGN_WITH`.
- Optional for broadcasting: `WEB3_RPC_URL` pointed to your network RPC (Sepolia/Goerli/Mainnet, etc.).

## Setup
```bash
cp examples/turnkey/env.example .env
# Fill in TURNKEY_* values and optional TX_* params
```

## Running the demos
### 1) Build an unsigned EIP-1559 tx
```bash
python -m examples.turnkey.build_unsigned_eip1559_tx
```
Reads `WEB3_RPC_URL`, `TURNKEY_SIGN_WITH`, and TX_* vars to estimate gas and emit `TURNKEY_UNSIGNED_TX_HEX`. Copy that hex into your `.env` when using the trading demo.

### 2) Single-identity signing & audit
```bash
python -m examples.turnkey.turnkey_trading_use_case
```
Requires `TURNKEY_SIGN_WITH` and optionally `TURNKEY_UNSIGNED_TX_HEX` to sign an EIP-1559 payload. With `WEB3_RPC_URL` set, it will attempt to broadcast the signed tx. Always signs a message and EIP-712 sample, then fetches recent activities for audit.

### 3) Multi-account workflow
```bash
python -m examples.turnkey.multi_account_use_case
```
Discovers organization wallets/accounts, builds unsigned tx per account (no prebuilt hex needed), signs them, and optionally broadcasts when `MULTI_ENABLE_BROADCAST=1` and `TX_VALUE_WEI>0`. Also signs per-account messages and an EIP-712 sample, then lists activities. Limit traversal with `MULTI_MAX_ACCOUNTS` (default 3).

