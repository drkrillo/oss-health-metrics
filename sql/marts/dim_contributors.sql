-- One row per contributor per repo — summary profile.
-- Derived from fct_contributor_events.
-- Includes funnel stage for conversion rate visualization.

with events as (
    select * from fct_contributor_events
),

first_non_fork as (
    select repo, author, min(event_at) as first_non_fork_at
    from events
    where event_type != 'fork'
    group by repo, author
),

summary as (
    select
        repo, author,
        min(event_at) as first_event_at,
        max(event_at) as last_event_at,
        count(*) as total_events,
        date_diff('day', min(event_at), max(event_at)) as days_active_span,
        min(event_type) filter (where event_sequence = 1) as first_event_type,
        min(event_at) filter (where event_type = 'fork') as forked_at,
        count(*) filter (where event_type = 'pr_opened') as prs_opened,
        count(*) filter (where event_type = 'pr_merged') as prs_merged,
        count(*) filter (where event_type = 'issue_opened') as issues_opened,
        count(*) filter (where event_type = 'comment') as comments_made,
        count(*) filter (where event_type = 'review') as reviews_given,
        count(*) filter (
            where seconds_since_prev_event is not null
            and seconds_since_prev_event < 60
        ) as burst_events,
        min(seconds_since_prev_event) filter (
            where seconds_since_prev_event > 0
        ) as min_seconds_between_events
    from events
    group by repo, author
)

select
    s.*,
    (s.prs_merged > 0) as has_merged_pr,
    (s.total_events > 1) as returned_after_first,
    (s.forked_at is not null) as has_fork,
    date_diff('minute', s.forked_at, fnf.first_non_fork_at) as minutes_fork_to_first_action,
    case
        when s.prs_opened > 1 and s.prs_merged > 0 then 'repeat_contributor'
        when s.prs_merged > 0 then 'merged'
        when s.prs_opened > 0 then 'pr_opened'
        when s.forked_at is not null then 'forked'
        else 'engaged'
    end as funnel_stage
from summary s
left join first_non_fork fnf
    on s.repo = fnf.repo and s.author = fnf.author
