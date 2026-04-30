"""Shared context for agent collaboration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class MigrationContext:
    """Blackboard-style shared context across agents."""

    project_root: Path
    legacy_file: Path
    scan_result: Dict[str, Any] = field(default_factory=dict)
    call_graph: Dict[str, List[str]] = field(default_factory=dict)
    risk_reports: Dict[str, Any] = field(default_factory=dict)
    generated_files: List[Path] = field(default_factory=list)
    validation_result: Dict[str, Any] = field(default_factory=dict)

