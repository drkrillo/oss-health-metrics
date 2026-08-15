-- Weekly time series: WIP, throughput, and cycle time.
-- Implements Little's Law: cycle_time = wip / throughput

with

week_bounds as (
    select repo,
        date_trunc('week', min(created_at))::date as first_week,
        date_trunc('week', current_date)::date    as last_week
    from stg_pull_requests
    group by repo
),

all_weeks as (
    select wb.repo,
        unnest(generate_series(wb.first_week, wb.last_week, interval '7 days'))::date as week_start
    from week_bounds wb
),

opened as (
    select repo, date_trunc('week', created_at)::date as week_start,
           count(*) as prs_opened
    from stg_pull_requests
    group by repo, week_start
),

closed as (
    select repo,
        date_trunc('week', coalesce(merged_at, closed_at))::date as week_start,
        count(*) as prs_closed,
        count(*) filter (where merged_at is not null) as prs_merged
    from stg_pull_requests
    where closed_at is not null or merged_at is not null
    group by repo, week_start
),

weekly_flow as (
    select
        aw.repo, aw.week_start,
        coalesce(o.prs_opened, 0) as prs_opened,
        coalesce(c.prs_closed, 0) as prs_closed,
        coalesce(c.prs_merged, 0) as prs_merged,
        sum(coalesce(o.prs_opened, 0)) over w
            - sum(coalesce(c.prs_closed, 0)) over w as wip,
        -- Throughput must be the SAME exit that drains the WIP, or the two
        -- sides of Little's Law disagree. WIP drops on every close, so
        -- throughput counts every close (merged or not), not merges alone —
        -- otherwise ~21% of exits (closed-without-merge) go uncounted and the
        -- cycle-time estimate inflates. This is a derived flow ESTIMATE; the
        -- canonical cycle time is CHAOSS Change Requests Duration.
        avg(coalesce(c.prs_closed, 0)) over (
            partition by aw.repo order by aw.week_start
            rows between 3 preceding and current row
        ) as throughput_4w_avg
    from all_weeks aw
    left join opened o on aw.repo = o.repo and aw.week_start = o.week_start
    left join closed c on aw.repo = c.repo and aw.week_start = c.week_start
    window w as (partition by aw.repo order by aw.week_start)
)

select
    repo, week_start, prs_opened, prs_merged, prs_closed,
    wip, throughput_4w_avg,
    case
        when throughput_4w_avg > 0
        then round(wip::numeric / throughput_4w_avg, 1)
    end as cycle_time_weeks
from weekly_flow
