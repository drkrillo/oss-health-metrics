"""Contributor Funnel — conversion between nested stages."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from ..theme import COLORS
from ._layout import apply_layout


def _contributed(df: pd.DataFrame) -> pd.Series:
    """Activity that is something other than forking."""
    return (
        df["comments_made"] + df["reviews_given"]
        + df["prs_opened"] + df["issues_opened"]
    ) > 0


#: Funnel steps, widest first.  Every predicate MUST select a subset of the
#: step above it: the funnel reports conversion between nested populations,
#: so a step that is not contained in its predecessor makes the percentages
#: meaningless.
#:
#: ``dim_contributors.funnel_stage`` is deliberately NOT used here.  Those
#: stages are mutually exclusive labels for colouring charts, and they are
#: not nested — someone can comment without ever forking — so adding them up
#: would sum disjoint populations.
_STEPS: list[tuple[str, object]] = [
    ("Reached (any activity)",
     lambda d: pd.Series(True, index=d.index)),
    ("Engaged (beyond forking)",
     _contributed),
    ("Opened a PR",
     lambda d: d["prs_opened"] > 0),
    ("Merged at least 1 PR",
     lambda d: d["prs_merged"] > 0),
    ("Repeat (>1 PR, at least 1 merged)",
     lambda d: (d["prs_opened"] > 1) & (d["prs_merged"] > 0)),
]


def build_funnel(df: pd.DataFrame) -> go.Figure:
    """Contributor funnel chart.

    Each bar counts the contributors who reached that stage.  Because the
    stages are nested, ``percent initial`` reads as a real conversion rate
    from the widest population down.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No contributor data", showarrow=False, font_size=16)
        apply_layout(fig)
        return fig

    labels = [label for label, _ in _STEPS]
    values = [int(predicate(df).sum()) for _, predicate in _STEPS]

    fig = go.Figure(go.Funnel(
        y=labels, x=values,
        textinfo="value+percent initial",
        marker=dict(color=[
            COLORS["secondary"], COLORS["primary"], COLORS["purple"],
            COLORS["success"], COLORS["accent"],
        ][:len(labels)]),
    ))
    apply_layout(fig)
    return fig
