"""Tests for legacy example code."""

from __future__ import annotations

from examples.legacy_code import compute_invoice_total, process_order


def test_compute_invoice_total() -> None:
    assert compute_invoice_total(100.0, 5.0) == 105.0


def test_process_order_line() -> None:
    line = process_order("Alice", 100.0, 5.0)
    assert "Alice" in line
    assert "105.00" in line

