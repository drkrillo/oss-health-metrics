-- One row per open PR/issue — who needs to act next?
--
-- "The ball" is response debt, not ownership.  Three states:
--
--   maintainer  — somebody outside the team spoke last, or an outside item has
--                 gone unanswered.  This is the number that matters.
--   contributor — the team answered somebody; the outsider owes the next move.
--   nobody      — the team's own backlog.  No outsider is involved, so no one
--                 is being kept waiting.
--
-- The third state is why this query reads `opened_by` and not just the role of
-- the last actor.  Judging by the last actor alone misfiles every item a
-- maintainer opened: a maintainer commenting on their own issue looked exactly
-- like a maintainer replying to a contributor, so the item flipped to
-- "contributor", turned green, and dropped out of the maintainer KPI even
-- though nothing had been handed to anyone.

with open_prs as (
    select repo, pr_number as item_number, 'pr' as item_type,
           title, author, created_at
    from stg_pull_requests where state = 'open'
),

open_issues as (
    select repo, issue_number as item_number, 'issue' as item_type,
           title, author, created_at
    from stg_issues where state = 'open'
),

open_items as (
    select * from open_prs
    union all
    select * from open_issues
),

interactions as (
    select c.repo, c.issue_number as item_number, c.author as actor,
           c.author_association, c.created_at as acted_at, 'comment' as action_type
    from stg_issue_comments c
    inner join open_items oi on c.repo = oi.repo and c.issue_number = oi.item_number

    union all

    select r.repo, r.pr_number as item_number, r.author as actor,
           r.author_association, r.submitted_at as acted_at, 'review' as action_type
    from stg_pr_reviews r
    inner join open_items oi on r.repo = oi.repo and r.pr_number = oi.item_number
),

last_action as (
    select repo, item_number, actor as last_actor,
           author_association as last_actor_role,
           acted_at as last_action_at, action_type as last_action_type,
           row_number() over (partition by repo, item_number order by acted_at desc) as rn
    from interactions
),

interaction_counts as (
    select repo, item_number,
           count(*) as total_interactions,
           count(*) filter (
               where author_association not in ('OWNER', 'COLLABORATOR', 'MEMBER')
           ) as outside_interactions
    from interactions
    group by repo, item_number
)

select
    oi.repo, oi.item_type, oi.item_number, oi.title,
    oi.author as opened_by, oi.created_at as opened_at,
    (m.author is not null) as opened_by_maintainer,
    la.last_actor, la.last_actor_role, la.last_action_at, la.last_action_type,
    date_diff('hour', coalesce(la.last_action_at, oi.created_at),
              utc_now()) as hours_waiting,
    date_diff('hour', oi.created_at, utc_now()) as hours_since_opened,
    coalesce(ic.total_interactions, 0) as total_interactions,
    coalesce(ic.outside_interactions, 0) as outside_interactions,
    case
        -- Somebody outside the team spoke last: the team owes a reply.
        when la.last_actor is not null
             and la.last_actor_role not in ('OWNER', 'COLLABORATOR', 'MEMBER')
            then 'maintainer'
        -- Nobody has responded at all.  That is response debt only when the
        -- item came from outside; a maintainer's own silent issue is backlog.
        when la.last_actor is null
            then case when m.author is not null then 'nobody' else 'maintainer' end
        -- A maintainer spoke last, which is a handoff only if there is
        -- somebody outside to hand it to — either because they opened the
        -- item or because they joined the thread.
        else case when m.author is null
                       or coalesce(ic.outside_interactions, 0) > 0
                  then 'contributor' else 'nobody' end
    end as waiting_on
from open_items oi
left join dim_maintainers m
    on oi.repo = m.repo and oi.author = m.author
left join last_action la
    on oi.repo = la.repo and oi.item_number = la.item_number and la.rn = 1
left join interaction_counts ic
    on oi.repo = ic.repo and oi.item_number = ic.item_number
