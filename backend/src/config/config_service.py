"""Configuration service for loading and managing application configuration."""

from __future__ import annotations

import os

from dotenv import load_dotenv

from ..models.config import ChatConfig
from ..tracing import TracingConfig


class ConfigService:
    """Service for loading and managing application configuration."""

    def __init__(self) -> None:
        """Initialize configuration service."""
        load_dotenv()

    def get_api_key(self) -> str:
        """Get API key from environment variables."""
        api_key = os.getenv("ZAI_API_KEY")
        if not api_key:
            msg = "ZAI_API_KEY not found in environment"
            raise ValueError(msg)
        return api_key

    def create_chat_config(
        self,
        base_url: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
        tracing: TracingConfig | None = None,
    ) -> ChatConfig:
        """Create chat configuration from environment and parameters."""
        api_key = self.get_api_key()
        return ChatConfig.default(
            api_key=api_key,
            base_url=base_url or "https://api.z.ai/api/coding/paas/v4",
            model=model or "glm-4.7",
            system_prompt=system_prompt,
            tracing=tracing,
        )
