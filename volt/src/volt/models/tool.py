from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Tool:
    name: str
    description: str
    category: str
    command: str
    binary: str = ""
    tags: list[str] = field(default_factory=list)
    documentation: str = ""
    installed: bool = False
    favorite: bool = False
    binary_path: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "command": self.command,
            "binary": self.binary or self.command,
            "tags": self.tags,
            "documentation": self.documentation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Tool:
        return cls(
            name=data["name"],
            description=data["description"],
            category=data["category"],
            command=data["command"],
            binary=data.get("binary", data["command"]),
            tags=data.get("tags", []),
            documentation=data.get("documentation", ""),
        )


@dataclass
class ExecutionRecord:
    tool_name: str
    command: str
    timestamp: str
    exit_code: int = -1
    duration: float = 0.0
