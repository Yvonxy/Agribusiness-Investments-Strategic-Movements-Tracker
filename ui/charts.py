from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.multivalue import explode_dimension

from config import (
    COMMODITY_GROUP_COLORS,
    COMMODITY_GROUP_ORDER,
    EVENT_GROUP_COLORS,
    EVENT_TYPE_ORDER,
    EVENT_TYPE_TO_GROUP,
    PLAYER_ORDER,
    VALUE_CHAIN_COLORS,
    VALUE_CHAIN_LINK_ORDER,
    VALUE_CHAIN_LINK_TO_CHAIN,
)

PLOTLY_TEMPLATE = "plotly_white"

PLOT_CONFIG = {
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "scale": 2},
}

METRIC_EVENT_COUNT = "Event count"
METRIC_DEAL_VALUE = "Disclosed deal value"
METRIC_OPTIONS = [METRIC_EVENT_COUNT, METRIC_DEAL_VALUE]

AGGREGATE_COUNTRY_LABELS = {
    "",
    "Unknown",
    "Global",
    "Multiple",
    "Africa",
    "Pan-Africa",
    "West Africa",
    "Europe",
}

COUNTRY_NAME_NORMALIZATION = {
    "Côte d’Ivoire": "Côte d'Ivoire",
    "US": "United States",
    "USA": "United States",
    "U.S.": "United States",
    "United States of America": "United States",
    "UK": "United Kingdom",
}


# -----------------------------------------------------------------------------
# Generic UI / chart helpers
# -----------------------------------------------------------------------------

def _empty_chart(message: str = "No data available for this view.") -> None:
    st.info(message)


def _base_layout(fig, height: int) -> None:
    fig.update_layout(
        height=height,
        margin=dict(l=30, r=20, t=58, b=54),
        paper_bgcolor="white",
        plot_bgcolor="white",
        title_font_size=16,
        font=dict(size=12, color="#111827"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="left", x=0),
        legend_title_text="",
    )
    fig.update_xaxes(showgrid=False, linecolor="#E5E7EB", tickfont=dict(color="#374151"))
    fig.update_yaxes(gridcolor="#EEF2F7", zerolinecolor="#E5E7EB", tickfont=dict(color="#374151"))


def _chart_separator() -> None:
    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)


def _chart_group_title(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"#### {title}")
    if subtitle:
        st.markdown(f"<div class='section-note'>{subtitle}</div>", unsafe_allow_html=True)


def _metric_selector(label: str, key: str) -> str:
    return st.radio(label, METRIC_OPTIONS, index=0, horizontal=True, key=key)


def _metric_column(metric: str) -> str:
    return "metric_value" if metric == METRIC_DEAL_VALUE else "events"


def _metric_axis_label(metric: str) -> str:
    return "Disclosed deal value" if metric == METRIC_DEAL_VALUE else "Unique events"


def _metric_hover_label(metric: str) -> str:
    return "Deal value" if metric == METRIC_DEAL_VALUE else "Events"


def _metric_chart_suffix(metric: str) -> str:
    return "by disclosed deal value" if metric == METRIC_DEAL_VALUE else "by event count"


def _metric_caption_suffix(metric: str) -> str:
    if metric == METRIC_DEAL_VALUE:
        return " Amount is summed from deal_value_numeric; blank or undisclosed values count as 0. No FX conversion is applied."
    return " Counts use unique event_id."


def _format_metric_value(value: float | int, metric: str) -> str:
    if metric == METRIC_DEAL_VALUE:
        return f"{float(value):,.0f}"
    return f"{int(round(float(value))):,}"


def _format_share(value: float) -> str:
    return f"{float(value):.0%}"


# -----------------------------------------------------------------------------
# Ordering and color helpers
# -----------------------------------------------------------------------------

def _ordered_player_values(values: list[str]) -> list[str]:
    """Return player values in the requested strategic peer-set order."""
    clean_values = [str(v) for v in values if str(v).strip()]
    defined = [player for player in PLAYER_ORDER if player in clean_values]
    extras = sorted(
        [value for value in clean_values if value not in PLAYER_ORDER and value != "Others"],
        key=lambda value: value.lower(),
    )
    if "Others" in clean_values:
        extras.append("Others")
    return defined + extras


def _ordered_commodity_values(values: list[str]) -> list[str]:
    """Return commodity groups in taxonomy order, with Unknown last."""
    clean_values = [str(v) for v in values if str(v).strip()]
    defined = [value for value in COMMODITY_GROUP_ORDER if value in clean_values]
    extras = sorted(
        [value for value in clean_values if value not in COMMODITY_GROUP_ORDER and value != "Others"],
        key=lambda value: value.lower(),
    )
    if "Others" in clean_values and "Others" not in defined:
        extras.append("Others")
    return defined + extras


