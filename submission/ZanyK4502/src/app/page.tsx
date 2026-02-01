"use client";

import { useEffect, useRef, useState } from "react";

// --- 类型定义 ---
type VerdictOutput = {
  case_title: string;
  wallet: string;
  verdict: string;
  tags: string[];
  radar: { wealth: number; holding: number; governance: number; builder: number; degen: number };
  merits: { claim: string; proof_url: string }[];
  charges: { claim: string; proof_url: string }[];
  risk_flags: string[];
};

type PersonaText = {
  verdict: string;
  radar: { wealth: number; holding: number; governance: number; builder: number; degen: number };
  tags: string[];
  merits: string[];
  charges: string[];
};

// --- 常量定义 ---

const PERSONA_GOD: PersonaText = {
  verdict: "警告：本判官无权审判神。SpoonOS 系统已跪下。此人乃 以太坊之父 / 赛博上帝。",
  radar: { wealth: 100, holding: 100, governance: 100, builder: 100, degen: 100 },
  tags: ["The Chosen One", "Ethereum Father", "Supreme Leader"],
  merits: [
    "Created Ethereum (创造了以太坊)",
    "Wrote the Whitepaper (撰写白皮书)",
    "Donated SHIB to India (神之慈悲)",
  ],
  charges: [
    "Gas Fees too high (Gas 费太贵)",
    "Scaling too slow (扩容太慢)",
    "Wears weird pajamas (穿睡衣开会)",
  ],
};

const PERSONA_BUILDER: PersonaText = {
  verdict: "此人乃 Web3 工匠 / 基础设施守护者。代码即法律的践行者，比起价格，更关心技术革新。",
  radar: { wealth: 60, holding: 80, governance: 90, builder: 95, degen: 10 },
  tags: ["Public Goods Builder", "DAO Steward", "Contract Deployer"],
  merits: ["Voted on 50+ Proposals (治理活跃)", "Donated to Gitcoin (捐赠者)", "ENS OG (早期 ENS 拥有者)"],
  charges: [
    "Missed the Meme Season (错过了土狗季)",
    "Over-diversification (持仓过于分散)",
    "Gas Inefficiency (不计成本部署合约)",
  ],
};

const PERSONA_WHALE: PersonaText = {
  verdict: "此人乃 深海巨兽 / 市场定海神针。举手投足引发 K 线震动，钱包余额足以买下半个赛道。",
  radar: { wealth: 98, holding: 95, governance: 80, builder: 20, degen: 15 },
  tags: ["Diamond Hands", "Market Mover", "Smart Money"],
  merits: [
    "HODLing ETH since 2018 (穿越牛熊)",
    "Major Liquidity Provider on Curve/Uni (DeFi 基石)",
    "Blue Chip NFT Collector (蓝筹收藏家)",
  ],
  charges: [
    "Market Manipulation (潜在的市场操纵嫌疑)",
    "Centralization Risk (持仓过于集中)",
    "Too Big To Fail (大而不能倒)",
  ],
};

const PERSONA_HUNTER: PersonaText = {
  verdict: "此人乃 链上勤奋蜂 / 交互机器。为了空投不知疲倦，哪里有交互，哪里就有他的足迹。",
  radar: { wealth: 30, holding: 20, governance: 10, builder: 85, degen: 60 },
  tags: ["Volume Farmer", "Cross-chain King", "Sybil Suspect"],
  merits: [
    "10,000+ Transactions (万次交互成就)",
    "Active on 12 different L2s (L2 活跃用户)",
    "Gitcoin Passport Scorer (护照高分)",
  ],
  charges: [
    "Minimum Balance Strategy (每个号只留 0.001 ETH)",
    "Bot-like Behavior (行为像机器人)",
    "Dumping Airdrops (拿到空投立马砸盘)",
  ],
};

const PERSONA_DEGEN: PersonaText = {
  verdict: "此人乃 链上绞肉机 / 波动率信徒。在归零与百倍之间反复横跳，视 Gas 费如粪土。",
  radar: { wealth: 45, holding: 10, governance: 5, builder: 0, degen: 99 },
  tags: ["High Leverage", "Rug Survivor", "Fomo Buyer"],
  merits: [
    "Provided exit liquidity for community (为社区提供了退出流动性)",
    "Top 1% Gas Spender (尊贵的 Gas 贡献者)",
    "Early Adopter of 50+ Meme coins (Meme 先锋)",
  ],
  charges: ["Sold ETH for JPGs (卖币买图，血亏)", "High failure rate txs (交易失败率极高，操作急躁)", "Chasing pumps (追涨杀跌)"],
};

const SPECIAL_BY_ADDRESS: Record<string, PersonaText> = {
  "0xd8da6bf26964af9d7eed9e03e53415d37aa96045": PERSONA_GOD,
  "0x28c6c06298d514db089934071355e5743bf21d60": PERSONA_HUNTER,
  "0x564286362092d8e7936f0549571a803b203aaced": PERSONA_DEGEN,
  "0x742d35cc6634c0532925a3b844bc454e4438f44e": PERSONA_WHALE,
};

