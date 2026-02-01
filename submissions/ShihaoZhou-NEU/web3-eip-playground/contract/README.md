# web3-eip-playground / contract

本目录包含一个可转移的 ERC-721 合约 `GameBadgeNFT`（仅项目方可 mint，项目方承担 gas），以及对应 Foundry 测试与部署脚本。

## 功能概述

- **合约类型**：ERC-721（可转移）
- **Mint 模式**：仅 `minter` 可调用 `mintTo` 给用户地址发放 NFT
- **发放场景**：用户通关成功后，由后端触发链上 mint
- **图案随机**：从固定图库 \(N=15\) 中弱随机挑 1 个 `index(0..14)` 并固化到 `tokenToIndex[tokenId]`
- **元数据**：预上传 Pinata/IPFS，合约使用 `baseURI = ipfs://<METADATA_FOLDER_CID>/`
- **tokenURI**：`baseURI + index + ".json"`（metadata 必须命名为 `0.json` ... `14.json`）
- **多次发放**：同一用户可以获得多枚 NFT（不同游戏/多次通关）
- **防重**：链上 `claimUsed[claimId]` 双保险（后端也应做幂等）

## 目录结构

- `src/GameBadgeNFT.sol`：合约实现
- `test/GameBadgeNFT.t.sol`：Foundry 测试
- `script/Deploy.s.sol`：部署脚本（读环境变量）

## 前置条件：安装 Foundry

如果你本机还没有 Foundry（`forge` 不存在），先安装：

参考官方安装文档：`https://book.getfoundry.sh/getting-started/installation`

安装完成后确认：

```bash
forge --version
```

## 安装依赖（OpenZeppelin / forge-std）

在本目录执行：

```bash
forge install foundry-rs/forge-std --no-commit
forge install OpenZeppelin/openzeppelin-contracts --no-commit
```

本仓库已提供 `remappings.txt`，默认可直接编译。

## 运行测试

```bash
forge test -vvv
```

## 部署（forge script）

设置环境变量（可参考 `.env.example`）：

```bash
export BASE_URI="ipfs://<METADATA_FOLDER_CID>/"
export OWNER="0xYourOwnerAddress"
export MINTER="0xYourMinterAddress"
# 可选
export START_TOKEN_ID=1
```

也可以把以上变量写到 `.env`，再执行：

```bash
set -a
source .env
set +a
```

本地模拟链（anvil）部署示例：

```bash
anvil
export PRIVATE_KEY="0x..."
forge script script/Deploy.s.sol:Deploy --rpc-url http://127.0.0.1:8545 --private-key $PRIVATE_KEY --broadcast -vvv
```

## 后端如何发放（核心调用）

后端使用项目方 `minter` 热钱包直接调用：

```solidity
mintTo(userAddress, gameId, claimId)
```

- `gameId`：业务层游戏/关卡/活动标识（`uint256`）
- `claimId`：后端生成的幂等 ID（`bytes32`，必须全局唯一；建议把 `chainId`、`contract`、`user`、`gameId`、`runId` 等编码进去）

链上会发出事件：

`Minted(to, tokenId, index, gameId, claimId)`

后端可用事件索引 `tokenId/index` 写 DB，前端直接展示，无需用户再次签名或弹钱包。

## 随机性说明（重要）

合约内的 `index` 使用 `block.prevrandao / timestamp / to / tokenId / gameId / claimId` 组合做 **弱随机**，适合“15 张固定图案随机展示”这种场景；不适用于需要强公平/防操纵的抽奖。
