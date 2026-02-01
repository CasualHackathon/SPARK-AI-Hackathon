<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/b873b99b-02f7-4bec-82f5-ff0ea44a3df2" />


  # 0xScribe 链上判官 ⚖️

  ### "Wallet is your History. AI is the Judge."
  ### 钱包即历史，AI 即判官。

  <p align="center">
    
  </p>

  ![License](https://img.shields.io/badge/license-MIT-green)
  ![Track](https://img.shields.io/badge/Track-SpoonOS_LLM_App-blueviolet)
  ![Stack](https://img.shields.io/badge/Stack-Next.js_Python_SpoonOS-blue)
</div>


## 📖 Project Intro (项目简介)

**0xScribe** 是一个基于 **SpoonOS Graph Agent** 的「链上判官」AI 应用。

区块链是极度透明的，但**“可查”不代表“可懂”**。普通用户面对的是冰冷的哈希值和复杂的交易日志。**0xScribe** 旨在解决这一痛点：
它输入钱包地址，系统自动抓取并解释链上交互，生成极具赛博风格的**“判决书”**、**标签**与**五维能力图谱**，并为每一条结论提供**可点击的区块浏览器证据链接 (Click-to-Verify)**。

无论是 **Degen (赌狗)**、**Whale (巨鲸)**、**Hunter (撸毛党)** 还是 **Builder (工匠)**，AI 都能精准识别并给出审判。

---

## ✨ Demo Highlights 

### 1. ⚖️ 一键审判 (One-Click Judgment)
* 输入地址 → 自动输出判决书 + 五维能力图谱 (**WEALTH / HOLDING / GOVERNANCE / BUILDER / DEGEN**)。
* 视觉反馈：数值动画从 0 动态增长，配合赛博朋克 UI，沉浸感拉满。

### 2. 🔗 可验证证据 (Click-to-Verify)
* **拒绝 AI 瞎编**：Merits (功) 与 Charges (罪) 的每一条目，都附带 `🔗` 链接。
* **Etherscan v2 集成**：直接跳转到区块浏览器的真实 Transaction 页面，所见即所得。

### 3. 🛡️ 稳定演示机制 (Robust Demo)
为了保证黑客松演示期间的绝对稳定，系统内置**智能回退策略**，并通过 `risk_flags` 显式告知评委：
* **Live Mode**: 能拉到真实交易 → 用真实 Hash 生成 Proof Links。
* **Fallback Mode**: 网络超时/地址无记录 → 自动回退到 Sample Proof Links，**保证 Demo 流程不崩**。

### 4. 🎭 Web3 原生梗 (Interactive Memes)
* **V神彩蛋**: 输入 Vitalik 地址 (`0xd8da...`) 触发隐藏的神级模式。
* **赛博风格**: CRT 扫描线 + 呼吸网格背景 + 打字机音效。

---

## 🧠 System Architecture (系统架构)

本项目严格遵循 **SpoonOS Framework** 的设计范式，构建了一个基于图（Graph）的 Agent 系统。

```
graph LR
    A[Frontend: Next.js] -- "POST /api/judge" --> B(Backend: Route Handler)
    B -- "Invoke" --> C{SpoonOS Graph (Python)}
    C -- "Orchestrate" --> D[Analysis & Verdict Generation]
    B -- "Fetch Live Tx" --> E[Etherscan API v2]
    E -- "Tx Hashes" --> B
    D --> B
    B -- "JSON Response (Verdict + Proofs)" --> A
    A -- "Render UI" --> F[User Screen]



```

## 📦 Directory Structure (目录结构)
本目录是一个可独立运行的 Next.js 项目。 注意：已移除 .env.local 与 Python 虚拟环境 spoon-env/；如需运行请按下方指南配置。
```
Plaintext
submission/ZanyK4502/
├── src/
│   ├── app/page.tsx           # 主 UI（输入、按钮、判词卡、五维图谱）
│   └── app/api/judge/route.ts # 后端接口（调用 SpoonOS + Etherscan v2）
├── spoonos/
│   └── judge_graph.py         # SpoonOS Graph Agent (Python 核心逻辑)
├── ledger/
│   └── sampleA.json           # 演示用 Mock Ledger (Fallback 时的 proof 数据来源)
├── public/                    # 静态资源 (Next.js fonts, icons)
├── package.json               # 前端依赖
└── README.md                  # 项目说明

```

## 🚀 Getting Started (本地运行指南)
环境要求:

Node.js 18+ (推荐 20)

Python 3.10+ (Windows / macOS / Linux 均可)

(可选) Etherscan API Key

## Step 1: 安装前端依赖
```
Bash
npm install
# or
yarn install
# or
pnpm install
```

## Step 2: 配置环境变量 (可选，但强烈推荐)
在项目根目录新建 .env.local 文件：
```
Ini, TOML
# .env.local
ETHERSCAN_API_KEY=你的key
```
说明：不填也能跑，但 proof links 可能会走 sample fallback（为了 demo 稳定）。

## Step 3: 配置 Python 环境 (必须)
由于仓库不提交虚拟环境，你需要自己建一个。 (推荐 Windows PowerShell)：

1、创建虚拟环境:
```
PowerShell
python -m venv spoon-env
```

2、激活并安装依赖: 本项目的 Python Graph 依赖以 judge_graph.py 的 import 为准。
```
PowerShell
.\spoon-env\Scripts\python.exe -m pip install --upgrade pip
.\spoon-env\Scripts\python.exe -m pip install spoonos langchain openai
```
(如果有 requirements.txt，请运行 pip install -r requirements.txt；如果没有，请根据报错安装缺少的包即可。)

## Step 4: 启动 dev server
```
Bash
npm run dev
```

打开浏览器访问： http://localhost:3000

## 🧪 Verification (验证方式)
1. Live Proof (有 Etherscan key 且地址有 tx)

输入一个交互丰富的钱包地址 -> 点击审判。

Merits/Charges 的 🔗 点击应跳到该地址真实 tx（Etherscan）。

2. Fallback / Mock (地址无 tx 或接口返回空)

输入 tx 很少或接口查不到的地址。

系统会显示回退提示（仍可点击 sample proof links，确保 demo 可用）。

## 🧰 Troubleshooting (常见问题)
Q1: proof links 总是指向 sample？

A: 说明 live tx hash 未成功拉取。检查：

.env.local 是否存在且 ETHERSCAN_API_KEY 正确。

后端是否使用了 Etherscan v2 endpoint。

该地址是否确实存在 mainnet 交易记录。

Q2: Python Graph 报错 / 找不到依赖？

A: 你需要在 spoon-env 里安装对应依赖：先升级 pip，再按报错逐个安装缺少的包。

Q3: Windows 执行 python 路径不对？

A: 后端默认调用 spoon-env/Scripts/python.exe。确保你在项目根目录创建了名为 spoon-env 的文件夹。


## 测试钱包：
- 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045（vitalik ✅）
- 0x742d35Cc6634C0532925a3b844Bc454e4438f44e（Bitfinex wallet 常用示例）
- 0x28C6c06298d514Db089934071355E5743bf21d60（Binance 热钱包常用示例）
- 0x564286362092D8e7936f0549571a803B203aAceD（Coinbase 常用示例）


## 📚 Standard Next.js Documentation

This is a [Next.js](https://nextjs.org/) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

### Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

### Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

---

*Submitted by **ZanyK4502** for SPARK AI Hackathon 2026*