// --- 工具函数 ---
function normalizeAddr(a: string) {
  return (a || "").trim().toLowerCase();
}

function pickPersonaByAddress(a: string): PersonaText {
  const key = normalizeAddr(a);
  return SPECIAL_BY_ADDRESS[key] ?? PERSONA_BUILDER;
}

function applyPersonaText(out: any, p: PersonaText) {
  out.verdict = p.verdict;
  out.tags = p.tags;
  out.radar = p.radar;

  if (Array.isArray(out.merits)) {
    out.merits = out.merits.map((m: any, i: number) => ({
      ...m,
      claim: p.merits[i] ?? m?.claim ?? "",
    }));
  }

  if (Array.isArray(out.charges)) {
    out.charges = out.charges.map((c: any, i: number) => ({
      ...c,
      claim: p.charges[i] ?? c?.claim ?? "",
    }));
  }
}

// 2. 打字机特效组件 (AI Feel)
const TypewriterVerdict = ({ text }: { text: string }) => {
  const [displayed, setDisplayed] = useState("");
  const [isDone, setIsDone] = useState(false);

  useEffect(() => {
    setDisplayed("");
    setIsDone(false);
    let i = 0;
    const timer = setInterval(() => {
      if (i < text.length) {
        setDisplayed((prev) => prev + text.charAt(i));
        i++;
      } else {
        setIsDone(true);
        clearInterval(timer);
      }
    }, 30); // 打字速度
    return () => clearInterval(timer);
  }, [text]);

  // 高亮逻辑复用，但这次是基于动态生成的文本
  const parts = displayed.split("。");
  const headline = parts[0];
  const rest = parts.slice(1).join("。");
  const cleanHeadline = headline.replace("此人乃", "").trim();

  return (
    <div className="leading-snug min-h-[80px]"> {/* 预留高度防止抖动 */}
      <span className="text-green-200/80 mr-2">此人乃</span>
      <span className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-green-300 to-emerald-500">
        {cleanHeadline}
      </span>
      {/* 光标闪烁 */}
      {!isDone && <span className="inline-block w-2 h-6 bg-green-500 ml-1 animate-pulse align-middle"></span>}
      
      {displayed.includes("。") && (
         <>
           <span className="text-green-100 font-bold">。</span>
           <div className="mt-2 text-lg text-green-100/80 font-normal animate-[fadeIn_0.5s_ease-out]">{rest && rest + (isDone ? "。" : "")}</div>
         </>
      )}
    </div>
  );
};

const ZERO_RADAR = { wealth: 0, holding: 0, governance: 0, builder: 0, degen: 0 };

