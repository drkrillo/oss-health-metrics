-- Contributor Absence Factor (a.k.a. Bus Factor).
-- CHAOSS: "the smallest number of contributors responsible for 50% of total
-- contributions." A low number means the project leans on few people — if they
-- leave, most of the activity leaves with them.
--
-- One row per (repo, window, definition) — 4 windows x 2 definitions = up to 8
-- rows per repo. All values are precomputed so the dashboard card can switch
-- between them client-side without a server.
--
-- Windows are trailing from today: 30d / 90d / 1y / all.
-- Definitions of "contribution":
--   normal — everything except forks (a fork is interest, not a contribution;
--            CHAOSS "Types of Contributions" does not list it)
--   strict — code work only: PRs opened, PRs merged, reviews given
--
-- Forks are always excluded: a fork is not a contribution under CHAOSS.

with events as (
    select
        repo, author, event_at,
        (event_type <> 'fork')                                  as counts_normal,
        (event_type in ('pr_opened', 'pr_merged', 'review'))    as counts_strict
    from fct_contributor_events
),

-- Trailing window cutoffs. 'all' uses an epoch far in the past.
windows(window_key, cutoff) as (
    values
        ('30d', current_timestamp - interval '30 days'),
        ('90d', current_timestamp - interval '90 days'),
        ('1y',  current_timestamp - interval '365 days'),
        ('all', timestamp '1970-01-01')
),

-- Contributions per author, exploded across every (window, definition) it
-- falls into. An event 5 days old counts in 30d, 90d, 1y and all.
contrib as (
    select w.window_key, 'normal' as definition, e.repo, e.author, count(*) as n
    from events e
    join windows w on e.event_at >= w.cutoff
    where e.counts_normal
    group by 1, 2, 3, 4

    union all

    select w.window_key, 'strict' as definition, e.repo, e.author, count(*) as n
    from events e
    join windows w on e.event_at >= w.cutoff
    where e.counts_strict
    group by 1, 2, 3, 4
),

-- Rank authors by contribution volume and accumulate toward the 50% line.
ranked as (
    select *,
        sum(n) over (partition by repo, window_key, definition) as total_n,
        sum(n) over (
            partition by repo, window_key, definition
            order by n desc, author
            rows between unbounded preceding and current row
        ) as cum_n,
        row_number() over (
            partition by repo, window_key, definition
            order by n desc, author
        ) as rnk
    from contrib
)

select
    repo, window_key, definition,
    -- Bus factor: the first rank at which the running total reaches half.
    min(rnk) filter (where cum_n >= total_n / 2.0)  as bus_factor,
    count(*)                                          as total_contributors,
    max(total_n)                                      as total_contributions,
    -- Share of the single biggest contributor — context for how skewed it is.
    round(max(n) * 100.0 / max(total_n), 1)          as top_contributor_pct
from ranked
group by repo, window_key, definition
