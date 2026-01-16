"""Tests for MessageRepository."""

from __future__ import annotations

from src.models.message import MessageRole
from src.services.message_repository import MessageRepository


class TestMessageRepository:
    """Tests for MessageRepository."""

    def test_initialization_with_system_prompt(self):
        """Test repository initializes with system message."""
        repo = MessageRepository("Test system prompt")
        messages = repo.get_all_messages()

        assert len(messages) == 1
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[0].content == "Test system prompt"

    def test_add_user_message(self, message_repository):
        """Test adding user message."""
        message_repository.add_user_message("Hello")
        messages = message_repository.get_all_messages()

        assert len(messages) == 2
        assert messages[-1].role == MessageRole.USER
        assert messages[-1].content == "Hello"

    def test_add_assistant_message(self, message_repository):
        """Test adding assistant message."""
        message_repository.add_assistant_message("Hi there")
        messages = message_repository.get_all_messages()

        assert len(messages) == 2
        assert messages[-1].role == MessageRole.ASSISTANT
        assert messages[-1].content == "Hi there"

    def test_multiple_messages(self, message_repository):
        """Test adding multiple messages maintains order."""
        message_repository.add_user_message("First")
        message_repository.add_assistant_message("Response")
        message_repository.add_user_message("Second")

        messages = message_repository.get_all_messages()

        assert len(messages) == 4
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[1].content == "First"
        assert messages[2].content == "Response"
        assert messages[3].content == "Second"

    def test_get_messages_for_api(self, message_repository):
        """Test converting messages to API format."""
        message_repository.add_user_message("Hello")
        message_repository.add_assistant_message("Hi")

        api_messages = message_repository.get_messages_for_api()

        assert len(api_messages) == 3
        assert api_messages[0]["role"] == "system"
        assert api_messages[1]["role"] == "user"
        assert api_messages[2]["role"] == "assistant"
        assert all(isinstance(msg, dict) for msg in api_messages)

    def test_get_messages_for_api_format(self, message_repository):
        """Test API format structure."""
        message_repository.add_user_message("Test")
        api_messages = message_repository.get_messages_for_api()

        assert "role" in api_messages[1]
        assert "content" in api_messages[1]
        assert api_messages[1]["role"] == "user"
        assert api_messages[1]["content"] == "Test"

    def test_clear_preserves_system_message(self, message_repository):
        """Test clearing messages preserves system message."""
        message_repository.add_user_message("User 1")
        message_repository.add_assistant_message("Assistant 1")
        message_repository.add_user_message("User 2")

        message_repository.clear()
        messages = message_repository.get_all_messages()

        assert len(messages) == 1
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[0].content == "Test system prompt"

    def test_get_all_messages_returns_copy(self, message_repository):
        """Test get_all_messages returns a copy, not reference."""
        messages1 = message_repository.get_all_messages()
        message_repository.add_user_message("New message")
        messages2 = message_repository.get_all_messages()

        assert len(messages1) == 1
        assert len(messages2) == 2
        assert messages1 is not messages2
