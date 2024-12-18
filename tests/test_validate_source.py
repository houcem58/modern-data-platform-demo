"""Unit tests for validate_source.py quality gate logic."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

# Patch psycopg2 before the module is imported so no real DB is needed
_psycopg2_mock = MagicMock()
sys.modules.setdefault("psycopg2", _psycopg2_mock)

from ingestion.validate_source import CHECKS  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_check(description: str, value) -> bool:
    """Return True if the check FAILS (should trigger sys.exit in production)."""
    for desc, _sql, fail_if in CHECKS:
        if desc == description:
            return fail_if(value)
    raise KeyError(f"Check not found: {description!r}")


# ---------------------------------------------------------------------------
# Row count
# ---------------------------------------------------------------------------

def test_row_count_zero_fails():
    assert _run_check("Row count > 0", 0) is True


def test_row_count_positive_passes():
    assert _run_check("Row count > 0", 1000) is False


def test_row_count_one_passes():
    assert _run_check("Row count > 0", 1) is False


# ---------------------------------------------------------------------------
# NULL ORDER_ID rate
# ---------------------------------------------------------------------------

def test_null_order_id_at_threshold_fails():
    assert _run_check("NULL ORDER_ID rate < 1%", 1.0) is True


def test_null_order_id_above_threshold_fails():
    assert _run_check("NULL ORDER_ID rate < 1%", 5.2) is True


def test_null_order_id_below_threshold_passes():
    assert _run_check("NULL ORDER_ID rate < 1%", 0.5) is False


def test_null_order_id_zero_passes():
    assert _run_check("NULL ORDER_ID rate < 1%", 0.0) is False


def test_null_order_id_none_passes():
    # NULLIF returns None when table is empty — treat as passing
    assert _run_check("NULL ORDER_ID rate < 1%", None) is False


# ---------------------------------------------------------------------------
# NULL ORDER_DATE rate
# ---------------------------------------------------------------------------

def test_null_order_date_above_threshold_fails():
    assert _run_check("NULL ORDER_DATE rate < 1%", 2.0) is True


def test_null_order_date_below_threshold_passes():
    assert _run_check("NULL ORDER_DATE rate < 1%", 0.0) is False


# ---------------------------------------------------------------------------
# Future ORDER_DATE
# ---------------------------------------------------------------------------

def test_future_dates_present_fails():
    assert _run_check("No future ORDER_DATE", 3) is True


def test_no_future_dates_passes():
    assert _run_check("No future ORDER_DATE", 0) is False


# ---------------------------------------------------------------------------
# Negative lead time (SHIP_DATE < ORDER_DATE)
# ---------------------------------------------------------------------------

def test_negative_lead_time_fails():
    assert _run_check("SHIP_DATE >= ORDER_DATE (no negative lead time)", 1) is True


def test_lead_time_clean_passes():
    assert _run_check("SHIP_DATE >= ORDER_DATE (no negative lead time)", 0) is False


# ---------------------------------------------------------------------------
# UNITS_SOLD positive
# ---------------------------------------------------------------------------

def test_zero_units_sold_fails():
    assert _run_check("UNITS_SOLD all positive", 5) is True


def test_all_units_sold_positive_passes():
    assert _run_check("UNITS_SOLD all positive", 0) is False


# ---------------------------------------------------------------------------
# Integration: all checks present
# ---------------------------------------------------------------------------

def test_all_six_checks_defined():
    assert len(CHECKS) == 6


def test_all_check_descriptions_unique():
    descriptions = [desc for desc, _, _ in CHECKS]
    assert len(descriptions) == len(set(descriptions))
