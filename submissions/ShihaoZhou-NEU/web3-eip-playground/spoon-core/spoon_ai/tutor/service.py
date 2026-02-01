from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from spoon_ai.agents import SpoonReactAI
from spoon_ai.chat import ChatBot
from spoon_ai.prompts.spoon_react import NEXT_STEP_PROMPT_TEMPLATE, SYSTEM_PROMPT
from spoon_ai.tools.tool_manager import ToolManager


# Load .env automatically for local/demo usage, matching README guidance.
load_dotenv(override=True)


# ----------------------------
# Models
# ----------------------------


class TxContext(BaseModel):
    """Lightweight transaction context for better explanations."""

    to: Optional[str] = None
    value_eth: Optional[float] = Field(default=None, alias="valueEth")
    data: Optional[str] = None
    note: Optional[str] = None

    model_config = {"populate_by_name": True}


class Tutor1559ExplainRequest(BaseModel):
    """Inputs for EIP-1559 tutoring."""

    base_fee_per_gas_gwei: float = Field(alias="baseFeePerGasGwei")
    max_fee_per_gas_gwei: float = Field(alias="maxFeePerGasGwei")
    max_priority_fee_per_gas_gwei: float = Field(alias="maxPriorityFeePerGasGwei")
    gas_limit: int = Field(default=21_000, alias="gasLimit")
    user_input: Optional[str] = Field(default=None, alias="userInput")
    tx_context: Optional[TxContext] = Field(default=None, alias="txContext")

    model_config = {"populate_by_name": True}


class DelegationContext(BaseModel):
    """Minimal delegation/authorization context for EIP-7702."""

    delegate: Optional[str] = None
    scope: Optional[str] = None
    expiry: Optional[int] = None
    functions: List[str] = Field(default_factory=list)
    limits: Dict[str, Any] = Field(default_factory=dict)


class SafetyContext(BaseModel):
    """Safety signals provided by the DApp (e.g., simulation results)."""

    is_simulation_ok: Optional[bool] = Field(default=None, alias="isSimulationOk")
    warnings: List[str] = Field(default_factory=list)
    risk_hints: List[str] = Field(default_factory=list, alias="riskHints")

    model_config = {"populate_by_name": True}


class Tutor7702ExplainRequest(BaseModel):
    """Inputs for EIP-7702 tutoring."""

    delegation_context: DelegationContext = Field(alias="delegationContext")
    safety_context: SafetyContext = Field(default_factory=SafetyContext, alias="safetyContext")
    user_input: Optional[str] = Field(default=None, alias="userInput")
    tx_context: Optional[TxContext] = Field(default=None, alias="txContext")

    model_config = {"populate_by_name": True}


class TutorExplainResponse(BaseModel):
    """Stable response shape for frontend rendering."""

    summary: str
    bullets: List[str]
    next_steps: List[str] = Field(alias="nextSteps")
    derived: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class QuizAnswerRequest(BaseModel):
    """Inputs for quiz answer submission."""

    session_id: str = Field(alias="sessionId")
    answer: str

    model_config = {"populate_by_name": True}


class QuizResponse(BaseModel):
    """Stable response shape for quiz flow."""

    session_id: str = Field(alias="sessionId")
    done: bool
    question_index: int = Field(alias="questionIndex")
    assistant_message: str = Field(alias="assistantMessage")
    passed: Optional[bool] = None

    model_config = {"populate_by_name": True}


# ----------------------------
# Quiz configs and helpers
# ----------------------------


@dataclass(frozen=True)
class QuizKeyPoint:
    tokens: List[str]
    hint: str


@dataclass(frozen=True)
class QuizQuestion:
    prompt: str
    key_points: List[QuizKeyPoint]


@dataclass
class QuizSession:
    session_id: str
    eip: str
    questions: List[QuizQuestion]
    current_index: int = 0
    scores: List[int] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)
    completed: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


