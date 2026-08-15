-- Timestamps go through UTC explicitly — see stg_issues.sql.
select
    repo,
    comment_id,
    issue_number,
    author,
    author_association,
    created_at::timestamptz AT TIME ZONE 'UTC' as created_at,
    updated_at::timestamptz AT TIME ZONE 'UTC' as updated_at
from {source}
