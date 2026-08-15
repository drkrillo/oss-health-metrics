-- Change-request flow, per trailing window (30d / 90d / 1y / all).
-- Two CHAOSS metrics, measured directly (no Little's Law division):
--
--   Change Requests Duration  — CHAOSS: time from a change request opening to
--     its MERGE, for accepted (merged) change requests only. We report the
--     median in hours. https://chaoss.community/kb/metric-change-requests-duration/
--
--   Change Request Closure Ratio — CHAOSS: change requests CLOSED in a period
--     over change requests OPENED in that period. >1 means the project closes
--     faster than new ones arrive (backlog shrinking); <1 means it is falling
--     behind. https://chaoss.community/kb/metric-change-request-closure-ratio/
--
-- A "close" is any terminal event — merged OR closed-without-merge — since both
-- take the request out of the queue. Duration counts merges only, per CHAOSS.

with prs as (
    select
        repo, created_at, merged_at,
        coalesce(merged_at, closed_at) as closed_at   -- terminal event, if any
    from stg_pull_requests
),

windows(window_key, cutoff) as (
    values
        ('30d', current_timestamp - interval '30 days'),
        ('90d', current_timestamp - interval '90 days'),
        ('1y',  current_timestamp - interval '365 days'),
        ('all', timestamp '1970-01-01')
),

per_window as (
    select
        w.window_key,
        p.repo,
        count(*) filter (where p.created_at >= w.cutoff)                    as opened,
        count(*) filter (where p.closed_at is not null and p.closed_at >= w.cutoff) as closed,
        count(*) filter (where p.merged_at is not null and p.merged_at >= w.cutoff) as merged,
        -- Minutes, not hours: most PRs here merge within the hour, so whole
        -- hours collapse the median to 0. The render formats m / h / d.
        median(date_diff('minute', p.created_at, p.merged_at))
            filter (where p.merged_at is not null and p.merged_at >= w.cutoff) as median_merge_minutes
    from prs p
    cross join windows w
    group by w.window_key, p.repo
)

select
    repo, window_key, opened, closed, merged,
    -- Closure ratio: closed / opened in the window. NULL when nothing opened.
    case when opened > 0 then round(closed * 1.0 / opened, 2) end as closure_ratio,
    median_merge_minutes
from per_window
