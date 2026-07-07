from __future__ import annotations

import pandas as pd
import streamlit as st

from config import DETAIL_COLUMNS
from utils.multivalue import split_multivalue
from utils.text_utils import html_escape


CHIP_FIELDS = {
    "event_group",
    "event_type",
    "commodity_group",
    "commodity_subcategory",
    "value_chain",
    "value_chain_link",
    "country",
    "needs_review",
}


def _safe(row: pd.Series, field: str) -> str:
    value = row.get(field, "")
    if pd.isna(value):
        return ""
    return str(value)


def _chips(value: str) -> str:
    return "".join(f"<span class='chip'>{html_escape(v)}</span>" for v in split_multivalue(value))


def _option_label(row: pd.Series) -> str:
    pieces = [
        _safe(row, "event_date") or _safe(row, "announcement_date") or "Unknown date",
        _safe(row, "company") or "Unknown company",
        _safe(row, "event_type") or "Unknown event type",
        _safe(row, "asset_name") or _safe(row, "source_title") or _safe(row, "event_id"),
    ]
    return " | ".join(pieces)


def render_event_details(table_df: pd.DataFrame) -> None:
    st.markdown("### Event detail")
    if table_df.empty:
        return

    labels = {_option_label(row): row["event_id"] for _, row in table_df.iterrows()}
    selected_label = st.selectbox("Select event to view details", options=list(labels.keys()), index=0)
    selected_id = labels[selected_label]
    row = table_df[table_df["event_id"] == selected_id].iloc[0]

    st.markdown("<div class='detail-card'>", unsafe_allow_html=True)
    st.markdown(f"#### {_safe(row, 'company')} — {_safe(row, 'event_type')}")

    chip_html = ""
    for field in ["event_group", "event_type", "commodity_group", "commodity_subcategory", "value_chain", "value_chain_link", "country", "needs_review"]:
        if field in row and _safe(row, field):
            chip_html += _chips(_safe(row, field))
    if chip_html:
        st.markdown(chip_html, unsafe_allow_html=True)

    left, right = st.columns(2)
    left_fields = [
        "event_id",
        "announcement_date",
        "event_date",
        "year",
        "company_tier",
        "company",
        "asset_name",
        "asset_type",
        "counterparty",
        "deal_value",
        "deal_currency",
        "deal_status",
    ]
    right_fields = [
        "event_group",
        "event_type",
        "commodity_group",
        "commodity_subcategory",
        "value_chain",
        "value_chain_link",
        "region",
        "country",
        "source_title",
        "source_type",
        "confidence_score",
        "needs_review",
        "created_at",
        "updated_at",
    ]

    with left:
        for field in left_fields:
            if field in row:
                st.markdown(f"**{field}:** {html_escape(_safe(row, field))}", unsafe_allow_html=True)
    with right:
        for field in right_fields:
            if field in row:
                st.markdown(f"**{field}:** {html_escape(_safe(row, field))}", unsafe_allow_html=True)

    source_url = _safe(row, "source_url")
    if source_url:
        st.markdown(f"**source_url:** [Open source]({source_url})")
    else:
        st.markdown("**source_url:** ")

    st.markdown("**evidence_text**")
    evidence = _safe(row, "evidence_text")
    st.markdown(f"<div class='evidence-box'>{html_escape(evidence) if evidence else 'No evidence text provided.'}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
