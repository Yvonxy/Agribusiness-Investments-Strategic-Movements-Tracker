from __future__ import annotations

import pandas as pd


def deduplicate_by_event_id(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    if df.empty or "event_id" not in df.columns:
        return df.copy(), 0

    result = df.copy()
    original_count = len(result)
    result["_row_order"] = range(len(result))

    if "updated_at" in result.columns:
        result["_updated_sort"] = pd.to_datetime(result["updated_at"], errors="coerce")
    else:
        result["_updated_sort"] = pd.NaT

    # For each event_id, keep the latest updated_at; if missing/tied, keep last CSV occurrence.
    result = result.sort_values(["event_id", "_updated_sort", "_row_order"], na_position="first")
    result = result.drop_duplicates(subset=["event_id"], keep="last")
    result = result.sort_values("_row_order").drop(columns=["_row_order", "_updated_sort"])
    removed = original_count - len(result)
    return result.reset_index(drop=True), removed
