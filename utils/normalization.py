from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from config import DATE_COLUMNS, EXPECTED_COLUMNS, UNKNOWN_IF_BLANK_FIELDS, EVENT_TYPE_TO_GROUP
from utils.date_utils import derive_year, normalize_date_columns
from utils.text_utils import clean_text, clean_text_preserve_semicolons, is_empty_like

TRUE_VALUES = {"true", "1", "yes", "y", "是", "review", "needs review"}
FALSE_VALUES = {"false", "0", "no", "n", "否", ""}


def normalize_needs_review(value: Any) -> str:
    if is_empty_like(value):
        return "False"
    text = str(value).strip().lower()
    if text in TRUE_VALUES:
        return "True"
    if text in FALSE_VALUES:
        return "False"
    return "True" if "true" in text or "yes" in text else "False"


def parse_deal_value(value: Any) -> tuple[Any, bool]:
    if is_empty_like(value):
        return pd.NA, False

    text = str(value).strip().replace(",", "")
    is_minimum = False
    if text.endswith("+"):
        is_minimum = True
        text = text[:-1].strip()

    try:
        return float(text), is_minimum
    except Exception:
        return pd.NA, is_minimum


def stable_event_id(row: pd.Series, row_index: int) -> str:
    fields = [
        "company",
        "event_date",
        "announcement_date",
        "event_type",
        "asset_name",
        "commodity_group",
        "value_chain_link",
        "country",
        "source_url",
        "evidence_text",
    ]
    raw = "|".join(str(row.get(field, "")).strip() for field in fields)
    if not raw.strip("|"):
        raw = f"row-{row_index}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:14]
    return f"evt_{digest}"


def ensure_event_id(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    result = df.copy()
    generated = 0
    if "event_id" not in result.columns:
        result["event_id"] = ""
    for idx, value in result["event_id"].items():
        if is_empty_like(value):
            result.at[idx, "event_id"] = stable_event_id(result.loc[idx], int(idx))
            generated += 1
        else:
            result.at[idx, "event_id"] = str(value).strip()
    return result, generated


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    for col in EXPECTED_COLUMNS:
        if col not in result.columns:
            result[col] = ""

    # Keep only expected columns first, then helper columns are added below.
    result = result[EXPECTED_COLUMNS]

    for col in result.columns:
        unknown = col in UNKNOWN_IF_BLANK_FIELDS
        if col in ["commodity_group", "commodity_subcategory", "value_chain", "value_chain_link", "region", "country", "counterparty"]:
            result[col] = result[col].apply(lambda x: clean_text_preserve_semicolons(x, unknown_if_blank=unknown))
        elif col not in ["year", "confidence_score"]:
            result[col] = result[col].apply(lambda x: clean_text(x, unknown_if_blank=unknown))

    # Use event_group from the CSV, but fill blanks from the fixed taxonomy mapping when possible.
    if "event_group" in result.columns and "event_type" in result.columns:
        blank_group = result["event_group"].astype(str).str.strip().isin(["", "Unknown"])
        result.loc[blank_group, "event_group"] = result.loc[blank_group, "event_type"].map(EVENT_TYPE_TO_GROUP).fillna("Unknown")

    result = normalize_date_columns(result, DATE_COLUMNS)
    result["year"] = result.apply(derive_year, axis=1)
    result["year"] = pd.to_numeric(result["year"], errors="coerce").astype("Int64")

    result["confidence_score"] = pd.to_numeric(result["confidence_score"], errors="coerce")
    result["needs_review"] = result["needs_review"].apply(normalize_needs_review)

    parsed_values = result["deal_value"].apply(parse_deal_value)
    result["deal_value_numeric"] = parsed_values.apply(lambda x: x[0])
    result["deal_value_numeric"] = pd.to_numeric(result["deal_value_numeric"], errors="coerce")
    result["deal_value_is_minimum"] = parsed_values.apply(lambda x: bool(x[1]))
    result["loaded_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    return result
