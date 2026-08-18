-- One row per event per contributor.
-- Universal source for contributor journey timelines and response velocity.
--
-- ``event_url`` points at the exact interaction, not just the item it happened
-- on.  A timeline saying somebody posted three comments forty seconds apart is
-- a number; one where each of those three opens the comment itself is readable.
-- The difference is the comment/review id GitHub returns for free, which this
-- mart used to drop before the render layer ever saw it.

with events as (
    select repo, author, forked_at as event_at,
           'fork' as event_type, null::integer as item_number,
           null::varchar as detail, null::bigint as event_id
    from stg_forks

    union all

    select repo, author, created_at as event_at,
           'issue_opened' as event_type, issue_number as item_number,
           title as detail, null::bigint as event_id
    from stg_issues

    union all

    select repo, author, created_at as event_at,
           'comment' as event_type, issue_number as item_number,
           author_association as detail, comment_id::bigint as event_id
    from stg_issue_comments

    union all

    select repo, author, created_at as event_at,
           'pr_opened' as event_type, pr_number as item_number,
           title as detail, null::bigint as event_id
    from stg_pull_requests

    union all

    select repo, author, merged_at as event_at,
           'pr_merged' as event_type, pr_number as item_number,
           title as detail, null::bigint as event_id
    from stg_pull_requests
    where merged_at is not null

    union all

    select repo, author, submitted_at as event_at,
           'review' as event_type, pr_number as item_number,
           review_state as detail, review_id::bigint as event_id
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
    repo, author, event_at, event_type, item_number, detail, event_id,
    -- GitHub redirects /issues/N to /pull/N for pull requests, but being
    -- explicit keeps the link honest about what it points at.  Forks have no
    -- per-event page: the fork itself is a repo, and it may since have been
    -- renamed, so there is nothing safe to link to.
    case event_type
        when 'comment' then
            'https://github.com/' || repo || '/issues/' || item_number
            || '#issuecomment-' || event_id
        when 'review' then
            'https://github.com/' || repo || '/pull/' || item_number
            || '#pullrequestreview-' || event_id
        when 'issue_opened' then
            'https://github.com/' || repo || '/issues/' || item_number
        when 'pr_opened' then
            'https://github.com/' || repo || '/pull/' || item_number
        when 'pr_merged' then
            'https://github.com/' || repo || '/pull/' || item_number
    end as event_url,
    seconds_since_prev_event,
    row_number() over (partition by repo, author order by event_at) as event_sequence
from with_velocity
