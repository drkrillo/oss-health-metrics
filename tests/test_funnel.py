"""The funnel only means anything if its steps are nested populations.

Percentages are read as conversion rates, so a step that includes someone the
previous step excluded silently turns the chart into fiction.
"""

from __future__ import annotations

import pandas as pd

from render.charts.funnel import _STEPS, build_funnel


def _contributor(author: str, **overrides) -> dict:
    row = dict(
        author=author, comments_made=0, reviews_given=0, issues_opened=0,
        prs_opened=0, prs_merged=0, has_fork=False,
    )
    row.update(overrides)
    return row


#: Carries the two shapes that broke the previous cumulative funnel: people who
#: engage without ever forking, and people with several PRs and no merge.
SAMPLE = pd.DataFrame([
    _contributor("fork-only", has_fork=True),
    _contributor("commenter-no-fork", comments_made=3),
    _contributor("reviewer-no-fork", reviews_given=2),
    _contributor("pr-never-merged", has_fork=True, prs_opened=2),
    _contributor("merged-once", has_fork=True, prs_opened=1, prs_merged=1),
    _contributor("repeat", has_fork=True, prs_opened=4, prs_merged=3),
])


def test_every_step_is_a_subset_of_the_previous_one():
    masks = [predicate(SAMPLE) for _, predicate in _STEPS]
    for (label, _), wider, narrower in zip(_STEPS[1:], masks, masks[1:]):
        leaked = SAMPLE.loc[narrower & ~wider, "author"].tolist()
        assert not leaked, f"{label!r} counts contributors the previous step excluded: {leaked}"


def test_counts_match_the_sample():
    values = list(build_funnel(SAMPLE).data[0].x)
    assert values == [6, 5, 3, 2, 1]


def test_empty_input_renders_a_placeholder_instead_of_raising():
    fig = build_funnel(pd.DataFrame())
    assert fig.data == ()
    assert "No contributor data" in fig.layout.annotations[0].text
