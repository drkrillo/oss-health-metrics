-- GitHub sends UTC with a Z suffix, which read_csv_auto sniffs as TIMESTAMPTZ.
-- Casting straight to ::timestamp rebases that to the session's zone, so every
-- value would land 3 hours off here and be correct under GitHub Actions.  Go
-- through UTC explicitly instead.  See Transformer.MACROS for the other half.
select
    repo,
    number          as issue_number,
    title,
    state,
    author,
    labels,
    comments        as comment_count,
    created_at::timestamptz AT TIME ZONE 'UTC' as created_at,
    closed_at::timestamptz  AT TIME ZONE 'UTC' as closed_at,
    updated_at::timestamptz AT TIME ZONE 'UTC' as updated_at
from {source}
