select
    repo,
    pr_number,
    review_id,
    author,
    author_association,
    state           as review_state,
    submitted_at::timestamp as submitted_at
from {source}
