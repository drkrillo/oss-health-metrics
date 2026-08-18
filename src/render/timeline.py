"""Velocity review — an account list beside one account's full timeline.

Lives outside ``html.py`` because it is a different kind of component: not a
wrapper around a Plotly figure but hand-written markup, and the thing it shows
is deliberately not a chart.  What matters about "three comments forty seconds
apart" is the text of each one and where it points, and a scatter plot carries
neither.  So the timeline is an ordered list, the gap between two events is the
connector between two rows, and every event links to the interaction itself.

Everything is embedded and switched client-side, like the KPI cards — the site
is static files on GitHub Pages and there is no server to ask.
"""

from __future__ import annotations

import html
import json

from .theme import COLORS, EVENT_COLORS

#: A gap at or under this many seconds is drawn as a warning.  Sixty is the
#: same threshold ``dim_contributors.burst_events`` counts with, so the row
#: highlighting and the burst column can never disagree.
BURST_SECONDS = 60

#: Columns of the account table: (key, header, is_numeric).
_COLUMNS = [
    ("author", "Account", False),
    ("fork_to_action", "Fork→1st", True),
    ("burst_events", "Bursts", True),
    ("min_gap", "Min gap", True),
    ("total_events", "Events", True),
    ("prs_opened", "PRs", True),
    ("prs_merged", "Merged", True),
]


def script_json(payload: dict) -> str:
    """JSON safe to embed inside a ``<script>`` block.

    Everything here comes from GitHub: issue titles, PR titles, account logins.
    ``json.dumps`` escapes quotes but leaves ``</script>`` intact, and the HTML
    parser closes the block at that sequence even inside a JSON string — so an
    issue titled ``</script><script>…`` gets its markup executed on the page.  ``<\\/`` is the same string to
    a JavaScript parser and invisible to the HTML one.
    """
    return json.dumps(payload).replace("</", "<\\/")


def _fmt_gap(seconds: int | None) -> str:
    """Largest sensible unit, and never rounded up into a lie.

    A four-second gap shown as "0m" reads as a rounding artefact; shown as "4s"
    it reads as what it is, which is the whole point of the column.
    """
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


def _fmt_minutes(minutes: int | None) -> str:
    if minutes is None:
        return "—"
    return _fmt_gap(minutes * 60)


