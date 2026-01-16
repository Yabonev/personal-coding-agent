"""Tests for ChatApiService."""

from __future__ import annotations

from unittest.mock import ANY
from unittest.mock import MagicMock
from unittest.mock import patch

from src.models.config import ChatConfig
from src.services.chat_api_service import ChatApiService


class TestChatApiService:
    """Tests for ChatApiService."""

    @patch("src.services.chat_api_service.ZaiClient")
    def test_initialization(self, mock_zai_client):
        """Test service initializes with correct config."""
        config = ChatConfig(
            api_key="test-key",
            base_url="https://test.api.com",
            model="test-model",
            system_prompt="Test",
        )

        service = ChatApiService(config)

        mock_zai_client.assert_called_once_with(
            api_key="test-key", base_url="https://test.api.com"
        )
        assert service._config == config

    @patch("src.services.chat_api_service.ZaiClient")
    def test_streaming_completion_context_manager(self, mock_zai_client):
        """Test streaming completion context manager calls API correctly."""
        config = ChatConfig(
            api_key="test-key",
            base_url="https://test.api.com",
            model="test-model",
            system_prompt="Test",
        )

        mock_client_instance = MagicMock()
        mock_completions = MagicMock()
        mock_chat = MagicMock()
        mock_client_instance.chat = mock_chat
        mock_chat.completions = mock_completions
        mock_completions.create = MagicMock(return_value=iter([]))

        mock_zai_client.return_value = mock_client_instance

        service = ChatApiService(config)
        messages = [{"role": "user", "content": "Hello"}]

        with service.streaming_completion(messages) as response:
            result = list(response)

        mock_completions.create.assert_called_once_with(
            model="test-model",
            messages=messages,
            stream=True,
            tools=ANY,
            tool_choice="auto",
        )
        assert result == []

    @patch("src.services.chat_api_service.ZaiClient")
    def test_streaming_completion_with_multiple_messages(self, mock_zai_client):
        """Test streaming completion with multiple messages."""
        config = ChatConfig(
            api_key="test-key",
            base_url="https://test.api.com",
            model="test-model",
            system_prompt="Test",
        )

        mock_client_instance = MagicMock()
        mock_completions = MagicMock()
        mock_chat = MagicMock()
        mock_client_instance.chat = mock_chat
        mock_chat.completions = mock_completions
        mock_completions.create = MagicMock(return_value=iter([]))

        mock_zai_client.return_value = mock_client_instance

        service = ChatApiService(config)
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]

        with service.streaming_completion(messages) as response:
            list(response)

        mock_completions.create.assert_called_once_with(
            model="test-model",
            messages=messages,
            stream=True,
            tools=ANY,
            tool_choice="auto",
        )
