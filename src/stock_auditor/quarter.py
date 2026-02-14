"""Pure date/quarter calculation logic."""

import datetime


def get_previous_quarter(reference_date: datetime.date) -> tuple[str, datetime.date, datetime.date]:
    """Return (quarter_label, start_date, end_date) for the previous quarter.

    Examples:
        2026-01-05 -> ("2025Q4", 2025-10-01, 2025-12-31)
        2026-04-01 -> ("2026Q1", 2026-01-01, 2026-03-31)
    """
    month = reference_date.month
    year = reference_date.year

    if month < 4:
        return (
            f"{year - 1}Q4",
            datetime.date(year - 1, 10, 1),
            datetime.date(year - 1, 12, 31),
        )
    elif month < 7:
        return (
            f"{year}Q1",
            datetime.date(year, 1, 1),
            datetime.date(year, 3, 31),
        )
    elif month < 10:
        return (
            f"{year}Q2",
            datetime.date(year, 4, 1),
            datetime.date(year, 6, 30),
        )
    else:
        return (
            f"{year}Q3",
            datetime.date(year, 7, 1),
            datetime.date(year, 9, 30),
        )


def get_output_dirname(user_name: str, reference_date: datetime.date) -> str:
    """Return the output directory name, e.g. '佳佳-2025Q4'."""
    label, _, _ = get_previous_quarter(reference_date)
    return f"{user_name}-{label}"
