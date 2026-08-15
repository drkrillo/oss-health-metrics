"""The funnel is CHAOSS Conversion Rate: independent cohorts per developer
level, with conversion read as the ratio between adjacent levels.

The failure this guards against is the opposite of the old one: CHAOSS levels
are NOT nested (comment without forking, merge without commenting), so forcing
them into subsets would drop real people. The sample deliberately includes both
non-nested shapes, and the chart must still count and convert them.
"""

from __future__ import annotations

import pandas as pd

from render.charts.funnel import _LEVELS, build_funnel


def _contributor(author: str, **overrides) -> dict:
    row = dict(
        author=author, comments_made=0, reviews_given=0, issues_opened=0,
        prs_opened=0, prs_merged=0, has_fork=False,
    )
    row.update(overrides)
    return row


#: p2 is in D1 but not D0 (commented, never forked); p4 is in D2 but not D1
#: (merged a PR without a single comment/issue/review). Both are the cases a
#: nested funnel would wrongly drop.
SAMPLE = pd.DataFrame([
    _contributor("fork-only", has_fork=True),
    _contributor("commenter-no-fork", comments_made=2),
    _contributor("reviewer-and-fork", has_fork=True, reviews_given=1),
    _contributor("merged-no-comment", has_fork=True, prs_opened=1, prs_merged=1),
    _contributor("full-journey", has_fork=True, comments_made=1, prs_opened=2, prs_merged=1),
])


def test_level_counts_match_chaoss_definitions():
    # Group A = 5; D0 (forked) = p1,p3,p4,p5 = 4; D1 (issue/comment/review)
    # = p2,p3,p5 = 3; D2 (opened & merged) = p4,p5 = 2.
    values = list(build_funnel(SAMPLE).data[0].x)
    assert values == [5, 4, 3, 2]


def test_levels_are_independent_cohorts_not_subsets():
    counts = {label: int(pred(SAMPLE).sum()) for label, pred in _LEVELS}
    d0 = _LEVELS[1][1](SAMPLE)
    d1 = _LEVELS[2][1](SAMPLE)
    # The commenter is counted in D1 despite not being in D0 — proof the funnel
    # does not require nesting.
    assert SAMPLE.loc[d1 & ~d0, "author"].tolist() == ["commenter-no-fork"]
    assert counts["D1 — issue / comment / review"] == 3


def test_conversion_is_reported_as_percent_previous():
    # CHAOSS conversion is Dn / D(n-1), which is Plotly's "percent previous".
    assert build_funnel(SAMPLE).data[0].textinfo == "value+percent previous"


def test_empty_input_renders_a_placeholder_instead_of_raising():
    fig = build_funnel(pd.DataFrame())
    assert fig.data == ()
    assert "No contributor data" in fig.layout.annotations[0].text
