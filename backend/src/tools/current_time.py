"""Current time tool."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from pydantic import Field

from .base import BaseTool
from .errors import ToolError


class CurrentTimeArgs(BaseModel):
    """Arguments for the current time tool."""

    timezone: str = Field(
        default="UTC",
        description="IANA timezone, e.g. 'UTC', 'America/New_York'.",
    )


class CurrentTimeTool(BaseTool[CurrentTimeArgs]):
    """Get current time for a timezone."""

    @property
    def name(self) -> str:
        """Tool name used in API calls."""
        return "get_current_time"

    @property
    def description(self) -> str:
        """Human-readable description for the LLM."""
        return "Get the current time for a given IANA timezone."

    @property
    def args_model(self) -> type[CurrentTimeArgs]:
        """Pydantic model class for arguments."""
        return CurrentTimeArgs

    def execute(self, args: CurrentTimeArgs) -> str:
        """Get current time for a timezone.

        Args:
            args: Validated arguments with timezone

        Returns:
            Formatted datetime string

        Raises:
            ValueError: If timezone is invalid
        """
        try:
            tz = ZoneInfo(args.timezone)
        except Exception as e:
            msg = (
                f"Invalid timezone '{args.timezone}'. "
                "Use IANA format like 'UTC' or 'America/New_York'."
            )
            raise ToolError(msg) from e

        now = datetime.now(tz)
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")