def velocity_review_panel(
    uid: str, accounts: list[dict], timelines: dict, multi_repo: bool = False,
) -> str:
    """Sortable account table wired to a vertical timeline of one account."""
    if not accounts:
        return (
            f'<p style="color:{COLORS["secondary"]}">'
            "No non-maintainer account has more than one event yet.</p>"
        )

    head = "".join(
        f'<th data-sort="{key}" class="{"num" if num else ""}">{label}</th>'
        for key, label, num in _COLUMNS
    )

    rows = []
    for account in accounts:
        label = html.escape(account["author"])
        if multi_repo:
            label = f'<span class="tl-repo">{html.escape(account["repo"])}</span> {label}'
        rows.append(
            f'<tr data-key="{html.escape(account["key"])}">'
            f"<td>{label}</td>"
            f'<td class="num">{_fmt_minutes(account["fork_to_action"])}</td>'
            f'<td class="num">{account["burst_events"]}</td>'
            f'<td class="num">{_fmt_gap(account["min_gap"])}</td>'
            f'<td class="num">{account["total_events"]}</td>'
            f'<td class="num">{account["prs_opened"]}</td>'
            f'<td class="num">{account["prs_merged"]}</td>'
            "</tr>"
        )

    payload = {
        "timelines": timelines,
        "accounts": {a["key"]: a for a in accounts},
        "eventColors": EVENT_COLORS,
        "burstSeconds": BURST_SECONDS,
        "danger": COLORS["danger"],
        "muted": COLORS["text_muted"],
    }

    return f"""<div class="tl-panel" id="{uid}">
  <div class="tl-list">
    <table class="tl-table">
      <thead><tr>{head}</tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
  </div>
  <div class="tl-detail" id="{uid}-detail"></div>
</div>
<script>
(function() {{
  var D = {script_json(payload)};
  var root = document.getElementById('{uid}');
  var detail = document.getElementById('{uid}-detail');
  var tbody = root.querySelector('tbody');

  // Serialising a text node escapes < > &, but not quotes — which is enough
  // for body text and not enough for the href attributes below.  Escaping
  // quotes too makes one function correct in both places.
  function esc(s) {{
    var d = document.createElement('div');
    d.textContent = s === null || s === undefined ? '' : String(s);
    return d.innerHTML.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }}

  function fmtGap(s) {{
    if (s === null || s === undefined) return '';
    if (s < 60) return s + 's';
    if (s < 3600) return Math.floor(s / 60) + 'm';
    if (s < 86400) return Math.floor(s / 3600) + 'h';
    return Math.floor(s / 86400) + 'd';
  }}

  function render(key) {{
    var events = D.timelines[key] || [];
    var acct = D.accounts[key] || {{}};
    var html = '<div class="tl-head"><h3>' + esc(acct.author) + '</h3>' +
      '<a href="' + esc(acct.profile) + '" target="_blank" rel="noopener">' +
      'GitHub profile &rarr;</a></div>' +
      '<p class="tl-sub">' + events.length + ' events &middot; ' +
      esc(acct.stage) + '</p><ol class="tl-events">';

    events.forEach(function(e, i) {{
      // The gap belongs between two rows, not inside one: it is a property of
      // the pair, and reading it as a connector is what makes a run of
      // same-minute events obvious at a glance.
      if (i > 0) {{
        var burst = e.gap !== null && e.gap <= D.burstSeconds;
        html += '<li class="tl-gap' + (burst ? ' tl-burst' : '') + '">' +
          '<span>+' + fmtGap(e.gap) + '</span></li>';
      }}
      var color = D.eventColors[e.type] || D.muted;
      var label = e.item ? '#' + e.item : '';
      var body = esc(e.type.replace(/_/g, ' ')) +
        (label ? ' <b>' + label + '</b>' : '') +
        (e.detail ? ' — ' + esc(e.detail) : '');
      html += '<li class="tl-event">' +
        '<time>' + esc(e.at) + '</time>' +
        '<span class="tl-dot" style="background:' + color + '"></span>' +
        '<span class="tl-body">' +
        (e.url ? '<a href="' + esc(e.url) + '" target="_blank" rel="noopener">' +
          body + '</a>' : body) +
        '</span></li>';
    }});
    detail.innerHTML = html + '</ol>';
  }}

  function select(tr) {{
    Array.prototype.forEach.call(tbody.querySelectorAll('tr'), function(x) {{
      x.classList.remove('active');
    }});
    tr.classList.add('active');
    render(tr.dataset.key);
  }}

  tbody.addEventListener('click', function(ev) {{
    var tr = ev.target.closest('tr');
    if (tr) select(tr);
  }});

  var asc = {{}};
  root.querySelectorAll('th[data-sort]').forEach(function(th) {{
    th.addEventListener('click', function() {{
      var field = th.dataset.sort;
      asc[field] = !asc[field];
      var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
      rows.sort(function(a, b) {{
        var x = D.accounts[a.dataset.key][field];
        var y = D.accounts[b.dataset.key][field];
        // A missing signal is not a small one, so nulls stay at the bottom
        // whichever way the column is pointing.
        if (x === null) return 1;
        if (y === null) return -1;
        if (x === y) return 0;
        return (x < y ? -1 : 1) * (asc[field] ? 1 : -1);
      }});
      rows.forEach(function(r) {{ tbody.appendChild(r); }});
    }});
  }});

  select(tbody.querySelector('tr'));
}})();
</script>"""
