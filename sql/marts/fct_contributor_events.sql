-- One row per event per contributor.
-- Universal source for contributor journey timelines and bot detection.

with events as (
    select repo, author, forked_at as event_at,
           'fork' as event_type, null::integer as item_number, null::varchar as detail
    from stg_forks

    union all

    select repo, author, created_at as event_at,
           'issue_opened' as event_type, issue_number as item_number, title as detail
    from stg_issues

    union all

    select repo, author, created_at as event_at,
           'comment' as event_type, issue_number as item_number, author_association as detail
    from stg_issue_comments

    union all

    select repo, author, created_at as event_at,
           'pr_opened' as event_type, pr_number as item_number, title as detail
    from stg_pull_requests

    union all

    select repo, author, merged_at as event_at,
           'pr_merged' as event_type, pr_number as item_number, title as detail
    from stg_pull_requests
    where merged_at is not null

    union all

    select repo, author, submitted_at as event_at,
           'review' as event_type, pr_number as item_number, review_state as detail
    from stg_pr_reviews
),

with_velocity as (
    select *,
        date_diff('second',
            lag(event_at) over (partition by repo, author order by event_at),
            event_at
        ) as seconds_since_prev_event
    from events
)

select
    repo, author, event_at, event_type, item_number, detail,
    seconds_since_prev_event,
    row_number() over (partition by repo, author order by event_at) as event_sequence
from with_velocity
