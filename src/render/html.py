"""HTML generation helpers — page shell, KPI cards, Plotly div wrappers.

All interactive JS (range buttons, click-to-open, auto Y-rescale) lives
here so chart builders stay pure Plotly figures with no HTML knowledge.
"""

from __future__ import annotations

import json
from datetime import datetime

import plotly.graph_objects as go

from .theme import COLORS, CSS

# ---------------------------------------------------------------------------
# Range-button config (rendered as HTML buttons via JS)
# ---------------------------------------------------------------------------

_RANGE_OPTIONS = [
    {"label": "1M", "months": 1},
    {"label": "3M", "months": 3},
    {"label": "6M", "months": 6},
    {"label": "1Y", "months": 12},
    {"label": "All", "months": 0},
]

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

NAV = [
    ("Overview", "index.html"),
    ("Weekly Pulse", "weekly_pulse.html"),
    ("Response Times", "response_times.html"),
    ("Open Items", "open_items.html"),
    ("Contributors", "contributors.html"),
]

# ---------------------------------------------------------------------------
# Div-id counter (module-level, reset per render run)
# ---------------------------------------------------------------------------

_DIV_COUNTER = 0


def reset_div_counter() -> None:
    """Reset between render runs (important when called multiple times)."""
    global _DIV_COUNTER
    _DIV_COUNTER = 0


def _next_div_id() -> str:
    global _DIV_COUNTER
    _DIV_COUNTER += 1
    return f"plot-{_DIV_COUNTER}"


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def plotly_div(fig: go.Figure, div_id: str | None = None) -> str:
    """Render a Plotly figure to an HTML div string (no full page)."""
    return fig.to_html(
        include_plotlyjs=False,
        full_html=False,
        div_id=div_id,
        config={"displayModeBar": True, "responsive": True},
    )


def time_series_div(
    fig: go.Figure,
    clickable_url_index: int | None = None,
    default_months: int | None = None,
) -> str:
    """Render a time-series figure with custom range buttons and auto Y-rescale.

    Parameters
    ----------
    clickable_url_index:
        If set, clicking a data point opens the URL found at this index
        in the point's customdata array.
    default_months:
        If set, the chart initially zooms to the last N months instead of
        showing all data (0 = All).
    """
    did = _next_div_id()
    btn_id = f"rng-{did}"
    html = plotly_div(fig, div_id=did)

    # Build HTML buttons
    btn_html = f'<div class="range-btns" id="{btn_id}">'
    for opt in _RANGE_OPTIONS:
        m = opt["months"]
        active = ""
        if default_months is not None and m == default_months:
            active = ' class="active"'
        elif default_months is None and m == 0:
            active = ' class="active"'
        btn_html += f'<button data-months="{m}"{active}>{opt["label"]}</button>'
    btn_html += "</div>"

    # Click-to-open handler (optional)
    click_js = ""
    if clickable_url_index is not None:
        click_js = f"""
    gd.on('plotly_click', function(data) {{
        var pt = data.points[0];
        if (pt && pt.customdata && pt.customdata[{clickable_url_index}]) {{
            window.open(pt.customdata[{clickable_url_index}], '_blank');
        }}
    }});"""

    default_m = default_months if default_months is not None else 0

    script = f"""
<script>
(function() {{
    var gd = document.getElementById('{did}');
    if (!gd) return;
    {click_js}

    // Gather all x timestamps and compute data bounds
    var allX = [];
    gd.data.forEach(function(t) {{
        if (t.x) for (var i = 0; i < t.x.length; i++) allX.push(new Date(t.x[i]).getTime());
    }});
    var dataMax = allX.length ? new Date(Math.max.apply(null, allX)) : new Date();
    var dataMin = allX.length ? new Date(Math.min.apply(null, allX)) : new Date();

    // Detect if Y-axis is categorical (string values — no numeric rescale)
    var isCategoricalY = false;
    gd.data.forEach(function(t) {{
        if (t.y && t.y.length && typeof t.y[0] === 'string') isCategoricalY = true;
    }});

    function setRange(months) {{
        var x0, x1 = dataMax.toISOString();
        if (months === 0) {{
            x0 = dataMin.toISOString();
        }} else {{
            var d = new Date(dataMax);
            d.setMonth(d.getMonth() - months);
            x0 = d.toISOString();
        }}
        Plotly.relayout(gd, {{'xaxis.range': [x0, x1]}});
    }}

    function rescaleY() {{
        if (isCategoricalY) return;
        var range = gd.layout.xaxis.range;
        if (!range || range.length < 2) return;
        var lo = new Date(range[0]).getTime(), hi = new Date(range[1]).getTime();
        if (isNaN(lo) || isNaN(hi)) return;
        var yMax = 0;
        gd.data.forEach(function(trace) {{
            if (!trace.x) return;
            for (var i = 0; i < trace.x.length; i++) {{
                var t = new Date(trace.x[i]).getTime();
                if (t >= lo && t <= hi) {{
                    var v = Math.abs(trace.y[i]);
                    if (v > yMax) yMax = v;
                }}
            }}
        }});
        if (yMax > 0) {{
            Plotly.relayout(gd, {{'yaxis.range': [0, yMax * 1.1], 'yaxis.autorange': false}});
        }}
    }}

    // Wire up custom range buttons
    var btns = document.querySelectorAll('#{btn_id} button');
    btns.forEach(function(btn) {{
        btn.addEventListener('click', function() {{
            btns.forEach(function(b) {{ b.classList.remove('active'); }});
            btn.classList.add('active');
            setRange(parseInt(btn.dataset.months));
            setTimeout(rescaleY, 50);
        }});
    }});

    // Auto Y-rescale on drag-zoom / rangeslider interaction
    var skipNext = false;
    gd.on('plotly_relayout', function(ed) {{
        if (skipNext) {{ skipNext = false; return; }}
        var hasX = ed['xaxis.range[0]'] !== undefined
                || ed['xaxis.range'] !== undefined;
        if (!hasX) return;
        skipNext = true;
        rescaleY();
    }});

    // Apply default range
    if ({default_m} > 0) {{
        setRange({default_m});
        setTimeout(rescaleY, 50);
    }}
}})();
</script>"""
    return btn_html + html + script