def _ordered_event_type_values(values: list[str]) -> list[str]:
    """Return event_type values in taxonomy order.

    Bankruptcy is intentionally kept last so Plotly draws it last and it appears
    at the top of stacked columns.
    """
    clean_values = [str(v) for v in values if str(v).strip()]
    order_without_bankruptcy = [v for v in EVENT_TYPE_ORDER if v != "Bankruptcy"]
    defined = [event_type for event_type in order_without_bankruptcy if event_type in clean_values]
    extras = sorted(
        [value for value in clean_values if value not in EVENT_TYPE_ORDER and value != "Others"],
        key=lambda value: value.lower(),
    )
    ordered = defined + extras
    if "Others" in clean_values:
        ordered.append("Others")
    if "Bankruptcy" in clean_values:
        ordered.append("Bankruptcy")
    return ordered


def event_type_color_map(values: list[str]) -> dict[str, str]:
    # Color event types by their parent event_group. Multiple event types in the same group share a calm color family.
    group_shades = {
        "Growth Investment": ["#2563EB", "#3B82F6", "#60A5FA", "#93C5FD", "#1D4ED8"],
        "Equity / Deal Activity": ["#0891B2", "#06B6D4", "#22D3EE"],
        "Partnership": ["#059669", "#10B981", "#34D399"],
        "Capital Market / Financing": ["#0D9488", "#14B8A6", "#2DD4BF"],
        "Portfolio Reduction": ["#F97316", "#FB923C", "#FDBA74"],
        "Restructuring / Distress": ["#DC2626", "#EF4444", "#F87171"],
        "Unknown": ["#64748B"],
        "Others": ["#94A3B8"],
    }
    counters = {k: 0 for k in group_shades}
    result = {}
    for value in values:
        if value == "Others":
            result[value] = "#94A3B8"
            continue
        group = EVENT_TYPE_TO_GROUP.get(value, "Unknown")
        shades = group_shades.get(group, group_shades["Unknown"])
        result[value] = shades[counters.get(group, 0) % len(shades)]
        counters[group] = counters.get(group, 0) + 1
    return result


def value_chain_color_map(values: list[str]) -> dict[str, str]:
    upstream_shades = ["#0E7490", "#0891B2", "#06B6D4", "#22D3EE", "#67E8F9", "#155E75", "#164E63"]
    downstream_shades = ["#6D28D9", "#7C3AED", "#8B5CF6", "#A78BFA", "#C4B5FD", "#5B21B6", "#4C1D95", "#9333EA", "#A855F7"]
    neutral_shades = ["#64748B", "#94A3B8", "#CBD5E1"]
    counters = {"Upstream": 0, "Downstream": 0, "Corporate / Multi-Chain": 0, "Unknown": 0}
    palettes = {
        "Upstream": upstream_shades,
        "Downstream": downstream_shades,
        "Corporate / Multi-Chain": neutral_shades,
        "Unknown": neutral_shades,
    }
    result = {}
    for value in values:
        if value == "Others":
            result[value] = "#94A3B8"
            continue
        chain = VALUE_CHAIN_LINK_TO_CHAIN.get(value, "Unknown")
        palette = palettes.get(chain, neutral_shades)
        result[value] = palette[counters.get(chain, 0) % len(palette)]
        counters[chain] = counters.get(chain, 0) + 1
    return result


def commodity_color_map(values: list[str]) -> dict[str, str]:
    return {v: COMMODITY_GROUP_COLORS.get(v, "#94A3B8") for v in values}


def event_group_color_map(values: list[str]) -> dict[str, str]:
    return {v: EVENT_GROUP_COLORS.get(v, "#94A3B8") for v in values}


# -----------------------------------------------------------------------------
# Aggregation helpers supporting count and deal value metrics
# -----------------------------------------------------------------------------

