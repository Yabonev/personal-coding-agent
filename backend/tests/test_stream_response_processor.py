"""Tests for StreamResponseProcessor."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.processors.stream_response_processor import StreamResponseProcessor
from src.services.message_repository import MessageRepository


class MockChunk:
    """Mock chunk for testing."""

    def __init__(self, reasoning_content=None, content=None, tool_calls=None):
        self.choices = []
        if (
            reasoning_content is not None
            or content is not None
            or tool_calls is not None
        ):
            choice = Mock()
            delta = Mock()
            delta.reasoning_content = reasoning_content
            delta.content = content
            delta.tool_calls = tool_calls
            choice.delta = delta
            self.choices = [choice]


class TestStreamResponseProcessor:
    """Tests for StreamResponseProcessor."""

    def test_processes_reasoning_chunks(self, mock_output_handler, mock_spinner):
        """Test processing reasoning chunks."""
        repo = MessageRepository("System")
        processor = StreamResponseProcessor(repo, mock_output_handler, mock_spinner)

        chunks = [
            MockChunk(reasoning_content="thinking"),
            MockChunk(reasoning_content=" more"),
        ]

        processor.process(iter(chunks))

        mock_spinner.stop.assert_called()
        assert mock_output_handler.display_reasoning.call_count == 2
        mock_output_handler.display_reasoning.assert_any_call("thinking", True)
        mock_output_handler.display_reasoning.assert_any_call(" more", False)

    def test_processes_content_chunks(self, mock_output_handler, mock_spinner):
        """Test processing content chunks."""
        repo = MessageRepository("System")
        processor = StreamResponseProcessor(repo, mock_output_handler, mock_spinner)

        chunks = [MockChunk(content="Hello"), MockChunk(content=" world")]

        processor.process(iter(chunks))

        mock_spinner.stop.assert_called()
        assert mock_output_handler.display_content.call_count == 2
        mock_output_handler.display_content.assert_any_call("Hello", True, False)
        mock_output_handler.display_content.assert_any_call(" world", False, False)

    def test_processes_mixed_reasoning_and_content(
        self, mock_output_handler, mock_spinner
    ):
        """Test processing both reasoning and content."""
        repo = MessageRepository("System")
        processor = StreamResponseProcessor(repo, mock_output_handler, mock_spinner)

        chunks = [MockChunk(reasoning_content="thinking"), MockChunk(content="answer")]

        processor.process(iter(chunks))

        mock_spinner.stop.assert_called()
        mock_output_handler.display_reasoning.assert_called_once_with("thinking", True)
        mock_output_handler.display_content.assert_called_once_with(
            "answer", True, True
        )
        mock_output_handler.newline.assert_called_once()

    def test_stops_spinner_on_reasoning(self, mock_output_handler, mock_spinner):
        """Test spinner stops when reasoning starts."""
        repo = MessageRepository("System")
        processor = StreamResponseProcessor(repo, mock_output_handler, mock_spinner)

        chunks = [MockChunk(reasoning_content="thinking")]

        processor.process(iter(chunks))

        # Spinner should stop when reasoning starts
        assert mock_spinner.stop.call_count >= 1

    def test_stops_spinner_on_content_without_reasoning(
        self, mock_output_handler, mock_spinner
    ):
        """Test spinner stops when content starts without reasoning."""
        repo = MessageRepository("System")
        processor = StreamResponseProcessor(repo, mock_output_handler, mock_spinner)

        chunks = [MockChunk(content="answer")]

        processor.process(iter(chunks))

        mock_spinner.stop.assert_called()

    def test_updates_message_repository(self, mock_output_handler, mock_spinner):
        """Test processor updates message repository with full content."""
        repo = MessageRepository("System")
        processor = StreamResponseProcessor(repo, mock_output_handler, mock_spinner)

        chunks = [MockChunk(content="Hello"), MockChunk(content=" world")]

        processor.process(iter(chunks))

        messages = repo.get_all_messages()
        assert len(messages) == 2
        assert messages[-1].content == "Hello world"

    def test_handles_empty_chunks(self, mock_output_handler, mock_spinner):
        """Test processor handles chunks without choices."""
        repo = MessageRepository("System")
        processor = StreamResponseProcessor(repo, mock_output_handler, mock_spinner)

        chunks = [MockChunk()]  # No choices

        processor.process(iter(chunks))

        # Should not crash, spinner should stop
        mock_spinner.stop.assert_called()
        mock_output_handler.newline.assert_called_once()

    def test_handles_empty_response(self, mock_output_handler, mock_spinner):
        """Test processor handles empty response."""
        repo = MessageRepository("System")
        processor = StreamResponseProcessor(repo, mock_output_handler, mock_spinner)

        chunks = []

        processor.process(iter(chunks))

        mock_spinner.stop.assert_called()
        mock_output_handler.newline.assert_called_once()
        # Should not add message if no content
        assert len(repo.get_all_messages()) == 1  # Only system message

    def test_handles_multiline_content(self, mock_output_handler, mock_spinner):
        """Test processor handles multiline content."""
        repo = MessageRepository("System")
        processor = StreamResponseProcessor(repo, mock_output_handler, mock_spinner)

        chunks = [MockChunk(content="Line 1\n"), MockChunk(content="Line 2")]

        processor.process(iter(chunks))

        messages = repo.get_all_messages()
        assert messages[-1].content == "Line 1\nLine 2"

    def test_error_handling_stops_spinner(self, mock_output_handler, mock_spinner):
        """Test error handling stops spinner and displays error."""
        repo = MessageRepository("System")
        processor = StreamResponseProcessor(repo, mock_output_handler, mock_spinner)

        def failing_chunks():
            yield MockChunk(content="test")
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            processor.process(failing_chunks())

        mock_spinner.stop.assert_called()
        mock_output_handler.display_error.assert_called_once()
        assert "Error processing response" in str(
            mock_output_handler.display_error.call_args
        )
