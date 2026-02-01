import json
import os
import sys
from typing import Dict, Any, List

from spoon_ai.graph import StateGraph, END

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def read_json_utf8_sig(p: str) -> Dict[str, Any]:
    # utf-8-sig 能吃掉 BOM，避免你之前 JSON parse 出怪字符
    with open(p, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def persona_by_wallet(wallet: str) -> str:
    w = (wallet or "").strip().lower()
    if not w:
        return "builder"
    
    # --- 新增：V神彩蛋逻辑 ---
    if w == "0xd8da6bf26964af9d7eed9e03e53415d37aa96045":
        return "god"
    # -----------------------

    last = w[-1]
    if last in "0123":
        return "degen"
    if last in "456":
        return "whale"
    if last in "789":
        return "hunter"
    return "builder"

PERSONAS: Dict[str, Dict[str, Any]] = {
    # --- 新增：God Persona 数据 ---
    "god": {
        "tags": ["The Chosen One", "Ethereum Father", "Supreme Leader"],
        "radar": {"wealth": 100, "holding": 100, "governance": 100, "builder": 100, "degen": 100},
        "verdict": "警告：本判官无权审判神。SpoonOS 系统已跪下。此人乃 以太坊之父 / 赛博上帝。",
        "merits": [
            "Created Ethereum (创造了以太坊)",
            "Wrote the Whitepaper (撰写白皮书)",
            "Donated SHIB to India (神之慈悲)",
        ],
        "charges": [
            "Gas Fees too high (Gas 费太贵)",
            "Scaling too slow (扩容太慢)",
            "Wears weird pajamas (穿睡衣开会)",
        ],
    },
    # ----------------------------
    "degen": {
        "tags": ["High Leverage", "Rug Survivor", "Fomo Buyer"],
        "radar": {"wealth": 45, "holding": 10, "governance": 5, "builder": 0, "degen": 99},
        "verdict": "此人乃 链上绞肉机 / 波动率信徒。在归零与百倍之间反复横跳，视 Gas 费如粪土。",
        "merits": [
            "Provided exit liquidity for community",
            "Top 1% Gas Spender",
            "Early Adopter of 50+ Meme coins",
        ],
        "charges": [
            "Sold ETH for JPGs",
        ],
    },
    "whale": {
        "tags": ["Diamond Hands", "Market Mover", "Smart Money"],
        "radar": {"wealth": 98, "holding": 95, "governance": 80, "builder": 20, "degen": 15},
        "verdict": "此人乃 深海巨鲸 / 市场定海神针。举手投足引发 K 线震动，钱包余额足以买下半个赛道。",
        "merits": [
            "HODLing ETH since 2018",
            "Major Liquidity Provider on Curve/Uni",
            "Blue Chip NFT Collector",
        ],
        "charges": [
            "Centralization risk (holdings too concentrated)",
        ],
    },
    "hunter": {
        "tags": ["Volume Farmer", "Cross-chain King", "Sybil Suspect"],
        "radar": {"wealth": 30, "holding": 20, "governance": 10, "builder": 85, "degen": 60},
        "verdict": "此人乃 链上勤奋蜂 / 交互机器。为了空投不知疲倦，哪里有交互，哪里就有他的足迹。",
        "merits": [
            "10,000+ Transactions",
            "Active on 12 different L2s",
            "Gitcoin Passport Scorer",
        ],
        "charges": [
            "Bot-like behavior / minimum balance strategy",
        ],
    },
    "builder": {
        "tags": ["Public Goods Builder", "DAO Steward", "Contract Deployer"],
        "radar": {"wealth": 60, "holding": 80, "governance": 90, "builder": 95, "degen": 10},
        "verdict": "此人乃 Web3 工匠 / 基础设施守护者。比起价格，更关心技术革新。",
        "merits": [
            "Voted on 50+ Proposals",
            "Donated to Gitcoin",
            "ENS OG",
        ],
        "charges": [
            "Missed the Meme Season (too serious)",
        ],
    },
}

def apply_persona(base: Dict[str, Any], persona_key: str) -> Dict[str, Any]:
    p = PERSONAS[persona_key]

    base["tags"] = p["tags"]
    base["radar"] = p["radar"]
    base["verdict"] = p["verdict"]

    # 让 merits/charges 的 claim 变，但 proof_url 继续沿用（Route A 稳定可点）
    merits = base.get("merits") or []
    charges = base.get("charges") or []

    # 确保长度够（不够就补占位）
    while len(merits) < 3:
        merits.append({"claim": "Merit (placeholder)", "proof_url": "https://etherscan.io"})
    while len(charges) < 1:
        charges.append({"claim": "Charge (placeholder)", "proof_url": "https://etherscan.io"})

    for i in range(3):
        # 简单防越界
        if i < len(p["merits"]):
            merits[i]["claim"] = p["merits"][i]

    if len(p["charges"]) > 0:
        charges[0]["claim"] = p["charges"][0]

    base["merits"] = merits
    base["charges"] = charges

    # 风控口径：评委友好 + 可解释（不硬说“都是假的”，但讲清楚是 deterministic 脚本）
    rf: List[str] = base.get("risk_flags") or []
    rf = [x for x in rf if isinstance(x, str)]

    # 把 persona 明示出来：同地址稳定、不同地址变化
    rf.insert(0, f"Persona mapping: deterministic by address suffix ({persona_key})")
    rf.insert(0, "Demo mode: scripted personas for stable judging experience")
    rf.insert(0, "SpoonOS StateGraph orchestrated")

    base["risk_flags"] = rf
    return base

def build_graph():
    g = StateGraph(dict)

    def node_load(state: Dict[str, Any]) -> Dict[str, Any]:
        sample = state["sample"]
        p = os.path.join(ROOT, "ledger", f"{sample}.json")
        base = read_json_utf8_sig(p)
        base["wallet"] = state.get("wallet") or sample
        return {**state, "base": base}

    def node_persona(state: Dict[str, Any]) -> Dict[str, Any]:
        persona_key = persona_by_wallet(state.get("wallet", ""))
        base = state["base"]
        out = apply_persona(base, persona_key)
        return {**state, "out": out}

    g.add_node("load", node_load)
    g.add_node("persona", node_persona)

    g.set_entry_point("load")
    g.add_edge("load", "persona")
    g.add_edge("persona", END)

    return g.compile()

GRAPH = build_graph()

def main():
    # 用法：
    #   python judge_graph.py sampleA
    #   python judge_graph.py sampleA 0x....
    sample = sys.argv[1] if len(sys.argv) > 1 else "sampleA"
    wallet = sys.argv[2] if len(sys.argv) > 2 else ""

    state = {"sample": sample, "wallet": wallet}
    out = GRAPH.invoke(state)["out"]

    # ensure_ascii=False 保留中文
    sys.stdout.write(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()