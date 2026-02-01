"""Declarative crypto analysis demo with brand-new modular nodes.

Features:
* Fully LLM-driven routing with HighLevelGraphAPI parameter inference.
* Real Binance data (via REST), PowerData toolkit indicators, Tavily MCP news.
* Parallel token analysis using new node implementations.
* Final aggregation mirroring the legacy functionality without reusing code.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict, Set
import aiohttp
from dotenv import load_dotenv

from zoneinfo import ZoneInfo

# Configure logging
logger = logging.getLogger(__name__)

from spoon_ai.graph import END
from spoon_ai.graph.builder import (
    DeclarativeGraphBuilder,
    EdgeSpec,
    GraphTemplate,
    HighLevelGraphAPI,
    MCPToolSpec,
    NodeSpec,
    ParallelGroupSpec,
)
from spoon_ai.graph.config import GraphConfig, ParallelGroupConfig
from spoon_ai.llm.manager import get_llm_manager
from spoon_ai.schema import Message

from spoon_toolkits.crypto.crypto_powerdata.tools import CryptoPowerDataCEXTool

load_dotenv()


class CryptoAnalysisState(TypedDict, total=False):
    user_query: str
    selected_tokens: List[str]
    token_details: Dict[str, Any]
    market_overview: Dict[str, Any]
    token_reports: Dict[str, Dict[str, Any]]
    token_scores: Dict[str, float]
    news_items: Dict[str, List[Dict[str, Any]]]
    final_summary: str
    execution_log: List[str]
    parallel_tasks_completed: int
    processing_time: float
    execution_metrics: Dict[str, Any]
    binance_market_data: Dict[str, Any]
    execution_history: List[Dict[str, Any]]
    analysis_flags: Set[str]


class DeclarativeCryptoAnalysisDemo:
    def __init__(self) -> None:
        self.api = HighLevelGraphAPI(CryptoAnalysisState)
        self.llm = get_llm_manager()
        self.powerdata_tool = CryptoPowerDataCEXTool()
        self.tavily_search_tool = None

        tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
        if tavily_key and "your-tavily-api-key-here" not in tavily_key:
            self.api.register_mcp_tool(
                intent_category="crypto_analysis",
                spec=MCPToolSpec(name="tavily-search", capability="news"),
                config={
                        "command": "npx",
                        "args": ["--yes", "tavily-mcp"],
                    "env": {"TAVILY_API_KEY": tavily_key},
                },
            )

        self.graph = self._build_graph()

    # ------------------------------------------------------------------
    # Node implementations (matching original functionality exactly)
    # ------------------------------------------------------------------

    async def _fetch_binance_market_data(self, state: CryptoAnalysisState, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch real Binance market data and select top 10 pairs by volume"""
        async with aiohttp.ClientSession() as session:
            url = "https://api.binance.com/api/v3/ticker/24hr"
            async with session.get(url) as response:
                if response.status != 200:
                    return {"error": f"Binance API failed: {response.status}"}
                binance_data = await response.json()

        stablecoins = {'USDCUSDT', 'FDUSDUSDT', 'TUSDUSDT', 'BUSDUSDT', 'DAIUSDT', 'USDPUSDT', 'FRAXUSDT', 'LUSDUSDT', 'SUSDUSDT', 'USTCUSDT', 'USDDUSDT', 'GUSDUSDT', 'PAXGUSDT', 'USTUSDT'}

        usdt_pairs = []
        for item in binance_data:
            if isinstance(item, dict) and item.get('symbol', '').endswith('USDT'):
                symbol = item.get('symbol', '')
                if symbol not in stablecoins and all(key in item for key in ['symbol', 'priceChangePercent', 'volume', 'lastPrice']):
                    usdt_pairs.append({
                        'symbol': symbol,
                        'priceChangePercent': float(item['priceChangePercent']),
                        'volume': float(item['volume']),
                        'lastPrice': float(item['lastPrice']),
                        'count': int(item.get('count', 0)),
                        'quoteVolume': float(item.get('quoteVolume', 0))
                    })

        top_pairs_by_volume = sorted(usdt_pairs, key=lambda x: x['quoteVolume'], reverse=True)[:10]

        log = list(state.get("execution_log", []))
        log.append(f"Fetched Binance data ({len(top_pairs_by_volume)} pairs)")

        return {
                "binance_market_data": {
                    "top_pairs": top_pairs_by_volume,
                    "total_pairs_available": len(usdt_pairs),
                    "selected_pairs_count": len(top_pairs_by_volume),
                    "timestamp": datetime.now().isoformat(),
                    "source": "binance_api_real"
                },
                "execution_history": {
                    "action": "fetch_binance_data",
                    "pairs_fetched": len(top_pairs_by_volume),
                    "real_data": True
                },
            "analysis_flags": {"binance_data_fetched"},
            "execution_log": log,
        }

    async def _prepare_token_list(self, state: CryptoAnalysisState, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare token list from Binance data"""
        binance_data = state.get("binance_market_data", {})
        top_pairs = binance_data.get("top_pairs", [])

        if not top_pairs:
            return {"error": "No Binance market data available"}

        selected_tokens = [pair["symbol"].replace("USDT", "") for pair in top_pairs]
        token_details: Dict[str, Any] = {}
        for pair in top_pairs:
            token = pair["symbol"].replace("USDT", "")
            token_details[token] = {
                "symbol": pair["symbol"],
                "price_change_24h": pair["priceChangePercent"],
                "volume_usdt": pair["quoteVolume"],
                "last_price": pair["lastPrice"],
                "trade_count": pair.get("count", 0),
                "rank_by_volume": top_pairs.index(pair) + 1,
            }

        log = list(state.get("execution_log", []))
        log.append(f"Prepared token list ({len(selected_tokens)} tokens)")

        return {
            "selected_tokens": selected_tokens,
            "token_details": token_details,
            "execution_history": {
                "action": "prepare_token_list",
                "tokens_count": len(selected_tokens),
            },
            "analysis_flags": {"tokens_prepared"},
            "execution_log": log,
        }

    async def _analyze_token_by_index(self, token_index: int, state: CryptoAnalysisState, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze a single token by index - matches original create_token_analyzer_by_index"""
        selected_tokens: List[str] = state.get("selected_tokens", [])
        if token_index >= len(selected_tokens):
            log = list(state.get("execution_log", []))
            log.append(f"No token available at index {token_index}")
            return {
                "execution_log": log,
                "parallel_tasks_completed": state.get("parallel_tasks_completed", 0),
            }

        token = selected_tokens[token_index]
        return await self._analyze_single_token(token, state)

    async def _analyze_single_token(self, token: str, state: CryptoAnalysisState, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Complete analysis of a single token - matches original create_token_analyzer"""
        logger.info(f"Start analyzing token: {token}")

        try:
            token_details = state.get("token_details", {})

            async def fetch_kline_data() -> Dict[str, Any]:
                try:
                    if not self.powerdata_tool:
                        return {"error": "PowerData tool not available", "data": None}

                    symbol = f"{token}/USDT"
                    indicators_config = {
                        "rsi": [{"timeperiod": 14}],
                        "ema": [{"timeperiod": 12}, {"timeperiod": 26}, {"timeperiod": 50}],
                        "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}],
                        "bbands": [{"timeperiod": 20, "nbdevup": 2, "nbdevdn": 2}],
                    }

                    daily_result = await self.powerdata_tool.execute(
                        exchange="binance",
                        symbol=symbol,
                        timeframe="1d",
                        limit=100,
                        indicators_config=json.dumps(indicators_config),
                        use_enhanced=True,
                    )

                    h4_result = await self.powerdata_tool.execute(
                        exchange="binance",
                        symbol=symbol,
                        timeframe="4h",
                        limit=100,
                        indicators_config=json.dumps(indicators_config),
                        use_enhanced=True,
                    )

                    return {
                        "daily_data": daily_result.output if daily_result and not daily_result.error else None,
                        "h4_data": h4_result.output if h4_result and not h4_result.error else None,
                        "error": None,
                    }
                except Exception:
                    return {"error": "kline fetch failed", "data": None}

            async def fetch_news_data() -> Dict[str, Any]:
                if self.tavily_search_tool:
                    result = await self.tavily_search_tool.execute(
                        query=f"{token} cryptocurrency news price analysis market trends",
                        max_results=3,
                        search_depth="basic",
                    )
                    return {"data": str(result), "error": None}
                return {"error": "no tavily mcp tool", "data": None}

            kline_result, news_result = await asyncio.gather(fetch_kline_data(), fetch_news_data())

            token_detail = token_details.get(token, {})
            current_price = token_detail.get("last_price", 0)
            price_change_24h = token_detail.get("price_change_24h", 0)

            ta_section = json.dumps(kline_result, indent=2, ensure_ascii=False) if kline_result.get("daily_data") else "TA unavailable"
            news_section = json.dumps(news_result, indent=2, ensure_ascii=False) if news_result.get("data") else "News unavailable"

            ta_prompt = f"""You are a professional crypto trading analyst. Provide a concise, actionable TECHNICAL trading recommendation for {token}.

Context:
- Token: {token}
- Current Price: ${current_price}
- 24h Change: {price_change_24h:+.2f}%

Technical Data (1d and 4h):
{ta_section}

Requirements:
1) Summarize technical trend and momentum
2) Key support/resistance levels (prices)
3) Entry plan (zones or triggers)
4) Stop loss
5) Targets (multiple if applicable)
6) Risk rating (Low/Medium/High) and a 1-10 opportunity score
Output in English, concise, bullet style."""

            news_prompt = f"""You are a professional crypto news/sentiment analyst. Based on recent NEWS for {token}, provide a concise, actionable NEWS-DRIVEN trading recommendation.

