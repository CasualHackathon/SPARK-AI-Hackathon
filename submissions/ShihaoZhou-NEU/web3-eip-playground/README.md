<p align="center">
  <img src="https://raw.githubusercontent.com/ShihaoZhou-NEU/web3-eip-playground/main/docs/assets/logo.png" alt="EIP Playground Logo" width="200" />
</p>

<h1 align="center">EIP Playground</h1>

<p align="center">
  <strong>玩游戏学以太坊，告别枯燥文档</strong>
</p>

<p align="center">
  <a href="https://eip-playground-spark.vercel.app/">在线体验</a> •
  <a href="#核心功能">核心功能</a> •
  <a href="#技术架构">技术架构</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#团队成员">团队成员</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react" alt="React" />
  <img src="https://img.shields.io/badge/Vite-7-646CFF?style=flat-square&logo=vite" alt="Vite" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Solidity-0.8.24-363636?style=flat-square&logo=solidity" alt="Solidity" />
  <img src="https://img.shields.io/badge/Foundry-latest-yellow?style=flat-square" alt="Foundry" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License" />
</p>

---

## 我们要解决什么问题？

以太坊改进提案（EIP）和 ERC 标准是以太坊生态的基石，但学习它们却困难重重：

- **技术文档晦涩难懂** — 长篇累牍的规范让新手望而却步
- **概念抽象难以理解** — Gas 机制、账户抽象、Agent 协议等概念复杂
- **学习方式太被动** — 光看文档根本建立不起直觉
- **缺乏互动资源** — 市面上几乎没有动手实践的学习工具

**结果**：陡峭的学习曲线把大量潜在开发者挡在 Web3 门外。

---

## 我们的解决方案

**EIP Playground** 通过游戏化的方式，彻底改变以太坊标准的学习体验：

| 方式 | 说明 |
|------|------|
| **游戏化学习** | 互动小游戏模拟真实的区块链机制 |
| **视觉化叙事** | 像素风漫画，把复杂概念拆解成易懂的故事 |
| **AI 智能导师** | 随时提问，获得即时、上下文相关的解答 |
| **动手实践** | 连接钱包，与真实智能合约交互 |
| **成就 NFT** | 完成学习模块，铸造链上成就徽章 |

> **核心理念**：标准应该通过实践来学习，而不是死记硬背。

---

## 核心功能

### 互动小游戏

<table>
<tr>
<td width="50%">

**EIP-1559：Gas 费机制**
- **Gas War 游戏**：体验旧版首价拍卖的混乱
- **Burner 游戏**：看看 Base Fee 是怎么被销毁的

</td>
<td width="50%">

**EIP-7702：账户抽象**
- **批量交易游戏**：把多笔交易打包成一笔
- **Gas 赞助游戏**：让别人帮你付 Gas 费
- **临时升级游戏**：EOA 变身智能合约，飞越障碍

</td>
</tr>
<tr>
<td width="50%">

**ERC-8004：Agent 协议**
- **Agent 学院**：铸造身份 → 执行任务 → 积累声誉 → 通过验证 → 领取 NFT

</td>
<td width="50%">

**更多内容即将推出...**
- ERC-20、ERC-721、EIP-4844 等！

</td>
</tr>
</table>

### AI 智能导师

一个友好的熊猫 AI 助手，它可以：
- 用通俗易懂的语言解释 EIP/ERC 概念
- 根据上下文回答你的追问
- 提供小测验检验学习效果（每个主题 3 道题）
- 实时反馈你的学习进度

### NFT 成就系统

- 完成学习模块后**铸造徽章**
- **9 种独特像素风设计**随机分配
- **链上证明**你的 Web3 知识
- **IPFS 托管元数据**确保去中心化

### 像素风漫画

每个 EIP 都配有漫画：
- 介绍该 EIP 要解决的问题
- 用图解方式解释机制原理
- 展示真实的应用场景

---

## 技术架构

### 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                          前端层                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   React 19  │  │   Vite 7    │  │   Tailwind CSS 4        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ RainbowKit  │  │   wagmi     │  │   Framer Motion         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     后端层 (SpoonOS)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   FastAPI   │  │ ReAct Agent │  │   多 LLM 支持            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   web3.py   │  │  MCP Tools  │  │   Quiz 系统             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         智能合约层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Foundry   │  │ OpenZeppelin│  │   ERC-721 (徽章)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                                                                  │
│                      部署于 Sepolia 测试网                        │
└─────────────────────────────────────────────────────────────────┘
```

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 19 | UI 框架 |
| Vite | 7 | 构建工具 & 开发服务器 |
| TypeScript | 5.6 | 类型安全 |
| Tailwind CSS | 4 | 样式系统 |
| Radix UI | latest | 无障碍组件库 |
| Framer Motion | 12 | 动画效果 |
| RainbowKit | 2.2 | 钱包连接 |
| wagmi | 3.4 | 以太坊 React Hooks |
| viem | 2.45 | 以太坊客户端 |
| TanStack Query | 5.90 | 数据请求 |

### 后端技术栈 (SpoonOS Agent 框架)

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.12+ | 运行时 |
| FastAPI | 0.115 | API 框架 |
| spoon-ai-sdk | 0.3.6 | Agent 框架 |
| web3.py | 7.11 | 区块链交互 |
| Anthropic SDK | 0.42 | Claude AI 集成 |
| OpenAI SDK | 1.70 | GPT 集成 |

**支持的 LLM 提供商**：OpenAI、Anthropic (Claude)、DeepSeek、Google Gemini、Ollama

### 智能合约技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Solidity | 0.8.24 | 合约语言 |
| Foundry | latest | 开发框架 |
| OpenZeppelin | latest | ERC-721 标准库 |
| IPFS | - | 元数据存储 |

---

## 快速开始

### 环境要求

- **Node.js** v18+（推荐 v20+）
- **Python** 3.12+
- **pnpm**（推荐）或 npm
- **Foundry**（智能合约开发用）

### 启动步骤

#### 1. 克隆仓库

```bash
git clone https://github.com/ShihaoZhou-NEU/web3-eip-playground.git
cd web3-eip-playground
```

#### 2. 启动前端

```bash
# 进入前端目录
cd apps/eip-playground

