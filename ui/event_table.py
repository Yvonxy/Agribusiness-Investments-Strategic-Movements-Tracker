from __future__ import annotations

import pandas as pd
import streamlit as st

from config import TABLE_COLUMNS


def get_table_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    table_df = df.drop_duplicates("event_id").copy()
    sort_cols = [col for col in ["year", "event_date", "company"] if col in table_df.columns]
    if sort_cols:
        ascending = [False if c == "year" else True for c in sort_cols]
        table_df = table_df.sort_values(sort_cols, ascending=ascending)
    return table_df


def render_event_table(df: pd.DataFrame) -> pd.DataFrame:
    st.markdown("### Filtered event list")
    if df.empty:
        st.info("No events match the current filters.")
        return df

    table_df = get_table_df(df)
    st.markdown(f"<div class='section-note'>Filtered events: <b>{table_df['event_id'].nunique()}</b></div>", unsafe_allow_html=True)
    columns = [col for col in TABLE_COLUMNS if col in table_df.columns]
    st.dataframe(
        table_df[columns],
        use_container_width=True,
        hide_index=True,
        height=380,
        column_config={
            "source_url": st.column_config.LinkColumn("source_url", display_text="Open source"),
            "source_title": st.column_config.TextColumn("source_title", width="medium"),
            "commodity_subcategory": st.column_config.TextColumn("commodity_subcategory", width="medium"),
            "value_chain_link": st.column_config.TextColumn("value_chain_link", width="medium"),
        },
    )
    return table_df


def render_export_button(table_df: pd.DataFrame) -> None:
    if table_df.empty:
        return
    csv = table_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "Export filtered events",
        data=csv,
        file_name="filtered_agribusiness_events.csv",
        mime="text/csv",
        use_container_width=False,
    )
