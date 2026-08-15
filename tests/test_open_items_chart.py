"""The overview asks a narrower question than the detail page.

One bar per open item is readable at eight rows and a 10,000px column at two
hundred, so the overview answers "what is waiting on me right now" — response
debt only, longest waits first, capped — while the detail page keeps every open
item and every ball state.  Both come out of the same builder, so the filtering
and the cap are what these pin.
"""

from __future__ import annotations

import pandas as pd

from render.charts.open_items import BALL_COLORS, build_open_items
from render.theme import COLORS


def _item(number: int, hours: int, waiting_on: str, title: str = "Something") -> dict:
    return dict(
        repo="acme/widget", item_number=number, item_type="issue",
        title=title, hours_waiting=hours, waiting_on=waiting_on,
    )


SAMPLE = pd.DataFrame([
    _item(1, 500, "nobody", "Old backlog idea"),
    _item(2, 300, "contributor", "Answered, their move"),
    _item(3, 200, "maintainer", "Oldest real debt"),
    _item(4, 100, "maintainer", "Newer debt"),
    _item(5, 50, "maintainer", "Newest debt"),
    _item(6, 10, "contributor", "Just answered"),
])


def _labels(fig) -> list[str]:
    return list(fig.data[0].y)


def test_the_detail_view_keeps_every_item_and_every_state():
    fig = build_open_items(SAMPLE)
    assert len(_labels(fig)) == 6


def test_the_overview_shows_response_debt_only():
    fig = build_open_items(SAMPLE, waiting_on="maintainer")
    assert [lbl.split()[0] for lbl in _labels(fig)] == ["#5", "#4", "#3"]


def test_the_overview_cap_keeps_the_longest_waits():
    # #1 waits longest of all but is backlog; the cap must not spend a slot
    # on it, and must drop the *newest* debt rather than an arbitrary row.
    fig = build_open_items(SAMPLE, waiting_on="maintainer", limit=2)
    assert [lbl.split()[0] for lbl in _labels(fig)] == ["#4", "#3"]


def test_the_longest_wait_is_drawn_at_the_top():
    """Plotly puts the first category at the bottom, so the order is inverted."""
    fig = build_open_items(SAMPLE)
    assert _labels(fig)[-1].startswith("#1")
    assert _labels(fig)[0].startswith("#6")


def test_a_cap_larger_than_the_data_changes_nothing():
    fig = build_open_items(SAMPLE, waiting_on="maintainer", limit=99)
    assert len(_labels(fig)) == 3


def test_each_ball_state_gets_its_own_colour():
    fig = build_open_items(SAMPLE)
    colors = dict(zip(_labels(fig), fig.data[0].marker.color))
    by_number = {lbl.split()[0]: c for lbl, c in colors.items()}
    assert by_number["#1"] == BALL_COLORS["nobody"]
    assert by_number["#2"] == BALL_COLORS["contributor"]
    assert by_number["#3"] == BALL_COLORS["maintainer"]


def test_an_unknown_state_still_renders_rather_than_blanking_the_bar():
    odd = pd.DataFrame([_item(9, 5, "something_new")])
    fig = build_open_items(odd)
    assert fig.data[0].marker.color[0] == COLORS["secondary"]


# -- empty states -----------------------------------------------------------

def test_no_open_items_at_all_says_so():
    fig = build_open_items(SAMPLE.iloc[:0])
    assert fig.data == ()
    assert "No open items" in fig.layout.annotations[0].text


def test_an_empty_inbox_is_reported_as_good_news_not_as_no_data():
    """Nothing waiting on the team is the best state, not a missing chart."""
    answered = SAMPLE[SAMPLE["waiting_on"] != "maintainer"]
    fig = build_open_items(answered, waiting_on="maintainer")
    assert fig.data == ()
    assert "Nothing is waiting on the team" in fig.layout.annotations[0].text
