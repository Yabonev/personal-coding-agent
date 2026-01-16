"""Base class for all tools."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from pydantic import BaseModel


class EmptyArgs(BaseModel):
    """Empty arguments model for tools that take no arguments."""


class BaseTool[ArgsT: BaseModel](ABC):
    """Base class for all tools.

    Each tool must define:
    - name: The tool name used in API calls
    - description: Human-readable description for the LLM
    - args_model: Pydantic model class for arguments
    - execute: The implementation that receives validated arguments
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name used in API calls."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for the LLM."""
        ...

    @property
    @abstractmethod
    def args_model(self) -> type[ArgsT]:
        """Pydantic model class for arguments."""
        ...

    @property
    def schema(self) -> dict[str, object]:
        """OpenAI-compatible tool definition for the API.

        Auto-generated from the Pydantic args_model.
        """
        json_schema = self.args_model.model_json_schema()

        # Extract properties and required fields from Pydantic schema
        properties = json_schema.get("properties", {})
        required = json_schema.get("required", [])

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def parse_arguments(self, arguments: dict[str, object]) -> ArgsT:
        """Parse and validate arguments using the Pydantic model.

        Args:
            arguments: Raw arguments dict from JSON

        Returns:
            Validated Pydantic model instance

        Raises:
            pydantic.ValidationError: If validation fails
        """
        return self.args_model.model_validate(arguments)

    @abstractmethod
    def execute(self, args: ArgsT) -> str:
        """Execute the tool with validated arguments.

        Args:
            args: Validated Pydantic model instance

        Returns:
            String result to return to the model

        Raises:
            Exception: Tool-specific errors (caught by executor)
        """
        ...
