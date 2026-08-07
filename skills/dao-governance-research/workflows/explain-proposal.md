# Workflow: explain a specific proposal

Goal: explain one proposal — what it does, its status, votes — from a link, title, external id, or a
DAO context. Standard + plus tier; apply the paid-call consent flow first.

## Steps

1. **No key yet?** Resolve from an external reference (standard). Exactly one of `url`, `title`,
   `externalId`:

```bash
curl -s "https://agent-api.degov.ai/v2/proposals/resolve?url=<proposal-url>&daoId=<daoId>"
curl -s "https://agent-api.degov.ai/v2/proposals/resolve?title=<exact-title>&daoId=<daoId>"
```

Pick the best candidate from `candidates[].match.type` + `matchedFields`. If nothing matches, fall
back to web search on the official forum/Snapshot/Tally page.

2. **List context** (if you have a DAO but no specific proposal):

```bash
curl -s "https://agent-api.degov.ai/v2/proposals?daoId=<daoId>&sort=updatedDesc&limit=25"
```

3. **Detail** (plus):

```bash
curl -s "https://agent-api.degov.ai/v2/proposals/<proposalKey>"
```

Use `title`, `bodyText`, `proposerId`, `lifecycleStatus`, `outcome`, `choices`, `quorumRaw`,
`startAt`, `endAt`, `sourceUrl`, `discussionUrl`.

4. **Votes** (plus) when the user asks about support/outcome:

```bash
curl -s "https://agent-api.degov.ai/v2/proposals/<proposalKey>/votes/summary"
curl -s "https://agent-api.degov.ai/v2/proposals/<proposalKey>/votes?order=power&limit=100"   # top voters by power
```

## Decision rules

- `resolve` is optional — if a list/event/signal already returned the key, skip it.
- Ordinary explanations stop after detail (+ vote summary when asked). Do **not** call `evidence`
  unless the answer is citation/audit-oriented (see [evidence.md](evidence.md)).
- `bodyText` may be long; summarize, do not paste. Quote short key passages with the source link.
- Readiness: if `meta.readiness.status` is `backfilling`/`stale`, say the data may lag.

## Output

Plain-language explanation: what the proposal does, current status, vote totals/quorum when
relevant, key dates, and the source links. For security-oriented questions, switch to
[proposal-security.md](proposal-security.md).
