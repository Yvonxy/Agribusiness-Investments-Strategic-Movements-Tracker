from __future__ import annotations

import pandas as pd
import streamlit as st

from services.analytics_service import apply_advanced_filters, filter_by_year_range, unique_count, unique_event_count
from services.db import init_db
from services.event_service import load_current_dataset
from ui.charts import render_four_time_series_charts
from ui.data_quality import render_minimal_summary
from ui.event_detail import render_event_details
from ui.event_table import render_event_table, render_export_button
from ui.sidebar import render_sidebar_filters
from ui.styles import inject_css
from ui.upload_panel import render_upload_panel


st.set_page_config(
    page_title="Agribusiness Strategic Investment Tracker",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_header(df: pd.DataFrame) -> None:
    if df.empty:
        status = "Upload a CSV file to start the analysis."
    else:
        event_count = unique_event_count(df)
        company_count = unique_count(df, "company")
        years = pd.to_numeric(df["year"], errors="coerce").dropna().astype(int).tolist() if "year" in df.columns else []
        year_label = f"{min(years)}-{max(years)}" if years else "Unknown years"
        status = f"Current dataset: {event_count} events | {company_count} companies | {year_label}"
    st.markdown(
        f"""
        <div class="hero">
            <h1>Agribusiness Strategic Investment Tracker</h1>
            <div class="subtitle">Portfolio movements by player, commodity, event type, and value chain</div>
            <div class="status-line">{status}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.info("Upload a CSV file to start the analysis.")


def main() -> None:
    inject_css()
    init_db()
    current_df, _source_label = load_current_dataset()

    render_header(current_df)
    upload_summary = render_upload_panel()

    if current_df.empty:
        render_empty_state()
        return

    sidebar_filters = render_sidebar_filters(current_df)
    year_range = sidebar_filters.pop("_year_range", None)
    year_filtered_df = filter_by_year_range(current_df, year_range)
    filtered_df = apply_advanced_filters(year_filtered_df, sidebar_filters)

    render_minimal_summary(filtered_df, upload_summary=upload_summary)

    render_four_time_series_charts(filtered_df)

    st.markdown("---")
    table_df = render_event_table(filtered_df)
    render_event_details(table_df)
    render_export_button(table_df)


if __name__ == "__main__":
    main()
