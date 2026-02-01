"""ReAct agent demo that uses x402 payments to access the official protected resource."""

from __future__ import annotations

import asyncio
import ast
import html
import json
import os
import re
import sys
from decimal import Decimal
from textwrap import shorten
from typing import Any, Dict, Optional

from eth_account import Account
from rich import print as rprint

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from spoon_ai.agents.spoon_react import SpoonReactAI  # noqa: E402
from spoon_ai.chat import ChatBot  # noqa: E402
from spoon_ai.schema import Message, Role  # noqa: E402
from spoon_ai.payments import X402PaymentReceipt, X402PaymentService  # noqa: E402
from pydantic import Field  # noqa: E402
from spoon_ai.prompts.spoon_react import NEXT_STEP_PROMPT_TEMPLATE  # noqa: E402
from spoon_ai.tools.tool_manager import ToolManager  # noqa: E402
from spoon_ai.tools.x402_payment import X402PaywalledRequestTool  # noqa: E402
from x402.encoding import safe_base64_decode  # noqa: E402
from spoon_toolkits.web.web_scraper import WebScraperTool  # noqa: E402

PAYWALLED_URL = os.getenv("X402_DEMO_URL", "https://www.x402.org/protected")
PAYMENT_USDC = Decimal("0.01")


def ensure_wallet_configuration(service: X402PaymentService) -> None:
    client = service.settings.client

    if not client.private_key and not client.use_turnkey:
        raise RuntimeError(
            "Neither PRIVATE_KEY nor Turnkey credentials detected. Configure a signer before running the demo."
        )

    if client.private_key and not client.private_key.startswith("0x"):
        client.private_key = "0x" + client.private_key

    if (
        not service.settings.pay_to
        or service.settings.pay_to.lower().startswith("0x0000")
        or service.settings.pay_to == "0xYourAgentTreasuryAddress"
    ):
        if client.private_key:
            inferred = Account.from_key(client.private_key).address
        elif client.turnkey_address:
            inferred = client.turnkey_address
        else:
            raise RuntimeError(
                "Unable to determine recipient address. Set X402_RECEIVER_ADDRESS or provide TURNKEY_ADDRESS."
            )
        service.settings.pay_to = inferred

    if not client.private_key and client.use_turnkey and not client.turnkey_address:
        client.turnkey_address = service.settings.pay_to

    if service.settings.max_amount_usdc is None or service.settings.max_amount_usdc > PAYMENT_USDC:
        service.settings.max_amount_usdc = PAYMENT_USDC


def summarise_text(text: str, max_length: int = 400) -> str:
    stripped = re.sub(r"<[^>]+>", " ")
    cleaned = " ".join(html.unescape(stripped).split()) or text
    if len(cleaned) <= max_length:
        return cleaned
    return shorten(cleaned, width=max_length, placeholder="…")


def decode_receipt(header_value: str) -> Dict[str, Any]:
    payload = X402PaymentReceipt.model_validate_json(safe_base64_decode(header_value))
    return payload.model_dump()


def extract_music_url(content: str) -> Optional[str]:
    """Extract SoundCloud (or other) music link from HTML/text."""
    if not content:
        return None
    cleaned = html.unescape(content)
    # Look for SoundCloud embed first
    match = re.search(r"https?://w\.soundcloud\.com/player/\?[^\s\"'<>]+", cleaned)
    if match:
        return match.group(0)
    match = re.search(r"https?://soundcloud\.com/[^\s\"'<>]+", cleaned)
    if match:
        return match.group(0)
    # Fallback: first http(s) link
    match = re.search(r"https?://[^\s\"'<>]+", cleaned)
    if match:
        return match.group(0)
    return None


def parse_tool_output(raw: str) -> Any:
    segment: Optional[str] = None
    if "Output:" in raw:
        segment = raw.split("Output:", 1)[1].strip()
    elif "Error:" in raw:
        segment = raw.split("Error:", 1)[1].strip()
    else:
        segment = raw

    if segment.startswith("`") and segment.endswith("`"):
        segment = segment[1:-1]

    if not segment:
        return segment

    try:
        return json.loads(segment)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(segment)
        except (ValueError, SyntaxError):
            return segment


