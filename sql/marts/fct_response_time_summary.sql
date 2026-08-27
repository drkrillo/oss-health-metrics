-- Time to First Response, summarized per (item type x trailing window).
-- CHAOSS reports the MEDIAN (the Responsiveness guide: median is closer to how
-- people perceive the wait than the mean, and it ignores the long tail).
-- Issues and change requests are separate activity types in CHAOSS, so each is
-- reported on its own, plus a combined "all".
--
-- Window filters on the item's creation date: "of the items created in this
-- period, how long until the first human response". Items with no response yet
-- (first_response_at is null) are excluded from the median. They have no
-- duration, but that absence is visible in the Who-Has-The-Ball view.
--
-- Bots are already excluded upstream in fct_response_times.

with base as (
    select repo, item_type, created_at, hours_to_first_response
    from fct_response_times
    where hours_to_first_response is not null
),

-- item_type on its own, plus an "all" pseudo-type covering both.
typed as (
    select repo, item_type as type_key, created_at, hours_to_first_response from base
    union all
    select repo, 'all' as type_key, created_at, hours_to_first_response from base
),

windows(window_key, cutoff) as (
    values
        ('30d', utc_now() - interval '30 days'),
        ('90d', utc_now() - interval '90 days'),
        ('1y',  utc_now() - interval '365 days'),
        ('all', timestamp '1970-01-01')
)

select
    t.repo,
    w.window_key,
    t.type_key,
    count(*)                                   as n_items,
    round(median(t.hours_to_first_response), 1) as median_hours
from typed t
cross join windows w
where t.created_at >= w.cutoff
group by t.repo, w.window_key, t.type_key
