"""Risk agent with long-chain reasoning on call graph."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set

from migra_agent.agents.base_agent import AgentMessage, BaseAgent
from migra_agent.context import MigrationContext
from migra_agent.graph.call_graph_builder import CallGraphBuilder


@dataclass
class RiskScore:
    """Risk score components."""

    direct_change_complexity: float
    downstream_impact: float
    test_gap: float
    total: float
    level: str


class RiskAgent(BaseAgent):
    """Assess migration risk using call graph traversal and weighted scoring."""

    def __init__(self) -> None:
        super().__init__(name="RiskAgent")
        self.graph_builder = CallGraphBuilder()

    def long_chain_reasoning(
        self,
        call_graph: Dict[str, List[str]],
        target_api: str,
        test_functions: Set[str] | None = None,
    ) -> Dict[str, Any]:
        """
        Run multi-step reasoning chain for a target API risk assessment.

        Steps:
        1. Direct neighborhood inspection (callers/callees).
        2. DFS downstream impact analysis.
        3. DFS upstream propagation analysis.
        4. Test coverage gap estimation.
        5. Weighted risk aggregation.
        """
        if target_api not in call_graph:
            raise ValueError(f"target_api '{target_api}' not present in call graph.")

        test_functions = test_functions or set()
        reverse_graph = self.graph_builder.reverse_edges(call_graph)

        direct_callees = call_graph.get(target_api, [])
        direct_callers = reverse_graph.get(target_api, [])
        direct_degree = len(set(direct_callees + direct_callers))

        print(
            f"Step 1: 分析函数 {target_api} 的直接关系 -> "
            f"callers={direct_callers}, callees={direct_callees}, degree={direct_degree}"
        )

        downstream_nodes = self._dfs(call_graph, target_api)
        downstream_nodes.discard(target_api)
        print(
            f"Step 2: 下游传播分析 -> {target_api} 影响函数: "
            f"{sorted(downstream_nodes)} (count={len(downstream_nodes)})"
        )

        upstream_nodes = self._dfs(reverse_graph, target_api)
        upstream_nodes.discard(target_api)
        print(
            f"Step 3: 上游入口追溯 -> 调用 {target_api} 的链路函数: "
            f"{sorted(upstream_nodes)} (count={len(upstream_nodes)})"
        )

        all_affected = set(downstream_nodes) | set(upstream_nodes) | {target_api}
        tested_affected = {fn for fn in all_affected if fn in test_functions}
        uncovered = all_affected - tested_affected
        print(
            "Step 4: 测试覆盖缺口估算 -> "
            f"affected={len(all_affected)}, covered={len(tested_affected)}, uncovered={len(uncovered)}"
        )

        direct_score = min(100.0, direct_degree * 20.0)
        downstream_score = min(100.0, len(downstream_nodes) * 12.0 + len(upstream_nodes) * 8.0)
        test_gap_ratio = (len(uncovered) / max(len(all_affected), 1)) * 100.0
        test_gap_score = min(100.0, test_gap_ratio)

        total = direct_score * 0.35 + downstream_score * 0.40 + test_gap_score * 0.25
        level = self._risk_level(total)
        print(
            "Step 5: 风险聚合 -> "
            f"direct={direct_score:.2f}, impact={downstream_score:.2f}, test_gap={test_gap_score:.2f}, total={total:.2f}, level={level}"
        )

        score = RiskScore(
            direct_change_complexity=round(direct_score, 2),
            downstream_impact=round(downstream_score, 2),
            test_gap=round(test_gap_score, 2),
            total=round(total, 2),
            level=level,
        )

        return {
            "target_api": target_api,
            "direct_callers": sorted(direct_callers),
            "direct_callees": sorted(direct_callees),
            "downstream_nodes": sorted(downstream_nodes),
            "upstream_nodes": sorted(upstream_nodes),
            "all_affected": sorted(all_affected),
            "covered_functions": sorted(tested_affected),
            "uncovered_functions": sorted(uncovered),
            "score": score.__dict__,
            "reasoning_summary": (
                f"Target {target_api} has {direct_degree} direct links, "
                f"{len(downstream_nodes)} downstream, {len(upstream_nodes)} upstream, "
                f"uncovered ratio {test_gap_ratio:.2f}%."
            ),
        }

    @staticmethod
    def _dfs(graph: Dict[str, List[str]], start: str) -> Set[str]:
        visited: Set[str] = set()
        stack: List[str] = [start]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            for nxt in graph.get(node, []):
                if nxt not in visited:
                    stack.append(nxt)
        return visited

    @staticmethod
    def _risk_level(score: float) -> str:
        if score >= 75:
            return "HIGH"
        if score >= 45:
            return "MEDIUM"
        return "LOW"

    def process(self, message: AgentMessage, context: MigrationContext) -> AgentMessage:
        """Assess risk for deprecated APIs discovered by ScannerAgent."""
        if message.action != "assess_risk":
            raise ValueError(f"Unsupported action for RiskAgent: {message.action}")

        scan_result = message.payload.get("scan_result") or context.scan_result
        if not scan_result:
            raise ValueError("RiskAgent requires scan result.")

        graph = self.graph_builder.build_graph(scan_result["functions"])
        context.call_graph = graph

        tests = scan_result.get("test_functions", [])
        test_set = set(tests)

        reports: Dict[str, Any] = {}
        deprecated_hits: Dict[str, List[str]] = scan_result.get("deprecated_hits", {})

        target_apis: Set[str] = set()
        for hit_list in deprecated_hits.values():
            target_apis.update(hit_list)

        for target in sorted(target_apis):
            if target not in graph:
                graph[target] = []
            reports[target] = self.long_chain_reasoning(graph, target, test_set)

        context.risk_reports = reports
        return self.send(
            receiver="RefactorAgent",
            action="generate_refactor",
            payload={"risk_reports": reports, "scan_result": scan_result},
        )

    @staticmethod
    def save_report(report: Dict[str, Any], output_path: Path) -> None:
        """Persist report as JSON."""
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

