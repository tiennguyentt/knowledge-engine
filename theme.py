"""Portfolio-matched theme for Streamlit apps.

Single-file, reusable: drop `theme.py` + `.streamlit/config.toml` into any
Streamlit app to get the tiennguyentt.github.io design language — dark
editor surface, indigo accent, IBM Plex Sans headings, JetBrains Mono
labels, git-diff details. Call `theme.inject()` once at the top of the app,
then build blocks with the helpers below (they return HTML strings; pass
them to `theme.card(...)` / `st.markdown(..., unsafe_allow_html=True)`).
"""

import html as _html

import streamlit as st

PALETTE = {
    "bg": "#0B0E14",
    "panel": "#0E1219",
    "line": "#1E2430",
    "text": "#E7EAF0",
    "dim": "#9AA4B2",
    "accent": "#7C8CFF",
    "add": "#3FB950",
    "del": "#F85149",
    "warn": "#F2A65A",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {
  background: #0B0E14; color: #E7EAF0;
  font-family: 'Inter', sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1080px; padding-top: 2.2rem; }

h1, h2, h3, [data-testid="stMetricValue"] {
  font-family: 'IBM Plex Sans', sans-serif !important; letter-spacing: -0.01em;
}
[data-testid="stSidebar"] {
  background: #0E1219; border-right: 1px solid #1E2430;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  font-family: 'JetBrains Mono', monospace !important; font-size: 12px !important;
  text-transform: uppercase; letter-spacing: .14em; color: #7C8CFF !important;
}
.stTabs [data-baseweb="tab-list"] { gap: 2px; border-bottom: 1px solid #1E2430; }
.stTabs [data-baseweb="tab"] {
  font-family: 'JetBrains Mono', monospace; font-size: 12px;
  letter-spacing: .06em; color: #9AA4B2; background: transparent;
}
.stTabs [aria-selected="true"] { color: #7C8CFF !important; }
[data-testid="stMetricLabel"] {
  font-family: 'JetBrains Mono', monospace; font-size: 11px !important;
  text-transform: uppercase; letter-spacing: .12em; color: #9AA4B2;
}
.stButton button, .stDownloadButton button {
  font-family: 'JetBrains Mono', monospace; font-size: 13px;
  border-radius: 6px; border: 1px solid #2A3242;
}
[data-testid="stExpander"] {
  border: 1px solid #1E2430; border-radius: 8px; background: #0E1219;
}
[data-testid="stExpander"] summary {
  font-family: 'JetBrains Mono', monospace; font-size: 12px;
  letter-spacing: .08em; text-transform: uppercase; color: #9AA4B2;
}
.stTextInput input, .stSelectbox div, .stRadio label { font-family: 'Inter', sans-serif; }

/* ---- custom blocks -------------------------------------------------- */
.se-kicker {
  font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #9AA4B2;
  text-transform: uppercase; letter-spacing: .14em; margin: 0 0 4px;
}
.se-kicker::before { content: '+ '; color: #3FB950; }
.se-spechead {
  display: flex; align-items: baseline; gap: 12px;
  border-bottom: 1px solid #1E2430; padding-bottom: 8px; margin: 4px 0 14px;
}
.se-spechead .sid { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #7C8CFF; }
.se-spechead .stitle {
  font-family: 'IBM Plex Sans', sans-serif; font-weight: 600; font-size: 18px; color: #E7EAF0;
}
.se-spechead .sstatus { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #9AA4B2; margin-left: auto; }
.se-card {
  border: 1px solid #1E2430; background: #0E1219; border-radius: 8px;
  padding: 14px 16px; margin: 0 0 10px;
}
.se-card .rowtop { display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap; }
.se-id { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #7C8CFF; }
.se-topic { font-family: 'IBM Plex Sans', sans-serif; font-weight: 600; color: #E7EAF0; }
.se-body { color: #C7CEDA; font-size: 14px; line-height: 1.55; margin-top: 6px; }
.se-chip {
  font-family: 'JetBrains Mono', monospace; font-size: 10.5px; letter-spacing: .06em;
  border: 1px solid #2A3242; border-radius: 999px; padding: 2px 10px;
  color: #9AA4B2; margin-left: auto; white-space: nowrap;
}
.se-quote {
  font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #8A94A6;
  border-left: 2px solid #2A3242; padding: 2px 0 2px 10px; margin: 8px 0 0;
}
.se-ac { color: #C7CEDA; font-size: 13.5px; margin: 4px 0 0 2px; }
.se-ac::before { content: '▸ '; color: #7C8CFF; }
.se-trace { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #6B7585; margin-top: 8px; }
.se-issue { color: #C7CEDA; font-size: 13px; margin-top: 4px; }
.se-issue::before { content: '! '; font-family: 'JetBrains Mono', monospace; color: #F2A65A; font-weight: 600; }
.se-bar { height: 6px; border-radius: 3px; background: #1E2430; margin-top: 6px; }
.se-bar > div { height: 6px; border-radius: 3px; background: #7C8CFF; }
.se-verdict-ship { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #3FB950; }
.se-verdict-revise { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #F2A65A; }
.se-block {
  border-left: 3px solid #F85149; background: rgba(248,81,73,.06);
  border-radius: 0 8px 8px 0; padding: 12px 14px; margin-top: 12px;
  color: #E7EAF0; font-size: 13.5px;
}
.se-conflict-win { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #3FB950; margin-top: 8px; }
.se-flag {
  font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #F2A65A;
  border: 1px dashed rgba(242,166,90,.5); border-radius: 6px;
  padding: 6px 10px; margin-top: 10px; display: inline-block;
}

/* ---- hero / red-team ------------------------------------------------- */
.se-hero-head {
  font-family: 'IBM Plex Sans', sans-serif; font-weight: 700; font-size: 30px;
  letter-spacing: -0.015em; color: #E7EAF0; line-height: 1.25; margin: 4px 0 6px;
}
.se-hero-sub { color: #9AA4B2; font-size: 15.5px; max-width: 780px; line-height: 1.6; }
.se-stats { display: flex; gap: 10px; flex-wrap: wrap; margin: 16px 0 4px; }
.se-stat {
  border: 1px solid #1E2430; background: #0E1219; border-radius: 8px;
  padding: 10px 16px; min-width: 130px;
}
.se-stat .v { font-family: 'IBM Plex Sans', sans-serif; font-weight: 600; font-size: 20px; color: #E7EAF0; }
.se-stat .v .from { color: #6B7585; font-size: 15px; }
.se-stat .v .delta { color: #3FB950; }
.se-stat .l { font-family: 'JetBrains Mono', monospace; font-size: 10.5px; letter-spacing: .1em; text-transform: uppercase; color: #9AA4B2; margin-top: 2px; }
.se-catch {
  border: 1px solid #1E2430; border-left: 3px solid #F85149; background: #0E1219;
  border-radius: 0 10px 10px 10px; padding: 16px 18px; margin: 0 0 12px;
}
.se-catch .chead { display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap; }
.se-catch .cnum { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #F85149; font-weight: 600; }
.se-catch .ctitle { font-family: 'IBM Plex Sans', sans-serif; font-weight: 600; font-size: 15.5px; color: #E7EAF0; }
.se-vs { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #6B7585; margin: 8px 0 2px; letter-spacing: .08em; }
.se-diff-del {
  font-family: 'JetBrains Mono', monospace; font-size: 12.5px; color: #FCA5A5;
  background: rgba(248,81,73,.08); border-left: 2px solid #F85149;
  padding: 6px 10px; margin-top: 6px; white-space: pre-wrap;
}
.se-diff-del::before { content: '- '; color: #F85149; font-weight: 600; }
.se-diff-add {
  font-family: 'JetBrains Mono', monospace; font-size: 12.5px; color: #86EFAC;
  background: rgba(63,185,80,.08); border-left: 2px solid #3FB950;
  padding: 6px 10px; margin-top: 2px; white-space: pre-wrap;
}
.se-diff-add::before { content: '+ '; color: #3FB950; font-weight: 600; }
.se-summon {
  font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #F85149;
  border: 1px solid rgba(248,81,73,.4); border-radius: 999px;
  padding: 2px 10px; display: inline-block; margin-top: 8px;
}
.se-gatehit { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #C7CEDA; margin-top: 5px; }
.se-gatehit .rid { color: #F85149; font-weight: 600; }
.se-gatehit .warn { color: #F2A65A; font-weight: 600; }
.se-stepper { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin: 8px 0 14px; font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: .06em; }
.se-step { border: 1px solid #2A3242; border-radius: 999px; padding: 3px 12px; color: #6B7585; }
.se-step.done { color: #3FB950; border-color: rgba(63,185,80,.4); }
.se-step.active { color: #7C8CFF; border-color: #7C8CFF; }
.se-step-arrow { color: #2A3242; }
.se-notes {
  border-top: 1px dashed #2A3242; margin-top: 10px; padding-top: 8px;
  font-family: 'JetBrains Mono', monospace; font-size: 11.5px; color: #8A94A6; line-height: 1.6;
}
.se-notes b { color: #9AA4B2; font-weight: 600; }
.se-noobj { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #6B7585; margin: 2px 0; }
.se-noobj::before { content: '○ '; color: #3FB950; }

/* ---- debate bubbles -------------------------------------------------- */
.se-turn {
  border: 1px solid #1E2430; border-left-width: 3px; background: #0E1219;
  border-radius: 0 10px 10px 10px; padding: 12px 14px; margin: 0 0 10px;
  animation: seFade .35s ease-out;
}
@keyframes seFade { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; } }
.se-turn .thead {
  display: flex; gap: 10px; align-items: baseline;
  font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: .08em;
}
.se-turn .trole { font-weight: 600; text-transform: uppercase; }
.se-turn .tstance { color: #9AA4B2; }
.se-turn .tround { color: #6B7585; margin-left: auto; }
.se-turn .tmsg { color: #C7CEDA; font-size: 13.5px; line-height: 1.55; margin-top: 6px; }
</style>
"""

ROLE_COLORS = {
    "po": PALETTE["accent"],
    "eng": PALETTE["warn"],
    "qa": PALETTE["add"],
    "arbiter": PALETTE["text"],
}


def esc(value) -> str:
    return _html.escape(str(value))


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def kicker(text: str) -> None:
    st.markdown(f'<p class="se-kicker">{esc(text)}</p>', unsafe_allow_html=True)


def section(sid: str, title: str, status: str = "") -> None:
    status_html = f'<span class="sstatus">{esc(status)}</span>' if status else ""
    st.markdown(
        f'<div class="se-spechead"><span class="sid">{esc(sid)}</span>'
        f'<span class="stitle">{esc(title)}</span>{status_html}</div>',
        unsafe_allow_html=True,
    )


def card(inner_html: str) -> None:
    st.markdown(f'<div class="se-card">{inner_html}</div>', unsafe_allow_html=True)


def bubble(role_key: str, role_label: str, stance: str, message: str, refs: list[str], rnd, color: str | None = None) -> str:
    color = color or ROLE_COLORS.get(role_key, PALETTE["dim"])
    refs_html = f' · {esc(", ".join(refs))}' if refs else ""
    return (
        f'<div class="se-turn" style="border-left-color:{color}">'
        f'<div class="thead"><span class="trole" style="color:{color}">{esc(role_label)}</span>'
        f'<span class="tstance">{esc(stance)}{refs_html}</span>'
        f'<span class="tround">round {rnd}</span></div>'
        f'<div class="tmsg">{esc(message)}</div></div>'
    )


def bar(value: int, max_value: int = 5) -> str:
    pct = max(0, min(100, round(value / max_value * 100)))
    return f'<div class="se-bar"><div style="width:{pct}%"></div></div>'
