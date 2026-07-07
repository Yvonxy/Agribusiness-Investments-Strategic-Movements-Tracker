from __future__ import annotations

import streamlit as st

from services.analytics_service import quality_summary
from ui.kpi_cards import render_kpi_cards


def render_minimal_summary(df, upload_summary: dict | None = None) -> None:
    summary = quality_summary(df, upload_summary=upload_summary)
    kpis = [
        {"label": "Total Events", "value": summary.get("total_events", 0)},
        {"label": "Companies", "value": summary.get("companies", 0)},
        {"label": "Countries", "value": summary.get("countries", 0)},
    ]
    render_kpi_cards(kpis)

    with st.expander("Data quality details", expanded=False):
        cols = st.columns(4)
        cols[0].metric("Duplicate event_id", summary.get("duplicate_event_id_count", 0))
        cols[1].metric("Missing source URL", summary.get("missing_source_url_count", 0))
        cols[2].metric("Missing evidence", summary.get("missing_evidence_text_count", 0))
        cols[3].metric("Missing deal value", summary.get("missing_deal_value_count", 0))
        cols2 = st.columns(4)
        cols2[0].metric("Unknown commodity", summary.get("unknown_commodity_count", 0))
        cols2[1].metric("Unknown value chain", summary.get("unknown_value_chain_count", 0))
        cols2[2].metric("Year coverage", summary.get("year_coverage", "Unknown"))
        cols2[3].metric("Last loaded", summary.get("last_loaded_timestamp", "Not loaded"))
