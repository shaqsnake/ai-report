"""Tests for quarter date calculation logic."""

import datetime

import pytest

from stock_auditor.quarter import get_output_dirname, get_previous_quarter


@pytest.mark.parametrize(
    "ref_date, expected_label, expected_start, expected_end",
    [
        # Q1 (Jan-Mar) -> previous Q4
        (datetime.date(2026, 1, 5), "2025Q4", datetime.date(2025, 10, 1), datetime.date(2025, 12, 31)),
        (datetime.date(2026, 3, 31), "2025Q4", datetime.date(2025, 10, 1), datetime.date(2025, 12, 31)),
        # Q2 (Apr-Jun) -> previous Q1
        (datetime.date(2026, 4, 1), "2026Q1", datetime.date(2026, 1, 1), datetime.date(2026, 3, 31)),
        # Q3 (Jul-Sep) -> previous Q2
        (datetime.date(2026, 7, 15), "2026Q2", datetime.date(2026, 4, 1), datetime.date(2026, 6, 30)),
        # Q4 (Oct-Dec) -> previous Q3
        (datetime.date(2026, 10, 1), "2026Q3", datetime.date(2026, 7, 1), datetime.date(2026, 9, 30)),
        # Year boundary: Jan 1 -> previous year Q4
        (datetime.date(2027, 1, 1), "2026Q4", datetime.date(2026, 10, 1), datetime.date(2026, 12, 31)),
    ],
)
def test_get_previous_quarter(ref_date, expected_label, expected_start, expected_end):
    label, start, end = get_previous_quarter(ref_date)
    assert label == expected_label
    assert start == expected_start
    assert end == expected_end


def test_get_output_dirname():
    dirname = get_output_dirname("佳佳", datetime.date(2026, 1, 5))
    assert dirname == "佳佳-2025Q4"


def test_get_output_dirname_q2():
    dirname = get_output_dirname("夏秋", datetime.date(2026, 7, 15))
    assert dirname == "夏秋-2026Q2"