Context:
- Token: {token}
- Current Price: ${current_price}

News Data (headlines, snippets, sources):
{news_section}

Requirements:
1) Summarize news sentiment and key events
2) Impact on price (bullish/bearish/neutral)
3) Trading implications (buy/sell/hold)
4) Risk factors from news
5) Confidence level (1-10)
Output in English, concise, bullet style."""

            ta_response = await self.llm.chat([Message(role="user", content=ta_prompt)])
            news_response = await self.llm.chat([Message(role="user", content=news_prompt)])

            report = {
                "token": token,
                "symbol": f"{token}/USDT",
                "technical_analysis": ta_response.content.strip(),
                "news_analysis": news_response.content.strip(),
                "current_price": current_price,
                "price_change_24h": price_change_24h,
                "indicators": kline_result,
                "news": news_result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            log = list(state.get("execution_log", []))
            log.append(f"Analysis completed for {token}")

            token_reports = dict(state.get("token_reports", {}))
            token_reports[token] = report
            token_scores = dict(state.get("token_scores", {}))
            token_scores[token] = self._score_token(report)

            completed = state.get("parallel_tasks_completed", 0) + 1

            return {
                "token_reports": token_reports,
                "token_scores": token_scores,
                "parallel_tasks_completed": completed,
                "execution_log": log,
            }
        except Exception as exc:
            log = list(state.get("execution_log", []))
            log.append(f"Analysis failed for {token}: {exc}")
            token_reports = dict(state.get("token_reports", {}))
            token_reports[token] = {"error": str(exc)}
            completed = state.get("parallel_tasks_completed", 0) + 1
            return {
                "token_reports": token_reports,
                "parallel_tasks_completed": completed,
                "execution_log": log,
            }

    def _score_token(self, report: Dict[str, Any]) -> float:
        """Derive a heuristic opportunity score (0-1)."""
        score = 0.5
        price_change = report.get("price_change_24h") or 0
        if isinstance(price_change, (int, float)):
            score += max(min(price_change / 100.0, 0.2), -0.2)

        sentiment_bonus = 0.0
        tech_text = (report.get("technical_analysis") or "").lower()
        news_text = (report.get("news_analysis") or "").lower()
        if "bullish" in tech_text or "bullish" in news_text:
            sentiment_bonus += 0.1
        if "bearish" in tech_text or "bearish" in news_text:
            sentiment_bonus -= 0.1

        score += sentiment_bonus
        return float(max(0.0, min(1.0, score)))

    async def _fetch_token_news(self, token: str, state: CryptoAnalysisState, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch news for a specific token"""
        tool = self.api.create_mcp_tool("tavily-search")
        if not tool:
            return {}

        try:
            result = await tool.execute(query=f"{token} cryptocurrency news price analysis market trends", max_results=3, search_depth="basic")
            payload = result.output if hasattr(result, "output") else result
        except Exception as exc:
            payload = [{"title": "News fetch failed", "content": str(exc)}]

        items = []
        if isinstance(payload, list):
            items = [
                {
                    "title": entry.get("title", ""),
                    "url": entry.get("url", ""),
                    "content": (entry.get("content", "") or "")[:400],
                }
                for entry in payload
                if isinstance(entry, dict)
            ]
        elif isinstance(payload, str):
            items = [{"title": "Summary", "content": payload[:400]}]

        return {"news_items": {token: items}}

    async def _aggregate_results(self, state: CryptoAnalysisState, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Aggregate all token analyses into final report"""
        token_reports = state.get("token_reports", {})

        if not token_reports:
            return {"final_summary": "No token analyses available"}

        simplified_reports = {}
        for token, report in token_reports.items():
            if "error" in report:
                simplified_reports[token] = {"error": report["error"]}
                continue
            
            simplified_reports[token] = {
                "price": report.get("current_price"),
                "change_24h": report.get("price_change_24h"),
                "technical_summary": report.get("technical_analysis"), 
                "news_summary": report.get("news_analysis")           
            }


        summary_prompt = f"""You are a senior crypto analyst. Create a comprehensive market analysis report based on the summarized analysis of the top tokens.

TOKEN SUMMARIES:
{json.dumps(simplified_reports, indent=2, ensure_ascii=False)}

Create a structured report with:
1) Market Overview (current sentiment, trends based on the top tokens)
2) Top Trading Opportunities (Pick the best 3 tokens based on the technical and news summaries)
3) Risk Warnings (Common risks identified across tokens)
4) Overall Market Outlook