_QUIZ_QUESTION_BANK: Dict[str, List[QuizQuestion]] = {
    "1559": [
        QuizQuestion(
            prompt="解释 EIP-1559 中有效 gas 价格的计算方式，说明 baseFee、maxFee、maxPriority 的关系。",
            key_points=[
                QuizKeyPoint(tokens=["有效gas", "effectivegas", "有效gas价"], hint="有效 gas 价格概念"),
                QuizKeyPoint(tokens=["min(", "min(", "最小值", "min"], hint="取 min(maxFee, baseFee + priority)"),
                QuizKeyPoint(tokens=["basefee", "base fee", "baseFee"], hint="baseFee 参与计算"),
                QuizKeyPoint(tokens=["priority", "maxpriority", "小费"], hint="priority fee 参与计算"),
            ],
        ),
        QuizQuestion(
            prompt="若 baseFee=30、maxFee=40、maxPriority=5（单位 gwei），这笔交易能否进块？实际小费是多少？",
            key_points=[
                QuizKeyPoint(tokens=["能进", "可以进", "maxfee>=basefee", "40>=30"], hint="能进块（maxFee>=baseFee）"),
                QuizKeyPoint(tokens=["小费", "priority", "5"], hint="小费为 5 gwei"),
                QuizKeyPoint(tokens=["35", "basefee+priority", "30+5"], hint="有效 gas 价为 35 gwei"),
            ],
        ),
        QuizQuestion(
            prompt="为什么 maxFeePerGas 通常需要比 baseFeePerGas 高一些？",
            key_points=[
                QuizKeyPoint(tokens=["上涨", "波动", "增加"], hint="应对 baseFee 上涨/波动"),
                QuizKeyPoint(tokens=["卡住", "失败", "进块"], hint="避免交易卡住/提升进块概率"),
                QuizKeyPoint(tokens=["缓冲", "余量", "冗余"], hint="给手续费留出缓冲空间"),
            ],
        ),
    ],
    "7702": [
        QuizQuestion(
            prompt="EIP-7702 主要带来什么能力或体验？一句话说明其核心价值。",
            key_points=[
                QuizKeyPoint(tokens=["授权", "委托", "delegate"], hint="授权/委托执行"),
                QuizKeyPoint(tokens=["一次", "临时", "单次"], hint="临时/一次性能力"),
                QuizKeyPoint(tokens=["一键", "体验", "简化"], hint="提升用户体验/一键流程"),
            ],
        ),
        QuizQuestion(
            prompt="在 7702 授权中，哪些字段最需要限制或提示风险？",
            key_points=[
                QuizKeyPoint(tokens=["scope", "权限", "范围"], hint="权限范围（scope）"),
                QuizKeyPoint(tokens=["expiry", "过期", "时长", "时间"], hint="授权时长/expiry"),
                QuizKeyPoint(tokens=["functions", "方法", "函数"], hint="可调用函数范围"),
                QuizKeyPoint(tokens=["limits", "额度", "限额"], hint="额度/上限限制"),
            ],
        ),
        QuizQuestion(
            prompt="如果授权已过期或 scope 太大，应当如何处理？",
            key_points=[
                QuizKeyPoint(tokens=["拒绝", "不要", "不能执行"], hint="过期应拒绝执行"),
                QuizKeyPoint(tokens=["收敛", "缩小", "限制"], hint="收敛 scope"),
                QuizKeyPoint(tokens=["缩短", "重新授权", "新的授权"], hint="缩短时长/重新授权"),
            ],
        ),
    ],
    "erc8004": [
        QuizQuestion(
            prompt="ERC-8004 主要解决什么问题？请说明它与“可信 AI Agent”相关的核心价值。",
            key_points=[
                QuizKeyPoint(tokens=["身份", "did", "agentcard"], hint="身份/DID/Agent Card"),
                QuizKeyPoint(tokens=["信誉", "reputation", "评价"], hint="信誉/评价机制"),
                QuizKeyPoint(tokens=["可信", "信任", "trustless"], hint="建立可信/可验证的 AI Agent"),
            ],
        ),
        QuizQuestion(
            prompt="ERC-8004 的身份信息里通常包含哪些关键信息？",
            key_points=[
                QuizKeyPoint(tokens=["did", "身份"], hint="DID/身份标识"),
                QuizKeyPoint(tokens=["service", "endpoint", "服务"], hint="服务/Endpoint"),
                QuizKeyPoint(tokens=["metadata", "能力", "capability"], hint="能力/元信息"),
            ],
        ),
        QuizQuestion(
            prompt="为什么需要 reputation 或 validation 机制？",
            key_points=[
                QuizKeyPoint(tokens=["信任", "可信", "trust"], hint="建立信任"),
                QuizKeyPoint(tokens=["评价", "反馈", "评分"], hint="评价/反馈"),
                QuizKeyPoint(tokens=["防止", "滥用", "风险"], hint="防止滥用/降低风险"),
            ],
        ),
    ],
}