# 安装依赖
pnpm install

# 启动开发服务器
pnpm run dev
```

浏览器打开 http://localhost:3000 即可体验。

#### 3. 启动后端

```bash
# 进入后端目录
cd spoon-core

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量模板
cp .env.example .env

# 在 .env 中配置你的 API 密钥
# 必填：ANTHROPIC_API_KEY 或 OPENAI_API_KEY

# 启动服务
uvicorn spoon_ai.tutor.service:app --reload --port 8000
```

#### 4. 部署智能合约（可选）

```bash
# 进入合约目录
cd contract

# 安装 Foundry 依赖
forge install

# 复制环境变量模板
cp .env.example .env

# 运行测试
forge test

# 部署到 Sepolia（需要有余额的钱包）
forge script script/Deploy.s.sol --rpc-url $SEPOLIA_RPC_URL --broadcast
```

### 环境变量配置

<details>
<summary>前端 (.env)</summary>

```env
VITE_API_URL=http://localhost:8000
VITE_WALLET_CONNECT_PROJECT_ID=your_project_id
```

</details>

<details>
<summary>后端 (.env)</summary>

```env
# LLM API 密钥（至少配置一个）
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# 区块链配置
SEPOLIA_RPC_URL=https://...
MINTER_PRIVATE_KEY=0x...
CONTRACT_ADDRESS=0x...
```

</details>

---

## 在线演示

**线上地址**：https://eip-playground-spark.vercel.app/

---

## 部署信息

| 网络 | 合约 | 地址 |
|------|------|------|
| Sepolia | GameBadgeNFT | [`0xc444c475CB448BFc9E87EF79274426286Ec98cEC`](https://sepolia.etherscan.io/address/0xc444c475CB448BFc9E87EF79274426286Ec98cEC) |

**NFT 元数据**：[IPFS Gateway](https://ipfs.io/ipfs/bafybeiadgwost5sefktvwsohhjtybut4n7ni3xeta2bwvifuxuumqtx3t4/)

---

## 项目结构

```
eip-playground/
├── apps/
│   └── eip-playground/           # 前端应用
│       ├── client/
│       │   └── src/
│       │       ├── components/   # React 组件
│       │       │   ├── games/    # 互动游戏
│       │       │   │   ├── eip1559/
│       │       │   │   ├── eip7702/
│       │       │   │   └── erc8004/
│       │       │   ├── AITutor.tsx
│       │       │   ├── ComicReader.tsx
│       │       │   └── ...
│       │       ├── pages/        # 页面组件
│       │       ├── data/         # EIP 内容数据
│       │       └── lib/          # 工具函数 & 配置
│       └── server/               # Express 服务器
│
├── spoon-core/                   # 后端 AI 框架
│   └── spoon_ai/
│       ├── agents/               # ReAct Agent 系统
│       ├── tutor/                # AI 导师服务
│       ├── llm/                  # 多 LLM 提供商
│       └── tools/                # Agent 工具
│
├── contract/                     # 智能合约
│   ├── src/
│   │   └── GameBadgeNFT.sol      # 成就 NFT
│   ├── test/                     # Forge 测试
│   └── script/                   # 部署脚本
│
└── docs/                         # 文档
    └── ARCHITECTURE.md
```

---

## 发展路线

### 第一阶段：基础功能（当前）
- [x] EIP-1559 学习模块 + 游戏
- [x] EIP-7702 学习模块 + 游戏
- [x] ERC-8004 介绍
- [x] AI 导师集成
- [x] NFT 成就系统
- [x] 钱包连接（RainbowKit）

### 第二阶段：内容扩展
- [ ] ERC-20 代币标准模块
- [ ] ERC-721 NFT 标准模块
- [ ] EIP-4844（Proto-Danksharding）模块
- [ ] 排行榜系统
- [ ] 社交分享功能

### 第三阶段：社区驱动
- [ ] 用户贡献内容
- [ ] 多语言支持
- [ ] 移动端适配
- [ ] DAO 治理内容筛选

---

## 团队成员

<table>
<tr>
<td align="center" width="33%">
<strong>Swen</strong><br/>
AI 导师 & 后端<br/>
<em>SpoonOS Agent 框架</em>
</td>
<td align="center" width="33%">
<strong>David</strong><br/>
前端 & 用户体验<br/>
<em>游戏 & 教育设计</em>
</td>
<td align="center" width="33%">
<strong>Dudu</strong><br/>
智能合约 & Web3<br/>
<em>NFT 系统 & 链上集成</em>
</td>
</tr>
</table>

---

## 致谢

- **ETHPanda** — 社区支持与灵感
- **LXDAO** — 技术指导与资源
- **OpenZeppelin** — 安全的智能合约库
- **以太坊基金会** — 创造了我们正在教授的标准

---

## 开源协议

本项目基于 [MIT License](LICENSE) 开源。

---

<p align="center">
  <strong>ETHPanda x LXDAO 黑客松作品</strong>
</p>


