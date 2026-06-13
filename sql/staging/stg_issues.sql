select
    repo,
    number          as issue_number,
    title,
    state,
    author,
    labels,
    comments        as comment_count,
    created_at::timestamp as created_at,
    closed_at::timestamp  as closed_at,
    updated_at::timestamp as updated_at
from {source}
