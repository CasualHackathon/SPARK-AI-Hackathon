from __future__ import annotations

import os
from decimal import Decimal, ROUND_DOWN
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from spoon_ai.utils.config_manager import ConfigManager


class X402ConfigurationError(Exception):
    """Raised when required x402 configuration is missing or invalid."""


class X402PaywallBranding(BaseModel):
    """Optional branding customisations for the embedded paywall template."""

    app_name: Optional[str] = Field(default=None)
    app_logo: Optional[str] = Field(default=None)
    session_token_endpoint: Optional[str] = Field(default=None)
    cdp_client_key: Optional[str] = Field(default=None)


class X402ClientConfig(BaseModel):
    """Holds client-side signing configuration used for outbound payments."""

    private_key: Optional[str] = Field(default=None, description="0x-prefixed hex private key")
    private_key_env: str = Field(default="X402_AGENT_PRIVATE_KEY")
    use_turnkey: bool = Field(default=False, description="Whether to use Turnkey for signing instead of a local private key")
    turnkey_sign_with: Optional[str] = Field(default=None, description="Turnkey signing identity (address, wallet ID, or key ID)")
    turnkey_address: Optional[str] = Field(default=None, description="Address that should appear as the payer when signing via Turnkey")

    @classmethod
    def from_raw(cls, raw: Optional[Dict[str, Any]] = None) -> "X402ClientConfig":
        raw = raw or {}

        private_key_env = raw.get("private_key_env") or "X402_AGENT_PRIVATE_KEY"
        env_private_key = os.getenv(private_key_env)
        if env_private_key in (None, ""):
            env_private_key = os.getenv("X402_AGENT_PRIVATE_KEY")
        if env_private_key in (None, ""):
            env_private_key = os.getenv("PRIVATE_KEY")

        private_key = raw.get("private_key") or env_private_key
        if isinstance(private_key, str) and not private_key.strip():
            private_key = None

        def _to_bool(value: Any) -> bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "on"}
            return False
        raw_toggle = raw.get("use_turnkey")
        env_toggle = os.getenv("X402_USE_TURNKEY")
        if env_toggle in (None, ""):
            env_toggle = os.getenv("TURNKEY_ENABLED")
        if raw_toggle is not None:
            use_turnkey = _to_bool(raw_toggle)
        else:
            use_turnkey = _to_bool(env_toggle)
        turnkey_sign_with = (
            raw.get("turnkey_sign_with")
            or os.getenv("X402_TURNKEY_SIGN_WITH")
            or os.getenv("TURNKEY_SIGN_WITH")
        )
        turnkey_address = (
            raw.get("turnkey_address")
            or os.getenv("X402_TURNKEY_ADDRESS")
            or os.getenv("TURNKEY_ADDRESS")
            or turnkey_sign_with
        )

        if not use_turnkey and not private_key and (turnkey_sign_with or os.getenv("TURNKEY_SIGN_WITH")):
            use_turnkey = True

        return cls(
            private_key=private_key,
            private_key_env=private_key_env,
            use_turnkey=use_turnkey,
            turnkey_sign_with=turnkey_sign_with,
            turnkey_address=turnkey_address,
        )


