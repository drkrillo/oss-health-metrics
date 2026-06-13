"""Shared layout helpers used by all chart builders."""

from __future__ import annotations

import plotly.graph_objects as go

from ..theme import COLORS, LAYOUT_DEFAULTS


def apply_layout(fig: go.Figure, **kwargs) -> go.Figure:
    """Apply the default dark layout to a figure."""
    fig.update_layout(**{**LAYOUT_DEFAULTS, **kwargs})
    fig.update_xaxes(gridcolor=COLORS["border"], zeroline=False)
    fig.update_yaxes(gridcolor=COLORS["border"], zeroline=False)
    return fig


def apply_time_axis(fig: go.Figure) -> go.Figure:
    """Add range slider and lin/log toggle.

    Range-selector buttons (1M, 3M, …) are implemented in JS
    (see html.time_series_div) so they always go backward from the
    actual max data date, preventing future-date issues.
    """
    min_date = max_date = None
    for trace in fig.data:
        if hasattr(trace, "x") and trace.x is not None and len(trace.x) > 0:
            tmax = max(trace.x)
            tmin = min(trace.x)
            if max_date is None or str(tmax) > str(max_date):
                max_date = tmax
            if min_date is None or str(tmin) < str(min_date):
                min_date = tmin

    xaxis_kwargs: dict = dict(
        rangeslider=dict(
            visible=True, bgcolor=COLORS["card_bg"], thickness=0.04,
        ),
        autorange=False,
    )
    if max_date is not None and min_date is not None:
        xaxis_kwargs["range"] = [str(min_date), str(max_date)]
    fig.update_xaxes(**xaxis_kwargs)

    # Lin/Log toggle button (top-right)
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=1.0, y=1.08,
                xanchor="right", yanchor="top",
                bgcolor=COLORS["card_bg"],
                font=dict(color=COLORS["text"], size=11),
                buttons=[
                    dict(label="Linear", method="relayout",
                         args=[{"yaxis.type": "linear"}]),
                    dict(label="Log", method="relayout",
                         args=[{"yaxis.type": "log"}]),
                ],
            )
        ],
    )
    return fig
