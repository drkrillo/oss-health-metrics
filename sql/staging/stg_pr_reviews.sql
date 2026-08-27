-- Timestamps go through UTC explicitly, see stg_issues.sql.
select
    repo,
    pr_number,
    review_id,
    author,
    author_association,
    state           as review_state,
    submitted_at::timestamptz AT TIME ZONE 'UTC' as submitted_at
from {source}
