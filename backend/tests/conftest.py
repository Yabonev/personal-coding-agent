"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.models.config import ChatConfig
from src.services.message_repository import MessageRepository
from src.ui.console_output import ConsoleOutput
from src.ui.loading_spinner import LoadingSpinner


@pytest.fixture
def sample_config():
    """Create a sample chat configuration."""
    return ChatConfig(
        api_key="test-api-key",
        base_url="https://test.api.com",
        model="test-model",
        system_prompt="Test system prompt",
    )


@pytest.fixture
def message_repository():
    """Create a message repository with test system prompt."""
    return MessageRepository("Test system prompt")


@pytest.fixture
def mock_output_handler():
    """Create a mock output handler."""
    return Mock(spec=ConsoleOutput)


@pytest.fixture
def mock_spinner():
    """Create a mock loading spinner."""
    spinner = Mock(spec=LoadingSpinner)
    spinner.start = Mock()
    spinner.stop = Mock()
    return spinner


@pytest.fixture
def mock_message_repository():
    """Create a mock message repository."""
    repo = Mock(spec=MessageRepository)
    repo.get_messages_for_api = Mock(return_value=[])
    repo.add_user_message = Mock()
    repo.add_assistant_message = Mock()
    return repo