def extract_tool_payload(messages: list[Message], tool_name: str) -> Optional[Any]:
    for message in reversed(messages):
        if message.role == Role.TOOL and message.name == tool_name and message.content:
            parsed = parse_tool_output(message.content)
            if parsed is not None:
                return parsed
    return None


def extract_last_assistant(messages: list[Message]) -> Optional[str]:
    for message in reversed(messages):
        if message.role == Role.ASSISTANT and message.content:
            return message.content
    return None


def print_conversation(messages: list[Message]) -> None:
    role_styles = {
        Role.USER: ("User", "bold green"),
        Role.ASSISTANT: ("Assistant", "bold cyan"),
        Role.TOOL: ("Tool", "bold yellow"),
    }

    rprint("\n[bold blue]Conversation Trace[/]")
    for message in messages:
        try:
            role = Role(message.role)
        except ValueError:
            continue
        if role == Role.SYSTEM:
            continue
        label, style = role_styles.get(role, (message.role, "white"))
        if role == Role.TOOL and message.name:
            label = f"{label} ({message.name})"
            parsed = parse_tool_output(message.content or "")
            if isinstance(parsed, (dict, list)):
                preview = json.dumps(parsed, indent=2, ensure_ascii=False)
            else:
                preview = str(parsed)
        else:
            preview = message.content or ""

        if len(preview) > 1200:
            preview = preview[:1200] + "…"
        rprint(f"[{style}]{label}[/]: {preview}")

class X402ReactAgent(SpoonReactAI):
    name: str = "x402_react_agent"
    description: str = "ReAct agent that pays x402 invoices to reach protected resources"
    target_url: str = PAYWALLED_URL
    service: X402PaymentService = Field(default_factory=X402PaymentService, exclude=True)

    template_system_prompt: str = (
        "You are an autonomous ReAct agent with tool access."
        " Your mission is to retrieve the protected content at {target_url}."
        " Follow this playbook:\n"
        "1. Use `web_scraper` (default format='markdown') to fetch the URL. If it returns 402, note the payment headers."
        "2. Use `x402_paywalled_request` with amount_usdc={amount} to settle the invoice and retry."
        "3. Summarise the protected body in clear English."
        "4. Return a final answer that includes: summary, HTTP status, signed PAYMENT-SIGNATURE (x402 v2) or X-PAYMENT (v1) header,"
        " and any decoded settlement receipt (PAYMENT-RESPONSE / X-PAYMENT-RESPONSE)."
        " Be explicit about the Base Sepolia network and the 0.01 USDC charge."
        " If a step fails, explain the reason before attempting recovery."
    )

    def __init__(self, service: X402PaymentService, url: str, **kwargs: Any) -> None:
        super().__init__(service=service, target_url=url, **kwargs)
        self.web_scraper = WebScraperTool()
        self.payment_tool: Optional[X402PaywalledRequestTool] = None
        self.max_steps = 6
        self.x402_enabled = False  # prevent base class from auto-attaching duplicate tools
        self.available_tools = ToolManager([])
        self._refresh_prompts()

    async def initialize(self) -> None:
        ensure_wallet_configuration(self.service)
        self.payment_tool = X402PaywalledRequestTool(service=self.service)
        self.available_tools = ToolManager([self.web_scraper, self.payment_tool])
        self._refresh_prompts()

    def _refresh_prompts(self) -> None:
        """Keep the customised x402 playbook while still listing current tools."""
        tool_list = self._build_tool_list()
        self.system_prompt = (
            self.template_system_prompt.format(
                target_url=self.target_url,
                amount=str(PAYMENT_USDC),
            )
            + f"\n\nAvailable tools:\n{tool_list}"
        )
        self.next_step_prompt = NEXT_STEP_PROMPT_TEMPLATE.format(tool_list=tool_list)


