from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from config import CRITICAL_COLUMNS_AFTER_EVENT_ID_GENERATION, EXPECTED_COLUMNS
from utils.normalization import ensure_event_id
from utils.text_utils import is_empty_like


@dataclass
class ValidationResult:
    ok: bool
    missing_expected_columns: list[str] = field(default_factory=list)
    missing_critical_columns: list[str] = field(default_factory=list)
    generated_event_ids: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def validate_columns(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, ValidationResult]:
    df = raw_df.copy()
    result = ValidationResult(ok=True)

    df, generated_event_ids = ensure_event_id(df)
    result.generated_event_ids = generated_event_ids
    if generated_event_ids:
        result.warnings.append(f"Generated {generated_event_ids} missing event_id value(s).")

    missing_expected = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    result.missing_expected_columns = missing_expected

    missing_critical = [col for col in CRITICAL_COLUMNS_AFTER_EVENT_ID_GENERATION if col not in df.columns]
    result.missing_critical_columns = missing_critical

    if missing_critical:
        result.ok = False
        result.errors.append("Critical columns are missing: " + ", ".join(missing_critical))
        return df, result

    for col in missing_expected:
        df[col] = ""

    # Reject files where a critical column exists but is entirely blank.
    entirely_blank_critical = []
    for col in CRITICAL_COLUMNS_AFTER_EVENT_ID_GENERATION:
        if col in df.columns and df[col].apply(is_empty_like).all():
            entirely_blank_critical.append(col)
    if entirely_blank_critical:
        result.ok = False
        result.errors.append("Critical columns are present but entirely blank: " + ", ".join(entirely_blank_critical))

    return df, result
