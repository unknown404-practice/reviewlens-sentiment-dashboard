"""
ReviewLens Streamlit Application Wrapper
========================================
Thin, production-ready host for the ReviewLens custom HTML/CSS/JavaScript dashboard.
Reads API_BASE_URL safely, injects it without template collisions, and renders the
responsive analytics application.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


# 1. Page Configuration
st.set_page_config(
    page_title="ReviewLens — Sentiment Dashboard",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom minimal CSS to tighten Streamlit's default container padding
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        max-width: 100%;
    }
    header[data-testid="stHeader"] {
        display: none;
    }
    footer {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_api_base_url() -> str:
    """
    Resolve API_BASE_URL following precedence:
    1. Environment variable API_BASE_URL
    2. Streamlit secret API_BASE_URL (if defined)
    3. Fallback: http://127.0.0.1:8000
    """
    url = os.getenv("API_BASE_URL")
    if not url:
        try:
            if hasattr(st, "secrets") and "API_BASE_URL" in st.secrets:
                url = str(st.secrets["API_BASE_URL"])
        except Exception:
            pass

    if not url:
        url = "http://127.0.0.1:8000"

    cleaned = url.strip()
    if cleaned.endswith("/"):
        cleaned = cleaned[:-1]
    return cleaned


def build_dashboard_html() -> str:
    """
    Load HTML, CSS, and JS from the frontend/ directory, inject the JSON-safe
    API_BASE_URL token, and combine into a unified iframe document.
    """
    root = Path(__file__).resolve().parent
    frontend_dir = root / "frontend"

    html_path = frontend_dir / "dashboard.html"
    css_path = frontend_dir / "dashboard.css"
    js_path = frontend_dir / "dashboard.js"

    missing_files = []
    for p in (html_path, css_path, js_path):
        if not p.exists():
            missing_files.append(p.name)

    if missing_files:
        st.error(
            f"ReviewLens frontend assets are missing: {', '.join(missing_files)}. "
            "Please ensure the frontend/ directory is intact."
        )
        st.stop()

    try:
        html_content = html_path.read_text(encoding="utf-8")
        css_content = css_path.read_text(encoding="utf-8")
        js_content = js_path.read_text(encoding="utf-8")
    except Exception as exc:
        st.error(f"Failed to load frontend assets: {exc}")
        st.stop()

    api_url = get_api_base_url()
    # Safely replace token without Python string formatting collisions
    json_escaped_url = json.dumps(api_url)
    js_injected = js_content.replace('"__API_BASE_URL__"', json_escaped_url).replace("'__API_BASE_URL__'", json_escaped_url).replace("__API_BASE_URL__", json_escaped_url)

    # Combine into a self-contained iframe document
    combined_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ReviewLens Dashboard</title>
  <style>
{css_content}
  </style>
</head>
<body>
{html_content}
  <script>
{js_injected}
  </script>
</body>
</html>
"""
    return combined_document


def main() -> None:
    """Main Streamlit execution routine."""
    html_document = build_dashboard_html()

    # Render custom responsive HTML/CSS/JS dashboard
    components.html(
        html_document,
        height=2200,
        scrolling=True,
    )

    # Native transparency caption
    st.caption(
        "🔍 ReviewLens uses VADER for transparent lexicon-based sentiment analysis. "
        "Demo data is processed local project data."
    )


if __name__ == "__main__":
    main()
