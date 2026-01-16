"""Tests for ChatOrchestrator."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from src.models.config import ChatConfig
from src.models.tool import StreamResult
from src.orchestrators.chat_orchestrator import ChatOrchestrator


def _mock_streaming_completion(return_value):
    """Create a mock streaming_completion context manager."""

    @contextmanager
    def _streaming_completion(_messages):
        yield return_value

    return _streaming_completion


class TestChatOrchestrator:
    """Tests for ChatOrchestrator."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ChatConfig(
            api_key="test-key",
            base_url="https://test.api.com",
            model="test-model",
            system_prompt="Test system prompt",
        )

    def test_initialization(self, config):
        """Test orchestrator initializes all components."""
        orchestrator = ChatOrchestrator(config)

        assert orchestrator._config == config
        assert orchestrator._api_service is not None
        assert orchestrator._message_repository is not None
        assert orchestrator._output_handler is not None
        assert orchestrator._spinner is not None
        assert orchestrator._response_processor is not None

    @patch("src.orchestrators.chat_orchestrator.ToolExecutor")
    @patch("src.orchestrators.chat_orchestrator.ChatApiService")
    @patch("src.orchestrators.chat_orchestrator.MessageRepository")
    @patch("src.orchestrators.chat_orchestrator.ConsoleOutput")
    @patch("src.orchestrators.chat_orchestrator.LoadingSpinner")
    @patch("src.orchestrators.chat_orchestrator.StreamResponseProcessor")
    def test_should_exit(
        self,
        mock_processor,
        mock_spinner,
        mock_output,
        mock_repo,
        mock_api,
        mock_tool_executor,
        config,
    ):
        """Test exit command detection."""
        orchestrator = ChatOrchestrator(config)

        assert orchestrator._should_exit("exit") is True
        assert orchestrator._should_exit("EXIT") is True
        assert orchestrator._should_exit("quit") is True
        assert orchestrator._should_exit("bye") is True
        assert orchestrator._should_exit("continue") is False
        assert orchestrator._should_exit("") is False

    @patch("src.orchestrators.chat_orchestrator.ToolExecutor")
    @patch("src.orchestrators.chat_orchestrator.StreamResponseProcessor")
    @patch("src.orchestrators.chat_orchestrator.LoadingSpinner")
    @patch("src.orchestrators.chat_orchestrator.ConsoleOutput")
    @patch("src.orchestrators.chat_orchestrator.MessageRepository")
    @patch("src.orchestrators.chat_orchestrator.ChatApiService")
    def test_process_user_message_flow(
        self,
        mock_api_class,
        mock_repo_class,
        mock_output_class,
        mock_spinner_class,
        mock_processor_class,
        mock_tool_executor_class,
        config,
    ):
        """Test processing user message flow."""
        # Setup mocks
        mock_api = Mock()
        mock_repo = Mock()
        mock_output = Mock()
        mock_spinner = Mock()
        mock_processor = Mock()

        mock_api_class.return_value = mock_api
        mock_repo_class.return_value = mock_repo
        mock_output_class.return_value = mock_output
        mock_spinner_class.return_value = mock_spinner
        mock_processor_class.return_value = mock_processor

        mock_repo.get_messages_for_api.return_value = [
            {"role": "user", "content": "test"}
        ]
        mock_api.streaming_completion = _mock_streaming_completion(iter([]))
        mock_processor.process.return_value = StreamResult(
            content="Hi", has_content=True
        )

        orchestrator = ChatOrchestrator(config)
        orchestrator._process_user_message("Hello")

        # Verify flow
        mock_repo.add_user_message.assert_called_once_with("Hello")
        mock_spinner.start.assert_called_once()
        mock_repo.get_messages_for_api.assert_called_once()
        mock_processor.process.assert_called_once()

    @patch("src.orchestrators.chat_orchestrator.ToolExecutor")
    @patch("src.orchestrators.chat_orchestrator.StreamResponseProcessor")
    @patch("src.orchestrators.chat_orchestrator.LoadingSpinner")
    @patch("src.orchestrators.chat_orchestrator.ConsoleOutput")
    @patch("src.orchestrators.chat_orchestrator.MessageRepository")
    @patch("src.orchestrators.chat_orchestrator.ChatApiService")
    def test_process_user_message_error_handling(
        self,
        mock_api_class,
        mock_repo_class,
        mock_output_class,
        mock_spinner_class,
        mock_processor_class,
        mock_tool_executor_class,
        config,
    ):
        """Test error handling in message processing."""
        # Setup mocks
        mock_api = Mock()
        mock_repo = Mock()
        mock_output = Mock()
        mock_spinner = Mock()
        mock_processor = Mock()

        mock_api_class.return_value = mock_api
        mock_repo_class.return_value = mock_repo
        mock_output_class.return_value = mock_output
        mock_spinner_class.return_value = mock_spinner
        mock_processor_class.return_value = mock_processor

        @contextmanager
        def _raise_error(_messages):
            raise ValueError("API Error")
            yield  # type: ignore[misc]

        mock_api.streaming_completion = _raise_error

        orchestrator = ChatOrchestrator(config)

        with pytest.raises(ValueError):
            orchestrator._process_user_message("Hello")

        mock_spinner.stop.assert_called_once()

    @patch("src.orchestrators.chat_orchestrator.ToolExecutor")
    @patch("src.orchestrators.chat_orchestrator.StreamResponseProcessor")
    @patch("src.orchestrators.chat_orchestrator.LoadingSpinner")
    @patch("src.orchestrators.chat_orchestrator.ConsoleOutput")
    @patch("src.orchestrators.chat_orchestrator.MessageRepository")
    @patch("src.orchestrators.chat_orchestrator.ChatApiService")
    def test_run_exit_command(
        self,
        mock_api_class,
        mock_repo_class,
        mock_output_class,
        mock_spinner_class,
        mock_processor_class,
        mock_tool_executor_class,
        config,
    ):
        """Test run loop exits on exit command."""
        mock_output = Mock()
        mock_output.get_user_input.side_effect = ["exit"]
        mock_output_class.return_value = mock_output

        orchestrator = ChatOrchestrator(config)
        orchestrator.run()

        mock_output.display_welcome.assert_called_once()
        mock_output.display_goodbye.assert_called_once()
        mock_output.get_user_input.assert_called_once()

    @patch("src.orchestrators.chat_orchestrator.ToolExecutor")
    @patch("src.orchestrators.chat_orchestrator.StreamResponseProcessor")
    @patch("src.orchestrators.chat_orchestrator.LoadingSpinner")
    @patch("src.orchestrators.chat_orchestrator.ConsoleOutput")
    @patch("src.orchestrators.chat_orchestrator.MessageRepository")
    @patch("src.orchestrators.chat_orchestrator.ChatApiService")
    def test_run_keyboard_interrupt(
        self,
        mock_api_class,
        mock_repo_class,
        mock_output_class,
        mock_spinner_class,
        mock_processor_class,
        mock_tool_executor_class,
        config,
    ):
        """Test run loop handles keyboard interrupt."""
        mock_output = Mock()
        mock_output.get_user_input.side_effect = KeyboardInterrupt()
        mock_output_class.return_value = mock_output

        orchestrator = ChatOrchestrator(config)
        orchestrator.run()

        mock_output.display_welcome.assert_called_once()
        mock_output.display_goodbye.assert_called_once()

    @patch("src.orchestrators.chat_orchestrator.ToolExecutor")
    @patch("src.orchestrators.chat_orchestrator.StreamResponseProcessor")
    @patch("src.orchestrators.chat_orchestrator.LoadingSpinner")
    @patch("src.orchestrators.chat_orchestrator.ConsoleOutput")
    @patch("src.orchestrators.chat_orchestrator.MessageRepository")
    @patch("src.orchestrators.chat_orchestrator.ChatApiService")
    def test_run_error_handling_continues_loop(
        self,
        mock_api_class,
        mock_repo_class,
        mock_output_class,
        mock_spinner_class,
        mock_processor_class,
        mock_tool_executor_class,
        config,
    ):
        """Test run loop continues after error."""
        mock_output = Mock()
        mock_output.get_user_input.side_effect = ["test", "exit"]
        mock_output_class.return_value = mock_output

        call_count = 0

        @contextmanager
        def _raise_once(_messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Error")
            yield iter([])

        mock_api = Mock()
        mock_api.streaming_completion = _raise_once
        mock_api_class.return_value = mock_api

        mock_repo = Mock()
        mock_repo.get_messages_for_api.return_value = []
        mock_repo_class.return_value = mock_repo

        orchestrator = ChatOrchestrator(config)
        orchestrator.run()

        # Should display error and continue
        mock_output.display_error.assert_called()
        assert mock_output.get_user_input.call_count == 2
        mock_output.display_goodbye.assert_called_once()

    @patch("src.orchestrators.chat_orchestrator.ToolExecutor")
    @patch("src.orchestrators.chat_orchestrator.StreamResponseProcessor")
    @patch("src.orchestrators.chat_orchestrator.LoadingSpinner")
    @patch("src.orchestrators.chat_orchestrator.ConsoleOutput")
    @patch("src.orchestrators.chat_orchestrator.MessageRepository")
    @patch("src.orchestrators.chat_orchestrator.ChatApiService")
    def test_run_skips_empty_input(
        self,
        mock_api_class,
        mock_repo_class,
        mock_output_class,
        mock_spinner_class,
        mock_processor_class,
        mock_tool_executor_class,
        config,
    ):
        """Test run loop skips empty input."""
        mock_output = Mock()
        mock_output.get_user_input.side_effect = ["", "exit"]
        mock_output_class.return_value = mock_output

        orchestrator = ChatOrchestrator(config)
        orchestrator.run()

        # Should skip empty input and exit on "exit"
        assert mock_output.get_user_input.call_count == 2
        mock_output.display_goodbye.assert_called_once()
