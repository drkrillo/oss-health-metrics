select
    repo,
    number          as pr_number,
    title,
    state,
    author,
    merged_at::timestamp  as merged_at,
    created_at::timestamp as created_at,
    closed_at::timestamp  as closed_at,
    updated_at::timestamp as updated_at
from {source}
