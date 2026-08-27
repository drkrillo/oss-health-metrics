-- Timestamps go through UTC explicitly, see stg_issues.sql.
select
    repo,
    author,
    forked_at::timestamptz AT TIME ZONE 'UTC' as forked_at
from {source}
