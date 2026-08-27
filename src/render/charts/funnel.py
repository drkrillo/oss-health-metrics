"""Contributor Funnel, CHAOSS Conversion Rate developer levels.

CHAOSS defines the funnel as cohort sizes at successive developer levels, and
the conversion rate as the ratio between adjacent levels:

    Group A , anyone who interacted
    D0      , starred, watched, or forked
    D1      , created issues, commented, or reviewed
    D2      , opened a change request AND merged it

    CR(D0) = D0 / Group A     CR(D1) = D1 / D0     CR(D2) = D2 / D1

These levels are NOT nested: someone can comment (D1) without forking (D0), or
merge a PR (D2) without ever leaving a comment. So this is not a subset funnel , 
each bar is an independent cohort and "percent previous" is the CHAOSS
conversion rate between the two.

Note: we only extract forks, not stars/watches, so D0 here is "forked".
https://chaoss.community/kb/metric-conversion-rate/
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from ..theme import COLORS
from ._layout import apply_layout

#: CHAOSS developer levels, widest first. Each is an independent cohort, the
#: predicates deliberately do NOT nest (see module docstring).
_LEVELS: list[tuple[str, object]] = [
    ("Group A, any activity",
     lambda d: pd.Series(True, index=d.index)),
    ("D0: forked",
     lambda d: d["has_fork"]),
    ("D1: issue / comment / review",
     lambda d: (d["comments_made"] > 0) | (d["reviews_given"] > 0) | (d["issues_opened"] > 0)),
    ("D2: opened & merged a PR",
     lambda d: (d["prs_opened"] > 0) & (d["prs_merged"] > 0)),
]


def build_funnel(df: pd.DataFrame) -> go.Figure:
    """CHAOSS contributor funnel: cohort size per developer level.

    ``percent previous`` on the funnel is the CHAOSS conversion rate between
    adjacent levels (D0/GroupA, D1/D0, D2/D1).
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No contributor data", showarrow=False, font_size=16)
        apply_layout(fig)
        return fig

    labels = [label for label, _ in _LEVELS]
    values = [int(predicate(df).sum()) for _, predicate in _LEVELS]

    fig = go.Figure(go.Funnel(
        y=labels, x=values,
        textinfo="value+percent previous",
        marker=dict(color=[
            COLORS["secondary"], COLORS["primary"],
            COLORS["purple"], COLORS["success"],
        ]),
    ))
    apply_layout(fig)
    return fig
