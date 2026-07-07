from __future__ import annotations

import pandas as pd

from services.csv_service import load_latest_csv_if_exists, save_latest_csv
from services.db import load_events, replace_events


def load_current_dataset() -> tuple[pd.DataFrame, str]:
    """Load DB first; if empty, auto-load data/latest_events.csv when present."""
    df = load_events()
    if not df.empty:
        return df, "SQLite database"

    latest_df, _, validation = load_latest_csv_if_exists()
    if validation is not None and validation.ok and not latest_df.empty:
        replace_events(latest_df)
        save_latest_csv(latest_df)
        return latest_df, "data/latest_events.csv"

    return df, "No dataset loaded"
