"""Time to First Response — monthly median trend, split by activity type.

CHAOSS recommends response-time *trends* by activity type over the raw
per-item distribution. A scatter of every item is noise; the monthly median
per type is the signal — and median (not mean) is what the CHAOSS
Responsiveness guide recommends, since it tracks how the wait is perceived.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from ..theme import COLORS
from ._layout import apply_layout, apply_time_axis


def build_response_times(df: pd.DataFrame) -> go.Figure:
    """Line chart: monthly median hours-to-first-response for PRs and issues."""
    df = df[df["hours_to_first_response"].notna()].copy()
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["month"] = df["created_at"].dt.to_period("M").dt.to_timestamp()

    fig = go.Figure()
    for item_type, color in [("pr", COLORS["purple"]), ("issue", COLORS["accent"])]:
        subset = df[df["item_type"] == item_type]
        monthly = (
            subset.groupby("month")["hours_to_first_response"]
            .median()
            .reset_index()
        )
        fig.add_trace(go.Scatter(
            x=monthly["month"], y=monthly["hours_to_first_response"],
            mode="lines+markers", name=f"{item_type.upper()}s (median)",
            line=dict(color=color, width=2),
            marker=dict(size=5),
            hovertemplate="%{x|%b %Y}<br>median %{y:.1f}h<extra></extra>",
        ))

    apply_layout(fig)
    fig.update_yaxes(title_text="Median hours to first response")
    apply_time_axis(fig)
    return fig
