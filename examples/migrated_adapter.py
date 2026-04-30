"""Auto-generated migration adapters by MigraAgent."""

from __future__ import annotations

from typing import Any


def modern_finance_calc(x: float, y: float) -> float:
    """Modern replacement for old_finance_calc."""
    # Example policy adjustment: preserve old behavior baseline with explicit float math.
    return (x + y) * 1.02


def modern_logger(message: str) -> None:
    """Modern logger replacement."""
    print(f"[ModernLogger] {message}")


class LegacyAdapter:
    """Namespace style adapter holder for legacy APIs."""

    @staticmethod
    def deprecated_logger(message: str) -> None:
        """Compatibility adapter for legacy deprecated_logger."""
        if not isinstance(message, str):
            raise TypeError("deprecated_logger expects a string message.")
        print("[Adapter] deprecated_logger mapped to modern_logger")
        modern_logger(message)


    @staticmethod
    def old_finance_calc(x: float, y: float) -> float:
        """Compatibility adapter for legacy old_finance_calc."""
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise TypeError("old_finance_calc expects numeric inputs.")
        print("[Adapter] old_finance_calc is deprecated; routing to modern_finance_calc.")
        return modern_finance_calc(float(x), float(y))
