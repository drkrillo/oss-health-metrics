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


def _item(
    number: int, hours: int, waiting_on: str,
    title: str = "Something", repo: str = "acme/widget",
) -> dict:
    return dict(
        repo=repo, item_number=number, item_type="issue",
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


def _keys(fig) -> list[str]:
    """The y values, which Plotly uses as category identity."""
    return list(fig.data[0].y)


def _numbers(fig) -> list[str]:
    return [k.split("#")[-1] for k in _keys(fig)]


def _text(fig) -> list[str]:
    """What actually gets printed down the axis."""
    return list(fig.layout.yaxis.ticktext)


def test_the_detail_view_keeps_every_item_and_every_state():
    fig = build_open_items(SAMPLE)
    assert len(_keys(fig)) == 6


def test_the_overview_shows_response_debt_only():
    fig = build_open_items(SAMPLE, waiting_on="maintainer")
    assert _numbers(fig) == ["5", "4", "3"]


def test_the_overview_cap_keeps_the_longest_waits():
    # #1 waits longest of all but is backlog; the cap must not spend a slot
    # on it, and must drop the *newest* debt rather than an arbitrary row.
    fig = build_open_items(SAMPLE, waiting_on="maintainer", limit=2)
    assert _numbers(fig) == ["4", "3"]


def test_the_longest_wait_is_drawn_at_the_top():
    """Plotly puts the first category at the bottom, so the order is inverted."""
    fig = build_open_items(SAMPLE)
    assert _numbers(fig) == ["6", "5", "4", "3", "2", "1"]


def test_a_cap_larger_than_the_data_changes_nothing():
    fig = build_open_items(SAMPLE, waiting_on="maintainer", limit=99)
    assert len(_keys(fig)) == 3


def test_each_ball_state_gets_its_own_colour():
    fig = build_open_items(SAMPLE)
    by_number = dict(zip(_numbers(fig), fig.data[0].marker.color))
    assert by_number["1"] == BALL_COLORS["nobody"]
    assert by_number["2"] == BALL_COLORS["contributor"]
    assert by_number["3"] == BALL_COLORS["maintainer"]


# -- axis identity ----------------------------------------------------------

def test_two_repos_sharing_an_item_number_stay_two_bars():
    """Plotly merges equal categories, so identity cannot be the item number.

    Issue numbers restart per repo, so pointing this at an org guarantees
    collisions — and a merged bar is a row that vanished without an error.
    """
    collide = pd.DataFrame([
        _item(5, 100, "maintainer", "Fix the thing", repo="acme/widget"),
        _item(5, 200, "maintainer", "Fix the thing", repo="acme/gadget"),
    ])
    fig = build_open_items(collide)
    assert len(_keys(fig)) == 2
    assert len(set(_keys(fig))) == 2


def test_titles_that_agree_for_fifty_characters_stay_two_bars():
    # The dependabot case: same prefix, different tail.
    same_prefix = "Bump actions/checkout from 4 to 5 in the group of "
    collide = pd.DataFrame([
        _item(10, 100, "maintainer", same_prefix + "frontend actions"),
        _item(11, 200, "maintainer", same_prefix + "backend actions"),
    ])
    fig = build_open_items(collide)
    assert len(set(_keys(fig))) == 2


def test_the_repo_is_shown_on_the_axis_only_when_there_are_several():
    one = build_open_items(SAMPLE)
    assert not any(t.startswith("acme/") for t in _text(one))

    several = build_open_items(pd.DataFrame([
        _item(1, 10, "maintainer", repo="acme/widget"),
        _item(2, 20, "maintainer", repo="acme/gadget"),
    ]))
    assert all(t.startswith("acme/") for t in _text(several))


def test_the_hover_shows_the_readable_label_not_the_key():
    fig = build_open_items(SAMPLE)
    assert "customdata[4]" in fig.data[0].hovertemplate
    assert fig.data[0].customdata[0][4] in _text(fig)


def test_the_url_stays_where_the_click_handler_looks_for_it():
    """clickable_plotly_div defaults to customdata index 3."""
    fig = build_open_items(SAMPLE)
    assert fig.data[0].customdata[0][3].startswith("https://github.com/")


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