_QUIZ_SESSIONS: Dict[str, QuizSession] = {}


def _normalize_answer(text: str) -> str:
    return "".join((text or "").lower().split())


def _score_answer(answer: str, key_points: List[QuizKeyPoint]) -> tuple[int, List[str]]:
    normalized = _normalize_answer(answer)
    missing: List[str] = []
    matched = 0

    for kp in key_points:
        if any(token.lower() in normalized for token in kp.tokens):
            matched += 1
        else:
            missing.append(kp.hint)

    if not key_points:
        return 0, missing

    score = int(round((matched / len(key_points)) * 10))
    return max(0, min(score, 10)), missing


def _rule_feedback(score: int, missing: List[str]) -> str:
    if not missing:
        return "回答比较完整，核心要点覆盖到了。"
    missing_text = "，".join(missing[:3])
    return f"要点基本覆盖，但还可以补充：{missing_text}。"


def _rule_final_feedback(history: List[Dict[str, Any]]) -> str:
    missing_all: List[str] = []
    for item in history:
        missing_all.extend(item.get("missing", []))

    unique_missing: List[str] = []
    for hint in missing_all:
        if hint not in unique_missing:
            unique_missing.append(hint)

    if not unique_missing:
        return "整体回答较完整，建议继续巩固并结合示例多做演练。"

    missing_text = "、".join(unique_missing[:5])
    return f"你的薄弱点主要在：{missing_text}。建议针对这些点做系统复习，并结合例子重新推导。"


# EIP-1559 derived calculations
# ----------------------------


def _gas_fee_eth(gwei_per_gas: float, gas_limit: int) -> float:
    """
    Convert a gas price in gwei into ETH cost for a given gas limit.

    1 ETH = 1e9 gwei, so:
      fee_eth = (gwei_per_gas * gas_limit) / 1e9
    """
    return (gwei_per_gas * float(gas_limit)) / 1_000_000_000.0


