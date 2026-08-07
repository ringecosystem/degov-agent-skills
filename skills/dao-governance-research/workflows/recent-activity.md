# Workflow: recent governance activity

Goal: answer "what has <DAO> been doing lately?" or "what happened in governance this week?" Paid
(standard tier) — apply the paid-call consent flow in [SKILL.md](../SKILL.md) first.

## Steps

1. Resolve the DAO (see [discovery.md](discovery.md)) and decide the window. Compute RFC 3339
   timestamps, e.g. `from=<now - 168h>` to `<now>` for "this week".

2. Event-time feed (timing semantics matter — deadlines, vote starts/ends, "what happened today"):

```bash
curl -s "https://agent-api.degov.ai/v2/events?daoId=<daoId>&from=<RFC3339>&to=<RFC3339>&limit=200"
# or multi-DAO: omit daoId
curl -s "https://agent-api.degov.ai/v2/events?from=<RFC3339>&to=<RFC3339>&eventTypes=proposal_created,proposal_voting_ended&limit=200"
```

3. Curated signals ("biggest stories", watch-style summaries):

```bash
curl -s "https://agent-api.degov.ai/v2/signals?from=<RFC3339>&to=<RFC3339>&signalTypes=proposal_result,governance_radar&surface=agent&limit=100"
```

4. Proposals list for a DAO scan (last-updated ordering):

```bash
curl -s "https://agent-api.degov.ai/v2/proposals?daoId=<daoId>&sort=updatedDesc&limit=25"
```

5. For the most important items, follow their keys into detail (plus tier, confirm with user if the
   budget matters):

```bash
curl -s "https://agent-api.degov.ai/v2/proposals/<proposalKey>"
curl -s "https://agent-api.degov.ai/v2/proposals/<proposalKey>/votes/summary"
```

## Decision rules

- Use `events` when the answer depends on _when_ things happened (deadlines, "ended today", vote
  windows).
- Use `signals` for _curated_ highlights (result announcements, deadline reminders, radar) — fewer,
  higher-signal items.
- Use `proposals` for a raw last-updated scan; separate proposal/forum scans are unnecessary in v2
  (use `forum-topics` only when the question is about forum discussion).
- Paginate with `meta.page.nextCursor` when `hasMore` is true; if `CURSOR_STALE`, re-run without a
  cursor.

## Output

Plain-language summary of the window: what happened, which DAO(s), timing, importance. Cite the
event/signal sources (`url` fields) and say whether the data came from the API, the web, or both.
