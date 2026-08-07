# Workflow: DAO discovery

Goal: figure out which DAO(s) the API covers and pick the right `daoId` for a follow-up question.
All free endpoints — no payment needed.

## Steps

1. Ambiguous or unknown DAO name → list the directory:

```bash
curl -s "https://agent-api.degov.ai/v2/daos?hasVoteData=true&limit=100"
```

Note: production DAO ids often carry suffixes (`ens-dao`, `uniswap` is `uniswap` — verify). Match by
`name` (case-insensitive) and by `daoId`; some short names are ambiguous, so prefer `daoId` in
follow-up calls.

2. Narrow the candidate:

```bash
curl -s "https://agent-api.degov.ai/v2/daos?limit=100&cursor=<nextCursor>"   # paginate if needed
curl -s "https://agent-api.degov.ai/v2/meta/data-status?daoId=<daoId>"       # per-DAO freshness
```

3. Chosen DAO → get context:

```bash
curl -s "https://agent-api.degov.ai/v2/daos/<daoId>"
```

Use `proposalCounts`, `outcomes`, `participation`, `coverageStatus`, and `voteCoverageStatus` to
describe the DAO and set expectations (e.g. "ENS has 74 proposals, 1 active; vote data
unavailable").

## Output

State the resolved `daoId`, why it was chosen, and the DAO summary in plain language. Then continue
with the relevant workflow ([recent-activity.md](recent-activity.md) or
[explain-proposal.md](explain-proposal.md)) or answer directly if the free data already answers the
question.
