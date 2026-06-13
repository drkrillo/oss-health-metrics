"""Chart builders — one function per metric, each returns a pure go.Figure."""

from .community import build_community_activity
from .contributors import (
    build_bot_signals,
    build_contributor_scatter,
    build_contributor_timeline,
)
from .funnel import build_funnel
from .open_items import build_open_items
from .response_times import build_response_times
from .weekly_pulse import build_weekly_pulse

__all__ = [
    "build_community_activity",
    "build_bot_signals",
    "build_contributor_scatter",
    "build_contributor_timeline",
    "build_funnel",
    "build_open_items",
    "build_response_times",
    "build_weekly_pulse",
]
