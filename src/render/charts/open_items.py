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


def build_open_items(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart — who has the ball."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No open items", showarrow=False, font_size=16)
        apply_layout(fig)
        return fig

    df = df.sort_values("hours_waiting", ascending=True).copy()
    df["label"] = df.apply(
        lambda r: f"#{r['item_number']} {r['title'][:50]}", axis=1,
    )
    df["color"] = df["waiting_on"].map(BALL_COLORS).fillna(COLORS["secondary"])
    df["display_hours"] = df["hours_waiting"].clip(lower=1)
    df["url"] = df.apply(
        lambda r: f"https://github.com/{r['repo']}/issues/{r['item_number']}",
        axis=1,
    )

    fig = go.Figure(go.Bar(
        y=df["label"], x=df["display_hours"],
        orientation="h",
        marker_color=df["color"],
        customdata=df[["waiting_on", "item_type", "hours_waiting", "url"]].values,
        hovertemplate=(
            "%{y}<br>Waiting: %{customdata[2]:.0f}h<br>"
            "Ball with: %{customdata[0]}<br>"
            "<i>Click to open on GitHub</i><extra></extra>"
        ),
    ))

    apply_layout(
        fig,
        yaxis=dict(tickfont=dict(size=11)),
        height=max(250, len(df) * 50 + 100),
    )
    fig.update_xaxes(title_text="Hours Waiting")
    return fig