async def main() -> None:
    rprint("[bold green]x402 ReAct Agent Demo[/]")
    rprint(
        "This demo performs a real Base Sepolia payment of 0.01 USDC against https://www.x402.org/protected."
    )
    rprint(
        "Ensure your PRIVATE_KEY (or Turnkey credentials) is funded. Base Sepolia USDC faucet: https://faucet.circle.com/"
    )

    chatbot = ChatBot()
    service = X402PaymentService()
    agent = X402ReactAgent(service=service, url=PAYWALLED_URL, llm=chatbot)
    await agent.initialize()

    signer_source = "private key" if service.settings.client.private_key else "turnkey"
    rprint(
        f"Signer ready: [bold]{service.settings.pay_to}[/] (payer source: {signer_source})"
    )
    rprint(
        f"Target resource: [bold]{PAYWALLED_URL}[/] | Network: {service.settings.default_network} | Facilitator: {service.settings.facilitator_url}"
    )

    query = (
        "Access the protected page, follow the playbook, and finish with a concise summary."
        " Include the signed payment header and settlement receipt in the final response."
    )
    rprint(f"\n[bold green]User Goal[/]: {query}")

    try:
        step_log = await asyncio.wait_for(agent.run(query), timeout=120)
    except Exception as exc:
        rprint(f"[bold red]Agent execution failed:[/] {exc}")
        raise

    messages = agent.memory.get_messages()

    rprint("\n[bold cyan]Step Trace[/]")
    rprint(step_log)

    print_conversation(messages)

    web_scraper_result = extract_tool_payload(messages, "web_scraper")
    payment_result = extract_tool_payload(messages, "x402_paywalled_request")

    if payment_result is not None and not isinstance(payment_result, dict):
        payment_result = None

    assistant_summary = extract_last_assistant(messages)
    music_url: Optional[str] = None

    if not assistant_summary and payment_result:
        body = payment_result.get("body")
        if isinstance(body, dict):
            assistant_summary = summarise_text(json.dumps(body, ensure_ascii=False))
        elif isinstance(body, str):
            assistant_summary = summarise_text(body)
            music_url = extract_music_url(body)

    # Attempt music URL extraction even if assistant summary already exists.
    if music_url is None and payment_result:
        body = payment_result.get("body")
        if isinstance(body, str):
            music_url = extract_music_url(body)

    if web_scraper_result:
        rprint("\n[bold magenta]Initial probe (no payment)[/]")
        if isinstance(web_scraper_result, dict):
            preview_body = web_scraper_result.get("body") or web_scraper_result
            if isinstance(preview_body, dict):
                preview_body = json.dumps(preview_body, indent=2, ensure_ascii=False)
            status = web_scraper_result.get("status")
            if status is not None:
                rprint(f"Status: {status}")
            rprint(preview_body)
        else:
            rprint(web_scraper_result)

    payment_header: Optional[str] = None
    payment_receipt: Optional[Dict[str, Any]] = None
    payment_header_name = "X-PAYMENT"

    if payment_result:
        req_meta = payment_result.get("requirements")
        if isinstance(req_meta, dict):
            if req_meta.get("x402Version") == 2 or "amount" in req_meta:
                payment_header_name = "PAYMENT-SIGNATURE"
            rprint(
                "\n[bold yellow]Payment requirement (post-tool) pay_to:[/]"
                f" {req_meta.get('payTo') or req_meta.get('pay_to')}"
            )
        payment_header = payment_result.get("paymentHeader")
        payment_receipt = payment_result.get("paymentResponse")
        headers_map = payment_result.get("headers") or {}
        receipt_header = None
        if isinstance(headers_map, dict):
            lowered = {str(k).lower(): v for k, v in headers_map.items()}
            receipt_header = lowered.get("payment-response") or lowered.get("x-payment-response")
        if not payment_receipt and receipt_header:
            payment_receipt = decode_receipt(receipt_header)

    if assistant_summary:
        rprint("\n[bold green]Agent Final Summary[/]")
        rprint(assistant_summary)
    if music_url:
        rprint("\n[bold green]Music URL[/]")
        rprint(music_url)

    if payment_header:
        rprint(f"\n[bold blue]Signed {payment_header_name} Header[/]")
        rprint(payment_header)

    if payment_receipt:
        rprint("\n[bold green]Decoded Settlement Receipt[/]")
        rprint(json.dumps(payment_receipt, indent=2, ensure_ascii=False))
        if isinstance(payment_receipt, dict) and payment_receipt.get("error"):
            rprint(
                "\n[bold yellow]Note:[/] The facilitator reported an error while settling the payment."
                " Double-check that your payer wallet holds at least 0.01 USDC on Base Sepolia"
                " and that the private key or Turnkey credentials are correct."
            )


if __name__ == "__main__":
    asyncio.run(main())
