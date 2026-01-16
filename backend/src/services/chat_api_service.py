"""Service for interacting with the chat API."""

from __future__ import annotations

import json
from collections.abc import Generator
from collections.abc import Iterable
from contextlib import contextmanager
from typing import TYPE_CHECKING

from zai import ZaiClient

from ..models.config import ChatConfig
from ..tools import get_tool_schemas
from ..tracing import SpanKind
from ..tracing import span

if TYPE_CHECKING:
    from zai.types.chat.chat_completion_chunk import ChatCompletionChunk


class ChatApiService:
    """Service for making API calls to the chat service."""

    def __init__(self, config: ChatConfig) -> None:
        """Initialize API service with configuration."""
        self._config = config
        self._client = ZaiClient(api_key=config.api_key, base_url=config.base_url)

    @contextmanager
    def streaming_completion(
        self, messages: list[dict[str, object]]
    ) -> Generator[Iterable[ChatCompletionChunk], None, None]:
        """Context manager for streaming chat completion.

        Keeps api.request span active while consuming the stream,
        so child spans (api.stream, tool.execute) are properly nested.

        Args:
            messages: List of message dictionaries in API format

        Yields:
            Iterator over response chunks
        """
        tool_schemas = get_tool_schemas()

        with span("llm", kind=SpanKind.LLM) as s:
            s.set(
                model=self._config.model,
                message_count=len(messages),
                tool_count=len(tool_schemas),
            )
            if self._config.tracing.include_sensitive_data:
                messages_str = json.dumps(messages, ensure_ascii=False)
                s.set(messages=messages_str)

            response = self._client.chat.completions.create(
                model=self._config.model,
                messages=messages,
                stream=True,
                tools=tool_schemas,
                tool_choice="auto",
            )

            try:
                yield response
            finally:
                close = getattr(response, "close", None)
                if callable(close):
                    close()
