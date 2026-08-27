-- Contributor counts per trailing window (30d / 90d / 1y / all): total vs active.
--
--   total , distinct people with ANY activity in the window (forks, comments,
--            issues, PRs, reviews). The whole surface of people around the repo.
--   active, distinct people with a real CONTRIBUTION in the window. CHAOSS
--            "Types of Contributions" does not count a fork as a contribution,
--            so active excludes fork-only people.
--
-- One number is the reach, the other is who actually did something.

with events as (
    select repo, author, event_at, (event_type <> 'fork') as is_contribution
    from fct_contributor_events
),

windows(window_key, cutoff) as (
    values
        ('30d', utc_now() - interval '30 days'),
        ('90d', utc_now() - interval '90 days'),
        ('1y',  utc_now() - interval '365 days'),
        ('all', timestamp '1970-01-01')
)

select
    e.repo,
    w.window_key,
    count(distinct e.author)                                    as total_contributors,
    count(distinct e.author) filter (where e.is_contribution)   as active_contributors
from events e
cross join windows w
where e.event_at >= w.cutoff
group by e.repo, w.window_key
