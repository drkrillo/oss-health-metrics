"""Contributor Funnel — cumulative conversion rates."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from ..theme import COLORS, FUNNEL_LABELS, FUNNEL_ORDER
from ._layout import apply_layout


def build_funnel(df: pd.DataFrame) -> go.Figure:
    """Contributor funnel chart with cumulative counts.

    Each contributor is assigned to their HIGHEST stage (mutually exclusive).
    For the funnel, values are cumulative: each stage includes everyone who
    reached that stage OR any stage above it.
    """
    exclusive = df["funnel_stage"].value_counts()
    cumulative = {}
    for i, stage in enumerate(FUNNEL_ORDER):
        cumulative[stage] = sum(
            exclusive.get(s, 0) for s in FUNNEL_ORDER[i:]
        )

    stages = [s for s in FUNNEL_ORDER if cumulative.get(s, 0) > 0]
    values = [cumulative[s] for s in stages]
    labels = [FUNNEL_LABELS.get(s, s) for s in stages]

    fig = go.Figure(go.Funnel(
        y=labels, x=values,
        textinfo="value+percent initial",
        marker=dict(color=[
            COLORS["secondary"], COLORS["primary"], COLORS["purple"],
            COLORS["success"], COLORS["accent"],
        ][:len(stages)]),
    ))
    apply_layout(fig)
    return fig
