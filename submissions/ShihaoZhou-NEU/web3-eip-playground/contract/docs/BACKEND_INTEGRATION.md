# GameBadgeNFT 后端对接文档

## 1. 合约信息

| 项目 | 值 |
|------|-----|
| **合约地址** | `0xc444c475CB448BFc9E87EF79274426286Ec98cEC` |
| **网络** | Sepolia Testnet (Chain ID: 11155111) |
| **RPC URL** | `https://sepolia.infura.io/v3/<YOUR_KEY>` |

## 2. 核心方法

### 2.1 mintTo - 铸造 NFT

用户完成游戏后，后端调用此方法为用户铸造 NFT Badge。

```solidity
function mintTo(address to, uint256 gameId, bytes32 claimId) external onlyMinter
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `to` | address | 用户钱包地址 |
| `gameId` | uint256 | 游戏/关卡 ID（业务标识） |
| `claimId` | bytes32 | 唯一领取 ID（防重放，推荐使用 keccak256 哈希） |

**Python 示例（使用 web3.py）：**

```python
from web3 import Web3
from eth_account import Account
import hashlib

# 配置
RPC_URL = "https://sepolia.infura.io/v3/YOUR_KEY"
CONTRACT_ADDRESS = "0xc444c475CB448BFc9E87EF79274426286Ec98cEC"
MINTER_PRIVATE_KEY = "0x..."  # Minter 私钥

# 合约 ABI（仅 mintTo 方法）
ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "gameId", "type": "uint256"},
            {"name": "claimId", "type": "bytes32"}
        ],
        "name": "mintTo",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# 初始化
w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
account = Account.from_key(MINTER_PRIVATE_KEY)


def mint_badge(user_address: str, game_id: int, claim_id: str) -> str:
    """
    为用户铸造 NFT Badge

    Args:
        user_address: 用户钱包地址
        game_id: 游戏 ID
        claim_id: 唯一领取标识（如 "user123-game1-timestamp"）

    Returns:
        交易哈希
    """
    # 生成 bytes32 claimId
    claim_id_bytes = Web3.keccak(text=claim_id)

    # 构建交易
    tx = contract.functions.mintTo(
        Web3.to_checksum_address(user_address),
        game_id,
        claim_id_bytes
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 150000,
        'gasPrice': w3.eth.gas_price
    })

    # 签名并发送
    signed_tx = w3.eth.account.sign_transaction(tx, MINTER_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # 等待确认
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt['status'] == 1:
        return tx_hash.hex()
    else:
        raise Exception("Transaction failed")


# 使用示例
if __name__ == "__main__":
    user = "0x1d4F0DB612b4b376F3fC988b61cb23aeD699aB2C"
    game_id = 101
    claim_id = f"user123-game{game_id}-{int(time.time())}"

    tx_hash = mint_badge(user, game_id, claim_id)
    print(f"Minted! TX: https://sepolia.etherscan.io/tx/{tx_hash}")
```

## 3. 错误处理

合约可能抛出以下错误：

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `NotMinter()` | 调用者不是 Minter | 确保使用 Minter 私钥签名 |
| `Paused()` | 合约已暂停 | 联系 Owner 解除暂停 |
| `ZeroAddress()` | 用户地址为零地址 | 验证用户地址有效性 |
| `ClaimAlreadyUsed()` | claimId 已被使用 | 生成新的唯一 claimId |

**Python 错误处理：**

```python
from web3.exceptions import ContractLogicError

try:
    tx_hash = mint_badge(user, game_id, claim_id)
except ContractLogicError as e:
    error_msg = str(e)
    if "NotMinter" in error_msg:
        raise PermissionError("当前账户没有铸造权限")
    elif "ClaimAlreadyUsed" in error_msg:
        raise ValueError("该领取已被使用，请勿重复领取")
    elif "Paused" in error_msg:
        raise RuntimeError("合约已暂停，请稍后再试")
    else:
        raise
```

## 4. claimId 生成策略

`claimId` 用于防止重复铸造，推荐格式：

```python
import hashlib
import time

def generate_claim_id(user_id: str, game_id: int) -> str:
    """
    生成唯一的 claimId
    格式: user_{user_id}_game_{game_id}_ts_{timestamp}
    """
    raw = f"user_{user_id}_game_{game_id}_ts_{int(time.time() * 1000)}"
    return raw

# 示例
claim_id = generate_claim_id("abc123", 101)
# => "user_abc123_game_101_ts_1706500000000"
```

**重要：** 后端应在数据库中记录已使用的 claimId，在调用合约前先检查，避免浪费 Gas。

## 5. 事件监听（可选）

监听 `Minted` 事件获取铸造结果：

```python
# Minted 事件 ABI
MINTED_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "to", "type": "address"},
        {"indexed": True, "name": "tokenId", "type": "uint256"},
        {"indexed": False, "name": "index", "type": "uint8"},
        {"indexed": True, "name": "gameId", "type": "uint256"},
        {"indexed": False, "name": "claimId", "type": "bytes32"}
    ],
    "name": "Minted",
    "type": "event"
}

def parse_minted_event(receipt):
    """从交易回执解析 Minted 事件"""
    logs = contract.events.Minted().process_receipt(receipt)
    if logs:
        event = logs[0]['args']
        return {
            'to': event['to'],
            'tokenId': event['tokenId'],
            'index': event['index'],  # NFT 图片索引 1-9
            'gameId': event['gameId'],
            'claimId': event['claimId'].hex()
        }
    return None