class X402Settings(BaseModel):
    """Resolved configuration view for x402 payments inside SpoonOS."""

    facilitator_url: str = Field(default="https://x402.org/facilitator")
    default_scheme: str = Field(default="exact")
    default_network: str = Field(default="base-sepolia")

    asset: str = Field(default="0xa063B8d5ada3bE64A24Df594F96aB75F0fb78160")
    asset_name: str = Field(default="USDC")
    asset_version: str = Field(default="2")
    asset_decimals: int = Field(default=6)

    pay_to: str = Field(default="0x0000000000000000000000000000000000000000")
    resource: str = Field(default="https://localhost/spoon/agent")
    description: str = Field(default="SpoonOS agent service")
    mime_type: str = Field(default="application/json")
    max_timeout_seconds: int = Field(default=120)

    max_amount_usdc: Optional[Decimal] = Field(default=Decimal("0.10"))
    extra: Dict[str, Any] = Field(default_factory=dict)

    paywall_branding: X402PaywallBranding = Field(default_factory=X402PaywallBranding)
    client: X402ClientConfig = Field(default_factory=X402ClientConfig)

    @field_validator("facilitator_url")
    @classmethod
    def _ensure_http_scheme(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise X402ConfigurationError("X402 facilitator URL must start with http:// or https://")
        return value.rstrip("/")

    @field_validator("asset")
    @classmethod
    def _ensure_lower_hex(cls, value: str) -> str:
        return value.lower()

    @property
    def amount_in_atomic_units(self) -> str:
        """Return the configured maximum amount encoded as atomic units (string)."""
        amount = self.max_amount_usdc or Decimal("0")
        scaled_decimal = (amount * (Decimal(10) ** self.asset_decimals)).quantize(Decimal("1"), rounding=ROUND_DOWN)
        scaled = int(scaled_decimal)
        return str(scaled)

    def build_asset_extra(self) -> Dict[str, Any]:
        """Construct the `extra` payload for the payment requirements."""
        metadata = {
            "name": self.asset_name,
            "version": self.asset_version,
            "decimals": self.asset_decimals,
        }
        return {**metadata, **self.extra}

    @classmethod
    def load(cls, config_manager: Optional[ConfigManager] = None) -> "X402Settings":
        """Load settings from config.json with .env fallbacks."""
        manager = config_manager or ConfigManager()
        raw_config = manager.get("x402", {}) or {}

        facilitator_url = os.getenv("X402_FACILITATOR_URL", raw_config.get("facilitator_url", cls.model_fields["facilitator_url"].default))
        default_scheme = os.getenv("X402_DEFAULT_SCHEME", raw_config.get("default_scheme", cls.model_fields["default_scheme"].default))
        default_network = os.getenv("X402_DEFAULT_NETWORK", raw_config.get("default_network", cls.model_fields["default_network"].default))

        asset = os.getenv("X402_DEFAULT_ASSET", raw_config.get("asset", cls.model_fields["asset"].default))
        asset_metadata = raw_config.get("asset_metadata", {}) or {}
        asset_name = asset_metadata.get("name", cls.model_fields["asset_name"].default)
        asset_version = asset_metadata.get("version", cls.model_fields["asset_version"].default)
        asset_decimals = int(raw_config.get("asset_decimals", cls.model_fields["asset_decimals"].default))

        pay_to = os.getenv("X402_RECEIVER_ADDRESS", raw_config.get("pay_to", cls.model_fields["pay_to"].default))
        resource = raw_config.get("resource", cls.model_fields["resource"].default)
        description = raw_config.get("description", cls.model_fields["description"].default)
        mime_type = raw_config.get("mime_type", cls.model_fields["mime_type"].default)
        max_timeout_seconds = raw_config.get("max_timeout_seconds", cls.model_fields["max_timeout_seconds"].default)

        max_amount_env = os.getenv("X402_DEFAULT_AMOUNT_USDC")
        max_amount_usdc = Decimal(str(max_amount_env)) if max_amount_env else raw_config.get("max_amount_usdc", cls.model_fields["max_amount_usdc"].default)
        if not isinstance(max_amount_usdc, Decimal):
            max_amount_usdc = Decimal(str(max_amount_usdc))

        paywall_branding = X402PaywallBranding(
            app_name=os.getenv("X402_PAYWALL_APP_NAME", (raw_config.get("paywall") or {}).get("app_name")),
            app_logo=os.getenv("X402_PAYWALL_APP_LOGO", (raw_config.get("paywall") or {}).get("app_logo")),
            session_token_endpoint=os.getenv("X402_SESSION_TOKEN_ENDPOINT", (raw_config.get("paywall") or {}).get("session_token_endpoint")),
            cdp_client_key=(raw_config.get("paywall") or {}).get("cdp_client_key"),
        )

        client = X402ClientConfig.from_raw(raw_config.get("client"))

        extra = raw_config.get("extra", {})

        return cls(
            facilitator_url=facilitator_url,
            default_scheme=default_scheme,
            default_network=default_network,
            asset=asset,
            asset_name=asset_name,
            asset_version=asset_version,
            asset_decimals=asset_decimals,
            pay_to=pay_to,
            resource=resource,
            description=description,
            mime_type=mime_type,
            max_timeout_seconds=max_timeout_seconds,
            max_amount_usdc=max_amount_usdc,
            extra=extra,
            paywall_branding=paywall_branding,
            client=client,
        )
