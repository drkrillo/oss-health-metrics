"""Time to First Response scatter chart with rolling median."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from ..theme import COLORS
from ._layout import apply_layout, apply_time_axis


def build_response_times(df: pd.DataFrame) -> go.Figure:
    """Scatter plot of hours to first response with rolling average.

    customdata layout: [item_number, author, url, first_response_type] —
    index 2 is the URL used by clickable div for click-to-open.
    """
    df = df[df["hours_to_first_response"].notna()].copy()
    df = df.sort_values("created_at")
    df["url"] = df.apply(
        lambda r: f"https://github.com/{r['repo']}/issues/{r['item_number']}",
        axis=1,
    )

    fig = go.Figure()

    for item_type, color in [("pr", COLORS["purple"]), ("issue", COLORS["accent"])]:
        subset = df[df["item_type"] == item_type]
        fig.add_trace(go.Scatter(
            x=subset["created_at"], y=subset["hours_to_first_response"],
            mode="markers", name=f"{item_type.upper()}s",
            marker=dict(color=color, size=7, opacity=0.6),
            hovertemplate=(
                "#%{customdata[0]} by %{customdata[1]}<br>"
                "%{y:.0f} hours to first %{customdata[3]}<br>"
                "<i>Click to open on GitHub</i><extra></extra>"
            ),
            customdata=subset[
                ["item_number", "author", "url", "first_response_type"]
            ].values,
        ))

    if len(df) >= 5:
        df["rolling_avg"] = df["hours_to_first_response"].rolling(
            window=10, min_periods=3, center=True,
        ).median()
        fig.add_trace(go.Scatter(
            x=df["created_at"], y=df["rolling_avg"],
            mode="lines", name="Rolling Median (10)",
            line=dict(color=COLORS["primary"], width=3),
        ))

    apply_layout(fig)
    fig.update_yaxes(title_text="Hours to First Response")
    apply_time_axis(fig)
    return fig