def compute_eip1559_derived(req: Tutor1559ExplainRequest) -> Dict[str, Any]:
    """
    Compute the most useful EIP-1559 derived metrics for tutoring.

    Key formulas:
    - effectiveGasPrice = min(maxFeePerGas, baseFeePerGas + maxPriorityFeePerGas)
    - effectivePriorityFee = min(maxPriorityFeePerGas, maxFeePerGas - baseFeePerGas)
    - maxBaseFeeSupported = maxFeePerGas - maxPriorityFeePerGas
    """
    base_fee = max(req.base_fee_per_gas_gwei, 0.0)
    max_fee = max(req.max_fee_per_gas_gwei, 0.0)
    max_priority = max(req.max_priority_fee_per_gas_gwei, 0.0)
    gas_limit = max(int(req.gas_limit), 0)

    # Inclusion requires maxFeePerGas >= baseFeePerGas.
    inclusion_likely = max_fee >= base_fee

    # Effective gas price and tip capping behavior under EIP-1559.
    effective_gas_price = min(max_fee, base_fee + max_priority)
    priority_fee_cap = max(max_fee - base_fee, 0.0)
    effective_priority_fee = min(max_priority, priority_fee_cap)
    tip_is_capped = max_priority > priority_fee_cap + 1e-9

    # Headroom against rising base fee.
    max_base_fee_supported = max(max_fee - max_priority, 0.0)
    base_fee_buffer = max_base_fee_supported - base_fee
    max_fee_minus_base = max_fee - base_fee

    derived: Dict[str, Any] = {
        "inclusionLikely": inclusion_likely,
        "effectiveGasPriceGwei": round(effective_gas_price, 6),
        "effectivePriorityFeeGwei": round(effective_priority_fee, 6),
        "priorityFeeCapGwei": round(priority_fee_cap, 6),
        "tipIsCapped": tip_is_capped,
        "maxBaseFeeSupportedGwei": round(max_base_fee_supported, 6),
        "baseFeeBufferGwei": round(base_fee_buffer, 6),
        "maxFeeMinusBaseFeeGwei": round(max_fee_minus_base, 6),
        "expectedFeeEth": round(_gas_fee_eth(effective_gas_price, gas_limit), 12),
        "worstCaseFeeEth": round(_gas_fee_eth(max_fee, gas_limit), 12),
        "burnedBaseFeeEth": round(_gas_fee_eth(base_fee, gas_limit), 12) if inclusion_likely else None,
        "priorityFeeEth": round(_gas_fee_eth(effective_priority_fee, gas_limit), 12),
        "gasLimit": gas_limit,
    }

    return derived


def _explain_1559(req: Tutor1559ExplainRequest, derived: Dict[str, Any]) -> TutorExplainResponse:
    inclusion_likely = bool(derived["inclusionLikely"])
    max_fee_headroom = float(derived["maxFeeMinusBaseFeeGwei"])
    tip_is_capped = bool(derived["tipIsCapped"])

    if not inclusion_likely:
        summary = "这笔交易当前无法进入区块，因为 maxFeePerGas 低于 baseFeePerGas。"
    elif max_fee_headroom < 1.0:
        summary = "这笔交易虽然能进块，但 maxFeePerGas 只比 baseFeePerGas 高一点点，容易被波动卡住。"
    else:
        summary = "这组 1559 参数总体合理：既能进块，也保留了一定缓冲。"

    bullets: List[str] = [
        (
            "有效 gas 价 = min(maxFeePerGas, baseFeePerGas + maxPriorityFeePerGas)，"
            f"当前约为 {derived['effectiveGasPriceGwei']} gwei。"
        ),
        (
            "最坏手续费按 maxFeePerGas 计算，"
            f"约为 {derived['worstCaseFeeEth']} ETH（不含转账 value）。"
        ),
        (
            "其中 base fee 会被销毁（burn），"
            f"本次预计销毁约 {derived['burnedBaseFeeEth']} ETH。"
            if derived.get("burnedBaseFeeEth") is not None
            else "由于 maxFeePerGas < baseFeePerGas，本次不会产生有效的 base fee burn。"
        ),
    ]

    if tip_is_capped:
        bullets.append(
            "你的 maxPriorityFeePerGas 高于可支付上限（maxFee - baseFee），实际小费会被截断。"
        )

    next_steps: List[str] = []

    if not inclusion_likely:
        suggested_max_fee = round(req.base_fee_per_gas_gwei + req.max_priority_fee_per_gas_gwei + 1.0, 3)
        next_steps.append(f"把 maxFeePerGas 至少提高到 ~{suggested_max_fee} gwei（高于 baseFee + priority）。")
    else:
        if max_fee_headroom < 1.0:
            next_steps.append("为了避免 base fee 小幅上涨就卡住，建议适度提高 maxFeePerGas。")
        if tip_is_capped:
            next_steps.append("要让小费真正生效，需要同时提高 maxFeePerGas 或降低 maxPriorityFeePerGas。")

    if not next_steps:
        next_steps.append("可以把这组参数作为“默认模板”，再根据是否拥堵做微调。")

    return TutorExplainResponse(
        summary=summary,
        bullets=bullets,
        nextSteps=next_steps,
        derived=derived,
        meta={"standard": "EIP-1559"},
    )


