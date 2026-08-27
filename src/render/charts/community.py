"""Community Activity, stacked area chart of events by week."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from ..theme import COLORS, EVENT_COLORS
from ._layout import apply_layout, apply_time_axis


def build_community_activity(df: pd.DataFrame) -> go.Figure:
    """Stacked area chart, all events by week, coloured by type."""
    df = df.copy()
    df["week"] = pd.to_datetime(df["event_at"]).dt.to_period("W").dt.start_time

    weekly = df.groupby(["week", "event_type"]).size().reset_index(name="count")

    fig = go.Figure()
    for event_type in [
        "fork", "comment", "issue_opened", "pr_opened", "pr_merged", "review",
    ]:
        subset = weekly[weekly["event_type"] == event_type]
        fig.add_trace(go.Scatter(
            x=subset["week"], y=subset["count"],
            mode="lines", stackgroup="one",
            name=event_type.replace("_", " ").title(),
            line=dict(width=0.5),
            fillcolor=EVENT_COLORS.get(event_type, COLORS["secondary"]),
        ))

    apply_layout(fig)
    fig.update_yaxes(title_text="Events per Week")
    apply_time_axis(fig)
    return fig
