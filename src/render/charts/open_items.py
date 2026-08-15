"""Who Has The Ball — horizontal bar chart for open PRs/issues."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from ..theme import COLORS
from ._layout import apply_layout

#: Colour per ``fct_open_items.waiting_on`` state.  "nobody" is the team's own
#: backlog — real, but not somebody being kept waiting — so it reads as muted
#: rather than as either a debt (red) or a handoff (green).
BALL_COLORS = {
    "maintainer": COLORS["danger"],
    "contributor": COLORS["success"],
    "nobody": COLORS["secondary"],
}

#: How many rows the overview shows.  One bar per open item is readable at
#: eight and a 10,000px column at two hundred, and the overview is meant to be
#: a to-do list rather than an inventory — the detail page keeps everything.
OVERVIEW_LIMIT = 5


def _axis_keys_and_text(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Unique category per row, plus the text a person should read on the axis.

    Plotly treats the y values of a horizontal bar chart as categories and
    merges any two that are equal, so labelling rows with the item number and a
    truncated title silently collapses them into one bar: the same number in
    two repos, or two dependabot PRs whose titles agree for fifty characters.
    The category is the mart's own key, which is unique by construction; the
    tick text is free to repeat.
    """
    keys = [f"{r.repo}#{r.item_number}" for r in df.itertuples()]
    # The repo only earns axis space when there is more than one to tell apart.
    prefix = df["repo"].nunique() > 1
    text = [
        f"{r.repo + ' ' if prefix else ''}#{r.item_number} {r.title[:50]}"
        for r in df.itertuples()
    ]
    return keys, text


def _empty(text: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=text, showarrow=False, font_size=16)
    apply_layout(fig)
    return fig


def build_open_items(
    df: pd.DataFrame,
    waiting_on: str | None = None,
    limit: int | None = None,
) -> go.Figure:
    """Horizontal bar chart — who has the ball.

    ``waiting_on`` narrows to a single ball state and ``limit`` keeps only the
    longest-waiting rows.  The overview passes both to ask the one question a
    maintainer opens a dashboard for — what is waiting on me right now — while
    the detail page passes neither and shows every open item.
    """
    if df.empty:
        return _empty("No open items")

    if waiting_on is not None:
        df = df[df["waiting_on"] == waiting_on]
        if df.empty:
            return _empty("Nothing is waiting on the team")

    if limit is not None:
        df = df.nlargest(limit, "hours_waiting")

    # Plotly draws the first category at the bottom of a horizontal bar chart,
    # so sorting ascending is what puts the longest wait at the top.
    df = df.sort_values("hours_waiting", ascending=True).copy()
    keys, text = _axis_keys_and_text(df)
    df["color"] = df["waiting_on"].map(BALL_COLORS).fillna(COLORS["secondary"])
    df["display_hours"] = df["hours_waiting"].clip(lower=1)
    df["url"] = df.apply(
        lambda r: f"https://github.com/{r['repo']}/issues/{r['item_number']}",
        axis=1,
    )
    # The URL stays at index 3 — clickable_plotly_div reads it from there.
    df["label"] = text

    fig = go.Figure(go.Bar(
        y=keys, x=df["display_hours"],
        orientation="h",
        marker_color=df["color"],
        customdata=df[
            ["waiting_on", "item_type", "hours_waiting", "url", "label"]
        ].values,
        hovertemplate=(
            "%{customdata[4]}<br>Waiting: %{customdata[2]:.0f}h<br>"
            "Ball with: %{customdata[0]}<br>"
            "<i>Click to open on GitHub</i><extra></extra>"
        ),
    ))

    apply_layout(
        fig,
        yaxis=dict(
            tickfont=dict(size=11),
            tickmode="array", tickvals=keys, ticktext=text,
        ),
        height=max(250, len(df) * 50 + 100),
    )
    fig.update_xaxes(title_text="Hours Waiting")
    return fig
