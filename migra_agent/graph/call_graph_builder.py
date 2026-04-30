"""Call graph builder with optional networkx integration."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

try:
    import networkx as nx
except ImportError:  # pragma: no cover - optional dependency
    nx = None


class CallGraphBuilder:
    """Build call graph from scanner output."""

    def build_graph(self, functions: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Build adjacency dict graph."""
        graph: Dict[str, List[str]] = {}
        for caller, callees in functions.items():
            graph[caller] = list(dict.fromkeys(callees))
            for callee in callees:
                graph.setdefault(callee, [])
        return graph

    def to_networkx(self, graph: Dict[str, List[str]]) -> Any:
        """Convert adjacency dict to a networkx DiGraph when available."""
        if nx is None:
            return None

        digraph = nx.DiGraph()
        for src, targets in graph.items():
            digraph.add_node(src)
            for dst in targets:
                digraph.add_edge(src, dst)
        return digraph

    @staticmethod
    def reverse_edges(graph: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Build reverse adjacency mapping."""
        reversed_graph: Dict[str, List[str]] = {node: [] for node in graph}
        for src, targets in graph.items():
            reversed_graph.setdefault(src, [])
            for dst in targets:
                reversed_graph.setdefault(dst, [])
                reversed_graph[dst].append(src)
        return reversed_graph

    @staticmethod
    def iter_edges(graph: Dict[str, List[str]]) -> Iterable[tuple[str, str]]:
        """Yield graph edges."""
        for src, targets in graph.items():
            for dst in targets:
                yield src, dst