# ----------------------------
# EIP-7702 derived heuristics
# ----------------------------


def _now_ts() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp())


def _derive_7702(req: Tutor7702ExplainRequest) -> Dict[str, Any]:
    now_ts = _now_ts()
    expiry = req.delegation_context.expiry
    expiry_in_seconds: Optional[int] = None
    is_expired = False

    if expiry is not None:
        expiry_in_seconds = int(expiry) - now_ts
        is_expired = expiry_in_seconds <= 0

    scope_text = (req.delegation_context.scope or "").lower()
    scope_is_broad = any(k in scope_text for k in ["unlimited", "any", "all", "broad", "full"])

    warnings = list(req.safety_context.warnings or [])
    simulation_ok = req.safety_context.is_simulation_ok

    if is_expired:
        risk_level = "high"
    elif simulation_ok is False or warnings:
        risk_level = "high"
    elif scope_is_broad or (expiry_in_seconds is not None and expiry_in_seconds > 7 * 24 * 3600):
        risk_level = "medium"
    else:
        risk_level = "low"

    derived: Dict[str, Any] = {
        "nowTs": now_ts,
        "expiryTs": expiry,
        "expiryInSeconds": expiry_in_seconds,
        "isExpired": is_expired,
        "scopeIsBroad": scope_is_broad,
        "simulationOk": simulation_ok,
        "warningsCount": len(warnings),
        "riskLevel": risk_level,
        "functionsCount": len(req.delegation_context.functions or []),
    }

    if expiry_in_seconds is not None:
        derived["expiryInMinutes"] = round(expiry_in_seconds / 60.0, 2)
        derived["expiryInHours"] = round(expiry_in_seconds / 3600.0, 2)

    return derived


def _explain_7702(req: Tutor7702ExplainRequest, derived: Dict[str, Any]) -> TutorExplainResponse:
    risk_level = str(derived["riskLevel"])
    is_expired = bool(derived["isExpired"])
    scope_is_broad = bool(derived["scopeIsBroad"])

    if is_expired:
        summary = "这个 7702 授权已经过期（或即将过期），当前不应继续执行。"
    elif risk_level == "high":
        summary = "这个 7702 授权存在明显风险信号，建议先收敛权限或修复告警。"
    elif risk_level == "medium":
        summary = "这个 7702 授权能用，但权限或时长偏大，建议更精细化。"
    else:
        summary = "这个 7702 授权相对克制，适合作为教学示例。"

    bullets: List[str] = [
        "EIP-7702 的教学重点可以放在：‘把一次复杂操作压缩为更顺滑的用户体验，但必须明确权限边界’。",
        f"当前风险等级评估为 {risk_level}（基于 scope、expiry、simulation 与 warnings）。",
        (
            f"授权剩余时间约 {derived.get('expiryInHours')} 小时。"
            if derived.get("expiryInHours") is not None
            else "本次没有提供 expiry，前端应提醒用户授权的持续时间与撤销方式。"
        ),
    ]

    if scope_is_broad:
        bullets.append("scope 描述偏‘全权/无限制’，这是最值得在 UI 上高亮解释的风险点。")
    if (req.safety_context.warnings or []) and risk_level == "high":
        bullets.append("前端传入了 warnings，Tutor 应该逐条解释这些告警意味着什么。")

    next_steps: List[str] = []
    if is_expired:
        next_steps.append("重新生成一个更短期的授权（例如仅本次任务有效）。")
    else:
        if scope_is_broad:
            next_steps.append("把 scope 收敛为‘仅本次任务/仅这些函数/仅这些额度’。")
        if derived.get("expiryInHours") is None or float(derived.get("expiryInHours") or 0) > 24:
            next_steps.append("给授权加上明确的 expiry（例如 10 分钟或 1 小时）。")
        if req.safety_context.is_simulation_ok is False:
            next_steps.append("先修复 simulation 失败原因，再引导用户签名。")
        if req.safety_context.warnings:
            next_steps.append("把 warnings 作为可展开的‘风险解释卡片’，逐条说明影响与缓解办法。")

    if not next_steps:
        next_steps.append("在教学场景里，建议同时展示‘如何撤销授权/如何限制授权范围’的操作入口。")

    return TutorExplainResponse(
        summary=summary,
        bullets=bullets,
        nextSteps=next_steps,
        derived=derived,
        meta={"standard": "EIP-7702"},
    )


