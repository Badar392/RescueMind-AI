"""Shared state passed between RescueMind AI agents.

The context is intentionally JSON-serializable so it can be stored in
AgentExecution.output_json and rendered by the Streamlit dashboard.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IncidentContext:
    incident_id: int
    incident_code: str
    description: str
    requested_category: str
    location_text: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    agent_trace: list[dict[str, Any]] = field(default_factory=list)

    def put(self, key: str, value: Any) -> None:
        self.data[key] = value

    def warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)

    def snapshot(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "incident_code": self.incident_code,
            "data": self.data,
            "warnings": self.warnings,
            "agent_trace": self.agent_trace,
        }