def _prepare_dimension_rows(
    df: pd.DataFrame,
    column: str,
    multivalue: bool,
) -> tuple[pd.DataFrame, str]:
    """Return event-level rows for a dimension, safe for both count and value metrics."""
    if df.empty or column not in df.columns or "event_id" not in df.columns or "year" not in df.columns:
        return pd.DataFrame(), column

    if multivalue:
        tmp = explode_dimension(df, column)
        dim_col = f"{column}_exploded"
    else:
        tmp = df.copy()
        dim_col = column

    keep_cols = ["event_id", "year", dim_col]
    if "deal_value_numeric" in tmp.columns:
        keep_cols.append("deal_value_numeric")
    tmp = tmp[keep_cols].dropna(subset=["year"])
    tmp["year"] = pd.to_numeric(tmp["year"], errors="coerce")
    tmp = tmp.dropna(subset=["year"])
    tmp["year"] = tmp["year"].astype(int)
    tmp[dim_col] = tmp[dim_col].astype(str).str.strip()
    tmp = tmp[tmp[dim_col] != ""]
    if "deal_value_numeric" not in tmp.columns:
        tmp["deal_value_numeric"] = 0.0
    tmp["deal_value_numeric"] = pd.to_numeric(tmp["deal_value_numeric"], errors="coerce").fillna(0.0)

    # Avoid duplicated counting and duplicated value within the same category-year.
    tmp = tmp.drop_duplicates(["event_id", "year", dim_col])
    return tmp, dim_col


def _time_series_by_dimension_metric(
    df: pd.DataFrame,
    column: str,
    multivalue: bool = False,
    order: list[str] | None = None,
) -> pd.DataFrame:
    tmp, dim_col = _prepare_dimension_rows(df, column, multivalue)
    if tmp.empty:
        return pd.DataFrame(columns=["year", column, "events", "metric_value"])

    result = (
        tmp.groupby(["year", dim_col])
        .agg(events=("event_id", "nunique"), metric_value=("deal_value_numeric", "sum"))
        .reset_index()
        .rename(columns={dim_col: column})
    )

    if order:
        category_values = [v for v in order if v in result[column].astype(str).unique().tolist()]
        extra_values = sorted([v for v in result[column].astype(str).unique().tolist() if v not in category_values])
        category_order = category_values + extra_values
        result[column] = pd.Categorical(result[column], categories=category_order, ordered=True)
        result = result.sort_values(["year", column])
        result[column] = result[column].astype(str)
    else:
        result = result.sort_values(["year", column])
    return result


def _pivot_dimension_year_metric(
    df: pd.DataFrame,
    column: str,
    multivalue: bool = True,
    order: list[str] | None = None,
    metric: str = METRIC_EVENT_COUNT,
) -> pd.DataFrame:
    tmp, dim_col = _prepare_dimension_rows(df, column, multivalue)
    if tmp.empty:
        return pd.DataFrame()

    if metric == METRIC_DEAL_VALUE:
        pivot = tmp.pivot_table(
            index=dim_col,
            columns="year",
            values="deal_value_numeric",
            aggfunc="sum",
            fill_value=0,
        )
    else:
        pivot = tmp.pivot_table(
            index=dim_col,
            columns="year",
            values="event_id",
            aggfunc=pd.Series.nunique,
            fill_value=0,
        )

    if order:
        idx = [v for v in order if v in pivot.index]
        extra = [v for v in pivot.index if v not in idx]
        pivot = pivot.loc[idx + sorted(extra)]
    else:
        totals = pivot.sum(axis=1).sort_values(ascending=False)
        pivot = pivot.loc[totals.index]
    pivot.columns = pivot.columns.astype(str)
    return pivot


# -----------------------------------------------------------------------------
# Chart primitives
# -----------------------------------------------------------------------------

def render_stacked_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str,
    metric: str,
    subtitle: str | None = None,
    color_discrete_map: dict[str, str] | None = None,
    category_orders: dict[str, list[str]] | None = None,
    height: int = 520,
) -> None:
    if df.empty:
        _empty_chart()
        return

    chart_df = df.copy()
    chart_df[y] = pd.to_numeric(chart_df[y], errors="coerce").fillna(0.0)
    chart_df = chart_df[chart_df[y] != 0] if metric == METRIC_DEAL_VALUE else chart_df
    if chart_df.empty:
        _empty_chart("No disclosed deal value available for this selection.")
        return

    chart_df["hover_value"] = chart_df[y].map(lambda value: _format_metric_value(value, metric))

    fig = px.bar(
        chart_df,
        x=x,
        y=y,
        color=color,
        title=title,
        template=PLOTLY_TEMPLATE,
        color_discrete_map=color_discrete_map,
        category_orders=category_orders,
        custom_data=[color, "hover_value"],
    )
    fig.update_layout(barmode="stack")
    _base_layout(fig, height)
    fig.update_yaxes(title=_metric_axis_label(metric))
    fig.update_traces(
        hovertemplate=(
            "Year=%{x}<br>"
            f"{_metric_hover_label(metric)}=%{{customdata[1]}}<br>"
            "Category=%{customdata[0]}<extra></extra>"
        )
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)
    if subtitle:
        st.caption(subtitle + _metric_caption_suffix(metric))


