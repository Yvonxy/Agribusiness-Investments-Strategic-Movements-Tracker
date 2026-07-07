from __future__ import annotations

from typing import Any

import streamlit as st

from config import (
    COMMODITY_GROUP_ORDER,
    EVENT_GROUP_ORDER,
    EVENT_TYPE_ORDER,
    PLAYER_ORDER,
    VALUE_CHAIN_LINK_ORDER,
)
from services.analytics_service import distinct_values, filter_by_year_range, get_available_years


COMPANY_TIER_ORDER = ["Tier 1", "Tier 2", "Tier 3", "Unknown"]

SIDEBAR_FILTERS = [
    ("company_tier", "Company Tier", False, COMPANY_TIER_ORDER),
    ("company", "Company", False, PLAYER_ORDER),
    ("commodity_group", "Commodity Group", True, COMMODITY_GROUP_ORDER),
    ("event_group", "Event Group", False, EVENT_GROUP_ORDER),
    ("event_type", "Event Type", False, EVENT_TYPE_ORDER),
    ("value_chain_link", "Value Chain Link", True, VALUE_CHAIN_LINK_ORDER),
    ("region", "Region", True, None),
]


def _ordered_options(options: list[str], order: list[str] | None) -> list[str]:
    """Keep All first, then apply taxonomy order when available."""
    if not order:
        return options
    has_all = "All" in options
    values = [v for v in options if v != "All"]
    order_index = {value: idx for idx, value in enumerate(order)}
    values = sorted(values, key=lambda v: (order_index.get(v, 10_000), str(v).lower()))
    return (["All"] if has_all else []) + values


def _normalize_all_selection(values: list[str], options: list[str]) -> list[str]:
    """Make All mutually exclusive with concrete selections.

    If a user selects one or more concrete options, the default All selection
    is removed automatically. If the user clears every concrete selection, the
    filter falls back to All so charts do not silently show no data.
    """
    allowed = set(options)
    cleaned = [value for value in values if value in allowed]
    concrete = [value for value in cleaned if value != "All"]

    if concrete:
        return concrete
    if "All" in allowed:
        return ["All"]
    return cleaned


def _on_multiselect_change(key: str, options: list[str]) -> None:
    current_value = st.session_state.get(key, [])
    if isinstance(current_value, str):
        current = [current_value]
    else:
        current = list(current_value or [])
    st.session_state[key] = _normalize_all_selection(current, options)


def _clean_multiselect_state(key: str, options: list[str]) -> None:
    """Remove stale selections and keep All mutually exclusive."""
    if key not in st.session_state:
        return

    current_value = st.session_state.get(key, [])
    if isinstance(current_value, str):
        current = [current_value]
    else:
        current = list(current_value or [])

    st.session_state[key] = _normalize_all_selection(current, options)


def _company_option_df(option_df, selected_company_tiers: list[str]):
    """Limit company options to the selected company_tier subset."""
    selected = [value for value in selected_company_tiers if value and value != "All"]
    if not selected or option_df.empty or "company_tier" not in option_df.columns:
        return option_df
    return option_df[option_df["company_tier"].astype(str).isin(selected)].copy()


def _event_type_option_df(option_df, selected_event_groups: list[str]):
    """Limit event_type options to the selected event_group subset."""
    selected = [value for value in selected_event_groups if value and value != "All"]
    if not selected or option_df.empty or "event_group" not in option_df.columns:
        return option_df
    return option_df[option_df["event_group"].astype(str).isin(selected)].copy()


def render_sidebar_filters(df) -> dict[str, Any]:
    """Render the global sidebar filters.

    Year range is applied first. Company Tier constrains the available Company
    options, and Event Group constrains the available Event Type options. The
    returned filter dict is the single source of truth for charts, summary
    cards, map, and event list.
    """
    filters: dict[str, Any] = {}
    with st.sidebar:
        st.markdown("### Filters")
        st.caption("Charts and event list update from this filter combination.")

        years = get_available_years(df)
        if years:
            min_year, max_year = min(years), max(years)
            if min_year == max_year:
                year_range = (min_year, max_year)
                st.caption(f"Year Range: {min_year}")
            else:
                selected_year_range = st.slider(
                    "Year Range",
                    min_value=min_year,
                    max_value=max_year,
                    value=(min_year, max_year),
                    step=1,
                )
                year_range = (int(selected_year_range[0]), int(selected_year_range[1]))
        else:
            year_range = None
            st.caption("Year Range: unavailable")

        filters["_year_range"] = year_range

        option_df = filter_by_year_range(df, year_range) if year_range else df

        for field, label, is_multivalue, order in SIDEBAR_FILTERS:
            source_df = option_df
            if field == "company":
                source_df = _company_option_df(option_df, filters.get("company_tier", []))
            elif field == "event_type":
                source_df = _event_type_option_df(option_df, filters.get("event_group", []))

            options = distinct_values(source_df, field, include_all=True, multivalue=is_multivalue)
            options = _ordered_options(options, order)
            default = ["All"] if "All" in options else []
            widget_key = f"sidebar_filter_{field}"
            _clean_multiselect_state(widget_key, options)
            filters[field] = st.multiselect(
                label,
                options=options,
                default=default,
                key=widget_key,
                on_change=_on_multiselect_change,
                args=(widget_key, options),
            )

    return filters
