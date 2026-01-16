"""Configuration data models."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from ..tracing import TracingConfig


@dataclass
class ChatConfig:
    """Chat configuration settings."""

    api_key: str
    base_url: str
    model: str
    system_prompt: str
    tracing: TracingConfig = field(default_factory=TracingConfig)

    @classmethod
    def default(
        cls,
        api_key: str,
        base_url: str = "https://api.z.ai/api/coding/paas/v4",
        model: str = "glm-4.7",
        system_prompt: str | None = None,
        tracing: TracingConfig | None = None,
    ) -> ChatConfig:
        """Create default configuration."""
        cwd = Path.cwd()
        default_prompt = (
            "You are an AI coding agent. You have access to tools and can call "
            "multiple tools in a single response when needed. Use tools proactively "
            "to accomplish tasks. When multiple independent operations are needed, "
            "call all relevant tools at once.\n\n"
            f"Current working directory: {cwd}"
        )
        return cls(
            api_key=api_key,
            base_url=base_url,
            model=model,
            system_prompt=system_prompt or default_prompt,
            tracing=tracing or TracingConfig(),
        )
