"""Random date tool."""

from __future__ import annotations

import secrets
from datetime import date
from datetime import timedelta

from pydantic import BaseModel
from pydantic import Field

from .base import BaseTool


class RandomDateArgs(BaseModel):
    """Arguments for the random date tool."""

    start_year: int = Field(
        default=2000,
        description="Start year for random date range (inclusive).",
    )
    end_year: int = Field(
        default=2030,
        description="End year for random date range (inclusive).",
    )


class RandomDateTool(BaseTool[RandomDateArgs]):
    """Generate a random date within a year range."""

    @property
    def name(self) -> str:
        """Tool name used in API calls."""
        return "get_random_date"

    @property
    def description(self) -> str:
        """Human-readable description for the LLM."""
        return "Generate a random date within a specified year range."

    @property
    def args_model(self) -> type[RandomDateArgs]:
        """Pydantic model class for arguments."""
        return RandomDateArgs

    def execute(self, args: RandomDateArgs) -> str:
        """Generate a random date.

        Args:
            args: Validated arguments with year range

        Returns:
            Random date in ISO format (YYYY-MM-DD)
        """
        start_date = date(args.start_year, 1, 1)
        end_date = date(args.end_year, 12, 31)

        days_between = (end_date - start_date).days
        random_days = secrets.randbelow(days_between + 1)
        random_date = start_date + timedelta(days=random_days)

        return random_date.isoformat()
