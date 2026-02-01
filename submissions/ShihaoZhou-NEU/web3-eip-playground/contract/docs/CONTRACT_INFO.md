# GameBadgeNFT 合约对接信息

## 合约地址

| 网络 | 地址 | Chain ID |
|------|------|----------|
| **Sepolia 测试网** | `0xc444c475CB448BFc9E87EF79274426286Ec98cEC` | 11155111 |

## RPC URL

```
https://sepolia.infura.io/v3/0d5361ef9a11422c9d1410889bdae068
```

## ABI 文件

完整 ABI: [GameBadgeNFT.abi.json](./GameBadgeNFT.abi.json)

## 核心方法

### 写入方法（需要 Minter 权限）

| 方法 | 参数 | 说明 |
|------|------|------|
| `mintTo(address to, uint256 gameId, bytes32 claimId)` | to: 用户地址, gameId: 游戏ID, claimId: 唯一领取ID | 铸造 NFT |

### 读取方法（任何人可调用）

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `ownerOf(uint256 tokenId)` | tokenId | address | 查询 NFT 所有者 |
| `balanceOf(address owner)` | owner | uint256 | 查询用户持有数量 |
| `tokenURI(uint256 tokenId)` | tokenId | string | 获取 NFT 元数据 URI |
| `tokenToIndex(uint256 tokenId)` | tokenId | uint8 | 获取 NFT 图片索引 (1-9) |
| `claimUsed(bytes32 claimId)` | claimId | bool | 检查 claimId 是否已使用 |
| `paused()` | - | bool | 检查合约是否暂停 |
| `nextTokenId()` | - | uint256 | 下一个 Token ID |

## 事件

```solidity
event Minted(
    address indexed to,
    uint256 indexed tokenId,
    uint8 index,
    uint256 indexed gameId,
    bytes32 claimId
);
```

## 前端对接示例 (ethers.js v6)

```javascript
import { ethers } from 'ethers';
import ABI from './GameBadgeNFT.abi.json';

const CONTRACT_ADDRESS = '0xc444c475CB448BFc9E87EF79274426286Ec98cEC';
const RPC_URL = 'https://sepolia.infura.io/v3/0d5361ef9a11422c9d1410889bdae068';

// 只读 Provider
const provider = new ethers.JsonRpcProvider(RPC_URL);
const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, provider);

// 查询用户持有的 NFT 数量
async function getBalance(userAddress) {
  return await contract.balanceOf(userAddress);
}

// 查询 NFT 元数据 URI
async function getTokenURI(tokenId) {
  return await contract.tokenURI(tokenId);
}

// 查询 NFT 图片索引
async function getTokenIndex(tokenId) {
  return await contract.tokenToIndex(tokenId);
}
```

## 后端对接示例 (Python web3.py)

```python
from web3 import Web3
import json

CONTRACT_ADDRESS = '0xc444c475CB448BFc9E87EF79274426286Ec98cEC'
RPC_URL = 'https://sepolia.infura.io/v3/0d5361ef9a11422c9d1410889bdae068'

w3 = Web3(Web3.HTTPProvider(RPC_URL))

with open('GameBadgeNFT.abi.json') as f:
    ABI = json.load(f)

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# 查询用户持有数量
def get_balance(user_address):
    return contract.functions.balanceOf(user_address).call()

# 铸造 NFT（需要 Minter 私钥）
def mint_to(user_address, game_id, claim_id, minter_private_key):
    account = w3.eth.account.from_key(minter_private_key)
    claim_id_bytes = Web3.keccak(text=claim_id)

    tx = contract.functions.mintTo(
        user_address,
        game_id,
        claim_id_bytes
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 150000,
        'gasPrice': w3.eth.gas_price
    })

    signed = w3.eth.account.sign_transaction(tx, minter_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return w3.eth.wait_for_transaction_receipt(tx_hash)
```

## Etherscan 链接

- 合约: https://sepolia.etherscan.io/address/0xc444c475CB448BFc9E87EF79274426286Ec98cEC
- 已验证源码: https://sepolia.etherscan.io/address/0xc444c475CB448BFc9E87EF79274426286Ec98cEC#code
