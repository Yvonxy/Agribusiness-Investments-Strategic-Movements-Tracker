from __future__ import annotations

import sqlite3

import pandas as pd

from config import DB_PATH, EXPECTED_COLUMNS, SCHEMA_PATH
from utils.deduplication import deduplicate_by_event_id

DB_COLUMNS = EXPECTED_COLUMNS + ["deal_value_numeric", "deal_value_is_minimum", "loaded_at"]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _existing_columns(conn: sqlite3.Connection) -> list[str]:
    try:
        rows = conn.execute("PRAGMA table_info(events)").fetchall()
    except sqlite3.Error:
        return []
    return [row[1] for row in rows]


def init_db() -> None:
    """Create the events table and add newly required columns when upgrading older local DBs."""
    with get_connection() as conn:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema_sql)
        existing = set(_existing_columns(conn))
        for col in DB_COLUMNS:
            if col not in existing:
                col_type = "REAL" if col in {"confidence_score", "deal_value_numeric"} else "INTEGER" if col in {"year", "deal_value_is_minimum"} else "TEXT"
                conn.execute(f'ALTER TABLE events ADD COLUMN "{col}" {col_type}')
        conn.commit()


def _prepare_for_sql(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for col in DB_COLUMNS:
        if col not in result.columns:
            result[col] = None
    result = result[DB_COLUMNS]
    result = result.where(pd.notnull(result), None)
    if "deal_value_is_minimum" in result.columns:
        result["deal_value_is_minimum"] = result["deal_value_is_minimum"].apply(lambda x: 1 if bool(x) else 0)
    return result


def replace_events(df: pd.DataFrame) -> None:
    init_db()
    prepared = _prepare_for_sql(df)
    with get_connection() as conn:
        conn.execute("DELETE FROM events")
        prepared.to_sql("events", conn, if_exists="append", index=False)
        conn.commit()


def append_events(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    current = load_events()
    combined = pd.concat([current, df], ignore_index=True) if not current.empty else df.copy()
    deduped, removed = deduplicate_by_event_id(combined)
    replace_events(deduped)
    return deduped, removed


def load_events() -> pd.DataFrame:
    init_db()
    with get_connection() as conn:
        try:
            df = pd.read_sql_query("SELECT * FROM events", conn)
        except Exception:
            return pd.DataFrame(columns=DB_COLUMNS)
    if df.empty:
        return pd.DataFrame(columns=DB_COLUMNS)
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    if "deal_value_numeric" in df.columns:
        df["deal_value_numeric"] = pd.to_numeric(df["deal_value_numeric"], errors="coerce")
    if "confidence_score" in df.columns:
        df["confidence_score"] = pd.to_numeric(df["confidence_score"], errors="coerce")
    if "deal_value_is_minimum" in df.columns:
        df["deal_value_is_minimum"] = df["deal_value_is_minimum"].fillna(0).astype(bool)
    return df


def last_loaded_at(df: pd.DataFrame) -> str:
    if df.empty or "loaded_at" not in df.columns:
        return "Not loaded"
    values = df["loaded_at"].dropna().astype(str)
    return values.max() if not values.empty else "Not loaded"
