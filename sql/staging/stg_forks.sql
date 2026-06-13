select
    repo,
    author,
    forked_at::timestamp as forked_at
from {source}
