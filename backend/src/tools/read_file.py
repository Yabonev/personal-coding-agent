"""Read file tool."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field

from .base import BaseTool
from .errors import ToolError


def _get_importers(file_path: Path) -> list[str]:
    """Get non-test files that import this module using tldr.

    Args:
        file_path: Path to the file

    Returns:
        List of file paths that import this module (excluding tests)
    """
    module_name = file_path.stem
    if module_name == "__init__":
        module_name = file_path.parent.name

    try:
        result = subprocess.run(  # noqa: S603
            ["tldr", "importers", module_name, "."],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    if result.returncode != 0:
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    importers: list[str] = []
    for item in data.get("importers", []):
        file = item.get("file", "")
        is_test = file.startswith("tests/") or "test_" in file
        if file and not is_test and file not in importers:
            importers.append(file)
    return importers


class ReadFileArgs(BaseModel):
    """Arguments for the read file tool."""

    path: str = Field(
        description="Absolute path to the file to read.",
    )
    start_line: int = Field(
        default=1,
        ge=1,
        description="First line to read (1-indexed, inclusive).",
    )
    end_line: int | None = Field(
        default=None,
        ge=1,
        description="Last line to read (inclusive). Reads to end if not set.",
    )


class ReadFileTool(BaseTool[ReadFileArgs]):
    """Read contents of a file."""

    @property
    def name(self) -> str:
        """Tool name used in API calls."""
        return "read_file"

    @property
    def description(self) -> str:
        """Human-readable description for the LLM."""
        return "Read the contents of a file. Supports reading specific line ranges."

    @property
    def args_model(self) -> type[ReadFileArgs]:
        """Pydantic model class for arguments."""
        return ReadFileArgs

    def execute(self, args: ReadFileArgs) -> str:
        """Read file contents.

        Args:
            args: Validated arguments with path and optional line range

        Returns:
            File contents with line numbers prefixed

        Raises:
            ToolError: If file not found, not a file, or not readable
        """
        file_path = Path(args.path)

        if not file_path.is_absolute():
            msg = f"Path must be absolute. Got '{args.path}'."
            raise ToolError(msg)

        if not file_path.exists():
            msg = f"File '{args.path}' not found. Check the path exists."
            raise ToolError(msg)

        if not file_path.is_file():
            msg = f"Path '{args.path}' is not a file. Use a file path."
            raise ToolError(msg)

        try:
            content = file_path.read_text(encoding="utf-8")
        except PermissionError as e:
            msg = f"Permission denied reading '{args.path}'."
            raise ToolError(msg) from e
        except UnicodeDecodeError as e:
            msg = f"File '{args.path}' is not valid UTF-8 text."
            raise ToolError(msg) from e

        lines = content.splitlines()
        total_lines = len(lines)

        start_idx = args.start_line - 1
        end_idx = args.end_line if args.end_line else total_lines

        if start_idx >= total_lines:
            msg = f"Start line {args.start_line} exceeds file length ({total_lines})."
            raise ToolError(msg)

        selected_lines = lines[start_idx:end_idx]
        numbered_lines = [
            f"{i}: {line}"
            for i, line in enumerate(selected_lines, start=args.start_line)
        ]

        header = f"[file: {args.path}]\n"
        if args.end_line or args.start_line > 1:
            actual_end = min(end_idx, total_lines)
            header += f"[lines: {args.start_line}-{actual_end} of {total_lines}]\n"

        importers = _get_importers(file_path)
        if importers:
            header += f"[used_by: {', '.join(importers)}]\n"

        return header + "\n" + "\n".join(numbered_lines)
