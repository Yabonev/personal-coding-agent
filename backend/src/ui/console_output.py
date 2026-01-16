"""Console output formatting and display."""

from __future__ import annotations

import sys
from typing import Protocol

from colorama import Fore
from colorama import Style


class OutputHandler(Protocol):
    """Protocol for output handlers (allows for different output strategies)."""

    def display_reasoning(self, content: str, is_first: bool) -> None:
        """Display reasoning content."""
        ...

    def display_content(
        self, content: str, is_first: bool, has_reasoning: bool
    ) -> None:
        """Display response content."""
        ...

    def display_error(self, message: str) -> None:
        """Display error message."""
        ...

    def display_info(self, message: str) -> None:
        """Display info message."""
        ...

    def display_goodbye(self) -> None:
        """Display goodbye message."""
        ...

    def display_welcome(self) -> None:
        """Display welcome message."""
        ...

    def get_user_input(self, prompt: str) -> str:
        """Get user input with formatted prompt."""
        ...

    def newline(self) -> None:
        """Print a newline."""
        ...

    def display_tool_call_start(self) -> None:
        """Display start of a tool call block (no-op for minimal UI)."""
        ...

    def display_tool_call_name(self, name: str) -> None:
        """Display tool call name (no-op for minimal UI)."""
        ...

    def display_tool_call(self, name: str, arguments: str) -> None:
        """Display tool call with name and arguments."""
        ...

    def display_tool_result(self, result: str, is_error: bool) -> None:
        """Display tool execution result."""
        ...


class ConsoleOutput:
    """Handles all console output formatting and display."""

    def display_reasoning(self, content: str, is_first: bool) -> None:
        """Display reasoning content with arrow, indented and greyed out."""
        if is_first:
            arrow = f"{Style.DIM}{Fore.CYAN}↪{Style.RESET_ALL}"
            thinking = f"{Style.DIM}{Fore.WHITE}Thinking{Style.RESET_ALL}"
            print(f"\n{arrow} {thinking}")
            print(
                f"{Style.DIM}{Fore.WHITE}    {content}{Style.RESET_ALL}",
                end="",
                flush=True,
            )
            return

        # Only indent newlines, not the first line
        indented_content = content.replace("\n", "\n    ")
        print(
            f"{Style.DIM}{Fore.WHITE}{indented_content}{Style.RESET_ALL}",
            end="",
            flush=True,
        )

    def display_content(
        self, content: str, is_first: bool, has_reasoning: bool
    ) -> None:
        """Display response content without arrow."""
        if is_first:
            # Add 2 newlines after thinking to separate content from reasoning
            if has_reasoning:
                print("\n\n", end="", flush=True)
            else:
                print("\n", end="", flush=True)
        print(f"{Fore.GREEN}{content}{Style.RESET_ALL}", end="", flush=True)

    def display_error(self, message: str) -> None:
        """Display error message."""
        print(f"\n{Fore.RED}Error: {message}{Style.RESET_ALL}", file=sys.stderr)

    def display_info(self, message: str) -> None:
        """Display info message."""
        print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")

    def display_goodbye(self) -> None:
        """Display goodbye message."""
        print(f"\n{Fore.CYAN}➤{Style.RESET_ALL} {Fore.GREEN}Bye!{Style.RESET_ALL}")

    def display_welcome(self) -> None:
        """Display welcome message."""
        print(f"{Fore.CYAN}Chat started. Type 'exit' to quit.{Style.RESET_ALL}\n")

    def get_user_input(self, prompt: str) -> str:  # noqa: ARG002
        """Get user input with formatted prompt."""
        return input(f"\n{Fore.BLUE}User:{Style.RESET_ALL} ").strip()

    def newline(self) -> None:
        """Print a newline."""
        print()

    def display_tool_call_start(self) -> None:
        """Display start of a tool call block (no-op for minimal UI)."""

    def display_tool_call_name(self, name: str) -> None:
        """Display tool call name (no-op for minimal UI)."""
        _ = name

    def display_tool_call(self, name: str, arguments: str) -> None:
        """Display tool call with name and arguments."""
        if arguments.strip() in ("", "{}"):
            print(f"\n{Fore.CYAN}⚡ {name}{Style.RESET_ALL}()")
        else:
            args_styled = f"{Style.DIM}{arguments}{Style.RESET_ALL}"
            print(f"\n{Fore.CYAN}⚡ {name}{Style.RESET_ALL}({args_styled})")

    def display_tool_result(self, result: str, is_error: bool) -> None:
        """Display tool execution result."""
        if is_error:
            print(f"   {Fore.RED}✗ {result}{Style.RESET_ALL}")
        else:
            print(f"   {Fore.GREEN}→ {result}{Style.RESET_ALL}")
