from __future__ import annotations

import hashlib

import streamlit as st

from services.csv_service import process_uploaded_csv, save_latest_csv
from services.db import replace_events


def _uploaded_file_signature(file) -> str:
    """Build a stable signature so Streamlit reruns do not reprocess the same upload forever."""
    data = file.getvalue()
    digest = hashlib.md5(data).hexdigest()
    size = getattr(file, "size", len(data))
    name = getattr(file, "name", "uploaded.csv")
    if hasattr(file, "seek"):
        file.seek(0)
    return f"{name}:{size}:{digest}"


def render_upload_panel() -> dict | None:
    """Minimal CSV upload UI. Replace local dataset by default.

    Important: Streamlit keeps the uploaded file object in widget state across reruns.
    Without a file signature guard, calling st.rerun() after a successful upload creates
    a process-upload-rerun loop and the dashboard never reaches the chart section.
    """
    pending_success = st.session_state.pop("upload_success_message", None)
    if pending_success:
        st.success(pending_success)

    file = st.file_uploader("Upload CSV", type=["csv"], accept_multiple_files=False, label_visibility="visible")

    if file is None:
        return st.session_state.get("last_upload_summary")

    signature = _uploaded_file_signature(file)
    if st.session_state.get("processed_upload_signature") == signature:
        # The same file is still present after a rerun. Do not process it again.
        return st.session_state.get("last_upload_summary")

    try:
        cleaned_df, upload_summary, validation = process_uploaded_csv(file)
    except Exception as exc:
        st.error(f"CSV read failed: {exc}")
        return None

    if not validation.ok:
        for error in validation.errors:
            st.error(error)
        if validation.missing_critical_columns:
            st.code("\n".join(validation.missing_critical_columns), language="text")
        return None

    for warning in validation.warnings:
        st.warning(warning)

    replace_events(cleaned_df)
    save_latest_csv(cleaned_df)

    unique_events = cleaned_df["event_id"].nunique() if "event_id" in cleaned_df.columns else len(cleaned_df)
    st.session_state["last_upload_summary"] = upload_summary
    st.session_state["processed_upload_signature"] = signature
    st.session_state["upload_success_message"] = f"CSV loaded successfully. {unique_events} unique events stored."
    st.rerun()

    return upload_summary
