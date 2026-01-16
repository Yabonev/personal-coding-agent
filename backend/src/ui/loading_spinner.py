"""Loading spinner UI component."""

from __future__ import annotations

import threading
import time

from colorama import Fore
from colorama import Style


class LoadingSpinner:
    """Simple loading spinner animation."""

    def __init__(self) -> None:
        """Initialize the loading spinner."""
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.running = False
        self.thread: threading.Thread | None = None

    def _animate(self) -> None:
        """Animation loop."""
        while self.running:
            char = self.spinner_chars[self.spinner_index % len(self.spinner_chars)]
            print(
                f"\r{Fore.CYAN}{char}{Style.RESET_ALL} Processing", end="", flush=True
            )
            self.spinner_index += 1
            time.sleep(0.1)

    def start(self) -> None:
        """Start the spinner animation."""
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Stop the spinner and clear the line."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.2)
        print("\r" + " " * 50 + "\r", end="", flush=True)
