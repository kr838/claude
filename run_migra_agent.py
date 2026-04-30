"""Main entrypoint to run MigraAgent migration pipeline."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Dict, List, Set

from migra_agent.agents.base_agent import AgentMessage
from migra_agent.agents.refactor_agent import RefactorAgent
from migra_agent.agents.risk_agent import RiskAgent
from migra_agent.agents.scanner_agent import ScannerAgent
from migra_agent.agents.validator_agent import ValidatorAgent
from migra_agent.context import MigrationContext


def extract_tested_functions(test_file: Path) -> Set[str]:
    """Extract function names called in test file as a simple coverage proxy."""
    if not test_file.exists():
        return set()

    tree = ast.parse(test_file.read_text(encoding="utf-8"), filename=str(test_file))
    called: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    return called


def print_scan_summary(scan_result: Dict[str, object]) -> None:
    print("\n=== 扫描结果 ===")
    print(f"目标文件: {scan_result.get('file')}")
    print(f"函数 API 清单: {scan_result.get('api_list')}")
    print(f"类清单: {scan_result.get('classes')}")
    print(f"过时 API 命中: {scan_result.get('deprecated_hits')}")


def main() -> None:
    project_root = Path(__file__).resolve().parent
    legacy_file = project_root / "examples" / "legacy_code.py"
    test_file = project_root / "examples" / "test_legacy.py"
    report_file = project_root / "examples" / "risk_report.json"

    context = MigrationContext(project_root=project_root, legacy_file=legacy_file)

    scanner = ScannerAgent()
    risk = RiskAgent()
    refactor = RefactorAgent()
    validator = ValidatorAgent()

    scan_msg = AgentMessage(
        sender="Orchestrator",
        receiver="ScannerAgent",
        action="scan",
        payload={"target_file": str(legacy_file)},
    )

    risk_msg = scanner.process(scan_msg, context)
    context.scan_result["test_functions"] = sorted(extract_tested_functions(test_file))
    print_scan_summary(context.scan_result)

    print("\n=== 风险推理过程 ===")
    refactor_msg = risk.process(risk_msg, context)
    RiskAgent.save_report(context.risk_reports, report_file)

    print("\n=== 风险报告（JSON） ===")
    print(json.dumps(context.risk_reports, ensure_ascii=False, indent=2))
    print(f"风险报告已写入: {report_file}")

    validate_msg = refactor.process(refactor_msg, context)

    print("\n=== 生成的适配器文件 ===")
    for generated in context.generated_files:
        print(f"- {generated}")
        print(generated.read_text(encoding='utf-8'))

    final_msg = validator.process(validate_msg, context)
    validation = final_msg.payload["validation"]

    print("\n=== 验证结果 ===")
    print(f"命令: {validation['command']}")
    print(f"返回码: {validation['return_code']}")
    if validation["stdout"]:
        print(validation["stdout"])
    if validation["stderr"]:
        print(validation["stderr"])
    print(f"测试通过: {validation['passed']}")


if __name__ == "__main__":
    main()

