"""Base tool infrastructure — dual API format support."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Unified result type for all tools."""
    success: bool
    data: dict = field(default_factory=dict)
    error: str = ""
    tool_name: str = ""

    def to_anthropic(self) -> dict:
        """Format for Anthropic tool_result blocks."""
        if self.success:
            return {"type": "tool_result", "content": str(self.data)}
        return {"type": "tool_result", "is_error": True, "content": self.error}

    def to_openai(self) -> dict:
        """Format for OpenAI function call responses."""
        if self.success:
            return {"role": "tool", "content": str(self.data)}
        return {"role": "tool", "content": f"Error: {self.error}"}


class BaseTool:
    """Abstract base for all nanobot tools."""
    name: str = ""
    description: str = ""
    parameters_schema: dict = {}

    def run(self, **kwargs: Any) -> ToolResult:
        raise NotImplementedError

    def to_anthropic_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters_schema,
        }

    def to_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }
