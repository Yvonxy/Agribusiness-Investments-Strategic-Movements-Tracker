# Agribusiness Strategic Investment Tracker v2 Filter Dashboard

A strictly CSV-driven Streamlit executive dashboard for agribusiness strategic investment and portfolio movement events.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data workflow

- Upload a structured CSV through the app.
- The app validates, normalizes, deduplicates by `event_id`, stores data in SQLite, and saves a local copy as `data/latest_events.csv`.
- No scraping, crawling, annual report parsing, LLM extraction, rule-based classification, or mock sample data is included.

## UI logic

- Sidebar has four global filters only:
  - Players
  - Commodity Group
  - Event Type
  - Value Chain Link
- The main chart area always shows four time-series views:
  - Players time series
  - Commodity group time series
  - Event type time series
  - Value chain link time series
- All four charts and the event list update from the selected sidebar filter combination.
- Summary cards reflect the current filter combination.
- Event details are rendered only for the selected event, not as a large list of expanders.

## Visual logic

- Event type charts use `event_group`-based color families.
- Commodity group charts use stable taxonomy colors.
- Value chain link charts follow the upstream-to-downstream taxonomy order.
- The interface uses a light, PPT-friendly executive dashboard style.

## Upload rerun fix

This version keeps the Streamlit upload rerun guard from the previous fix. It prevents the same uploaded file from being reprocessed repeatedly after `st.rerun()`.
