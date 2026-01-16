"""Tests for data models."""

from __future__ import annotations

from src.models.config import ChatConfig
from src.models.message import Message
from src.models.message import MessageRole


class TestMessage:
    """Tests for Message model."""

    def test_to_dict(self):
        """Test converting message to dictionary."""
        message = Message(role=MessageRole.USER, content="Hello")
        result = message.to_dict()

        assert result == {"role": "user", "content": "Hello"}

    def test_to_dict_assistant(self):
        """Test converting assistant message to dictionary."""
        message = Message(role=MessageRole.ASSISTANT, content="Hi there")
        result = message.to_dict()

        assert result == {"role": "assistant", "content": "Hi there"}

    def test_to_dict_system(self):
        """Test converting system message to dictionary."""
        message = Message(role=MessageRole.SYSTEM, content="System prompt")
        result = message.to_dict()

        assert result == {"role": "system", "content": "System prompt"}

    def test_from_dict(self):
        """Test creating message from dictionary."""
        data = {"role": "user", "content": "Hello"}
        message = Message.from_dict(data)

        assert message.role == MessageRole.USER
        assert message.content == "Hello"

    def test_from_dict_all_roles(self):
        """Test creating messages for all roles."""
        roles = [
            ({"role": "system", "content": "test"}, MessageRole.SYSTEM),
            ({"role": "user", "content": "test"}, MessageRole.USER),
            ({"role": "assistant", "content": "test"}, MessageRole.ASSISTANT),
        ]

        for data, expected_role in roles:
            message = Message.from_dict(data)
            assert message.role == expected_role


class TestMessageRole:
    """Tests for MessageRole enum."""

    def test_enum_values(self):
        """Test enum has correct values."""
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"


class TestChatConfig:
    """Tests for ChatConfig model."""

    def test_default_factory(self):
        """Test default factory method."""
        config = ChatConfig.default(
            api_key="test-key",
            base_url="https://test.com",
            model="test-model",
            system_prompt="Test prompt",
        )

        assert config.api_key == "test-key"
        assert config.base_url == "https://test.com"
        assert config.model == "test-model"
        assert config.system_prompt == "Test prompt"

    def test_default_factory_with_defaults(self):
        """Test default factory uses default values."""
        config = ChatConfig.default(api_key="test-key")

        assert config.api_key == "test-key"
        assert config.base_url == "https://api.z.ai/api/coding/paas/v4"
        assert config.model == "glm-4.7"
        assert config.system_prompt