def render_heatmap(
    pivot_df: pd.DataFrame,
    title: str,
    metric: str,
    subtitle: str | None = None,
    height: int = 520,
    color_continuous_scale: str = "Blues",
) -> None:
    if pivot_df.empty:
        _empty_chart("No matrix data available for this selection.")
        return
    if metric == METRIC_DEAL_VALUE and float(pivot_df.sum().sum()) == 0:
        _empty_chart("No disclosed deal value available for this selection.")
        return

    value_label = _metric_axis_label(metric)
    fig = px.imshow(
        pivot_df,
        text_auto=True,
        aspect="auto",
        title=title,
        template=PLOTLY_TEMPLATE,
        labels=dict(color=value_label, x="Year", y=""),
        color_continuous_scale=color_continuous_scale,
    )
    _base_layout(fig, height)
    fig.update_layout(coloraxis_colorbar=dict(title=value_label), legend=dict(orientation="h"))
    fig.update_traces(
        hovertemplate=f"Category=%{{y}}<br>Year=%{{x}}<br>{_metric_hover_label(metric)}=%{{z:,.0f}}<extra></extra>"
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)
    if subtitle:
        st.caption(subtitle + _metric_caption_suffix(metric))


# -----------------------------------------------------------------------------
# Year controls
# -----------------------------------------------------------------------------

def _available_year_options(df: pd.DataFrame) -> list[int]:
    if df.empty or "year" not in df.columns:
        return []
    years = pd.to_numeric(df["year"], errors="coerce").dropna().astype(int).unique().tolist()
    return sorted(years)


def _cumulative_year_slider(
    df: pd.DataFrame,
    label: str,
    key: str,
) -> tuple[int | None, int | None]:
    """Return a cumulative start/end year for map-style views."""
    years = _available_year_options(df)
    if not years:
        st.caption(f"{label}: unavailable")
        return None, None

    start_year = min(years)
    end_year = max(years)

    if start_year == end_year:
        st.caption(f"{label}: {start_year}")
        return start_year, end_year

    selected_end = st.slider(
        label,
        min_value=start_year,
        max_value=end_year,
        value=end_year,
        step=1,
        key=key,
        help=(
            f"Move the slider to see cumulative country activity from {start_year} "
            f"through the selected year. The maximum year shows the full-period total."
        ),
    )
    return start_year, int(selected_end)


def _filter_to_cumulative_year(df: pd.DataFrame, start_year: int | None, end_year: int | None) -> pd.DataFrame:
    if start_year is None or end_year is None or df.empty or "year" not in df.columns:
        return df.copy()
    years = pd.to_numeric(df["year"], errors="coerce")
    return df[(years >= int(start_year)) & (years <= int(end_year))].copy()


# -----------------------------------------------------------------------------
# Value chain evolution
# -----------------------------------------------------------------------------

def render_value_chain_link_year_heatmap(
    df: pd.DataFrame,
    title: str,
    metric: str,
    subtitle: str | None = None,
    height: int = 620,
) -> None:
    """Render value_chain_link × year as an upstream-to-downstream ordered heatmap."""
    if df.empty or "value_chain_link" not in df.columns or "event_id" not in df.columns:
        _empty_chart("No value chain data available for this selection.")
        return

    pivot_df = _pivot_dimension_year_metric(
        df,
        "value_chain_link",
        multivalue=True,
        order=VALUE_CHAIN_LINK_ORDER,
        metric=metric,
    )
    if pivot_df.empty:
        _empty_chart("No value chain evolution data available for this selection.")
        return

    ordered_index = [v for v in VALUE_CHAIN_LINK_ORDER if v in pivot_df.index]
    extra_index = [v for v in pivot_df.index if v not in ordered_index]
    pivot_df = pivot_df.loc[ordered_index + sorted(extra_index)]

    value_label = _metric_axis_label(metric)
    if metric == METRIC_DEAL_VALUE and float(pivot_df.sum().sum()) == 0:
        _empty_chart("No disclosed deal value available for value chain evolution.")
        return

    fig = px.imshow(
        pivot_df,
        text_auto=True,
        aspect="auto",
        title=title,
        template=PLOTLY_TEMPLATE,
        labels=dict(color=value_label, x="Year", y="Value chain link"),
        color_continuous_scale="YlGnBu",
    )
    _base_layout(fig, height)
    fig.update_layout(
        coloraxis_colorbar=dict(title=value_label),
        legend=dict(orientation="h"),
        margin=dict(l=170, r=30, t=60, b=55),
    )
    fig.update_traces(
        hovertemplate=(
            "Value chain link=%{y}<br>"
            "Year=%{x}<br>"
            f"{_metric_hover_label(metric)}=%{{z:,.0f}}<extra></extra>"
        )
    )

    y_labels = list(pivot_df.index)
    for divider_after in ["Processing", "Others"]:
        if divider_after in y_labels and y_labels.index(divider_after) < len(y_labels) - 1:
            fig.add_shape(
                type="line",
                xref="paper",
                x0=0,
                x1=1,
                yref="y",
                y0=y_labels.index(divider_after) + 0.5,
                y1=y_labels.index(divider_after) + 0.5,
                line=dict(color="#CBD5E1", width=1),
            )

    st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)
    if subtitle:
        st.caption(subtitle + _metric_caption_suffix(metric))


