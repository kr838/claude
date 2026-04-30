"""Base agent contract and message definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from migra_agent.context import MigrationContext


@dataclass
class AgentMessage:
    """Message object exchanged between agents."""

    sender: str
    receiver: str
    action: str
    payload: Dict[str, Any]


class BaseAgent:
    """Base class for all agents in the migration pipeline."""

    def __init__(self, name: str) -> None:
        self.name = name

    def process(self, message: AgentMessage, context: MigrationContext) -> AgentMessage:
        """Process incoming message and return outgoing message."""
        raise NotImplementedError("Agent must implement process().")

    def send(self, receiver: str, action: str, payload: Dict[str, Any]) -> AgentMessage:
        """Create an outbound message."""
        return AgentMessage(sender=self.name, receiver=receiver, action=action, payload=payload)