# ----------------------------
# Optional Spoon agent runtime
# ----------------------------


TUTOR_SYSTEM_PROMPT = (
    "You are a Tutor Agent embedded in a Web3 teaching game.\n"
    "- Your job is to explain the CURRENT action, not give generic theory.\n"
    "- Be concise, concrete, and tie explanations to provided numbers.\n"
    "- Prefer actionable advice over abstract definitions.\n"
)


class TutorAgent(SpoonReactAI):
    """
    Spoon agent with a tutor-specific prompt that survives prompt refreshes.

    SpoonReactAI rebuilds system prompts dynamically from tools, so we
    override _refresh_prompts to inject tutor instructions every run.
    """

    tutor_prompt: str = TUTOR_SYSTEM_PROMPT

    def _refresh_prompts(self) -> None:  # type: ignore[override]
        tool_list = self._build_tool_list()
        self.system_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            "Tutor instructions:\n"
            f"{self.tutor_prompt}\n\n"
            "Available tools:\n"
            f"{tool_list}"
        )
        self.next_step_prompt = NEXT_STEP_PROMPT_TEMPLATE.format(tool_list=tool_list)


def _has_any_llm_key() -> bool:
    key_envs = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "DEEPSEEK_API_KEY",
        "GEMINI_API_KEY",
        "OPENROUTER_API_KEY",
    ]
    return any(os.getenv(k, "").strip() for k in key_envs)


@dataclass
class TutorAgentRuntime:
    agent: Optional[SpoonReactAI] = None
    agent_error: Optional[str] = None

    async def get_agent(self) -> Optional[SpoonReactAI]:
        if self.agent or self.agent_error:
            return self.agent

        if not _has_any_llm_key():
            self.agent_error = "No LLM API key detected; running in deterministic-only mode."
            return None

        try:
            provider = os.getenv("TUTOR_LLM_PROVIDER", "").strip() or None
            chatbot = ChatBot(llm_provider=provider) if provider else ChatBot()
            agent = TutorAgent(
                name="tutor_agent",
                description="Teaching-focused tutor agent",
                available_tools=ToolManager([]),
                llm=chatbot,
                x402_enabled=False,
            )
            await agent.initialize()
            self.agent = agent
        except Exception as exc:  # pragma: no cover - defensive fallback
            self.agent_error = f"Failed to initialize tutor agent: {exc}"
            self.agent = None

        return self.agent

    async def tutor_note(self, standard: str, payload: Dict[str, Any]) -> Optional[str]:
        agent = await self.get_agent()
        if not agent:
            return None

        # Keep server responses stateless: clear previous conversation context.
        agent.memory.clear()

        prompt = (
            f"You are helping explain {standard} inside a teaching game.\n"
            "Write 1 short paragraph that references the numbers and ends with 1 actionable suggestion.\n\n"
            f"Context JSON:\n{json.dumps(payload, ensure_ascii=False)}"
        )

        try:
            note = await agent.run(prompt)
        except Exception:
            return None

        return note.strip() if isinstance(note, str) else None


runtime = TutorAgentRuntime()


def _get_quiz_questions(eip: str) -> List[QuizQuestion]:
    questions = _QUIZ_QUESTION_BANK.get(eip)
    if not questions:
        raise HTTPException(status_code=404, detail=f"Unsupported EIP quiz: {eip}")
    return questions


