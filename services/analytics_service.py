from __future__ import annotations

from typing import Iterable

import pandas as pd
from config import (
    COMMODITY_GROUP_ORDER,
    MULTIVALUE_FIELDS,
    VALUE_CHAIN_LINK_ORDER,
)
from utils.date_utils import available_years
from utils.multivalue import explode_dimension, filter_by_multivalue, unique_values_from_multivalue
from utils.text_utils import is_empty_like



def get_available_years(df: pd.DataFrame) -> list[int]:
    return available_years(df)


def filter_by_year_range(df: pd.DataFrame, year_range: tuple[int, int] | list[int] | None) -> pd.DataFrame:
    if df.empty or not year_range or "year" not in df.columns:
        return df.copy()
    start, end = int(year_range[0]), int(year_range[1])
    years = pd.to_numeric(df["year"], errors="coerce")
    return df[(years >= start) & (years <= end)].copy()


def unique_event_count(df: pd.DataFrame) -> int:
    return 0 if df.empty or "event_id" not in df.columns else int(df["event_id"].nunique())


def unique_count(df: pd.DataFrame, column: str, multivalue: bool = False) -> int:
    if df.empty or column not in df.columns:
        return 0
    if multivalue:
        return len([v for v in unique_values_from_multivalue(df, column) if v != "Unknown"])
    values = df[column].dropna().astype(str).str.strip()
    values = values[(values != "") & (values != "Unknown")]
    return int(values.nunique())


def distinct_values(df: pd.DataFrame, column: str, include_all: bool = False, multivalue: bool | None = None) -> list[str]:
    if column == "has_deal_value":
        values = ["Yes", "No"]
        return (["All"] + values) if include_all else values
    if df.empty or column not in df.columns:
        return ["All"] if include_all else []
    if multivalue is None:
        multivalue = column in MULTIVALUE_FIELDS
    if multivalue:
        values = unique_values_from_multivalue(df, column)
    else:
        series = df[column].dropna().astype(str).str.strip()
        values = sorted([v for v in series.unique().tolist() if v], key=lambda x: (x == "Unknown", x.lower()))
    return (["All"] + values) if include_all else values


def filter_exact(df: pd.DataFrame, column: str, selected_values: Iterable[str]) -> pd.DataFrame:
    selected = [v for v in selected_values if v and v != "All"]
    if not selected or df.empty or column not in df.columns:
        return df.copy()
    return df[df[column].astype(str).isin(selected)].copy()


def filter_has_deal_value(df: pd.DataFrame, selected_values: Iterable[str]) -> pd.DataFrame:
    selected = [v for v in selected_values if v and v != "All"]
    if not selected:
        return df.copy()
    has_value = df["deal_value"].apply(lambda x: not is_empty_like(x)) if "deal_value" in df.columns else pd.Series(False, index=df.index)
    if "Yes" in selected and "No" not in selected:
        return df[has_value].copy()
    if "No" in selected and "Yes" not in selected:
        return df[~has_value].copy()
    return df.copy()


def apply_advanced_filters(df: pd.DataFrame, filters: dict[str, list[str]]) -> pd.DataFrame:
    result = df.copy()
    for column, selected in filters.items():
        selected_clean = [v for v in selected if v and v != "All"] if selected else []
        if not selected_clean:
            continue
        if column == "has_deal_value":
            result = filter_has_deal_value(result, selected_clean)
        elif column in MULTIVALUE_FIELDS:
            result = filter_by_multivalue(result, column, selected_clean)
        else:
            result = filter_exact(result, column, selected_clean)
    return result


def count_by_dimension(df: pd.DataFrame, column: str, multivalue: bool = False, top_n: int | None = 15) -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return pd.DataFrame(columns=[column, "events"])
    if multivalue:
        tmp = explode_dimension(df, column)
        dim_col = f"{column}_exploded"
    else:
        tmp = df.copy()
        dim_col = column
    tmp = tmp[["event_id", dim_col]].dropna()
    tmp[dim_col] = tmp[dim_col].astype(str).str.strip()
    tmp = tmp[tmp[dim_col] != ""]
    tmp = tmp.drop_duplicates(["event_id", dim_col])
    result = tmp.groupby(dim_col)["event_id"].nunique().reset_index(name="events")
    result = result.sort_values("events", ascending=False).rename(columns={dim_col: column})
    if top_n:
        result = result.head(top_n)
    return result


def _ordered_values(values: list[str], order: list[str]) -> list[str]:
    order_index = {value: idx for idx, value in enumerate(order)}
    return sorted(values, key=lambda v: (order_index.get(v, 10_000), str(v).lower()))


def top_values(df: pd.DataFrame, column: str, multivalue: bool, top_n: int | None, order: list[str] | None = None) -> list[str]:
    vals = count_by_dimension(df, column, multivalue=multivalue, top_n=None)
    if vals.empty:
        return []
    if order:
        ordered = _ordered_values(vals[column].tolist(), order)
        if top_n:
            # Keep top_n by count, then display those values in taxonomy order.
            by_count = vals.sort_values("events", ascending=False).head(top_n)[column].tolist()
            return _ordered_values(by_count, order)
        return ordered
    return vals.sort_values("events", ascending=False).head(top_n)[column].tolist() if top_n else vals[column].tolist()


