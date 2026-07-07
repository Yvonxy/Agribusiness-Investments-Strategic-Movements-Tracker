from __future__ import annotations

from typing import Iterable

import pandas as pd

from utils.text_utils import is_empty_like


def split_multivalue(value) -> list[str]:
    if is_empty_like(value):
        return ["Unknown"]
    parts = [part.strip() for part in str(value).split(";")]
    cleaned = [part for part in parts if part and part.lower() not in {"nan", "none", "null", "n/a", "na"}]
    return cleaned if cleaned else ["Unknown"]


def explode_dimension(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return pd.DataFrame(columns=list(df.columns) + [f"{column}_exploded"])
    result = df.copy()
    exploded_col = f"{column}_exploded"
    result[exploded_col] = result[column].apply(split_multivalue)
    result = result.explode(exploded_col)
    result[exploded_col] = result[exploded_col].fillna("Unknown").astype(str).str.strip()
    return result


def unique_values_from_multivalue(df: pd.DataFrame, column: str) -> list[str]:
    if df.empty or column not in df.columns:
        return []
    values: set[str] = set()
    for value in df[column].dropna().tolist():
        values.update(split_multivalue(value))
    return sorted(values, key=lambda x: (x == "Unknown", x.lower()))


def filter_by_multivalue(df: pd.DataFrame, column: str, selected_values: Iterable[str]) -> pd.DataFrame:
    selected = [v for v in selected_values if v and v != "All"]
    if not selected or df.empty:
        return df.copy()
    exploded = explode_dimension(df, column)
    event_ids = exploded.loc[exploded[f"{column}_exploded"].isin(selected), "event_id"].unique()
    return df[df["event_id"].isin(event_ids)].copy()
