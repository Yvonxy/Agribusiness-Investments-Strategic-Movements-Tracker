from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

from config import LATEST_CSV_PATH
from services.validation_service import ValidationResult, validate_columns
from utils.deduplication import deduplicate_by_event_id
from utils.normalization import normalize_dataframe


def read_csv_file(file_obj) -> pd.DataFrame:
    """Read a user-uploaded CSV as strings while preserving blanks."""
    last_error = None
    for encoding in ["utf-8-sig", "utf-8", "latin1"]:
        try:
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            return pd.read_csv(file_obj, dtype=str, keep_default_na=False, encoding=encoding)
        except Exception as exc:
            last_error = exc
    raise ValueError(f"Unable to read CSV file: {last_error}")


def process_uploaded_csv(file_obj) -> tuple[pd.DataFrame, dict, ValidationResult]:
    raw_df = read_csv_file(file_obj)
    validated_df, validation = validate_columns(raw_df)
    if not validation.ok:
        return pd.DataFrame(), {
            "uploaded_rows": len(raw_df),
            "stored_unique_events": 0,
            "duplicates_removed": 0,
        }, validation

    normalized_df = normalize_dataframe(validated_df)
    deduped_df, duplicates_removed = deduplicate_by_event_id(normalized_df)

    summary = {
        "uploaded_rows": len(raw_df),
        "stored_unique_events": deduped_df["event_id"].nunique() if not deduped_df.empty else 0,
        "duplicates_removed": duplicates_removed,
        "missing_expected_columns": validation.missing_expected_columns,
        "generated_event_ids": validation.generated_event_ids,
    }
    return deduped_df, summary, validation


def save_latest_csv(df: pd.DataFrame) -> None:
    LATEST_CSV_PATH.parent.mkdir(exist_ok=True)
    # Preserve uploaded + helper fields in the local copy for fast reload.
    df.to_csv(LATEST_CSV_PATH, index=False, encoding="utf-8-sig")


def load_latest_csv_if_exists() -> tuple[pd.DataFrame, dict | None, ValidationResult | None]:
    if not LATEST_CSV_PATH.exists():
        return pd.DataFrame(), None, None
    with LATEST_CSV_PATH.open("rb") as f:
        return process_uploaded_csv(f)
