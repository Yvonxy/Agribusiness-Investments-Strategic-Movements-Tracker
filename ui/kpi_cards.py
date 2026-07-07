from __future__ import annotations

import math

import streamlit as st


def _fmt_value(value) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        if math.isnan(value):
            return "N/A"
        if abs(value) >= 1_000_000_000:
            return f"{value / 1_000_000_000:.2f}B"
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
        return f"{value:,.0f}"
    return str(value)


def render_kpi_cards(kpis: list[dict]) -> None:
    if not kpis:
        return
    cols = st.columns(len(kpis))
    for col, item in zip(cols, kpis):
        with col:
            note_html = f"<div class='note'>{item.get('note', '')}</div>" if item.get("note") else ""
            st.markdown(
                f"""
                <div class="mini-card">
                  <div class="label">{item.get('label', '')}</div>
                  <div class="value">{_fmt_value(item.get('value'))}</div>
                  {note_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