Keep it professional, actionable, and under 800 words."""

        try:
            
            response = await self.llm.chat([Message(role="user", content=summary_prompt)])
            final_summary = response.content.strip()

            log = list(state.get("execution_log", []))
            log.append("Final market analysis generated")

            return {
                "final_summary": final_summary,
                "execution_log": log,
            }
        except Exception as e:
            logger.error(f"LLM aggregation failed: {e}")
            
            fallback_summary = "Failed to generate AI summary due to error. Raw conclusions:\n"
            for t, r in simplified_reports.items():
                fallback_summary += f"\n{t}: {r.get('technical_summary', 'N/A')[:100]}..."
            
            return {
                "final_summary": fallback_summary,
                "execution_log": list(state.get("execution_log", [])) + [f"Aggregation failed: {str(e)}"]
            }



    def _build_graph(self):
        """Build the complete analysis graph matching original functionality"""
        # Create analyzer nodes - each node handles a specific token index
        analyzer_nodes = []
        analyzer_names = []

        for i in range(10):
            node_name = f"analyze_token_{i}"
            analyzer_names.append(node_name)

            # Create a node function that captures the token index
            def make_analyzer_node(token_idx):
                async def analyzer_node(state: CryptoAnalysisState, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
                    return await self._analyze_token_by_index(token_idx, state, config)
                return analyzer_node

            analyzer_func = make_analyzer_node(i)
            analyzer_nodes.append(NodeSpec(node_name, analyzer_func, parallel_group="token_analysis"))

        template = GraphTemplate(
            entry_point="fetch_binance_data",
            nodes=[
                NodeSpec("fetch_binance_data", self._fetch_binance_market_data),
                NodeSpec("prepare_token_list", self._prepare_token_list),
                *analyzer_nodes,
                NodeSpec("llm_final_aggregation", self._aggregate_results),
            ],
            edges=[
                EdgeSpec("fetch_binance_data", "prepare_token_list"),
                # Connect prepare_token_list to all analyzers
                *[EdgeSpec("prepare_token_list", name) for name in analyzer_names],
                # Connect all analyzers to final aggregation
                *[EdgeSpec(name, "llm_final_aggregation") for name in analyzer_names],
                EdgeSpec("llm_final_aggregation", END),
            ],
            parallel_groups=[
                ParallelGroupSpec(
                    name="token_analysis",
                    nodes=tuple(analyzer_names),
                    config=ParallelGroupConfig(join_strategy="all", error_strategy="collect_errors"),
                ),
            ],
            config=GraphConfig(max_iterations=100),
        )

        builder = DeclarativeGraphBuilder(CryptoAnalysisState)
        graph = builder.build(template)
        if hasattr(graph, "enable_monitoring"):
            graph.enable_monitoring([
                "execution_time",
                "llm_response_quality",
                "api_success_rate",
                "analysis_depth",
                "parallel_branch_efficiency"
            ])
        return graph

    async def run(self, query: str) -> Dict[str, Any]:
        """Run complete crypto analysis matching original functionality"""
        intent, base_state = await self.api.build_initial_state(query)
        self.api.ensure_mcp_for_intent(intent)

        # Initialize state with all required fields
        state: CryptoAnalysisState = {
            "user_query": query,
            "execution_log": [],
            "parallel_tasks_completed": 0,
        "selected_tokens": [],
        "token_details": {},
            "token_reports": {},
            "token_scores": {},
            "news_items": {},
            "final_summary": "",
            "binance_market_data": {},
        "execution_history": [],
        "analysis_flags": set(),
        }
        state.update(base_state)

        compiled = self.graph.compile()
        start = datetime.now(timezone.utc)
        result = await compiled.invoke(state, {"max_iterations": 100})
        result["processing_time"] = (datetime.now(timezone.utc) - start).total_seconds()
        try:
            result["execution_metrics"] = compiled.get_execution_metrics()
        except Exception:
            result["execution_metrics"] = {}
        return result

    def render(self, result: Dict[str, Any]) -> None:
        """Render results in the same format as original demo"""
        query = result.get("user_query", "")
        processing_time = result.get("processing_time", 0.0)
        report_date = self._current_date_label()
        summary = result.get("final_summary", "")
        execution_log = result.get("execution_log", [])

        print(f"\n{'=' * 80}")
        print(f"🔍 MARKET ANALYSIS REPORT")
        print(f"{'=' * 80}")
        print(f"📝 Query: {query}")
        print(f"📅 Date: {report_date}")
        print(f"⚡ Processing Time: {processing_time:.2f}s")
        print(f"{'-' * 80}")

        if execution_log:
            print("📋 Execution Steps:")
            for i, log_entry in enumerate(execution_log[-8:], 1):
                print(f"  {i}. {log_entry}")

        if summary:
            print("\n📊 ANALYSIS RESULTS:")
            print(summary)
        else:
            print("\n📊 ANALYSIS RESULTS: No summary generated")
        print(f"{'=' * 80}\n")

    def _current_date_label(self) -> str:
        try:
            tz_name = os.getenv("REPORT_TIMEZONE", "UTC")
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("UTC")
        return datetime.now(tz).strftime("%Y-%m-%d %H:%M %Z")


async def main() -> None:
    demo = DeclarativeCryptoAnalysisDemo()
    print("🚀 Declarative LLM Crypto Analysis Demo")
    print("=" * 80)

    # Test with empty query to match original behavior (uses LLM-driven token selection)
    result = await demo.run("")
    demo.render(result)


if __name__ == "__main__":
    asyncio.run(main())


