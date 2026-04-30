"""Basic unit tests for MigraAgent agents."""

from __future__ import annotations

from pathlib import Path

from migra_agent.agents.base_agent import AgentMessage
from migra_agent.agents.refactor_agent import RefactorAgent
from migra_agent.agents.risk_agent import RiskAgent
from migra_agent.agents.scanner_agent import ScannerAgent
from migra_agent.context import MigrationContext


def test_scanner_detects_deprecated_calls() -> None:
    scanner = ScannerAgent()
    file_path = Path("examples/legacy_code.py").resolve()
    result = scanner.scan_file(file_path)
    assert "compute_invoice_total" in result["functions"]
    assert "deprecated_hits" in result
    assert "old_finance_calc" in str(result["deprecated_hits"])


def test_risk_reasoning_returns_score() -> None:
    risk = RiskAgent()
    graph = {
        "process_order": ["compute_invoice_total", "build_report_line"],
        "compute_invoice_total": ["old_finance_calc", "deprecated_logger"],
        "build_report_line": ["deprecated_logger"],
        "old_finance_calc": [],
        "deprecated_logger": [],
    }
    report = risk.long_chain_reasoning(graph, "old_finance_calc", {"compute_invoice_total"})
    assert report["score"]["total"] >= 0
    assert report["score"]["level"] in {"LOW", "MEDIUM", "HIGH"}


def test_refactor_generates_adapter_code() -> None:
    agent = RefactorAgent()
    code = agent.generate_adapter_code(["old_finance_calc", "deprecated_logger"])
    assert "class LegacyAdapter" in code
    assert "def old_finance_calc" in code
    assert "def deprecated_logger" in code


def test_agent_pipeline_messages() -> None:
    context = MigrationContext(
        project_root=Path(".").resolve(),
        legacy_file=Path("examples/legacy_code.py").resolve(),
    )
    scanner = ScannerAgent()
    message = AgentMessage(
        sender="Orchestrator",
        receiver="ScannerAgent",
        action="scan",
        payload={"target_file": str(context.legacy_file)},
    )
    out = scanner.process(message, context)
    assert out.receiver == "RiskAgent"
    assert out.action == "assess_risk"

