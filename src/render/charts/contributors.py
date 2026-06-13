"""Contributor charts — timeline, scatter, and bot-signal detection."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ..theme import COLORS, EVENT_COLORS, FUNNEL_ORDER
from ._layout import apply_layout, apply_time_axis


def build_contributor_timeline(df: pd.DataFrame) -> go.Figure:
    """Scatter timeline — each dot is an event, y-axis is contributor."""
    top = df.groupby("author").size().nlargest(20).index.tolist()
    subset = df[df["author"].isin(top)].copy()

    fig = go.Figure()
    for event_type, color in EVENT_COLORS.items():
        ev = subset[subset["event_type"] == event_type]
        fig.add_trace(go.Scatter(
            x=ev["event_at"], y=ev["author"],
            mode="markers", name=event_type.replace("_", " ").title(),
            marker=dict(color=color, size=8, opacity=0.8),
            hovertemplate=(
                "%{y}<br>%{x}<br>"
                + event_type.replace("_", " ").title()
                + "<extra></extra>"
            ),
        ))

    apply_layout(
        fig,
        height=max(500, len(top) * 28 + 150),
        yaxis=dict(tickfont=dict(size=11)),
    )
    apply_time_axis(fig)
    return fig


def build_contributor_scatter(df: pd.DataFrame) -> go.Figure:
    """Scatter: prs_opened vs comments_made, size=total_events, colour=funnel."""
    fig = px.scatter(
        df, x="comments_made", y="prs_opened",
        size="total_events", color="funnel_stage",
        hover_name="author",
        hover_data=[
            "prs_merged", "reviews_given", "burst_events",
            "minutes_fork_to_first_action",
        ],
        category_orders={"funnel_stage": FUNNEL_ORDER},
        color_discrete_sequence=[
            COLORS["secondary"], COLORS["primary"], COLORS["purple"],
            COLORS["success"], COLORS["accent"],
        ],
    )
    apply_layout(fig)
    fig.update_xaxes(title_text="Comments Made")
    fig.update_yaxes(title_text="PRs Opened")
    return fig


def build_bot_signals(df: pd.DataFrame) -> go.Figure:
    """Scatter: minutes_fork_to_first_action vs burst_events."""
    forkers = df[df["has_fork"]].copy()
    if forkers.empty:
        fig = go.Figure()
        fig.add_annotation(text="No fork data", showarrow=False, font_size=16)
        apply_layout(fig)
        return fig

    fig = px.scatter(
        forkers,
        x="minutes_fork_to_first_action",
        y="burst_events",
        size="total_events",
        color="funnel_stage",
        hover_name="author",
        hover_data=["min_seconds_between_events", "prs_opened", "prs_merged"],
        category_orders={"funnel_stage": FUNNEL_ORDER},
        color_discrete_sequence=[
            COLORS["secondary"], COLORS["primary"], COLORS["purple"],
            COLORS["success"], COLORS["accent"],
        ],
    )
    apply_layout(fig)
    fig.update_xaxes(title_text="Minutes from Fork to First Action")
    fig.update_yaxes(title_text="Burst Events (<60s between actions)")
    return fig
