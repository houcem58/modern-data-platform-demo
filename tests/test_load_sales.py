"""Unit tests for load_sales.py — date parsing and row coercion."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

sys.modules.setdefault("psycopg2", MagicMock())
sys.modules.setdefault("psycopg2.extras", MagicMock())

from ingestion.load_sales import _parse_date, _coerce_row  # noqa: E402


# ---------------------------------------------------------------------------
# _parse_date
# ---------------------------------------------------------------------------

class TestParseDate:
    def test_us_format(self):
        assert _parse_date("01/15/2024") == "2024-01-15"

    def test_iso_format(self):
        assert _parse_date("2024-01-15") == "2024-01-15"

    def test_eu_format(self):
        assert _parse_date("15/01/2024") == "2024-01-15"

    def test_empty_string_returns_none(self):
        assert _parse_date("") is None

    def test_garbage_returns_none(self):
        assert _parse_date("not-a-date") is None

    def test_whitespace_stripped(self):
        assert _parse_date("  2024-06-30  ") == "2024-06-30"

    def test_end_of_year(self):
        assert _parse_date("12/31/2023") == "2023-12-31"


# ---------------------------------------------------------------------------
# _coerce_row
# ---------------------------------------------------------------------------

VALID_ROW = {
    "Order ID": "100001",
    "Region": "Europe",
    "Country": "France",
    "Item Type": "Baby Food",
    "Sales Channel": "Online",
    "Order Priority": "H",
    "Order Date": "01/15/2024",
    "Ship Date": "01/20/2024",
    "Units Sold": "500",
    "Unit Price": "9.28",
    "Unit Cost": "6.92",
    "Total Revenue": "4640.00",
    "Total Cost": "3460.00",
    "Total Profit": "1180.00",
}


class TestCoerceRow:
    def test_valid_row_returns_14_element_tuple(self):
        result = _coerce_row(VALID_ROW)
        assert len(result) == 14

    def test_order_id_is_int(self):
        result = _coerce_row(VALID_ROW)
        assert result[0] == 100001
        assert isinstance(result[0], int)

    def test_dates_are_iso_formatted(self):
        result = _coerce_row(VALID_ROW)
        assert result[6] == "2024-01-15"  # ORDER_DATE
        assert result[7] == "2024-01-20"  # SHIP_DATE

    def test_numeric_fields_are_float(self):
        result = _coerce_row(VALID_ROW)
        assert isinstance(result[9], float)   # UNIT_PRICE
        assert isinstance(result[10], float)  # UNIT_COST
        assert result[11] == pytest.approx(4640.0)  # TOTAL_REVENUE

    def test_string_fields_stripped(self):
        row = {**VALID_ROW, "Region": "  Europe  ", "Country": "  France  "}
        result = _coerce_row(row)
        assert result[1] == "Europe"
        assert result[2] == "France"

    def test_empty_order_id_defaults_to_zero(self):
        row = {**VALID_ROW, "Order ID": ""}
        result = _coerce_row(row)
        assert result[0] == 0

    def test_missing_key_defaults_gracefully(self):
        row = {k: v for k, v in VALID_ROW.items() if k != "Units Sold"}
        result = _coerce_row(row)
        assert result[8] == 0  # UNITS_SOLD defaults to 0

    def test_zero_unit_price_allowed(self):
        row = {**VALID_ROW, "Unit Price": "0"}
        result = _coerce_row(row)
        assert result[9] == 0.0

    def test_none_numeric_field_defaults_to_zero(self):
        row = {**VALID_ROW, "Total Revenue": None}
        result = _coerce_row(row)
        assert result[11] == 0.0
