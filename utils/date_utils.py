from __future__ import annotations

from typing import Any

import pandas as pd
from dateutil import parser

from utils.text_utils import is_empty_like


def parse_date_to_iso(value: Any) -> str:
    """Parse common date formats and return YYYY-MM-DD, otherwise blank."""
    if is_empty_like(value):
        return ""
    try:
        dt = parser.parse(str(value), fuzzy=True, dayfirst=False)
        return dt.date().isoformat()
    except Exception:
        try:
            dt = pd.to_datetime(value, errors="coerce")
            if pd.isna(dt):
                return ""
            return dt.date().isoformat()
        except Exception:
            return ""


def normalize_date_columns(df: pd.DataFrame, date_columns: list[str]) -> pd.DataFrame:
    result = df.copy()
    for col in date_columns:
        if col in result.columns:
            result[col] = result[col].apply(parse_date_to_iso)
    return result


def derive_year(row: pd.Series) -> Any:
    raw_year = row.get("year", "")
    try:
        year = int(float(str(raw_year).strip()))
        if 1900 <= year <= 2100:
            return year
    except Exception:
        pass

    for col in ["event_date", "announcement_date"]:
        value = row.get(col, "")
        if not is_empty_like(value):
            try:
                return int(str(value)[:4])
            except Exception:
                continue
    return pd.NA


def available_years(df: pd.DataFrame) -> list[int]:
    if df.empty or "year" not in df.columns:
        return []
    years = pd.to_numeric(df["year"], errors="coerce").dropna().astype(int)
    return sorted(years.unique().tolist())
