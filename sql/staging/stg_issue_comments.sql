select
    repo,
    comment_id,
    issue_number,
    author,
    author_association,
    created_at::timestamp as created_at,
    updated_at::timestamp as updated_at
from {source}
