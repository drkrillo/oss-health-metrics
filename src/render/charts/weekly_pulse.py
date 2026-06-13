"""Weekly Pulse — Little's Law chart (WIP, throughput, cycle time)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..theme import COLORS
from ._layout import apply_layout, apply_time_axis


def build_weekly_pulse(df: pd.DataFrame) -> go.Figure:
    """Combo chart: bars for opened/merged, lines for WIP and cycle time."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=df["week_start"], y=df["prs_opened"],
            name="PRs Opened", marker_color=COLORS["secondary"],
            opacity=0.5,
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(
            x=df["week_start"], y=df["prs_merged"],
            name="PRs Merged", marker_color=COLORS["success"],
            opacity=0.7,
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=df["week_start"], y=df["wip"],
            name="WIP (open PRs)", mode="lines+markers",
            line=dict(color=COLORS["accent"], width=2),
            marker=dict(size=4),
        ),
        secondary_y=False,
    )

    ct = df[df["cycle_time_weeks"].notna()]
    fig.add_trace(
        go.Scatter(
            x=ct["week_start"], y=ct["cycle_time_weeks"],
            name="Cycle Time (weeks)", mode="lines",
            line=dict(color=COLORS["purple"], width=2, dash="dot"),
        ),
        secondary_y=True,
    )

    apply_layout(fig, barmode="group")
    fig.update_yaxes(title_text="PRs / WIP", secondary_y=False)
    fig.update_yaxes(title_text="Cycle Time (weeks)", secondary_y=True)
    apply_time_axis(fig)
    return fig
