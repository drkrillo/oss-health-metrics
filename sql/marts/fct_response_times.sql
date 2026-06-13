-- One row per PR + one row per issue.
-- Time to first external response. No classification, raw durations.
--
-- IMPORTANT: In repos where the maintainer creates issues,
-- "time to first response" on issues = time until the COMMUNITY engages.

with

pr_first_comment as (
    select c.repo, c.issue_number as pr_number, min(c.created_at) as first_comment_at
    from stg_issue_comments c
    inner join stg_pull_requests p
        on c.repo = p.repo and c.issue_number = p.pr_number
    where c.author != p.author
    group by c.repo, c.issue_number
),

pr_first_review as (
    select r.repo, r.pr_number, min(r.submitted_at) as first_review_at
    from stg_pr_reviews r
    inner join stg_pull_requests p
        on r.repo = p.repo and r.pr_number = p.pr_number
    where r.author != p.author
    group by r.repo, r.pr_number
),

prs as (
    select
        p.repo, 'pr' as item_type, p.pr_number as item_number,
        p.author, p.state, p.created_at, p.merged_at, p.closed_at,
        least(fc.first_comment_at, fr.first_review_at) as first_response_at,
        date_diff('hour', p.created_at,
            least(fc.first_comment_at, fr.first_review_at)
        ) as hours_to_first_response,
        date_diff('hour', p.created_at, p.merged_at) as hours_to_merge
    from stg_pull_requests p
    left join pr_first_comment fc on p.repo = fc.repo and p.pr_number = fc.pr_number
    left join pr_first_review fr  on p.repo = fr.repo and p.pr_number = fr.pr_number
),

issue_first_comment as (
    select c.repo, c.issue_number, min(c.created_at) as first_comment_at
    from stg_issue_comments c
    inner join stg_issues i
        on c.repo = i.repo and c.issue_number = i.issue_number
    where c.author != i.author
    group by c.repo, c.issue_number
),

issues as (
    select
        i.repo, 'issue' as item_type, i.issue_number as item_number,
        i.author, i.state, i.created_at, null::timestamp as merged_at, i.closed_at,
        fc.first_comment_at as first_response_at,
        date_diff('hour', i.created_at, fc.first_comment_at) as hours_to_first_response,
        null::bigint as hours_to_merge
    from stg_issues i
    left join issue_first_comment fc
        on i.repo = fc.repo and i.issue_number = fc.issue_number
)

select * from prs
union all
select * from issues
