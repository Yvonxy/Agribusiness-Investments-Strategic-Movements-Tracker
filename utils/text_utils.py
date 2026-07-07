from __future__ import annotations

from typing import Any

EMPTY_TOKENS = {"", "nan", "none", "null", "n/a", "na", "nat", "-", "--"}


def is_empty_like(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text.lower() in EMPTY_TOKENS


def clean_text(value: Any, unknown_if_blank: bool = False) -> str:
    if is_empty_like(value):
        return "Unknown" if unknown_if_blank else ""
    return str(value).strip()


def clean_text_preserve_semicolons(value: Any, unknown_if_blank: bool = False) -> str:
    text = clean_text(value, unknown_if_blank=unknown_if_blank)
    if not text or text == "Unknown":
        return text
    parts = [p.strip() for p in text.split(";") if p.strip()]
    return "; ".join(parts) if parts else ("Unknown" if unknown_if_blank else "")


def html_escape(text: Any) -> str:
    import html

    return html.escape("" if text is None else str(text))