```

## 6. 完整 ABI

```json
[
  {
    "inputs": [
      {"name": "to", "type": "address"},
      {"name": "gameId", "type": "uint256"},
      {"name": "claimId", "type": "bytes32"}
    ],
    "name": "mintTo",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [{"name": "tokenId", "type": "uint256"}],
    "name": "ownerOf",
    "outputs": [{"name": "", "type": "address"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [{"name": "tokenId", "type": "uint256"}],
    "name": "tokenURI",
    "outputs": [{"name": "", "type": "string"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [{"name": "tokenId", "type": "uint256"}],
    "name": "tokenToIndex",
    "outputs": [{"name": "", "type": "uint8"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [{"name": "claimId", "type": "bytes32"}],
    "name": "claimUsed",
    "outputs": [{"name": "", "type": "bool"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "paused",
    "outputs": [{"name": "", "type": "bool"}],
    "stateMutability": "view",
    "type": "function"
  }
]
```

## 7. 对接流程图

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Frontend  │      │   Backend   │      │  Contract   │
│ (用户完成游戏) │      │ (spoon-core)│      │(GameBadgeNFT)│
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                    │                    │
       │  POST /claim-badge │                    │
       │  {wallet, gameId}  │                    │
       │───────────────────>│                    │
       │                    │                    │
       │                    │  生成 claimId       │
       │                    │  检查是否已领取      │
       │                    │                    │
       │                    │  mintTo(wallet,    │
       │                    │    gameId, claimId)│
       │                    │───────────────────>│
       │                    │                    │
       │                    │    Minted Event    │
       │                    │<───────────────────│
       │                    │                    │
       │  {tokenId, txHash} │                    │
       │<───────────────────│                    │
       │                    │                    │
```

## 8. 环境变量

后端需要配置以下环境变量：

```bash
# .env
SEPOLIA_RPC_URL="https://sepolia.infura.io/v3/YOUR_KEY"
CONTRACT_ADDRESS="0xc444c475CB448BFc9E87EF79274426286Ec98cEC"
MINTER_PRIVATE_KEY="0x..."  # 注意保密！
```

## 9. 铸造成功后的返回数据

后端铸造成功后，应返回以下数据给前端，方便用户查看和导入 NFT：

```python
def mint_badge_with_response(user_address: str, game_id: int, claim_id: str) -> dict:
    """
    铸造 NFT 并返回完整信息
    """
    # ... 铸造逻辑 ...

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt['status'] == 1:
        # 解析 Minted 事件获取 tokenId 和 index
        event = parse_minted_event(receipt)

        return {
            "success": True,
            "data": {
                "tokenId": event['tokenId'],
                "index": event['index'],
                "txHash": tx_hash.hex(),
                # 用户查看链接
                "etherscanUrl": f"https://sepolia.etherscan.io/tx/{tx_hash.hex()}",
                "nftUrl": f"https://sepolia.etherscan.io/nft/{CONTRACT_ADDRESS}/{event['tokenId']}",
                # 用户手动导入 NFT 所需信息
                "importInfo": {
                    "contractAddress": CONTRACT_ADDRESS,
                    "tokenId": str(event['tokenId'])
                }
            }
        }
    else:
        return {"success": False, "error": "Transaction failed"}
```

**返回示例：**

```json
{
  "success": true,
  "data": {
    "tokenId": 3,
    "index": 1,
    "txHash": "0xc0eda8e20752d658604a893ecab7060acccfa6fa4785b2cd204f55c3ca49540e",
    "etherscanUrl": "https://sepolia.etherscan.io/tx/0xc0eda8e...",
    "nftUrl": "https://sepolia.etherscan.io/nft/0xc444c475CB448BFc9E87EF79274426286Ec98cEC/3",
    "importInfo": {
      "contractAddress": "0xc444c475CB448BFc9E87EF79274426286Ec98cEC",
      "tokenId": "3"
    }
  }
}
```

## 10. 用户如何查看 NFT

由于后端代替用户铸造（用户不支付 Gas），NFT **不会自动显示**在用户钱包中。

前端应提示用户通过以下方式查看 NFT：

### 方式一：在区块链浏览器查看

提供 `nftUrl` 链接，用户可直接在 Etherscan 查看 NFT 详情。

### 方式二：手动导入到钱包

前端展示导入信息，引导用户：

1. 打开 MetaMask → 收藏品/NFT 标签
2. 点击「导入 NFT」
3. 输入：
   - **合约地址**: `0xc444c475CB448BFc9E87EF79274426286Ec98cEC`
   - **Token ID**: `{tokenId}`

**前端提示示例：**

```
🎉 铸造成功！

您的 NFT Badge 已铸造完成。

📋 查看方式：
1. [在 Etherscan 查看]({nftUrl})
2. 手动导入钱包：
   - 合约地址: 0xc444c475CB448BFc9E87EF79274426286Ec98cEC
   - Token ID: {tokenId}
```

> **注意**：主网部署后，NFT 会自动显示在钱包中（因为有 OpenSea 等索引服务）。测试网（Sepolia）由于 OpenSea 已停止支持，需要手动导入。

## 11. 安全注意事项

1. **私钥保护**：Minter 私钥必须安全存储，推荐使用环境变量或密钥管理服务（如 AWS Secrets Manager）
2. **重放保护**：后端应在数据库中记录已使用的 claimId，避免重复调用合约浪费 Gas
3. **用户验证**：确保用户已完成游戏后才能领取 Badge
4. **Gas 预估**：mintTo 大约消耗 120,000 Gas，确保 Minter 账户有足够 ETH
