"""Validator agent: run pytest for legacy sample validation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

from migra_agent.agents.base_agent import AgentMessage, BaseAgent
from migra_agent.context import MigrationContext


class ValidatorAgent(BaseAgent):
    """Run tests and return validation feedback."""

    def __init__(self) -> None:
        super().__init__(name="ValidatorAgent")

    def run_tests(self, project_root: Path) -> Dict[str, Any]:
        """Run pytest on examples/test_legacy.py and capture output."""
        cmd = [sys.executable, "-m", "pytest", "examples/test_legacy.py", "-q"]
        proc = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "command": " ".join(cmd),
            "return_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "passed": proc.returncode == 0,
        }

    def process(self, message: AgentMessage, context: MigrationContext) -> AgentMessage:
        """Handle validation action."""
        if message.action != "validate":
            raise ValueError(f"Unsupported action for ValidatorAgent: {message.action}")

        result = self.run_tests(context.project_root)
        context.validation_result = result
        return self.send(receiver="Orchestrator", action="done", payload={"validation": result})

