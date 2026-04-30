"""Scanner agent: parse legacy code and extract structural metadata."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List, Set

from migra_agent.agents.base_agent import AgentMessage, BaseAgent
from migra_agent.context import MigrationContext


DEPRECATED_APIS: Set[str] = {"old_finance_calc", "deprecated_logger"}


class _ScannerVisitor(ast.NodeVisitor):
    """AST visitor used by ScannerAgent."""

    def __init__(self) -> None:
        self.functions: Dict[str, List[str]] = {}
        self.classes: List[str] = []
        self.current_function: str | None = None
        self.external_calls: Set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        self.classes.append(node.name)
        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        prev = self.current_function
        self.current_function = node.name
        self.functions.setdefault(node.name, [])
        self.generic_visit(node)
        self.current_function = prev
        return None

    def visit_Call(self, node: ast.Call) -> Any:
        called_name = self._resolve_call_name(node.func)
        if called_name:
            if self.current_function is not None:
                self.functions.setdefault(self.current_function, []).append(called_name)
            else:
                self.external_calls.add(called_name)
        return self.generic_visit(node)

    @staticmethod
    def _resolve_call_name(call_node: ast.AST) -> str | None:
        if isinstance(call_node, ast.Name):
            return call_node.id
        if isinstance(call_node, ast.Attribute):
            return call_node.attr
        return None


class ScannerAgent(BaseAgent):
    """Scan a python file and summarize APIs/calls."""

    def __init__(self) -> None:
        super().__init__(name="ScannerAgent")

    def scan_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze target Python file with AST."""
        if not file_path.exists():
            raise FileNotFoundError(f"Legacy file not found: {file_path}")

        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
        visitor = _ScannerVisitor()
        visitor.visit(tree)

        deprecated_hits: Dict[str, List[str]] = {}
        for fn_name, calls in visitor.functions.items():
            hits = [call for call in calls if call in DEPRECATED_APIS]
            if hits:
                deprecated_hits[fn_name] = hits

        return {
            "file": str(file_path),
            "functions": visitor.functions,
            "classes": visitor.classes,
            "external_calls": sorted(visitor.external_calls),
            "deprecated_hits": deprecated_hits,
            "api_list": sorted(visitor.functions.keys()),
        }

    def process(self, message: AgentMessage, context: MigrationContext) -> AgentMessage:
        """Handle scan action and update context."""
        if message.action != "scan":
            raise ValueError(f"Unsupported action for ScannerAgent: {message.action}")

        target = message.payload.get("target_file")
        if not target:
            raise ValueError("ScannerAgent requires payload['target_file'].")

        result = self.scan_file(Path(target))
        context.scan_result = result

        return self.send(
            receiver="RiskAgent",
            action="assess_risk",
            payload={"scan_result": result},
        )

