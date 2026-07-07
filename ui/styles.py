from __future__ import annotations

import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #F6F7F9;
            --card: #FFFFFF;
            --card-soft: #F8FAFC;
            --border: #E5E7EB;
            --border-strong: #CBD5E1;
            --text: #111827;
            --text-soft: #6B7280;
            --accent: #2563EB;
            --accent-soft: #DBEAFE;
            --shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
        }

        section[data-testid="stSidebar"] {
            background: #FFFFFF;
            border-right: 1px solid var(--border);
            width: 235px !important;
            min-width: 235px !important;
        }

        section[data-testid="stSidebar"] > div { padding-top: 1rem; }

        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 1450px;
        }

        h1, h2, h3 { letter-spacing: -0.02em; color: var(--text); }
        h1 { font-size: 1.65rem !important; margin-bottom: 0.18rem !important; }
        h2 { font-size: 1.25rem !important; }
        h3 { font-size: 1.05rem !important; }
        p, li, div { font-size: 0.94rem; }

        .hero {
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 0.95rem 1.05rem;
            box-shadow: var(--shadow);
            margin-bottom: 0.72rem;
        }

        .subtitle {
            color: var(--text-soft);
            font-size: 0.88rem;
        }

        .status-line {
            color: #475569;
            font-size: 0.82rem;
            margin-top: 0.35rem;
        }

        .section-note {
            color: #64748B;
            font-size: 0.82rem;
            margin: -0.15rem 0 0.45rem 0;
        }

        .mini-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.72rem 0.78rem;
            min-height: 82px;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
        }

        .mini-card .label {
            color: var(--text-soft);
            font-size: 0.74rem;
            margin-bottom: 0.20rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .mini-card .value {
            color: var(--text);
            font-size: 1.42rem;
            line-height: 1.22;
            font-weight: 720;
        }

        .mini-card .note {
            color: var(--text-soft);
            font-size: 0.74rem;
            margin-top: 0.18rem;
        }

        .chip {
            display: inline-block;
            padding: 0.16rem 0.46rem;
            margin: 0.10rem 0.18rem 0.10rem 0;
            border-radius: 999px;
            background: #EEF2FF;
            border: 1px solid #C7D2FE;
            color: #3730A3;
            font-size: 0.75rem;
            white-space: nowrap;
        }

        .detail-card {
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.9rem 1rem;
            box-shadow: var(--shadow);
            margin-top: 0.5rem;
        }

        .evidence-box {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 0.85rem;
            white-space: pre-wrap;
            line-height: 1.45;
            color: #1F2937;
        }

        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 0.62rem 0.72rem;
            box-shadow: 0 6px 16px rgba(15,23,42,0.04);
        }

        div[data-testid="stMetricLabel"] p {
            color: var(--text-soft) !important;
            font-size: 0.75rem !important;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.06rem !important;
            color: var(--text) !important;
        }

        .stDataFrame, .stTable {
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid var(--border);
        }

        button, div[data-testid="stDownloadButton"] button {
            border-radius: 10px !important;
        }

        .stExpander {
            border-color: var(--border) !important;
            background: #FFFFFF !important;
            border-radius: 13px !important;
            box-shadow: 0 5px 15px rgba(15,23,42,0.04);
        }

        [data-testid="stFileUploader"] {
            background: #FFFFFF;
            border: 1px dashed var(--border-strong);
            border-radius: 13px;
            padding: 0.35rem 0.5rem;
        }

        hr { border-color: var(--border); margin-top: 1.1rem; margin-bottom: 1.1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
