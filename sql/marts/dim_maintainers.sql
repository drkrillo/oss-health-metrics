-- One row per (repo, maintainer).
--
-- GitHub does not hand back a roster, and the issue/PR payload carries no
-- author_association for whoever opened the item.  What it does stamp is the
-- association on every comment and review, so the roster is derived from that:
-- anyone who has ever spoken as OWNER, COLLABORATOR or MEMBER on a repo has
-- push access or org membership there and is treated as a maintainer of it.
--
-- CONTRIBUTOR is deliberately not on that list.  GitHub uses it for "has landed
-- a change here before", which is a returning contributor, not a maintainer.
--
-- Two marts need this and they need it to agree: fct_open_items, to tell
-- response debt from the team's own backlog, and dim_contributors, to keep
-- maintainers out of behavioural rankings they would otherwise top.

select distinct repo, author
from (
    select repo, author, author_association from stg_issue_comments
    union all
    select repo, author, author_association from stg_pr_reviews
)
where author_association in ('OWNER', 'COLLABORATOR', 'MEMBER')
