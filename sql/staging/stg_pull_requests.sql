-- Timestamps go through UTC explicitly — see stg_issues.sql.
select
    repo,
    number          as pr_number,
    title,
    state,
    author,
    merged_at::timestamptz  AT TIME ZONE 'UTC' as merged_at,
    created_at::timestamptz AT TIME ZONE 'UTC' as created_at,
    closed_at::timestamptz  AT TIME ZONE 'UTC' as closed_at,
    updated_at::timestamptz AT TIME ZONE 'UTC' as updated_at
from {source}
