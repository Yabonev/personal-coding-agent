"""Tests for ConsoleOutput."""

from __future__ import annotations

from io import StringIO
from unittest.mock import patch

from src.ui.console_output import ConsoleOutput


class TestConsoleOutput:
    """Tests for ConsoleOutput."""

    def test_display_reasoning_first(self):
        """Test displaying first reasoning content."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_reasoning("thinking...", is_first=True)
            result = fake_out.getvalue()

            assert "Thinking" in result
            assert "thinking..." in result

    def test_display_reasoning_subsequent(self):
        """Test displaying subsequent reasoning content."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_reasoning("more thinking", is_first=False)
            result = fake_out.getvalue()

            assert "more thinking" in result

    def test_display_reasoning_indents_newlines(self):
        """Test reasoning content indents newlines."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_reasoning("line1\nline2", is_first=False)
            result = fake_out.getvalue()

            assert "line1" in result
            assert "    line2" in result

    def test_display_content_first_with_reasoning(self):
        """Test displaying first content after reasoning."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_content("answer", is_first=True, has_reasoning=True)
            result = fake_out.getvalue()

            assert "\n\n" in result  # Should have double newline
            assert "answer" in result

    def test_display_content_first_without_reasoning(self):
        """Test displaying first content without reasoning."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_content("answer", is_first=True, has_reasoning=False)
            result = fake_out.getvalue()

            assert result.startswith("\n")  # Should have single newline
            assert "answer" in result

    def test_display_content_subsequent(self):
        """Test displaying subsequent content."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_content("more", is_first=False, has_reasoning=False)
            result = fake_out.getvalue()

            assert "more" in result

    def test_display_error(self):
        """Test displaying error message."""
        output = ConsoleOutput()

        with patch("sys.stderr", new=StringIO()) as fake_err:
            output.display_error("Something went wrong")
            result = fake_err.getvalue()

            assert "Error:" in result
            assert "Something went wrong" in result

    def test_display_info(self):
        """Test displaying info message."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_info("Information")
            result = fake_out.getvalue()

            assert "Information" in result

    def test_display_goodbye(self):
        """Test displaying goodbye message."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_goodbye()
            result = fake_out.getvalue()

            assert "Bye!" in result

    def test_display_welcome(self):
        """Test displaying welcome message."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_welcome()
            result = fake_out.getvalue()

            assert "Chat started" in result
            assert "exit" in result.lower()

    @patch("builtins.input")
    def test_get_user_input(self, mock_input):
        """Test getting user input."""
        mock_input.return_value = "  test input  "
        output = ConsoleOutput()

        result = output.get_user_input("")

        assert result == "test input"  # Should be stripped
        mock_input.assert_called_once()

    def test_newline(self):
        """Test printing newline."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.newline()
            result = fake_out.getvalue()

            assert result == "\n"

    def test_display_tool_call_start_is_noop(self):
        """Test tool call start is a no-op."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_tool_call_start()
            result = fake_out.getvalue()

            assert result == ""

    def test_display_tool_call_name_is_noop(self):
        """Test tool call name is a no-op."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_tool_call_name("get_time")
            result = fake_out.getvalue()

            assert result == ""

    def test_display_tool_call_with_arguments(self):
        """Test displaying tool call with arguments."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_tool_call("get_weather", '{"city": "NYC"}')
            result = fake_out.getvalue()

            assert "get_weather" in result
            assert '{"city": "NYC"}' in result
            assert "⚡" in result

    def test_display_tool_call_empty_arguments(self):
        """Test displaying tool call with empty arguments shows no braces."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_tool_call("get_time", "{}")
            result = fake_out.getvalue()

            assert "get_time" in result
            assert "()" in result
            assert "{}" not in result

    def test_display_tool_call_blank_arguments(self):
        """Test displaying tool call with blank arguments shows no braces."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_tool_call("get_time", "")
            result = fake_out.getvalue()

            assert "get_time" in result
            assert "()" in result

    def test_display_tool_result_success(self):
        """Test displaying successful tool result."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_tool_result("2024-01-15T10:30:00Z", is_error=False)
            result = fake_out.getvalue()

            assert "2024-01-15T10:30:00Z" in result
            assert "→" in result

    def test_display_tool_result_error(self):
        """Test displaying error tool result."""
        output = ConsoleOutput()

        with patch("sys.stdout", new=StringIO()) as fake_out:
            output.display_tool_result("Connection failed", is_error=True)
            result = fake_out.getvalue()

            assert "Connection failed" in result
            assert "✗" in result