def time_series_by_dimension(
    df: pd.DataFrame,
    column: str,
    multivalue: bool = False,
    top_n: int = 10,
    include_others: bool = True,
    order: list[str] | None = None,
) -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return pd.DataFrame(columns=["year", column, "events"])
    selected_values = top_values(df, column, multivalue=multivalue, top_n=top_n, order=order)
    if multivalue:
        tmp = explode_dimension(df, column)
        dim_col = f"{column}_exploded"
    else:
        tmp = df.copy()
        dim_col = column
    tmp = tmp[["event_id", "year", dim_col]].dropna(subset=["year"])
    tmp["year"] = pd.to_numeric(tmp["year"], errors="coerce")
    tmp = tmp.dropna(subset=["year"])
    tmp[dim_col] = tmp[dim_col].astype(str).str.strip()
    tmp = tmp[tmp[dim_col] != ""]
    if top_n and include_others:
        tmp[dim_col] = tmp[dim_col].where(tmp[dim_col].isin(selected_values), "Others")
        category_order = selected_values + (["Others"] if "Others" not in selected_values else [])
    elif selected_values:
        tmp = tmp[tmp[dim_col].isin(selected_values)]
        category_order = selected_values
    else:
        category_order = []
    tmp = tmp.drop_duplicates(["event_id", "year", dim_col])
    if tmp.empty:
        return pd.DataFrame(columns=["year", column, "events"])
    result = tmp.groupby([tmp["year"].astype(int), dim_col])["event_id"].nunique().reset_index(name="events")
    result = result.rename(columns={dim_col: column})
    if category_order:
        result[column] = pd.Categorical(result[column], categories=category_order, ordered=True)
        result = result.sort_values(["year", column])
        result[column] = result[column].astype(str)
    return result


def heatmap_by_year(
    df: pd.DataFrame,
    column: str,
    multivalue: bool = True,
    top_n: int = 12,
    order: list[str] | None = None,
) -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return pd.DataFrame()
    selected_values = top_values(df, column, multivalue=multivalue, top_n=top_n, order=order)
    if multivalue:
        tmp = explode_dimension(df, column)
        dim_col = f"{column}_exploded"
    else:
        tmp = df.copy()
        dim_col = column
    tmp = tmp[["event_id", "year", dim_col]].dropna(subset=["year"])
    tmp["year"] = pd.to_numeric(tmp["year"], errors="coerce")
    tmp = tmp.dropna(subset=["year"])
    tmp[dim_col] = tmp[dim_col].astype(str).str.strip()
    if selected_values:
        tmp = tmp[tmp[dim_col].isin(selected_values)]
    tmp = tmp.drop_duplicates(["event_id", "year", dim_col])
    if tmp.empty:
        return pd.DataFrame()
    pivot = tmp.pivot_table(index=dim_col, columns=tmp["year"].astype(int), values="event_id", aggfunc=pd.Series.nunique, fill_value=0)
    if order:
        idx = [v for v in order if v in pivot.index]
        extra = [v for v in pivot.index if v not in idx]
        pivot = pivot.loc[idx + sorted(extra)]
    else:
        totals = pivot.sum(axis=1).sort_values(ascending=False)
        pivot = pivot.loc[totals.index]
    pivot.columns = pivot.columns.astype(str)
    return pivot


def quality_summary(df: pd.DataFrame, upload_summary: dict | None = None) -> dict:
    years = available_years(df)
    return {
        "total_events": unique_event_count(df),
        "companies": unique_count(df, "company"),
        "countries": unique_count(df, "country", multivalue=True),
        "duplicate_event_id_count": upload_summary.get("duplicates_removed", 0) if upload_summary else max(0, len(df) - unique_event_count(df)),
        "missing_source_url_count": int(df["source_url"].apply(is_empty_like).sum()) if "source_url" in df.columns else 0,
        "missing_evidence_text_count": int(df["evidence_text"].apply(is_empty_like).sum()) if "evidence_text" in df.columns else 0,
        "missing_deal_value_count": int(df["deal_value"].apply(is_empty_like).sum()) if "deal_value" in df.columns else 0,
        "unknown_commodity_count": int(df["commodity_group"].astype(str).str.lower().isin(["", "unknown"]).sum()) if "commodity_group" in df.columns else 0,
        "unknown_value_chain_count": int(df["value_chain"].astype(str).str.lower().isin(["", "unknown"]).sum()) if "value_chain" in df.columns else 0,
        "year_coverage": f"{min(years)}–{max(years)}" if years else "Unknown",
        "last_loaded_timestamp": df["loaded_at"].dropna().astype(str).max() if "loaded_at" in df.columns and not df.empty else "Not loaded",
    }


def value_chain_order() -> list[str]:
    return VALUE_CHAIN_LINK_ORDER


def commodity_group_order() -> list[str]:
    return COMMODITY_GROUP_ORDER