// --- 主组件 ---
export default function Page() {
  const [loading, setLoading] = useState(false);
  const [out, setOut] = useState<VerdictOutput | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [walletInput, setWalletInput] = useState("");
  const [error, setError] = useState("");

  const [radarAnim, setRadarAnim] = useState<VerdictOutput["radar"]>(ZERO_RADAR);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (!out) {
      setRadarAnim(ZERO_RADAR);
      return;
    }

    const target = out.radar ?? ZERO_RADAR;
    const from = ZERO_RADAR;

    if (rafRef.current) cancelAnimationFrame(rafRef.current);

    const start = performance.now();
    const duration = 700;

    setRadarAnim(from);

    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const ease = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
      const lerp = (a: number, b: number) => Math.round(a + (b - a) * ease);

      setRadarAnim({
        wealth: lerp(from.wealth, target.wealth),
        holding: lerp(from.holding, target.holding),
        governance: lerp(from.governance, target.governance),
        builder: lerp(from.builder, target.builder),
        degen: lerp(from.degen, target.degen),
      });

      if (t < 1) rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [out]);

  async function judge(sampleKey: string) {
    // 验证输入：标准以太坊地址（42位，0x开头）
    const trimmedInput = walletInput.trim();
    if (trimmedInput.length !== 42 || !trimmedInput.startsWith("0x")) {
      setError("请输入正确的钱包地址");
      return;
    }

    setError("");
    setOut(null);
    setLoading(true);
    setLog([]);

    const push = (s: string) => setLog((x) => [...x, s]);

    push("[SpoonOS] Graph Agent initialized");
    await new Promise((r) => setTimeout(r, 400));
    push("[SpoonOS] Evidence loaded (mock ledger)");
    await new Promise((r) => setTimeout(r, 500));
    push("[SpoonOS] Classification complete");
    await new Promise((r) => setTimeout(r, 500));
    push("[SpoonOS] Verdict generating…");
    await new Promise((r) => setTimeout(r, 900));

    const mockData: any = {
      case_title: "The People v. SampleA",
      wallet: trimmedInput,
      verdict: "", 
      tags: [],
      radar: { wealth: 0, holding: 0, governance: 0, builder: 0, degen: 0 },
      merits: [{ claim: "", proof_url: "#" }, { claim: "", proof_url: "#" }, { claim: "", proof_url: "#" }],
      charges: [{ claim: "", proof_url: "#" }, { claim: "", proof_url: "#" }, { claim: "", proof_url: "#" }],
      risk_flags: sampleKey === "sampleA" ? ["no live tx", "fallback"] : ["live proof"] 
    };
    
    const res = await fetch(
      `/api/judge?sample=${encodeURIComponent(sampleKey)}&wallet=${encodeURIComponent(trimmedInput)}`
    );
    const data = (await res.json()) as any;

    const persona = pickPersonaByAddress(trimmedInput);
    applyPersonaText(data, persona);

    push("[SpoonOS] Proof links attached");
    setOut(data as VerdictOutput);
    setLoading(false);
  }

  function handleBribe() {
    alert("💸 贿赂通道拥堵中...\n\n本判官刚正不阿！(请直接向 0xScribe 项目方转账 10 ETH 以加速处理 Just Kidding)");
  }

  // 3. 分享功能 (Web3 Social) - 手动绘制图片
  function handleShare() {
    if (!out) {
      alert("未找到判决结果，请先进行判决");
      return;
    }

    try {
      // 创建 Canvas
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        alert("图片生成失败");
        return;
      }

      // 设置尺寸
      const width = 800;
      const height = 600;
      canvas.width = width;
      canvas.height = height;

      // MBTI 人格映射
      function getMBTI(): string {
        const { wealth, holding, governance, builder, degen } = out.radar;

        // God: 全满分
        if (wealth === 100 && holding === 100 && governance === 100) {
          return "INTJ-A"; // 建筑师（完美主义）
        }
        // Degen: 高 degen，低其他
        if (degen >= 90) {
          return "ESFP-A"; // 表演者（活在当下）
        }
        // Whale: 高 wealth/holding，低 builder
        if (wealth >= 90 && holding >= 90 && builder <= 30) {
          return "ISTJ-A"; // 物流师（稳重保守）
        }
        // Hunter: 高 builder，低 wealth
        if (builder >= 80 && wealth <= 40) {
          return "ESTJ-A"; // 总经理（高效执行）
        }
        // Builder: 高 governance/builder
        if (governance >= 85 && builder >= 90) {
          return "INTP-A"; // 逻辑学家（善于构建）
        }
        // 默认
        return "INFJ-A"; // 提倡者（理想主义）
      }

      const mbti = getMBTI();
      const mbtiDesc: Record<string, string> = {
        "INTJ-A": "建筑师 · 完美主义",
        "ESFP-A": "表演者 · 活在当下",
        "ISTJ-A": "物流师 · 稳重保守",
        "ESTJ-A": "总经理 · 高效执行",
        "INTP-A": "逻辑学家 · 善于构建",
        "INFJ-A": "提倡者 · 理想主义",
      };

      // MBTI 类型对应的视觉主题
      const mbtiThemes: Record<string, {
        primary: string;
        secondary: string;
        accent: string;
        symbol: string;
        pattern: string;
      }> = {
        "INTJ-A": {
          primary: "#4a3b6b",    // 深紫
          secondary: "#6b5b8a",  // 紫蓝
          accent: "#9d7cb5",     // 淡紫
          symbol: "🏗️",          // 建筑师
          pattern: "geometric"
        },
        "ESFP-A": {
          primary: "#e85d75",    // 珊瑚红
          secondary: "#f5a962",  // 橙色
          accent: "#f8d875",      // 金黄
          symbol: "🎭",          // 表演者
          pattern: "dynamic"
        },
        "ISTJ-A": {
          primary: "#5c5c3d",    // 橄榄绿
          secondary: "#7a7a5e",  // 灰绿
          accent: "#9e9e7a",     // 浅绿
          symbol: "🏛️",          // 物流师
          pattern: "structured"
        },
        "ESTJ-A": {
          primary: "#c8553d",    // 砖红
          secondary: "#d4766c",  // 珊瑚色
          accent: "#e8a898",     // 淡红
          symbol: "⚡",          // 总经理
          pattern: "bold"
        },
        "INTP-A": {
          primary: "#4a6b8a",    // 蓝绿
          secondary: "#6b8a9d",  // 淡蓝
          accent: "#8aabbe",     // 浅蓝绿
          symbol: "🔮",          // 逻辑学家
          pattern: "abstract"
        },
        "INFJ-A": {
          primary: "#8a5b7a",    // 紫红
          secondary: "#a87b9d",  // 淡紫粉
          accent: "#c4a4b8",     // 浅紫粉
          symbol: "✨",          // 提倡者
          pattern: "ethereal"
        }
      };

      // ==================== MBTI 主题背景 ====================
      const theme = mbtiThemes[mbti] || mbtiThemes["INFJ-A"];

      // 基础渐变背景（使用主题色）
      const bgGradient = ctx.createLinearGradient(0, 0, width, height);
      bgGradient.addColorStop(0, theme.primary + "15");    // 非常淡的主题色
      bgGradient.addColorStop(0.5, theme.secondary + "10");
      bgGradient.addColorStop(1, theme.accent + "05");
      ctx.fillStyle = bgGradient;
      ctx.fillRect(0, 0, width, height);

      // 绘制主题图案
      ctx.save();
      ctx.fillStyle = theme.primary + "12";
      ctx.strokeStyle = theme.secondary + "15";

      switch (theme.pattern) {
        case "geometric":  // INTJ - 建筑师风格：几何图形
          for (let i = 0; i < 8; i++) {
            const angle = (i * 45) * (Math.PI / 180);
            const x = width / 2 + Math.cos(angle) * 200;
            const y = height / 2 + Math.sin(angle) * 150;
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(x + 40, y + 40);
            ctx.lineTo(x - 30, y + 50);
            ctx.closePath();
            ctx.stroke();
          }
          // 中央几何图形
          ctx.beginPath();
          ctx.moveTo(width / 2, height / 2 - 80);
          ctx.lineTo(width / 2 + 60, height / 2 + 40);
          ctx.lineTo(width / 2 - 60, height / 2 + 40);
          ctx.closePath();
          ctx.fill();
          break;

        case "dynamic":  // ESFP - 表演者风格：动态波浪
          for (let i = 0; i < 5; i++) {
            ctx.beginPath();
            ctx.moveTo(0, height * 0.3 + i * 40);
            for (let x = 0; x <= width; x += 20) {
              const y = height * 0.3 + i * 40 + Math.sin(x * 0.02 + i) * 30;
              ctx.lineTo(x, y);
            }
            ctx.stroke();
          }
          // 动态圆圈
          for (let i = 0; i < 12; i++) {
            const angle = (i * 30) * (Math.PI / 180);
            const r = 80 + i * 15;
            ctx.beginPath();
            ctx.arc(width / 2, height / 2, r, angle, angle + 0.3);
            ctx.stroke();
          }
          break;

        case "structured":  // ISTJ - 物流师风格：网格结构
          ctx.lineWidth = 1;
          for (let x = 50; x < width; x += 60) {
            ctx.beginPath();
            ctx.moveTo(x, 50);
            ctx.lineTo(x, height - 100);
            ctx.stroke();
          }
          for (let y = 50; y < height - 100; y += 60) {
            ctx.beginPath();
            ctx.moveTo(50, y);
            ctx.lineTo(width - 50, y);
            ctx.stroke();
          }
          // 中央矩形
          ctx.fillRect(width / 2 - 70, height / 2 - 50, 140, 100);
          break;

        case "bold":  // ESTJ - 总经理风格：大胆形状
          ctx.lineWidth = 3;
          for (let i = 0; i < 6; i++) {
            ctx.beginPath();
            const size = 40 + i * 25;
            ctx.strokeRect(width / 2 - size, height / 2 - size * 0.7, size * 2, size * 1.4);
          }
          // 三角形装饰
          ctx.beginPath();
          ctx.moveTo(width / 2, height / 2 - 90);
          ctx.lineTo(width / 2 + 80, height / 2 + 50);
          ctx.lineTo(width / 2 - 80, height / 2 + 50);
          ctx.closePath();
          ctx.fillStyle = theme.primary + "20";
          ctx.fill();
          break;

        case "abstract":  // INTP - 逻辑学家风格：抽象曲线
          for (let i = 0; i < 15; i++) {
            ctx.beginPath();
            ctx.ellipse(
              width / 2 + Math.cos(i * 0.8) * 150,
              height / 2 + Math.sin(i * 0.6) * 100,
              60 + i * 8,
              40 + i * 5,
              i * 0.3,
              0,
              Math.PI * 2
            );
            ctx.stroke();
          }
          // 抽象节点
          for (let i = 0; i < 8; i++) {
            const angle = (i * 45) * (Math.PI / 180);
            ctx.beginPath();
            ctx.arc(width / 2 + Math.cos(angle) * 120, height / 2 + Math.sin(angle) * 80, 8, 0, Math.PI * 2);
            ctx.fill();
          }
          break;

        case "ethereal":  // INFJ - 提倡者风格：空灵流动
          // 柔和流动的曲线
          for (let i = 0; i < 20; i++) {
            ctx.beginPath();
            const startY = 80 + i * 25;
            ctx.moveTo(40, startY);
            for (let x = 40; x < width - 40; x += 30) {
              const y = startY + Math.sin(x * 0.01 + i * 0.5) * 20 + Math.cos(x * 0.008) * 15;
              ctx.lineTo(x, y);
            }
            ctx.strokeStyle = theme.secondary + (10 + i * 2).toString(16);
            ctx.stroke();
          }
          // 空灵光晕
          const glowGradient = ctx.createRadialGradient(width / 2, height / 2, 0, width / 2, height / 2, 250);
          glowGradient.addColorStop(0, theme.primary + "25");
          glowGradient.addColorStop(0.5, theme.secondary + "10");
          glowGradient.addColorStop(1, "transparent");
          ctx.fillStyle = glowGradient;
          ctx.fillRect(0, 0, width, height);
          // 心形装饰
          ctx.beginPath();
          ctx.moveTo(width / 2, height / 2 - 40);
          ctx.bezierCurveTo(width / 2 + 50, height / 2 - 70, width / 2 + 80, height / 2 - 20, width / 2, height / 2 + 40);
          ctx.bezierCurveTo(width / 2 - 80, height / 2 - 20, width / 2 - 50, height / 2 - 70, width / 2, height / 2 - 40);
          ctx.fillStyle = theme.primary + "18";
          ctx.fill();
          break;
      }
      ctx.restore();

      // 绘制主题色晕染效果
      ctx.save();
      const fogGradient = ctx.createRadialGradient(width * 0.5, height * 0.5, 0, width * 0.5, height * 0.5, 350);
      fogGradient.addColorStop(0, theme.primary + "08");
      fogGradient.addColorStop(1, "transparent");
      ctx.fillStyle = fogGradient;
      ctx.fillRect(0, 0, width, height);
      ctx.restore();

      // ==================== 装饰边框 ====================
      ctx.strokeStyle = theme.primary + "50";
      ctx.lineWidth = 4;
      ctx.strokeRect(15, 15, width - 30, height - 30);

      // 内边框（细线）
      ctx.strokeStyle = theme.secondary + "30";
      ctx.lineWidth = 1;
      ctx.strokeRect(20, 20, width - 40, height - 40);

      // 绘制四角装饰
      const cornerSize = 35;
      ctx.strokeStyle = theme.primary + "60";
      ctx.lineWidth = 2;

      [[20, 20, 1, 1], [width - 20, 20, -1, 1], [20, height - 20, 1, -1], [width - 20, height - 20, -1, -1]].forEach(([x, y, dx, dy]) => {
        ctx.beginPath();
        ctx.moveTo(x, y + cornerSize * dy);
        ctx.lineTo(x, y);
        ctx.lineTo(x + cornerSize * dx, y);
        ctx.stroke();
      });

      // ==================== MBTI 符号背景 ====================
      ctx.save();
      ctx.font = "120px serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = theme.primary + "10";
      ctx.fillText(theme.symbol, width / 2, height / 2);
      ctx.restore();

      // ==================== 标题区域 ====================
      ctx.save();
      ctx.font = "bold 36px 'Courier New', monospace";
      ctx.textAlign = "center";
      ctx.fillStyle = theme.primary;
      ctx.fillText("判 词", width / 2, 55);

      ctx.font = "18px 'Courier New', monospace";
      ctx.fillStyle = theme.secondary + "b0";
      ctx.fillText("0xScribe · 钱包即历史", width / 2, 80);
      ctx.restore();

      // 分隔线
      ctx.save();
      ctx.strokeStyle = theme.primary + "40";
      ctx.lineWidth = 2;
      ctx.setLineDash([12, 6, 4, 2]);
      ctx.beginPath();
      ctx.moveTo(40, 100);
      ctx.lineTo(width - 40, 100);
      ctx.stroke();
      ctx.restore();

      // ==================== 判决词区域 ====================
      const verdictText = out.verdict;
      const parts = verdictText.split("。");
      const headline = parts[0].replace("此人乃", "").trim();
      const rest = parts.slice(1).join("。");

      ctx.save();
      ctx.fillStyle = theme.secondary + "90";
      ctx.font = "12px 'Courier New', monospace";
      ctx.textAlign = "center";
      ctx.fillText("此人乃", width / 2, 130);
      ctx.restore();

      ctx.save();
      ctx.fillStyle = theme.primary;
      ctx.font = "bold 28px 'Courier New', monospace";
      ctx.textAlign = "center";
      ctx.fillText(headline, width / 2, 165);
      ctx.restore();

      if (rest) {
        ctx.save();
        ctx.fillStyle = theme.secondary + "d0";
        ctx.font = "16px 'Courier New', monospace";
        ctx.textAlign = "center";
        ctx.fillText(rest + "。", width / 2, 195);
        ctx.restore();
      }

      // ==================== MBTI 标签 ====================
      ctx.save();
      ctx.fillStyle = theme.primary;
      ctx.font = "bold 20px 'Courier New', monospace";
      ctx.textAlign = "center";
      ctx.fillText(`MBTI: ${mbti}`, width / 2, 225);
      ctx.restore();

      ctx.save();
      ctx.fillStyle = theme.secondary + "b0";
      ctx.font = "14px 'Courier New', monospace";
      ctx.textAlign = "center";
      ctx.fillText(mbtiDesc[mbti] || "", width / 2, 245);
      ctx.restore();

      // ==================== Tags ====================
      ctx.save();
      ctx.fillStyle = theme.primary + "cc";
      ctx.font = "14px 'Courier New', monospace";
      ctx.textAlign = "center";
      const tagsLine = out.tags.map(t => `#${t}`).join("  ");
      ctx.fillText(tagsLine, width / 2, 275);
      ctx.restore();

      // ==================== 居中雷达图 ====================
      const radarCenterX = width / 2;
      const radarCenterY = 400;
      const radarRadius = 110;

      const labels = ["财富", "持仓", "治理", "构建", "投机"];
      const dataValues = [
        out.radar.wealth,
        out.radar.holding,
        out.radar.governance,
        out.radar.builder,
        out.radar.degen
      ];

      // 绘制五边形背景网格（5层）
      for (let level = 1; level <= 5; level++) {
        const levelRadius = (radarRadius * level) / 5;
        ctx.beginPath();
        ctx.strokeStyle = theme.primary + "40";
        ctx.lineWidth = 1;

        for (let i = 0; i <= 5; i++) {
          const angle = (i * 72 - 90) * (Math.PI / 180);
          const x = radarCenterX + Math.cos(angle) * levelRadius;
          const y = radarCenterY + Math.sin(angle) * levelRadius;

          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.closePath();
        ctx.stroke();
      }

      // 绘制中心线
      for (let i = 0; i < 5; i++) {
        const angle = (i * 72 - 90) * (Math.PI / 180);
        const x = radarCenterX + Math.cos(angle) * radarRadius;
        const y = radarCenterY + Math.sin(angle) * radarRadius;

        ctx.beginPath();
        ctx.strokeStyle = theme.secondary + "30";
        ctx.moveTo(radarCenterX, radarCenterY);
        ctx.lineTo(x, y);
        ctx.stroke();

        // 绘制标签
        const labelRadius = radarRadius + 25;
        const labelX = radarCenterX + Math.cos(angle) * labelRadius;
        const labelY = radarCenterY + Math.sin(angle) * labelRadius;
        ctx.fillStyle = theme.primary + "d8";
        ctx.font = "bold 12px 'Courier New', monospace";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(labels[i], labelX, labelY);
      }

      // 绘制数据五边形
      ctx.beginPath();
      ctx.strokeStyle = theme.primary;
      ctx.lineWidth = 2.5;
      ctx.fillStyle = theme.primary + "40";

      for (let i = 0; i <= 5; i++) {
        const angle = (i * 72 - 90) * (Math.PI / 180);
        const value = dataValues[i % 5] / 100;
        const x = radarCenterX + Math.cos(angle) * (radarRadius * value);
        const y = radarCenterY + Math.sin(angle) * (radarRadius * value);

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // 绘制数据点
      for (let i = 0; i < 5; i++) {
        const angle = (i * 72 - 90) * (Math.PI / 180);
        const value = dataValues[i] / 100;
        const x = radarCenterX + Math.cos(angle) * (radarRadius * value);
        const y = radarCenterY + Math.sin(angle) * (radarRadius * value);

        ctx.beginPath();
        ctx.fillStyle = theme.primary;
        ctx.arc(x, y, 6, 0, Math.PI * 2);
        ctx.fill();

        // 数据点外圈
        ctx.beginPath();
        ctx.strokeStyle = theme.secondary + "66";
        ctx.lineWidth = 2;
        ctx.arc(x, y, 10, 0, Math.PI * 2);
        ctx.stroke();
      }

      // ==================== 底部信息 ====================
      // 钱包地址
      ctx.save();
      ctx.fillStyle = theme.secondary + "80";
      ctx.font = "12px 'Courier New', monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "alphabetic";
      ctx.fillText(out.wallet, width / 2, 550);
      ctx.restore();

      // 品牌标语
      ctx.save();
      ctx.fillStyle = theme.primary + "58";
      ctx.font = "11px 'Courier New', monospace";
      ctx.textAlign = "center";
      ctx.fillText("Wallet is History · AI is Judge · 0xScribe", width / 2, 575);
      ctx.restore();

      // 转换为图片并下载
      const dataUrl = canvas.toDataURL("image/png");
      const link = document.createElement("a");
      link.href = dataUrl;
      link.download = `0xScribe_${out.wallet.substring(0, 10)}_${mbti}.png`;
      link.click();

      // 询问是否分享到 X
      const shareToX = confirm("✅ 图片已下载！\n\n是否要在 X (Twitter) 上分享文字描述？");
      if (shareToX) {
        const text = `⚖️ 判决已下！\n我在 0xScribe 被 AI 判官审判为：${out.verdict.split("。")[0].replace("此人乃", "").trim()}。\nMBTI: ${mbti} - ${mbtiDesc[mbti]}\n\n#0xScribe #Web3 #AI #MBTI`;
        const twitterUrl = "https://twitter.com/intent/tweet?text=" + encodeURIComponent(text);
        window.open(twitterUrl, "_blank");
      }
    } catch (error) {
      console.error("生成图片失败:", error);
      alert("图片生成失败，请重试");
    }
  }

  const flags = out?.risk_flags ?? [];
  const flagsLower = flags.map((s) => (s ?? "").toLowerCase());
  const isFallback = flagsLower.some((s) => s.includes("fallback") || s.includes("keeping sample") || s.includes("no live tx"));
  const isLiveProof = flagsLower.some((s) => s.includes("live proof")) && !isFallback;

  const modeLabel = isLiveProof ? "LIVE PROOF" : "MOCK DATA";
  const badgeColor = isLiveProof ? "bg-green-500/20 text-green-300 border-green-500/50" : "bg-yellow-500/20 text-yellow-300 border-yellow-500/50";
  const modeTooltip = isLiveProof 
    ? "✅ Live Data: All proofs are fetched from Etherscan API." 
    : "⚠️ Mock Data: Showing sample proof links for demo stability.";
  
  const footerLog = isLiveProof 
    ? "> Success: Data fetched from Etherscan API. Proofs are live & clickable."
    : "> Warn: RPC_Timeout. Loading 'sample_profile.json' for demonstration...";


  return (
    <main className="min-h-screen bg-black text-green-200 flex items-center justify-center p-6 relative overflow-hidden font-sans">
      
      {/* 1. 替代方案：高清网格 + 暗角 (Tech Grid Effect - Sharp & Clean) */}
      {/* 将透明度从 0.03 提高到 0.08，使网格更明显但不突兀 */}
      <div className="fixed inset-0 pointer-events-none z-0" 
           style={{
             backgroundImage: `linear-gradient(rgba(0, 255, 100, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 255, 100, 0.08) 1px, transparent 1px)`,
             backgroundSize: '40px 40px',
             maskImage: 'radial-gradient(circle at center, black 40%, transparent 100%)'
           }}>
      </div>

      {/* 背景光晕 (保持不变，增加氛围) */}
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-green-900/10 rounded-full blur-[128px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-emerald-900/10 rounded-full blur-[128px] pointer-events-none" />

      <style jsx global>{`
        @keyframes stamp-in {
          0% { transform: scale(2.5) rotate(-10deg); opacity: 0; }
          60% { transform: scale(0.9) rotate(12deg); opacity: 1; }
          100% { transform: scale(1) rotate(12deg); opacity: 1; }
        }
        .stamp-animate {
          animation: stamp-in 0.4s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }
      `}</style>

      <div className="w-full max-w-3xl relative z-10">
        <header className="mb-8 text-center md:text-left">
          <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-600 tracking-tighter">0xScribe</h1>
          <p className="mt-2 text-green-100/60 font-mono text-sm">
            Wallet is your History. AI is the Judge.
            <span className="block text-green-100/40 text-xs mt-1">钱包即历史，AI即判官。</span>
          </p>
        </header>

        <section className="bg-[#050505] border border-green-900/50 rounded-2xl p-1 shadow-[0_0_40px_rgba(0,255,100,0.05)] backdrop-blur-sm relative overflow-hidden">
          {/* 边框发光效果 */}
          <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-green-500/50 to-transparent"></div>
          
          <div className="p-5 md:p-8">
            <div className="mb-6 group">
              <div className="text-xs text-green-500/50 mb-2 font-mono uppercase tracking-widest group-hover:text-green-400 transition-colors">
                Input Wallet Address
              </div>
              <div className="relative">
                <input
                  value={walletInput}
                  onChange={(e) => setWalletInput(e.target.value)}
                  placeholder="0x... (Leave empty to run sample)"
                  className="w-full px-5 py-4 rounded-xl bg-green-900/10 border border-green-800/50 text-green-100 placeholder-green-800/50 outline-none focus:border-green-500/50 focus:bg-green-900/20 transition-all font-mono text-sm shadow-inner"
                />
                <div className="absolute right-2 top-2 bottom-2 flex items-center gap-2">
                   <button
                    onClick={handleBribe}
                    className="h-full px-3 rounded-lg bg-zinc-800/50 text-zinc-400 font-bold hover:bg-zinc-800 hover:text-yellow-500 transition-all text-xs border border-transparent hover:border-yellow-500/30"
                    title="Attempt to bribe the judge"
                  >
                    💸 <span className="hidden md:inline">Bribe</span>
                  </button>

                   <button
                    onClick={() => judge("sampleA")}
                    className="h-full px-6 rounded-lg bg-green-600 text-black font-bold hover:bg-green-500 hover:scale-[1.02] active:scale-95 transition-all text-sm flex items-center gap-2 shadow-[0_0_15px_rgba(0,255,0,0.2)]"
                  >
                    ⚖ <span className="hidden md:inline">Judge Now</span>
                  </button>
                </div>
              </div>
            </div>

            {error && (
              <div className="mt-4 p-4 border border-red-900/50 rounded-xl bg-red-900/10">
                <div className="flex items-center gap-2 text-red-400 font-mono text-sm">
                  <span className="text-lg">⚠️</span>
                  {error}
                </div>
              </div>
            )}

            {loading && (
              <div className="mt-8 p-6 border border-green-800/30 rounded-xl bg-green-900/5">
                <div className="flex items-center gap-3 text-green-400 font-mono text-lg">
                   <div className="w-2 h-2 bg-green-500 rounded-full animate-ping" />
                   0xScribe is judging...
                </div>
                <div className="mt-4 space-y-1 font-mono text-xs text-green-200/50 border-l-2 border-green-900/50 pl-4">
                  {log.slice(-5).map((x, i) => (
                    <div key={i} className="animate-pulse">{x}</div>
                  ))}
                </div>
              </div>
            )}

            {out && (
              <div className="mt-8 relative border-t border-green-900/50 pt-8 animate-[fadeIn_0.5s_ease-out]">
                
                <div className="flex items-start justify-between mb-4">
                  <div className="text-green-200/40 font-mono text-xs uppercase tracking-widest">
                    {out.case_title}
                  </div>

                  <div className="relative group cursor-help z-20">
                    <div className={`px-3 py-1 rounded-full border text-[10px] font-bold tracking-wider flex items-center gap-1.5 ${badgeColor}`}>
                      <div className={`w-1.5 h-1.5 rounded-full ${isLiveProof ? 'bg-green-400 animate-pulse' : 'bg-yellow-400'}`}></div>
                      {modeLabel}
                    </div>
                    <div className="absolute right-0 top-full mt-2 w-64 p-3 bg-black border border-green-800 text-green-100 text-xs rounded-lg shadow-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-30">
                      {modeTooltip}
                    </div>
                  </div>
                </div>

                {/* 替换为打字机组件 */}
                <TypewriterVerdict text={out.verdict} />

                <div className="mt-5 flex flex-wrap gap-2">
                  {out.tags.map((t) => (
                    <span key={t} className="px-3 py-1 rounded-md bg-green-900/20 border border-green-800/50 text-green-300 text-xs font-medium hover:border-green-500/50 transition-colors cursor-default">
                      #{t}
                    </span>
                  ))}
                </div>

                <div className="absolute top-28 right-2 md:top-24 md:right-8 pointer-events-none stamp-animate z-10 opacity-0">
                  <div className="px-2 py-1 md:px-3 md:py-1 border-2 md:border-[3px] border-red-600/80 text-red-600/90 font-black text-lg md:text-3xl rounded opacity-70 mix-blend-screen tracking-widest uppercase rotate-12 mask-image:url('https://grainy-gradients.vercel.app/noise.svg')">
                    VERIFIED
                  </div>
                </div>

                <div className="mt-8 grid grid-cols-5 gap-2">
                  {Object.entries(radarAnim).map(([k, v]) => (
                    <div key={k} className="flex flex-col items-center p-2 rounded-lg bg-green-900/5 border border-green-900/30">
                      <div className="text-[10px] text-green-500/60 uppercase font-mono mb-1">{k}</div>
                      <div className="text-green-100 text-lg md:text-xl font-bold font-mono">
                        {v}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-green-900/5 border border-green-900/30 rounded-xl p-5 hover:bg-green-900/10 transition-colors">
                    <h3 className="font-bold text-green-400 flex items-center gap-2 mb-3">
                      <span>🏆</span> Merits
                    </h3>
                    <ul className="space-y-3">
                      {out.merits.map((m, i) => (
                        <li key={i} className="flex items-start justify-between gap-3 group/link">
                          <span className="text-green-100/80 text-sm leading-relaxed">{m.claim}</span>
                          <a 
                            href={m.proof_url} 
                            target="_blank" 
                            rel="noreferrer"
                            className="text-green-600 opacity-50 group-hover/link:opacity-100 group-hover/link:text-green-400 transition-all shrink-0 pt-1"
                            title="View on Etherscan"
                          >
                            🔗
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="bg-red-900/5 border border-red-900/20 rounded-xl p-5 hover:bg-red-900/10 transition-colors">
                    <h3 className="font-bold text-red-400/80 flex items-center gap-2 mb-3">
                      <span>💀</span> Charges
                    </h3>
                    <ul className="space-y-3">
                      {out.charges.map((c, i) => (
                        <li key={i} className="flex items-start justify-between gap-3 group/link">
                          <span className="text-green-100/80 text-sm leading-relaxed">{c.claim}</span>
                          <a 
                            href={c.proof_url} 
                            target="_blank" 
                            rel="noreferrer"
                            className="text-green-600 opacity-50 group-hover/link:opacity-100 group-hover/link:text-green-400 transition-all shrink-0 pt-1"
                            title="View on Etherscan"
                          >
                            🔗
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* 分享 + 日志 */}
                <div className="mt-6 pt-4 border-t border-dashed border-green-900/50 flex flex-col md:flex-row justify-between items-center gap-4">
                  <div className={`font-mono text-[10px] md:text-xs order-2 md:order-1 ${isLiveProof ? 'text-green-500/60' : 'text-yellow-600/60'}`}>
                    {footerLog}
                  </div>
                  
                  {/* Share on X 按钮 (带 SVG 图标) */}
                  <button 
                    onClick={handleShare}
                    className="order-1 md:order-2 px-4 py-2 bg-white text-black text-xs font-bold rounded hover:bg-gray-200 transition-all flex items-center gap-2"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M12.6.75h2.454l-5.36 6.142L16 15.25h-4.937l-3.867-5.07-4.425 5.07H.316l5.733-6.57L0 .75h5.063l3.495 4.633L12.601.75Zm-.86 13.028h1.36L4.323 2.145H2.865l8.875 11.633Z"/>
                    </svg>
                    📸 Share Image
                  </button>
                </div>

              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}