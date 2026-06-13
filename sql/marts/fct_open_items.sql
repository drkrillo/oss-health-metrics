-- One row per open PR/issue — who needs to act next?
--
-- Logic:
-- - Last action by OWNER/COLLABORATOR/MEMBER → ball with contributor
-- - Last action by anyone else (or no response) → ball with maintainer

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
    select repo, item_number, count(*) as total_interactions
    from interactions
    group by repo, item_number
)

select
    oi.repo, oi.item_type, oi.item_number, oi.title,
    oi.author as opened_by, oi.created_at as opened_at,
    la.last_actor, la.last_actor_role, la.last_action_at, la.last_action_type,
    date_diff('hour', coalesce(la.last_action_at, oi.created_at),
              current_timestamp) as hours_waiting,
    date_diff('hour', oi.created_at, current_timestamp) as hours_since_opened,
    coalesce(ic.total_interactions, 0) as total_interactions,
    case
        when la.last_actor is null then 'maintainer'
        when la.last_actor_role in ('OWNER', 'COLLABORATOR', 'MEMBER') then 'contributor'
        else 'maintainer'
    end as waiting_on
from open_items oi
left join last_action la
    on oi.repo = la.repo and oi.item_number = la.item_number and la.rn = 1
left join interaction_counts ic
    on oi.repo = ic.repo and oi.item_number = ic.item_number
