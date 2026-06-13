"""Design tokens and layout defaults for the OSS Health dashboard.

Single source of truth for colours, typography, and Plotly layout config.
Import from here — never hard-code colour values in chart or page modules.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Colour palette  (GitHub-inspired dark theme)
# ---------------------------------------------------------------------------

COLORS = {
    "primary": "#58a6ff",       # GitHub blue
    "secondary": "#8b949e",     # muted grey
    "accent": "#f78166",        # orange
    "success": "#3fb950",       # green
    "danger": "#f85149",        # red
    "purple": "#bc8cff",
    "bg": "#0d1117",            # dark background
    "card_bg": "#161b22",       # card / surface
    "text": "#e6edf3",          # primary text
    "text_muted": "#8b949e",    # secondary text
    "border": "#30363d",        # borders & dividers
}

EVENT_COLORS = {
    "fork": "#8b949e",
    "comment": "#58a6ff",
    "issue_opened": "#f78166",
    "pr_opened": "#bc8cff",
    "pr_merged": "#3fb950",
    "review": "#d2a8ff",
}

# ---------------------------------------------------------------------------
# Funnel constants
# ---------------------------------------------------------------------------

FUNNEL_ORDER = [
    "engaged", "forked", "pr_opened", "merged", "repeat_contributor",
]

FUNNEL_LABELS = {
    "engaged": "Engaged (comment/review only)",
    "forked": "Forked (no PR yet)",
    "pr_opened": "PR Opened (not merged)",
    "merged": "Merged (1 PR)",
    "repeat_contributor": "Repeat Contributor (>1 PR)",
}

# ---------------------------------------------------------------------------
# Plotly layout defaults
# ---------------------------------------------------------------------------

LAYOUT_DEFAULTS: dict = dict(
    template="plotly_dark",
    paper_bgcolor=COLORS["bg"],
    plot_bgcolor=COLORS["bg"],
    font=dict(family="Inter, system-ui, sans-serif", color=COLORS["text"], size=13),
    margin=dict(l=80, r=30, t=40, b=50),
    hoverlabel=dict(bgcolor=COLORS["card_bg"], font_size=12),
)

# ---------------------------------------------------------------------------
# CSS  (string-interpolated once at import time)
# ---------------------------------------------------------------------------

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    background: %(bg)s; color: %(text)s;
    font-family: Inter, system-ui, -apple-system, sans-serif;
    line-height: 1.6;
}
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
header {
    border-bottom: 1px solid %(border)s;
    padding: 24px 0; margin-bottom: 32px;
}
header h1 { font-size: 1.6rem; font-weight: 600; }
header p { color: %(text_muted)s; font-size: 0.9rem; margin-top: 4px; }

.kpi-row {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px; margin-bottom: 32px;
}
.kpi-card {
    background: %(card_bg)s; border: 1px solid %(border)s;
    border-radius: 8px; padding: 20px;
}
.kpi-card .value { font-size: 2rem; font-weight: 700; }
.kpi-card .label { color: %(text_muted)s; font-size: 0.85rem; margin-top: 4px; }

.chart-section { margin-bottom: 40px; }
.chart-section .section-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 12px;
}
.chart-section h2 { font-size: 1.1rem; font-weight: 600; }
.chart-section a.detail-link {
    color: %(primary)s; text-decoration: none; font-size: 0.85rem;
}
.chart-section a.detail-link:hover { text-decoration: underline; }

.two-col {
    display: grid; grid-template-columns: 1fr 1fr; gap: 24px;
}
@media (max-width: 768px) { .two-col { grid-template-columns: 1fr; } }

footer {
    border-top: 1px solid %(border)s; padding: 24px 0; margin-top: 40px;
    color: %(text_muted)s; font-size: 0.8rem; text-align: center;
}
nav a { color: %(primary)s; text-decoration: none; margin: 0 12px; }
nav a:hover { text-decoration: underline; }

.range-btns {
    display: flex; gap: 4px; margin-bottom: 8px;
}
.range-btns button {
    background: %(card_bg)s; color: %(text)s; border: 1px solid %(border)s;
    border-radius: 4px; padding: 3px 10px; font-size: 0.8rem;
    cursor: pointer; font-family: inherit;
}
.range-btns button:hover { border-color: %(primary)s; }
.range-btns button.active {
    background: %(primary)s; color: #fff; border-color: %(primary)s;
}
""" % COLORS
