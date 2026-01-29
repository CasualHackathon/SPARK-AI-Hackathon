"""Intent graph demo (template-based) with freshly implemented nodes.

This version demonstrates how the new graph architecture can:

* Infer tool parameters automatically through ``HighLevelGraphAPI`` and
  ``ParameterInferenceEngine``.
* Build graphs declaratively via ``GraphTemplate`` / ``NodeSpec`` while keeping
  all business logic inside modular node functions.
* Integrate real tools (PowerData, Tavily MCP, EVM swap) without hard-coding
  them in the core engine.

All nodes below are new implementations – no reuse of the legacy
``intent_graph_demo.py`` functions.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from dotenv import load_dotenv
from spoon_ai.graph import END
from spoon_ai.graph.builder import (
    DeclarativeGraphBuilder,
    EdgeSpec,
    GraphTemplate,
    Intent,
    HighLevelGraphAPI,
    MCPToolSpec,
    NodePlugin,
    NodeSpec,
    ParallelGroupSpec,
)
from spoon_ai.graph.config import GraphConfig, ParallelGroupConfig, RouterConfig
from spoon_ai.llm.manager import get_llm_manager
from spoon_ai.schema import Message

from spoon_toolkits.crypto.crypto_powerdata.tools import CryptoPowerDataCEXTool
from spoon_toolkits.crypto.evm import EvmSwapTool

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------------------------
# State schema for the new demo
# ---------------------------------------------------------------------------


class IntentGraphState(TypedDict, total=False):
    user_query: str
    user_name: str
    session_id: str
    query_intent: str
    symbol: str
    timeframes: List[str]
    include_news: bool

    short_timeframes: List[str]
    macro_timeframes: List[str]

    timeframe_payloads: Dict[str, Dict[str, Any]]
    short_term_data: Dict[str, Dict[str, Any]]
    short_term_metrics: Dict[str, Dict[str, Any]]
    macro_data: Dict[str, Dict[str, Any]]
    macro_metrics: Dict[str, Dict[str, Any]]
    macro_news: List[Dict[str, Any]]
    research_sources: List[Dict[str, Any]]

    short_term_summary: str
    macro_summary: str
    deep_research_report: str
    general_answer: str

    trade_plan: Optional[Dict[str, Any]]
    trade_status: str
    trade_error: Optional[str]

    execution_log: List[str]
    routing_trace: List[str]
    parallel_tasks_completed: int

    final_output: str
    processing_time: float
    execution_metrics: Dict[str, Any]
    memory_snapshot: Dict[str, Any]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


TIMEFRAME_CONFIG: Dict[str, Dict[str, Any]] = {
    "15m": {
        "limit": 60,
        "indicators": {
            "rsi": [{"timeperiod": 14}],
            "ema": [{"timeperiod": 12}, {"timeperiod": 26}],
            "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}],
        },
    },
    "30m": {
        "limit": 50,
        "indicators": {
            "rsi": [{"timeperiod": 14}],
            "ema": [{"timeperiod": 21}],
            "stoch": [{"fastkperiod": 14, "slowkperiod": 3, "slowdperiod": 3}],
        },
    },
    "1h": {
        "limit": 40,
        "indicators": {
            "rsi": [{"timeperiod": 14}],
            "ema": [{"timeperiod": 50}],
            "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}],
            "adx": [{"timeperiod": 14}],
        },
    },
    "4h": {
        "limit": 40,
        "indicators": {
            "rsi": [{"timeperiod": 14}],
            "ema": [{"timeperiod": 50}, {"timeperiod": 200}],
            "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}],
        },
    },
    "1d": {
        "limit": 60,
        "indicators": {
            "rsi": [{"timeperiod": 14}],
            "ema": [{"timeperiod": 50}, {"timeperiod": 200}],
            "bbands": [{"timeperiod": 20, "nbdevup": 2, "nbdevdn": 2}],
        },
    },
    "1w": {
        "limit": 80,
        "indicators": {
            "rsi": [{"timeperiod": 14}],
            "ema": [{"timeperiod": 50}, {"timeperiod": 200}],
            "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}],
        },
    },
}

SHORT_TIMEFRAMES = {"15m", "30m", "1h"}
MACRO_TIMEFRAMES = {"4h", "1d", "1w"}

CURRENT_DIR = Path(__file__).parent

MEMORY_FILE = CURRENT_DIR / "intent_graph_memory_new.json"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_json(path: Path, data: Dict[str, Any]) -> None:
    try:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def _ensure_symbol_pair(symbol: Optional[str]) -> str:
    if not symbol:
        return "BTC/USDT"
    token = symbol.strip().upper()
    if "/" in token:
        base, quote = token.split("/", 1)
        base = base or "BTC"
        quote = quote or "USDT"
        return f"{base}/{quote}"
    if token.endswith("USDT") and len(token) > 4:
        base = token[:-4] or "BTC"
        return f"{base}/USDT"
    if token.endswith("USD") and len(token) > 3:
        base = token[:-3] or "BTC"
        return f"{base}/USD"
    return f"{token}/USDT"


# ---------------------------------------------------------------------------
# Demo implementation
# ---------------------------------------------------------------------------


class IntentGraphTemplateDemo:
    """Declarative demo built on top of the new high-level API."""

    def __init__(self) -> None:
        self.llm = get_llm_manager()
        self.powerdata_tool = CryptoPowerDataCEXTool()
        self.swap_tool: Optional[EvmSwapTool] = None

        rpc_url = os.getenv("EVM_PROVIDER_URL") or os.getenv("RPC_URL")
        if rpc_url:
            self.swap_tool = EvmSwapTool(rpc_url=rpc_url)

        self.api = HighLevelGraphAPI(
            IntentGraphState,
            llm_manager=self.llm,
            intent_prompt_builder=self._build_intent_prompt,
            intent_parser=self._parse_intent_response,
            parameter_prompt_builder=self._build_parameter_prompt,
            parameter_parser=self._parse_parameter_response,
        )

        tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
        if tavily_key and "your-tavily-api-key-here" not in tavily_key:
            tavily_config = {
                "command": "npx",
                "args": ["--yes", "tavily-mcp"],
                "env": {"TAVILY_API_KEY": tavily_key},
            }
            self.api.register_mcp_tool(
                intent_category="crypto_macro",
                spec=MCPToolSpec(name="tavily-search", capability="news"),
                config=tavily_config,
            )
            self.api.register_mcp_tool(
                intent_category="deep_research",
                spec=MCPToolSpec(name="tavily-search", capability="research"),
                config=tavily_config,
            )

        self.graph = self._build_graph()

    def _build_intent_prompt(self, query: str) -> List[Message]:
        return [
            Message(
                role="system",
                content=(
                    "You classify user requests for SpoonAI portfolio assistant.\n"
                    "Respond strictly with JSON containing category, confidence, notes, tags.\n"
                    "Allowed categories: general_qa, crypto_short_term, crypto_macro, crypto_analysis, deep_research."
                ),
            ),
            Message(role="user", content=f"Classify the intent of: {query}"),
        ]

    def _parse_intent_response(self, content: str) -> Dict[str, Any]:
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def _build_parameter_prompt(self, query: str, intent: Intent) -> List[Message]:
        return [
            Message(
                role="system",
                content=(
                    "Extract structured trading parameters for SpoonAI.\n"
                    "Return JSON with symbol, timeframes (array), include_news (bool), confidence, notes."
                ),
            ),
            Message(
                role="user",
                content=(
                    f"Intent category: {intent.category}. Query: {query}.\n"
                    "Respond only with JSON."
                ),
            ),
        ]

    def _parse_parameter_response(self, content: str, intent: Intent) -> Dict[str, Any]:
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return {}

        if not isinstance(data, dict):
            return {}

        symbol = _ensure_symbol_pair(data.get("symbol"))
        if symbol:
            if "/" in symbol:
                base, quote = symbol.split("/", 1)
                symbol = f"{base or 'BTC'}/{quote or 'USDT'}"
            elif symbol.endswith("USDT") and len(symbol) > 4:
                base = symbol[:-4] or "BTC"
                symbol = f"{base}/USDT"
            elif symbol.endswith("USD") and len(symbol) > 3:
                base = symbol[:-3] or "BTC"
                symbol = f"{base}/USD"
            else:
                symbol = f"{symbol}/USDT"
        timeframes = data.get("timeframes")
        if isinstance(timeframes, str):
            timeframes = [tf.strip() for tf in timeframes.split(",") if tf.strip()]
        if not isinstance(timeframes, list) or not timeframes:
            timeframes = (
                ["4h", "1d", "1w"]
                if intent.category in {"crypto_macro", "crypto_analysis"}
                else ["15m", "30m", "1h"]
            )

        include_news = data.get("include_news")
        if isinstance(include_news, str):
            include_news = include_news.lower() in {"true", "1", "yes"}
        if include_news is None:
            include_news = intent.category in {"crypto_macro", "deep_research"}

        return {
            "symbol": symbol,
            "timeframes": timeframes,
            "include_news": include_news,
            "parameter_metadata": {
                "source": data.get("provider", "llm"),
                "confidence": data.get("confidence", 0.6),
                "notes": data.get("notes"),
            },
        }

    # ------------------------------------------------------------------
    # Node implementations
    # ------------------------------------------------------------------

    async def _bootstrap_session(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        session_id = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        log = list(state.get("execution_log", []))
        if "Session bootstrap completed" not in log:
            log.append("Session bootstrap completed")
        return {
            "session_id": session_id,
            "execution_log": log,
            "routing_trace": [],
            "timeframe_payloads": {},
            "short_term_data": {},
            "macro_data": {},
            "macro_news": [],
            "research_sources": [],
            "parallel_tasks_completed": 0,
            "trade_status": "NOT_EVALUATED",
        }

    async def _load_memory(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        all_mem = _load_json(MEMORY_FILE)
        key = (state.get("user_name") or "user").lower()
        snapshot = all_mem.get(key, {})
        user_name = state.get("user_name", "User")
        load_msg = f"Memory loaded for {user_name}"
        log = list(state.get("execution_log", []))
        if load_msg not in log:
            log.append(load_msg)
        return {
            "memory_snapshot": snapshot,
            "execution_log": log,
        }

    async def _plan_analysis(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        timeframes = state.get("timeframes", []) or ["15m", "1h", "4h", "1d"]
        short_tf = [tf for tf in timeframes if tf in SHORT_TIMEFRAMES]
        macro_tf = [tf for tf in timeframes if tf in MACRO_TIMEFRAMES]

        if not short_tf and state.get("query_intent") in {
            "crypto_short_term",
            "crypto_analysis",
        }:
            short_tf = ["15m", "1h"]
        if not macro_tf and state.get("query_intent") in {"crypto_macro"}:
            macro_tf = ["4h", "1d"]

        log = list(state.get("execution_log", []))
        plan_msg = (
            "Analysis plan -> short: "
            f"{short_tf or 'none'}, macro: {macro_tf or 'none'}, include_news: {state.get('include_news', False)}"
        )
        if plan_msg not in log:
            log.append(plan_msg)

        return {
            "short_timeframes": short_tf,
            "macro_timeframes": macro_tf,
            "execution_log": log,
        }

    async def _extract_trade_intent(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        prompt = f"""
        You analyze the user's request and extract trading instructions when they are explicit.

        Query: {state.get('user_query', '')}

        Respond in JSON with keys: trade (true/false), from_token, to_token, amount, notes.
        If no trade is requested, respond with {{"trade": false}}.
        """

        response = await self.llm.chat([Message(role="user", content=prompt)])
        plan: Optional[Dict[str, Any]] = None
        try:
            plan = json.loads(response.content)
        except Exception:
            plan = None

        log = list(state.get("execution_log", []))
        if "Trade intent analyzed" not in log:
            log.append("Trade intent analyzed")
        return {
            "trade_plan": plan if isinstance(plan, dict) else None,
            "execution_log": log,
        }

    async def _general_qa(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        prompt = f"""
        You are Ada, a helpful SpoonAI assistant.
        Answer the user's cryptocurrency question clearly and concisely.
        Question: {state.get('user_query', '')}
        """
        response = await self.llm.chat([Message(role="user", content=prompt)])
        log = list(state.get("execution_log", []))
        if "General Q&A completed" not in log:
            log.append("General Q&A completed")
        return {
            "general_answer": response.content.strip(),
            "execution_log": log,
        }

    async def _short_term_entry(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        log = list(state.get("execution_log", []))
        if "Entering short-term analysis" not in log:
            log.append("Entering short-term analysis")
        trace = list(state.get("routing_trace", []))
        trace.append("short_term")
        return {"execution_log": log, "routing_trace": trace}

    async def _collect_short_term_data(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        symbol = _ensure_symbol_pair(state.get("symbol", "BTC/USDT"))
        timeframes = state.get("short_timeframes", [])
        log = list(state.get("execution_log", []))

        async def fetch(tf: str) -> Optional[Dict[str, Any]]:
            spec = TIMEFRAME_CONFIG.get(tf)
            if not spec:
                return None
            try:
                result = await self.powerdata_tool.execute(
                    exchange="binance",
                    symbol=symbol,
                    timeframe=tf,
                    limit=spec.get("limit", 50),
                    indicators_config=json.dumps(spec.get("indicators", {})),
                    use_enhanced=True,
                )
                logger.info(f"PowerData tool result for {tf}: error={result.error}, output_type={type(result.output)}, output_len={len(result.output) if isinstance(result.output, list) else 'N/A'}")
                candles = getattr(result, "output", result)
                metrics = {}
                if isinstance(candles, list) and candles:
                    closes = [row.get("close") for row in candles if isinstance(row, dict)]
                    volumes = [row.get("volume") for row in candles if isinstance(row, dict)]
                    closes = [c for c in closes if isinstance(c, (int, float))]
                    volumes = [v for v in volumes if isinstance(v, (int, float))]
                    if volumes:
                        metrics["volume_sum"] = sum(volumes)
                    if closes:
                        closes_sorted = sorted(closes)
                        metrics["close_avg"] = sum(closes) / len(closes)
                        metrics["close_median"] = closes_sorted[len(closes_sorted) // 2]
                        metrics["close_high"] = max(closes)
                        metrics["close_low"] = min(closes)
                return {
                    "timeframe": tf,
                    "data": candles,
                    "metrics": metrics,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
            except Exception as exc:
                logger.error(f"PowerData tool exception for {tf}: {exc}")
                return {
                    "timeframe": tf,
                    "error": str(exc),
                }

        tasks = [fetch(tf) for tf in timeframes]
        results = [res for res in await asyncio.gather(*tasks) if res]

        payloads = dict(state.get("timeframe_payloads", {}))
        for item in results:
            payloads[item["timeframe"]] = item

        short_term_serialized = json.dumps(
            {r["timeframe"]: r for r in results if "error" not in r},
            ensure_ascii=False,
        )

        previews: List[str] = []
        for item in results:
            tf = item.get("timeframe", "?")
            if "error" in item:
                previews.append(f"{tf}: error={item['error']}")
                continue
            candles = item.get("data") or []
            sample_close: Optional[float] = None
            if isinstance(candles, list) and candles:
                first_row = next((row for row in candles if isinstance(row, dict)), {})
                sample_close = first_row.get("close")
            previews.append(
                f"{tf}: candles={len(candles)} sample_close={sample_close}"
            )
        if previews:
            preview_msg = "Short-term tool output -> " + "; ".join(previews)
            if preview_msg not in log:
                log.append(preview_msg)

        completed = state.get("parallel_tasks_completed", 0) + len(results)
        collect_msg = f"Short-term data collected for {len(results)} timeframes"
        if collect_msg not in log:
            log.append(collect_msg)

        return {
            "timeframe_payloads": payloads,
            "short_term_data": short_term_serialized,
            "short_term_metrics": {r["timeframe"]: r.get("metrics", {}) for r in results if "error" not in r},
            "short_term_debug": previews,
            "parallel_tasks_completed": completed,
            "execution_log": log,
        }

    async def _summarize_short_term(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        symbol = state.get("symbol", "BTC")
        data_raw = state.get("short_term_data", {})
        if isinstance(data_raw, str):
            data_json = data_raw
        else:
            data_json = json.dumps(data_raw, ensure_ascii=False)
        prompt = f"""
        You are a market analyst. Using the following multi-timeframe data, produce a concise
        short-term outlook for {symbol}. Focus on actionable insights for the next few hours.

        Data (JSON): {data_json[:4000]}

        Provide:
        - Market stance (bullish/neutral/bearish)
        - Key observations (2-3 bullet points)
        - Risk considerations
        End the response with a line: SIGNAL: BUY or SIGNAL: HOLD
        """

        metrics = state.get("short_term_metrics", {})
        market_stats = json.dumps(metrics, ensure_ascii=False).strip()
        debug_info = state.get("short_term_debug", [])
        debug_str = "; ".join(debug_info) if isinstance(debug_info, list) else str(debug_info)

        combined_prompt = f"""
        {prompt}

        Metrics:
        {market_stats}

        Debug:
        {debug_str}
        """

        response = await self.llm.chat([Message(role="user", content=combined_prompt)])
        summary = response.content.strip()
        signal = "HOLD"
        if "SIGNAL:" in summary.upper():
            marker = summary.upper().split("SIGNAL:", 1)[1].strip()
            if marker.startswith("BUY"):
                signal = "BUY"
            elif marker.startswith("SELL"):
                signal = "SELL"

        log = list(state.get("execution_log", []))
        summary_msg = f"Short-term summary generated (signal={signal})"
        if summary_msg not in log:
            log.append(summary_msg)

        return {
            "short_term_summary": summary,
            "trade_status": signal,
            "execution_log": log,
        }

    async def _review_trade(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        plan = state.get("trade_plan") or {}
        status = state.get("trade_status", "HOLD")
        log = list(state.get("execution_log", []))

        if status != "BUY" or not plan.get("trade"):
            if "Trade skipped" not in log:
                log.append("Trade skipped")
            return {"execution_log": log}

        if not self.swap_tool:
            log.append("Trade tool unavailable")
            return {
                "trade_status": "FAILED",
                "trade_error": "Swap tool not configured",
                "execution_log": log,
            }

        try:
            result = await self.swap_tool.execute(
                from_token=plan.get("from_token"),
                to_token=plan.get("to_token"),
                amount=plan.get("amount", "0"),
                signer_type=os.getenv("SIGNER_TYPE", "auto"),
            )
            if result.error:
                raise RuntimeError(result.error)
            log.append("Trade executed successfully")
            return {
                "trade_status": "EXECUTED",
                "execution_log": log,
            }
        except Exception as exc:
            log.append(f"Trade execution failed: {exc}")
            return {
                "trade_status": "FAILED",
                "trade_error": str(exc),
                "execution_log": log,
            }

    async def _macro_entry(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        log = list(state.get("execution_log", []))
        if "Entering macro analysis" not in log:
            log.append("Entering macro analysis")
        trace = list(state.get("routing_trace", []))
        trace.append("macro")
        return {"execution_log": log, "routing_trace": trace}

    async def _collect_macro_data(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        symbol = _ensure_symbol_pair(state.get("symbol", "BTC/USDT"))
        timeframes = state.get("macro_timeframes", [])
        log = list(state.get("execution_log", []))

        async def fetch(tf: str) -> Optional[Dict[str, Any]]:
            spec = TIMEFRAME_CONFIG.get(tf)
            if not spec:
                return None
            try:
                result = await self.powerdata_tool.execute(
                    exchange="binance",
                    symbol=symbol,
                    timeframe=tf,
                    limit=spec.get("limit", 60),
                    indicators_config=json.dumps(spec.get("indicators", {})),
                    use_enhanced=True,
                )
                candles = getattr(result, "output", result)
                metrics = {}
                if isinstance(candles, list) and candles:
                    closes = [row.get("close") for row in candles if isinstance(row, dict)]
                    volumes = [row.get("volume") for row in candles if isinstance(row, dict)]
                    closes = [c for c in closes if isinstance(c, (int, float))]
                    volumes = [v for v in volumes if isinstance(v, (int, float))]
                    if volumes:
                        metrics["volume_sum"] = sum(volumes)
                    if closes:
                        closes_sorted = sorted(closes)
                        metrics["close_avg"] = sum(closes) / len(closes)
                        metrics["close_median"] = closes_sorted[len(closes_sorted) // 2]
                        metrics["close_high"] = max(closes)
                        metrics["close_low"] = min(closes)
                return {
                    "timeframe": tf,
                    "data": candles,
                    "metrics": metrics,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
            except Exception as exc:
                return {
                    "timeframe": tf,
                    "error": str(exc),
                }

        tasks = [fetch(tf) for tf in timeframes]
        results = [res for res in await asyncio.gather(*tasks) if res]

        payloads = dict(state.get("timeframe_payloads", {}))
        for item in results:
            payloads[item["timeframe"]] = item

        macro_serialized = json.dumps(
            {r["timeframe"]: r for r in results if "error" not in r},
            ensure_ascii=False,
        )

        previews: List[str] = []
        for item in results:
            tf = item.get("timeframe", "?")
            if "error" in item:
                previews.append(f"{tf}: error={item['error']}")
                continue
            candles = item.get("data") or []
            sample_close: Optional[float] = None
            if isinstance(candles, list) and candles:
                first_row = next((row for row in candles if isinstance(row, dict)), {})
                sample_close = first_row.get("close")
            previews.append(
                f"{tf}: candles={len(candles)} sample_close={sample_close}"
            )
        if previews:
            preview_msg = "Macro tool output -> " + "; ".join(previews)
            if preview_msg not in log:
                log.append(preview_msg)

        macro_msg = f"Macro data collected for {len(results)} timeframes"
        if macro_msg not in log:
            log.append(macro_msg)
        completed = state.get("parallel_tasks_completed", 0) + len(results)

        return {
            "timeframe_payloads": payloads,
            "macro_data": macro_serialized,
            "macro_metrics": {r["timeframe"]: r.get("metrics", {}) for r in results if "error" not in r},
            "macro_debug": previews,
            "parallel_tasks_completed": completed,
            "execution_log": log,
        }

    async def _fetch_macro_news(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        include_news = state.get("include_news", False)
        tool = self.api.create_mcp_tool("tavily-search") if include_news else None
        if not include_news or not tool:
            return {}

        symbol = state.get("symbol", "BTC")
        query = f"{symbol} cryptocurrency weekly outlook market news"
        try:
            result = await tool.execute(
                query=query, max_results=5, search_depth="basic"
            )
            payload = result.output if hasattr(result, "output") else result
        except Exception as exc:
            payload = [{"title": "News fetch failed", "content": str(exc)}]

        items: List[Dict[str, Any]] = []
        if isinstance(payload, list):
            items = [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": (item.get("content", "") or "")[:500],
                }
                for item in payload[:5]
                if isinstance(item, dict)
            ]
        elif isinstance(payload, str):
            items = [{"title": "Summary", "content": payload[:500]}]

        log = list(state.get("execution_log", []))
        news_msg = f"Macro news fetched ({len(items)} items)"
        if news_msg not in log:
            log.append(news_msg)
        return {"macro_news": items, "execution_log": log}

    async def _summarize_macro(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        symbol = state.get("symbol", "BTC")
        data_raw = state.get("macro_data", {})
        if isinstance(data_raw, str):
            macro_json = data_raw
        else:
            macro_json = json.dumps(data_raw, ensure_ascii=False)
        metrics = state.get("macro_metrics", {})
        news_items = state.get("macro_news", [])
        debug_info = state.get("macro_debug", [])
        debug_str = "; ".join(debug_info) if isinstance(debug_info, list) else str(debug_info)
        prompt = f"""
        Produce a macro trend assessment for {symbol}.
        Market data: {macro_json[:4000]}
        News: {json.dumps(news_items, ensure_ascii=False)[:2000]}

        Provide outlook for the coming weeks, major drivers, and risk notice.
        Keep it under 180 words.
        """

        combined_prompt = f"""
        {prompt}

        Metrics:
        {json.dumps(metrics, ensure_ascii=False).strip()}

        Debug:
        {debug_str}
        """

        response = await self.llm.chat([Message(role="user", content=combined_prompt)])
        summary = response.content.strip()
        log = list(state.get("execution_log", []))
        if "Macro summary generated" not in log:
            log.append("Macro summary generated")
        return {"macro_summary": summary, "execution_log": log}

    async def _deep_research_entry(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        log = list(state.get("execution_log", []))
        if "Entering deep-research flow" not in log:
            log.append("Entering deep-research flow")
        trace = list(state.get("routing_trace", []))
        trace.append("deep_research")
        return {"execution_log": log, "routing_trace": trace}

    async def _fetch_research_sources(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        tool = self.api.create_mcp_tool("tavily-search")
        query = state.get("user_query", "crypto research")
        try:
            result = (
                await tool.execute(query=query, max_results=6, search_depth="advanced")
                if tool
                else []
            )
            payload = result.output if hasattr(result, "output") else result
        except Exception as exc:
            payload = [{"title": "Research fetch failed", "content": str(exc)}]

        sources: List[Dict[str, Any]] = []
        if isinstance(payload, list):
            sources = [
                {
                    "title": item.get("title", ""),
                    "excerpt": (item.get("content", "") or "")[:400],
                    "url": item.get("url", ""),
                }
                for item in payload[:6]
                if isinstance(item, dict)
            ]
        elif isinstance(payload, str):
            sources = [{"title": "Summary", "excerpt": payload[:400]}]

        log = list(state.get("execution_log", []))
        research_msg = f"Research sources gathered ({len(sources)} items)"
        if research_msg not in log:
            log.append(research_msg)
        return {"research_sources": sources, "execution_log": log}

    async def _produce_research_report(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        query = state.get("user_query", "")
        sources = state.get("research_sources", [])
        prompt = f"""
        Create a structured research memo for the following request.
        Request: {query}
        Sources: {json.dumps(sources)[:3000]}

        Provide sections: Overview, Key Findings, Risks, Opportunities. Limit to 220 words.
        """
        response = await self.llm.chat([Message(role="user", content=prompt)])
        report = response.content.strip()
        log = list(state.get("execution_log", []))
        if "Deep research report produced" not in log:
            log.append("Deep research report produced")
        return {"deep_research_report": report, "execution_log": log}

    async def _update_memory(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        snapshot = dict(state.get("memory_snapshot", {}))
        history = snapshot.setdefault("conversation_history", [])
        history.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "query": state.get("user_query", ""),
                "intent": state.get("query_intent", "unknown"),
                "symbol": state.get("symbol", ""),
                "trade_status": state.get("trade_status", "UNKNOWN"),
            }
        )
        history[:] = history[-200:]

        key = (state.get("user_name") or "user").lower()
        all_mem = _load_json(MEMORY_FILE)
        all_mem[key] = snapshot
        _save_json(MEMORY_FILE, all_mem)

        log = list(state.get("execution_log", []))
        if "Memory updated" not in log:
            log.append("Memory updated")
        return {"memory_snapshot": snapshot, "execution_log": log}

    async def _finalize_response(
        self, state: IntentGraphState, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        intent = state.get("query_intent", "general")
        output = (
            state.get("general_answer")
            or state.get("short_term_summary")
            or state.get("macro_summary")
            or state.get("deep_research_report")
            or "No result generated."
        )

        trade_status = state.get("trade_status", "NOT_EVALUATED")
        if trade_status == "EXECUTED":
            output += "\n\nTrade execution initiated."
        elif trade_status == "FAILED":
            output += (
                f"\n\nTrade attempt failed: {state.get('trade_error', 'unknown error')}"
            )

        log = list(state.get("execution_log", []))
        if "Response finalized" not in log:
            log.append("Response finalized")
        return {
            "final_output": output,
            "execution_log": log,
            "routing_trace": state.get("routing_trace", []) + [f"final:{intent}"],
        }

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self):
        template = GraphTemplate(
            entry_point="bootstrap_session",
            nodes=[
                NodeSpec("bootstrap_session", self._bootstrap_session),
                NodeSpec("load_memory", self._load_memory),
                NodeSpec("plan_analysis", self._plan_analysis),
                NodeSpec("extract_trade_intent", self._extract_trade_intent),
                NodeSpec("general_qa", self._general_qa),
                NodeSpec("short_term_entry", self._short_term_entry),
                NodeSpec("collect_short_term_data", self._collect_short_term_data),
                NodeSpec("short_term_summary", self._summarize_short_term),
                NodeSpec("trade_review", self._review_trade),
                NodeSpec("macro_entry", self._macro_entry),
                NodeSpec("collect_macro_data", self._collect_macro_data),
                NodeSpec("fetch_macro_news", self._fetch_macro_news),
                NodeSpec("macro_summary", self._summarize_macro),
                NodeSpec("deep_research_entry", self._deep_research_entry),
                NodeSpec("fetch_research_sources", self._fetch_research_sources),
                NodeSpec("deep_research_summary", self._produce_research_report),
                NodeSpec("update_memory", self._update_memory),
                NodeSpec("finalize_response", self._finalize_response),
            ],
            edges=[
                EdgeSpec("bootstrap_session", "load_memory"),
                EdgeSpec("load_memory", "plan_analysis"),
                EdgeSpec("plan_analysis", "extract_trade_intent"),
                EdgeSpec(
                    "extract_trade_intent",
        {
            "general_qa": "general_qa",
                        "short_term_flow": "short_term_entry",
                        "macro_flow": "macro_entry",
                        "deep_research_flow": "deep_research_entry",
                    },
                    condition=self._route_after_intent,
                ),
                EdgeSpec("general_qa", "update_memory"),
                EdgeSpec("short_term_entry", "collect_short_term_data"),
                EdgeSpec("collect_short_term_data", "short_term_summary"),
                EdgeSpec("short_term_summary", "trade_review"),
                EdgeSpec("trade_review", "update_memory"),
                EdgeSpec("macro_entry", "collect_macro_data"),
                EdgeSpec("collect_macro_data", "fetch_macro_news"),
                EdgeSpec("fetch_macro_news", "macro_summary"),
                EdgeSpec("macro_summary", "update_memory"),
                EdgeSpec("deep_research_entry", "fetch_research_sources"),
                EdgeSpec("fetch_research_sources", "deep_research_summary"),
                EdgeSpec("deep_research_summary", "update_memory"),
                EdgeSpec("update_memory", "finalize_response"),
                EdgeSpec("finalize_response", END),
            ],
            parallel_groups=[
                ParallelGroupSpec(
                    name="macro_collection",
                    nodes=("collect_macro_data", "fetch_macro_news"),
                    config=ParallelGroupConfig(
                        join_strategy="all", error_strategy="collect_errors"
                    ),
                ),
            ],
            config=GraphConfig(max_iterations=80, router=RouterConfig(allow_llm=False)),
        )

        builder = DeclarativeGraphBuilder(IntentGraphState)
        graph = builder.build(template)
        if hasattr(graph, "enable_monitoring"):
            graph.enable_monitoring(
                [
                    "execution_time",
                    "routing_performance",
                    "tool_latency",
                ]
            )
        return graph

    def _route_after_intent(self, state: IntentGraphState) -> str:
        intent = (state.get("query_intent") or "general").lower()
        if intent in {"crypto_short_term", "crypto_analysis"}:
            return "short_term_flow"
        if intent == "crypto_macro":
            return "macro_flow"
        if intent == "deep_research":
            return "deep_research_flow"
        return "general_qa"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process_query(
        self, user_query: str, user_name: str = "User"
    ) -> Dict[str, Any]:
        intent, base_state = await self.api.build_initial_state(user_query, user_name)
        self.api.ensure_mcp_for_intent(intent)

        state: IntentGraphState = {
            **base_state,
            "execution_log": [],
            "routing_trace": [],
            "short_term_summary": "",
            "macro_summary": "",
            "deep_research_report": "",
            "general_answer": "",
            "trade_plan": None,
            "trade_status": "NOT_EVALUATED",
            "trade_error": None,
            "macro_news": [],
            "research_sources": [],
            "timeframe_payloads": {},
            "short_term_data": {},
            "macro_data": {},
        }

        compiled = self.graph.compile()
        start = datetime.now(timezone.utc)
        result = await compiled.invoke(state, {"max_iterations": 80})
        result["processing_time"] = (datetime.now(timezone.utc) - start).total_seconds()
        try:
            result["execution_metrics"] = compiled.get_execution_metrics()
        except Exception:
            result["execution_metrics"] = {}
        result["query_intent"] = intent.category
        return result

    def display_result(self, result: Dict[str, Any]) -> None:
        header = (
            f"\n{'=' * 80}\n"
            "Intent Graph Template Demo\n"
            f"{'=' * 80}\n"
            f"Query: {result.get('user_query', '')}\n"
            f"Intent: {result.get('query_intent', 'unknown')} | Time {result.get('processing_time', 0):.2f}s\n"
            f"{'-' * 80}"
        )
        print(header)

        for idx, log in enumerate(result.get("execution_log", [])[-8:], 1):
            print(f"  {idx}. {log}")

        print("\nResult:\n" + (result.get("final_output") or "(empty)"))
        print(f"\nRouting trace: {result.get('routing_trace', [])}")
        trade = result.get("trade_status", "NOT_EVALUATED")
        if trade not in {"NOT_EVALUATED", "HOLD"}:
            print(f"Trade status: {trade}")
        print(f"{'=' * 80}\n")


async def main() -> None:
    demo = IntentGraphTemplateDemo()
    queries = [
        ("How does blockchain reach consensus?", "Ada"),
        ("Analyze ETH short-term momentum and buy 0.05 ETH if bullish", "Ben"),
        ("Give me a macro outlook for BTC", "Cara"),
        (
            "Research DeFi developments in Q2 2025 and summarize key opportunities",
            "Dana",
        ),
    ]

    for idx, (query, user) in enumerate(queries, 1):
        print(f"Run {idx}/{len(queries)} -> {query}")
        result = await demo.process_query(query, user)
        demo.display_result(result)
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
