"""Legacy code sample with deprecated APIs and call chain."""

from __future__ import annotations


def deprecated_logger(message: str) -> None:
    """Legacy logger API (deprecated)."""
    print(f"[DEPRECATED] {message}")


def old_finance_calc(x: float, y: float) -> float:
    """Legacy finance API (deprecated)."""
    return x + y


def compute_invoice_total(price: float, tax: float) -> float:
    """Business function depending on deprecated finance API."""
    deprecated_logger("Computing invoice total")
    total = old_finance_calc(price, tax)
    return round(total, 2)


def build_report_line(customer: str, amount: float) -> str:
    """Build report text."""
    deprecated_logger("Building report line")
    return f"{customer}: {amount:.2f}"


def process_order(customer: str, price: float, tax: float) -> str:
    """Top-level legacy workflow."""
    total = compute_invoice_total(price, tax)
    return build_report_line(customer, total)