async def _maybe_llm_quiz_feedback(
    eip: str,
    question: QuizQuestion,
    answer: str,
    score: int,
    missing: List[str],
    history: List[Dict[str, Any]],
) -> Optional[str]:
    agent = await runtime.get_agent()
    if not agent:
        return None

    # Keep quiz feedback deterministic across sessions by using explicit context.
    agent.memory.clear()
    prompt = (
        "You are a quiz tutor for EIP teaching. Provide concise feedback in Chinese.\n"
        f"EIP: {eip}\n"
        f"Question: {question.prompt}\n"
        f"User answer: {answer}\n"
        f"Score (0-10): {score}\n"
        f"Missing points: {missing}\n"
        f"History JSON: {json.dumps(history, ensure_ascii=False)}\n\n"
        "Rules:\n"
        "- Output 1-2 short sentences.\n"
        "- Do NOT ask a new question.\n"
        "- Focus on what is missing and how to improve.\n"
    )
    try:
        res = await agent.run(prompt)
    except Exception:
        return None

    return res.strip() if isinstance(res, str) else None


async def _maybe_llm_quiz_final_feedback(
    eip: str,
    history: List[Dict[str, Any]],
    passed: bool,
) -> Optional[str]:
    agent = await runtime.get_agent()
    if not agent:
        return None

    agent.memory.clear()
    prompt = (
        "You are a quiz tutor for EIP teaching. Summarize weaknesses and improvements in Chinese.\n"
        f"EIP: {eip}\n"
        f"Passed: {passed}\n"
        f"History JSON: {json.dumps(history, ensure_ascii=False)}\n\n"
        "Rules:\n"
        "- Output 2-3 sentences.\n"
        "- Mention main weak points and how to improve.\n"
    )
    try:
        res = await agent.run(prompt)
    except Exception:
        return None

    return res.strip() if isinstance(res, str) else None


# ----------------------------
# FastAPI app and endpoints
# ----------------------------


app = FastAPI(title="Spoon Tutor Service", version="0.1.0")


def _configure_cors(application: FastAPI) -> None:
    raw_origins = os.getenv("TUTOR_CORS_ORIGINS", "*")
    origins = [o.strip() for o in raw_origins.split(",") if o.strip()] or ["*"]
    allow_credentials = origins != ["*"]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )


_configure_cors(app)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "service": "spoon-tutor", "time": datetime.utcnow().isoformat()}


@app.post("/tutor/1559/explain", response_model=TutorExplainResponse)
async def tutor_1559_explain(req: Tutor1559ExplainRequest) -> TutorExplainResponse:
    derived = compute_eip1559_derived(req)
    response = _explain_1559(req, derived)

    payload = {
        "standard": "EIP-1559",
        "inputs": req.model_dump(by_alias=True),
        "derived": derived,
        "responseDraft": response.model_dump(by_alias=True),
    }
    note = await runtime.tutor_note("EIP-1559", payload)
    if note:
        response.bullets.append(f"Tutor Agent 补充：{note}")
        response.meta["agentNoteAdded"] = True
    else:
        response.meta["agentNoteAdded"] = False
        if runtime.agent_error:
            response.meta["agentError"] = runtime.agent_error

    return response


@app.post("/tutor/7702/explain", response_model=TutorExplainResponse)
async def tutor_7702_explain(req: Tutor7702ExplainRequest) -> TutorExplainResponse:
    derived = _derive_7702(req)
    response = _explain_7702(req, derived)

    payload = {
        "standard": "EIP-7702",
        "inputs": req.model_dump(by_alias=True),
        "derived": derived,
        "responseDraft": response.model_dump(by_alias=True),
    }
    note = await runtime.tutor_note("EIP-7702", payload)
    if note:
        response.bullets.append(f"Tutor Agent 补充：{note}")
        response.meta["agentNoteAdded"] = True
    else:
        response.meta["agentNoteAdded"] = False
        if runtime.agent_error:
            response.meta["agentError"] = runtime.agent_error

    return response