def clickable_plotly_div(
    fig: go.Figure, div_id: str, url_index: int = 3,
) -> str:
    """Render a Plotly figure with click-to-open-URL behavior.

    Parameters
    ----------
    url_index:
        Position of the URL in the customdata array (default 3).
    """
    html = plotly_div(fig, div_id=div_id)
    script = f"""
<script>
(function() {{
    var el = document.getElementById('{div_id}');
    if (!el) return;
    el.on('plotly_click', function(data) {{
        var pt = data.points[0];
        if (pt && pt.customdata && pt.customdata[{url_index}]) {{
            window.open(pt.customdata[{url_index}], '_blank');
        }}
    }});
}})();
</script>"""
    return html + script


# ---------------------------------------------------------------------------
# Page-level wrappers
# ---------------------------------------------------------------------------

def page_shell(
    title: str,
    body: str,
    nav_links: list[tuple[str, str]] | None = None,
) -> str:
    """Wrap body HTML in a full page with Plotly JS, CSS, and nav."""
    nav_html = ""
    if nav_links:
        links = "".join(
            f'<a href="{href}">{label}</a>' for label, href in nav_links
        )
        nav_html = f"<nav>{links}</nav>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div class="container">
{body}
<footer>
    Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} &middot;
    <a href="https://github.com/drkrillo/oss-health-metrics" style="color:{COLORS['primary']}">oss-health-metrics</a>
    {nav_html}
</footer>
</div>
</body>
</html>"""


def kpi_card(
    value: str | int | float, label: str, color: str = COLORS["text"],
) -> str:
    """Single KPI card HTML snippet."""
    return f"""<div class="kpi-card">
    <div class="value" style="color:{color}">{value}</div>
    <div class="label">{label}</div>
