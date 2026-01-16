"""Main entry point for the personal coding agent."""

from __future__ import annotations

import sys

from colorama import init

from src.config.config_service import ConfigService
from src.orchestrators.chat_orchestrator import ChatOrchestrator
from pathlib import Path

from src.tracing import SSEServer
from src.tracing import TracingConfig

init(autoreset=True)


def main() -> None:
    """Main application entry point."""
    sse_server: SSEServer | None = None

    try:
        config_service = ConfigService()

        tracing_config = TracingConfig.sqlite(sse_enabled=True)
        sse_server = SSEServer(port=8765, db_path=Path(tracing_config.sqlite_path))
        sse_server.start()
        print(f"Trace viewer: {sse_server.url}")

        config = config_service.create_chat_config(tracing=tracing_config)

        orchestrator = ChatOrchestrator(config)
        orchestrator.run()

    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if sse_server is not None:
            sse_server.stop()


if __name__ == "__main__":
    main()