def _create_quiz_session(eip: str) -> QuizSession:
    session_id = uuid4().hex
    questions = _get_quiz_questions(eip)
    session = QuizSession(session_id=session_id, eip=eip, questions=questions)
    _QUIZ_SESSIONS[session_id] = session
    return session


async def _quiz_start(eip: str) -> QuizResponse:
    session = _create_quiz_session(eip)
    first_question = session.questions[0].prompt
    return QuizResponse(
        sessionId=session.session_id,
        done=False,
        questionIndex=1,
        assistantMessage=f"题目1：{first_question}",
    )


async def _quiz_answer(eip: str, req: QuizAnswerRequest) -> QuizResponse:
    session = _QUIZ_SESSIONS.get(req.session_id)
    if not session or session.eip != eip:
        raise HTTPException(status_code=404, detail="Quiz session not found.")

    if session.completed:
        raise HTTPException(status_code=400, detail="Quiz already completed.")

    if session.current_index >= len(session.questions):
        raise HTTPException(status_code=400, detail="Quiz state invalid.")

    question = session.questions[session.current_index]
    score, missing = _score_answer(req.answer, question.key_points)

    history_entry = {
        "questionIndex": session.current_index + 1,
        "question": question.prompt,
        "answer": req.answer,
        "score": score,
        "missing": missing,
    }

    feedback = await _maybe_llm_quiz_feedback(
        eip=eip,
        question=question,
        answer=req.answer,
        score=score,
        missing=missing,
        history=session.history + [history_entry],
    )
    if not feedback:
        feedback = _rule_feedback(score, missing)

    history_entry["feedback"] = feedback
    session.history.append(history_entry)
    session.scores.append(score)
    session.current_index += 1

    if session.current_index < len(session.questions):
        next_question = session.questions[session.current_index].prompt
        return QuizResponse(
            sessionId=session.session_id,
            done=False,
            questionIndex=session.current_index + 1,
            assistantMessage=f"反馈：{feedback}\n\n题目{session.current_index + 1}：{next_question}",
        )

    total_score = sum(session.scores)
    passed = total_score >= 0
    session.completed = True

    final_feedback = await _maybe_llm_quiz_final_feedback(
        eip=eip,
        history=session.history,
        passed=passed,
    )
    if not final_feedback:
        final_feedback = _rule_final_feedback(session.history)

    status_line = "恭喜通过挑战，可以领取奖励。" if passed else "本次未通过挑战，建议复习后再试。"
    assistant_message = f"最终反馈：{final_feedback}\n\n{status_line}"

    return QuizResponse(
        sessionId=session.session_id,
        done=True,
        questionIndex=len(session.questions),
        assistantMessage=assistant_message,
        passed=passed,
    )


@app.post("/tutor/1559/quiz/start", response_model=QuizResponse)
async def tutor_1559_quiz_start() -> QuizResponse:
    return await _quiz_start("1559")


@app.post("/tutor/1559/quiz/answer", response_model=QuizResponse)
async def tutor_1559_quiz_answer(req: QuizAnswerRequest) -> QuizResponse:
    return await _quiz_answer("1559", req)


@app.post("/tutor/7702/quiz/start", response_model=QuizResponse)
async def tutor_7702_quiz_start() -> QuizResponse:
    return await _quiz_start("7702")


@app.post("/tutor/7702/quiz/answer", response_model=QuizResponse)
async def tutor_7702_quiz_answer(req: QuizAnswerRequest) -> QuizResponse:
    return await _quiz_answer("7702", req)


@app.post("/tutor/erc8004/quiz/start", response_model=QuizResponse)
async def erc8004_quiz_start() -> QuizResponse:
    return await _quiz_start("erc8004")


@app.post("/tutor/erc8004/quiz/answer", response_model=QuizResponse)
async def erc8004_quiz_answer(req: QuizAnswerRequest) -> QuizResponse:
    return await _quiz_answer("erc8004", req)