</div>"""


_CAB_WINDOWS = [("30d", "30d"), ("90d", "90d"), ("1y", "1Y"), ("all", "All")]
_CAB_DEFS = [("normal", "Normal"), ("strict", "Strict")]


def windowed_kpi_card(
    uid: str,
    label: str,
    data: dict,
    default_window: str = "all",
    color: str = COLORS["text"],
) -> str:
    """KPI card whose value switches by trailing window, client-side.

    Parameters
    ----------
    uid:
        Unique element-id prefix (one card per uid on a page).
    data:
        ``{window_key: {"value": str, "sub": str}}`` — values are preformatted.
    """
    btns = f'<div class="range-btns" data-cardwin="{uid}">'
    for val, lbl in _CAB_WINDOWS:
        active = ' class="active"' if val == default_window else ""
        btns += f'<button data-w="{val}"{active}>{lbl}</button>'
    btns += "</div>"

    cur = data.get(default_window, {})
    value = cur.get("value", "—")
    sub = cur.get("sub", "")

    return f"""<div class="kpi-card kpi-cab">
    <div class="value" id="{uid}-value" style="color:{color}">{value}</div>
    <div class="label">{label} <span class="cab-sub" id="{uid}-sub">{sub}</span></div>
    {btns}
</div>
<script>
(function() {{
    var DATA = {json.dumps(data)};
    var win = {json.dumps(default_window)};
    var valEl = document.getElementById('{uid}-value');
    var subEl = document.getElementById('{uid}-sub');
    function update() {{
        var cell = DATA[win] || {{}};
        valEl.textContent = cell.value || '—';
        subEl.textContent = cell.sub || '';
    }}
    var btns = document.querySelectorAll('[data-cardwin="{uid}"] button');
    btns.forEach(function(b) {{
        b.addEventListener('click', function() {{
            btns.forEach(function(x) {{ x.classList.remove('active'); }});
            b.classList.add('active');
            win = b.dataset.w;
            update();
        }});
    }});
    update();
}})();
</script>"""


def contributor_absence_card(
    absence: dict,
    default_window: str = "all",
    default_def: str = "normal",
) -> str:
    """Interactive KPI card for the Contributor Absence Factor (bus factor).

    Every (window, definition) value is embedded in the page; the window and
    definition buttons swap the displayed number client-side — no server.
    """
    def _btns(css_cls: str, attr: str, opts: list, default: str) -> str:
        html = f'<div class="range-btns {css_cls}">'
        for val, label in opts:
            active = ' class="active"' if val == default else ""
            html += f'<button data-{attr}="{val}"{active}>{label}</button>'
        return html + "</div>"

    cur = absence.get(default_window, {}).get(default_def, {})
    bus = cur.get("bus")
    top = cur.get("top_pct")
    value = "—" if bus is None else bus
    sub = "" if top is None else f"top does {top}%"

    return f"""<div class="kpi-card kpi-cab">
    <div class="value" id="cab-value" style="color:{COLORS['danger']}">{value}</div>
    <div class="label">Contributor Absence Factor <span class="cab-sub" id="cab-sub">{sub}</span></div>
    {_btns("cab-win", "w", _CAB_WINDOWS, default_window)}
    {_btns("cab-def", "d", _CAB_DEFS, default_def)}
</div>
<script>
(function() {{
    var DATA = {json.dumps(absence)};
    var win = {json.dumps(default_window)}, dfn = {json.dumps(default_def)};
    var valEl = document.getElementById('cab-value');
    var subEl = document.getElementById('cab-sub');
    function update() {{
        var cell = (DATA[win] || {{}})[dfn] || {{}};
        valEl.textContent = (cell.bus == null) ? '—' : cell.bus;
        subEl.textContent = (cell.top_pct == null) ? '' : 'top does ' + cell.top_pct + '%';
    }}
    function wire(sel, attr, apply) {{
        var btns = document.querySelectorAll(sel + ' button');
        btns.forEach(function(b) {{
            b.addEventListener('click', function() {{
                btns.forEach(function(x) {{ x.classList.remove('active'); }});
                b.classList.add('active');
                apply(b.dataset[attr]);
                update();
            }});
        }});
    }}
    wire('.cab-win', 'w', function(v) {{ win = v; }});
    wire('.cab-def', 'd', function(v) {{ dfn = v; }});
    update();
}})();
</script>"""