def _value_chain_side_mix(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Return annual Upstream / Downstream / Corporate mix based on value_chain_link mentions."""
    columns = ["year", "chain_side", "events", "metric_value", "share", "share_pct", "share_label", "hover_value"]
    if df.empty or "value_chain_link" not in df.columns or "event_id" not in df.columns or "year" not in df.columns:
        return pd.DataFrame(columns=columns)

    tmp = explode_dimension(df, "value_chain_link")
    dim_col = "value_chain_link_exploded"
    if tmp.empty or dim_col not in tmp.columns:
        return pd.DataFrame(columns=columns)

    keep_cols = ["event_id", "year", dim_col]
    if "deal_value_numeric" in tmp.columns:
        keep_cols.append("deal_value_numeric")
    tmp = tmp[keep_cols].dropna(subset=["year"])
    tmp["year"] = pd.to_numeric(tmp["year"], errors="coerce")
    tmp = tmp.dropna(subset=["year"])
    tmp["year"] = tmp["year"].astype(int)
    tmp[dim_col] = tmp[dim_col].astype(str).str.strip()
    tmp = tmp[(tmp[dim_col] != "") & (tmp[dim_col].str.lower() != "unknown")]
    if tmp.empty:
        return pd.DataFrame(columns=columns)

    if "deal_value_numeric" not in tmp.columns:
        tmp["deal_value_numeric"] = 0.0
    tmp["deal_value_numeric"] = pd.to_numeric(tmp["deal_value_numeric"], errors="coerce").fillna(0.0)
    tmp["chain_side"] = tmp[dim_col].map(VALUE_CHAIN_LINK_TO_CHAIN).fillna("Unknown")
    tmp = tmp.drop_duplicates(["event_id", "year", "chain_side"])

    result = (
        tmp.groupby(["year", "chain_side"])
        .agg(events=("event_id", "nunique"), metric_value=("deal_value_numeric", "sum"))
        .reset_index()
    )
    if result.empty:
        return pd.DataFrame(columns=columns)

    value_col = _metric_column(metric)
    if metric == METRIC_DEAL_VALUE:
        result = result[result["metric_value"] != 0]
    if result.empty:
        return pd.DataFrame(columns=columns)

    totals = result.groupby("year")[value_col].transform("sum")
    result = result[totals != 0].copy()
    totals = result.groupby("year")[value_col].transform("sum")
    result["share"] = result[value_col] / totals
    result["share_pct"] = result["share"] * 100
    result["share_label"] = result["share"].map(_format_share)
    result["hover_value"] = result[value_col].map(lambda value: _format_metric_value(value, metric))

    side_order = ["Upstream", "Downstream", "Corporate / Multi-Chain", "Unknown"]
    result["chain_side"] = pd.Categorical(result["chain_side"], categories=side_order, ordered=True)
    result = result.sort_values(["year", "chain_side"])
    result["chain_side"] = result["chain_side"].astype(str)
    return result


def render_upstream_downstream_mix(
    df: pd.DataFrame,
    title: str,
    metric: str,
    subtitle: str | None = None,
    height: int = 480,
) -> None:
    """Render annual Upstream / Downstream / Corporate mix as a 100% stacked bar."""
    chart_df = _value_chain_side_mix(df, metric)
    if chart_df.empty:
        if metric == METRIC_DEAL_VALUE:
            _empty_chart("No disclosed deal value available for upstream / downstream mix.")
        else:
            _empty_chart("No upstream / downstream mix data available for this selection.")
        return

    fig = px.bar(
        chart_df,
        x="year",
        y="share_pct",
        color="chain_side",
        title=title,
        template=PLOTLY_TEMPLATE,
        color_discrete_map=VALUE_CHAIN_COLORS,
        category_orders={"chain_side": ["Upstream", "Downstream", "Corporate / Multi-Chain", "Unknown"]},
        custom_data=["hover_value", "share_label", "events"],
        text="share_label",
    )
    fig.update_layout(barmode="stack")
    _base_layout(fig, height)
    fig.update_layout(
        yaxis_title=f"Share of {_metric_axis_label(metric).lower()}",
        xaxis_title="Year",
        legend=dict(orientation="h", yanchor="bottom", y=-0.30, xanchor="left", x=0),
        margin=dict(l=50, r=20, t=60, b=75),
    )
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    fig.update_xaxes(type="category")
    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        hovertemplate=(
            "Year=%{x}<br>"
            "Chain side=%{fullData.name}<br>"
            f"{_metric_hover_label(metric)}=%{{customdata[0]}}<br>"
            "Share=%{customdata[1]}<br>"
            "Event count=%{customdata[2]}<extra></extra>"
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)
    if subtitle:
        st.caption(subtitle + _metric_caption_suffix(metric))


def render_value_chain_evolution_module(
    df: pd.DataFrame,
    years_label: str,
) -> None:
    """Render the two-chart value chain evolution module."""
    st.markdown("#### Value Chain Evolution")
    st.markdown(
        "<div class='section-note'>Shows how activity extends across upstream, downstream, and corporate / multi-chain links over time. Switch between unique event count and disclosed deal value.</div>",
        unsafe_allow_html=True,
    )
    metric = _metric_selector("Value Chain Evolution metric", "metric_value_chain_evolution")

    render_value_chain_link_year_heatmap(
        df,
        f"Value chain link × year ordered heatmap ({years_label}, {_metric_chart_suffix(metric)})",
        metric,
        "Rows follow taxonomy order from upstream to downstream. Darker cells indicate greater activity in that value chain link and year.",
        height=640,
    )
    _chart_separator()

    render_upstream_downstream_mix(
        df,
        f"Upstream / downstream annual mix ({years_label}, {_metric_chart_suffix(metric)})",
        metric,
        "100% stacked bars summarize whether annual activity is weighted toward upstream, downstream, or corporate / multi-chain links. Events spanning multiple sides can contribute to more than one side.",
        height=500,
    )


# -----------------------------------------------------------------------------
# Geographic footprint map
# -----------------------------------------------------------------------------

def _clean_country_token(value: str) -> str:
    value = str(value).strip()
    return COUNTRY_NAME_NORMALIZATION.get(value, value)


def _country_mentions(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "country" not in df.columns or "event_id" not in df.columns:
        return pd.DataFrame(columns=["event_id", "country", "deal_value_numeric"])
    exploded = explode_dimension(df, "country")
    dim_col = "country_exploded"
    if exploded.empty or dim_col not in exploded.columns:
        return pd.DataFrame(columns=["event_id", "country", "deal_value_numeric"])

    if "deal_value_numeric" not in exploded.columns:
        exploded["deal_value_numeric"] = 0.0
    exploded["deal_value_numeric"] = pd.to_numeric(exploded["deal_value_numeric"], errors="coerce").fillna(0.0)

    rows: list[dict[str, object]] = []
    for row in exploded[["event_id", dim_col, "deal_value_numeric"]].dropna(subset=[dim_col]).itertuples(index=False):
        raw_country = str(getattr(row, dim_col)).strip()
        # Some entries use slash-separated geographic labels. Split them so country-level map points are not lost.
        tokens = [token.strip() for token in raw_country.split("/") if token.strip()]
        for token in tokens:
            country = _clean_country_token(token)
            if country in AGGREGATE_COUNTRY_LABELS:
                continue
            rows.append(
                {
                    "event_id": str(row.event_id),
                    "country": country,
                    "deal_value_numeric": float(row.deal_value_numeric or 0.0),
                }
            )

    result = pd.DataFrame(rows)
    if result.empty:
        return pd.DataFrame(columns=["event_id", "country", "deal_value_numeric"])
    return result.drop_duplicates(["event_id", "country"])


def _country_metric_df(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    tmp = _country_mentions(df)
    if tmp.empty:
        return pd.DataFrame(columns=["country", "events", "metric_value"])
    result = (
        tmp.groupby("country")
        .agg(events=("event_id", "nunique"), metric_value=("deal_value_numeric", "sum"))
        .reset_index()
    )
    if metric == METRIC_DEAL_VALUE:
        result = result[result["metric_value"] != 0]
    return result


def _country_map_scale_max(df: pd.DataFrame, metric: str) -> float:
    """Return max country metric for a fixed map color scale.

    This should be computed from the final cumulative period, not from the
    currently selected slider year, so the choropleth scale stays comparable
    as users move the cumulative year slider.
    """
    chart_df = _country_metric_df(df, metric)
    if chart_df.empty:
        return 0
    value_col = _metric_column(metric)
    return float(chart_df[value_col].max() or 0)


def render_country_distribution_map(
    df: pd.DataFrame,
    title: str,
    metric: str,
    subtitle: str | None = None,
    height: int = 600,
    color_range_max: float | None = None,
) -> None:
    if df.empty:
        _empty_chart("No country data available for this selection.")
        return

    chart_df = _country_metric_df(df, metric)
    if chart_df.empty:
        if metric == METRIC_DEAL_VALUE:
            _empty_chart("No disclosed deal value available for the country map.")
        else:
            _empty_chart("No mappable country data available for this selection.")
        return

    value_col = _metric_column(metric)
    value_label = _metric_axis_label(metric)
    chart_df = chart_df.sort_values(value_col, ascending=False)
    total = float(chart_df[value_col].sum())
    chart_df["share"] = chart_df[value_col] / total if total else 0
    chart_df["share_label"] = chart_df["share"].map(_format_share)
    chart_df["hover_value"] = chart_df[value_col].map(lambda value: _format_metric_value(value, metric))

    # Keep the map color scale fixed to the final cumulative period, so the
    # same shade means the same metric value as the user moves the year slider.
    scale_max = max(float(color_range_max or 0), float(chart_df[value_col].max() or 0), 1.0)

    fig = px.choropleth(
        chart_df,
        locations="country",
        locationmode="country names",
        color=value_col,
        hover_name="country",
        hover_data={"country": False, "events": True, "hover_value": True, "share_label": True},
        color_continuous_scale="Blues",
        range_color=(0, scale_max),
        title=title,
        template=PLOTLY_TEMPLATE,
        labels={value_col: value_label, "share_label": "Share", "events": "Event count"},
        projection="natural earth",
    )
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=60, b=20),
        paper_bgcolor="white",
        plot_bgcolor="white",
        title_font_size=16,
        font=dict(size=12, color="#111827"),
        coloraxis=dict(cmin=0, cmax=scale_max),
        coloraxis_colorbar=dict(title=value_label),
    )
    fig.update_geos(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#CBD5E1",
        showcountries=True,
        countrycolor="#E5E7EB",
        showland=True,
        landcolor="#F8FAFC",
        showocean=True,
        oceancolor="#FFFFFF",
    )
    fig.update_traces(
        hovertemplate=(
            "Country=%{hovertext}<br>"
            f"{_metric_hover_label(metric)}=%{{customdata[1]}}<br>"
            "Event count=%{customdata[0]}<br>"
            "Share=%{customdata[2]}<extra></extra>"
        )
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)
    if subtitle:
        excluded = ", ".join(sorted(label for label in AGGREGATE_COUNTRY_LABELS if label))
        st.caption(f"{subtitle}{_metric_caption_suffix(metric)} Aggregate geography labels excluded from the map: {excluded}.")


# -----------------------------------------------------------------------------
# Main rendering entry point
# -----------------------------------------------------------------------------

def _years_label(df: pd.DataFrame) -> str:
    if df.empty or "year" not in df.columns:
        return "all years"
    years = pd.to_numeric(df["year"], errors="coerce").dropna().astype(int).tolist()
    return f"{min(years)}-{max(years)}" if years else "all years"


def _cumulative_year_label(start_year: int | None, end_year: int | None) -> str:
    if start_year is None or end_year is None:
        return "all years"
    if int(start_year) == int(end_year):
        return str(int(end_year))
    return f"{int(start_year)}-{int(end_year)} cumulative"


def render_four_time_series_charts(df: pd.DataFrame) -> None:
    """Render the global charts controlled by sidebar filters.

    The first three charts remain annual time series. The value-chain section is
    a two-chart evolution module that shows both link-level change over time and
    annual upstream/downstream mix.
    """
    st.markdown("### Charts by current filter combination")
    st.markdown(
        "<div class='section-note'>Charts reflect the sidebar filters. Switch each module between unique event count and disclosed deal value. Semicolon-separated fields are exploded only for category aggregation.</div>",
        unsafe_allow_html=True,
    )

    if df.empty:
        _empty_chart("No events match the sidebar filters.")
        return

    years = _years_label(df)

    players_df = _time_series_by_dimension_metric(
        df,
        "company",
        multivalue=False,
        order=PLAYER_ORDER,
    )
    player_values = players_df["company"].dropna().astype(str).unique().tolist() if not players_df.empty else []
    player_category_order = _ordered_player_values(player_values)

    commodity_df = _time_series_by_dimension_metric(
        df,
        "commodity_group",
        multivalue=True,
        order=COMMODITY_GROUP_ORDER,
    )
    commodity_values = commodity_df["commodity_group"].dropna().astype(str).unique().tolist() if not commodity_df.empty else []
    commodity_category_order = _ordered_commodity_values(commodity_values)

    event_df = _time_series_by_dimension_metric(
        df,
        "event_type",
        multivalue=False,
        order=EVENT_TYPE_ORDER,
    )
    event_values = event_df["event_type"].dropna().astype(str).unique().tolist() if not event_df.empty else []
    event_type_category_order = _ordered_event_type_values(event_values)

    _chart_group_title(
        "Player Momentum",
        "Annual activity by company after applying sidebar filters. Players follow the strategic peer-set order defined in the taxonomy.",
    )
    player_metric = _metric_selector("Player Momentum metric", "metric_player_momentum")
    render_stacked_bar(
        players_df,
        "year",
        _metric_column(player_metric),
        "company",
        f"Player Momentum ({years}, {_metric_chart_suffix(player_metric)})",
        player_metric,
        "Players follow the strategic peer-set order; any unlisted players appear after the defined list.",
        category_orders={"company": player_category_order},
        height=540,
    )
    _chart_separator()

    _chart_group_title(
        "Commodity Exposure",
        "Annual activity by commodity group. Multi-value commodity fields are exploded for category aggregation.",
    )
    commodity_metric = _metric_selector("Commodity Exposure metric", "metric_commodity_exposure")
    render_stacked_bar(
        commodity_df,
        "year",
        _metric_column(commodity_metric),
        "commodity_group",
        f"Commodity Exposure ({years}, {_metric_chart_suffix(commodity_metric)})",
        commodity_metric,
        "Commodity groups follow taxonomy order; Unknown is stacked at the top when present.",
        color_discrete_map=commodity_color_map(commodity_values),
        category_orders={"commodity_group": commodity_category_order},
        height=540,
    )
    _chart_separator()

    _chart_group_title(
        "Strategic Movement Mix",
        "Annual mix of portfolio movements by event type. Colors follow event_group families to distinguish expansion-oriented and reduction-oriented movements.",
    )
    event_metric = _metric_selector("Strategic Movement Mix metric", "metric_strategic_movement_mix")
    render_stacked_bar(
        event_df,
        "year",
        _metric_column(event_metric),
        "event_type",
        f"Strategic Movement Mix ({years}, {_metric_chart_suffix(event_metric)})",
        event_metric,
        "Event types follow taxonomy order; Bankruptcy is stacked at the top when present. Colors follow event_group families.",
        color_discrete_map=event_type_color_map(event_values),
        category_orders={"event_type": event_type_category_order},
        height=560,
    )
    _chart_separator()

    render_value_chain_evolution_module(df, years)
    _chart_separator()

    _chart_group_title(
        "Geographic Footprint",
        "Cumulative distribution by country. Move the slider to see how country coverage builds from the first year to the selected end year.",
    )
    map_metric = _metric_selector("Geographic Footprint metric", "metric_geographic_footprint")
    map_start_year, map_end_year = _cumulative_year_slider(
        df,
        "Country map cumulative through year",
        "country_map_cumulative_end_year",
    )
    map_df = _filter_to_cumulative_year(df, map_start_year, map_end_year)
    map_year_options = _available_year_options(df)
    map_final_year = max(map_year_options) if map_year_options else map_end_year
    map_scale_df = _filter_to_cumulative_year(df, map_start_year, map_final_year)
    map_scale_max = _country_map_scale_max(map_scale_df, map_metric)
    map_label = _cumulative_year_label(map_start_year, map_end_year)
    map_scale_label = _cumulative_year_label(map_start_year, map_final_year)
    render_country_distribution_map(
        map_df,
        f"Geographic Footprint ({map_label}, {_metric_chart_suffix(map_metric)})",
        map_metric,
        f"Map shows cumulative {_metric_axis_label(map_metric).lower()} by country from the start year through the selected end year after the current sidebar filters. Color scale is fixed to the final {map_scale_label} maximum for year-to-year comparability.",
        height=620,
        color_range_max=map_scale_max,
    )
