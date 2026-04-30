"""Refactor agent: generate compatibility adapters for deprecated APIs."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List

from migra_agent.agents.base_agent import AgentMessage, BaseAgent
from migra_agent.context import MigrationContext


class RefactorAgent(BaseAgent):
    """Generate adapter wrappers for legacy APIs."""

    def __init__(self) -> None:
        super().__init__(name="RefactorAgent")

    def generate_adapter_code(self, target_functions: List[str]) -> str:
        """Generate Python adapter module content for target functions."""
        functions_block = []
        for fn in target_functions:
            if fn == "old_finance_calc":
                functions_block.append(
                    """
@staticmethod
def old_finance_calc(x: float, y: float) -> float:
    \"\"\"Compatibility adapter for legacy old_finance_calc.\"\"\"
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise TypeError("old_finance_calc expects numeric inputs.")
    print("[Adapter] old_finance_calc is deprecated; routing to modern_finance_calc.")
    return modern_finance_calc(float(x), float(y))
"""
                )
            elif fn == "deprecated_logger":
                functions_block.append(
                    """
@staticmethod
def deprecated_logger(message: str) -> None:
    \"\"\"Compatibility adapter for legacy deprecated_logger.\"\"\"
    if not isinstance(message, str):
        raise TypeError("deprecated_logger expects a string message.")
    print("[Adapter] deprecated_logger mapped to modern_logger")
    modern_logger(message)
"""
                )
            else:
                functions_block.append(
                    f"""
@staticmethod
def {fn}(*args, **kwargs):
    \"\"\"Generic adapter placeholder for {fn}.\"\"\"
    print("[Adapter] {fn} currently uses pass-through strategy.")
    raise NotImplementedError("No concrete adapter strategy for {fn}.")
"""
                )

        body = "\n".join(functions_block).strip()
        return f'''"""Auto-generated migration adapters by MigraAgent."""

from __future__ import annotations

from typing import Any


def modern_finance_calc(x: float, y: float) -> float:
    """Modern replacement for old_finance_calc."""
    # Example policy adjustment: preserve old behavior baseline with explicit float math.
    return (x + y) * 1.02


def modern_logger(message: str) -> None:
    """Modern logger replacement."""
    print(f"[ModernLogger] {{message}}")


class LegacyAdapter:
    """Namespace style adapter holder for legacy APIs."""

{self._indent_block(body, 4)}
'''

    @staticmethod
    def _indent_block(content: str, spaces: int) -> str:
        pad = " " * spaces
        return "\n".join(f"{pad}{line}" if line.strip() else line for line in content.splitlines())

    @staticmethod
    def _extract_function_defs(file_path: Path) -> List[str]:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
        return [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]

    def process(self, message: AgentMessage, context: MigrationContext) -> AgentMessage:
        """Generate adapter module and save to examples directory."""
        if message.action != "generate_refactor":
            raise ValueError(f"Unsupported action for RefactorAgent: {message.action}")

        risk_reports = message.payload.get("risk_reports") or context.risk_reports
        if not risk_reports:
            raise ValueError("RefactorAgent requires risk reports.")

        targets = sorted(risk_reports.keys())
        code = self.generate_adapter_code(targets)

        output_file = context.project_root / "examples" / "migrated_adapter.py"
        output_file.write_text(code, encoding="utf-8")
        context.generated_files.append(output_file)

        return self.send(
            receiver="ValidatorAgent",
            action="validate",
            payload={"generated_adapter": str(output_file), "targets": targets},
        )

