# Degov Agent API v2 — endpoint cards

The v2 API is the only supported surface. Base URL (production): `https://agent-api.degov.ai`. All endpoints return the uniform envelope:

```json
{
  "data": { "...": "..." },
  "meta": {
    "requestId": "req-xxx",
    "generatedAt": "2026-08-07T07:58:10.529Z",
    "dataAsOf": "2026-08-07T07:57:55.672Z",
    "readiness": { "status": "ready" },
    "page": { "limit": 25, "hasMore": true, "nextCursor": "..." }
  }
}
```

- `data` is the payload; `meta.generatedAt` is when the response was built; `meta.dataAsOf` is how fresh the underlying data is.
- `meta.readiness.status` ∈ `ready | backfilling | stale | unavailable`. Readiness is publication state — separate from domain coverage. Treat `backfilling`/`stale` as "data may lag", not "not found".
- `meta.page` appears on list endpoints: `limit`, `hasMore`, `nextCursor` (opaque, revision-bound). Pass `nextCursor` back as `cursor` to continue; never reuse a cursor with different filters (409 `CURSOR_STALE`) and never construct one.
- Errors: `{ "error": { "code", "message", "details?" }, "meta": { "requestId" } }` — see `errors.md`.
- Paid endpoints respond `402` with a `PAYMENT-REQUIRED` header until payment is attached — see `x402.md` and the payment ceremony in SKILL.md.

Limits: `limit` max 100 (events max 200, votes max 500); event window max 90 days; proposal window max 365 days; timeline max 240 months.

## Key acquisition

- `proposalKey` is returned by `GET /v2/proposals`, `GET /v2/proposals/resolve`, `GET /v2/events`, and `GET /v2/signals`. Never construct or parse it; treat it as opaque. Follow-up endpoints (`detail`, `votes/summary`, `votes`, `evidence`) accept only the key.
- `topicKey` is returned by `GET /v2/forum-topics`, `GET /v2/events` (forum event types), and `GET /v2/signals` (forum item type).
- `voterIdentity` is returned by `GET /v2/daos/:daoId/voters`; also usable directly when you know the address/identity.

## Endpoints

### Free

#### `GET /v2/meta/pricing`

Live pricing route table. No payment, no pagination.

Params: none.

Response `data`: `{ token: "USDC", network: "eip155:8453", routes: [{ routeId, method, path, tier, paid, price }] }` — `tier` ∈ `free | standard | plus`; `price` is a decimal string or `null`. See `pricing.md`.

```bash
curl -s https://agent-api.degov.ai/v2/meta/pricing
```

#### `GET /v2/meta/data-status`

Global (or per-DAO) data freshness and coverage. No payment.

Params:

| Param   | Type   | Notes                                  |
| ------- | ------ | -------------------------------------- |
| `daoId` | string | optional; scopes the report to one DAO |

Global `data`: `{ scope: "global", counts: { daos, proposals, voteProposals }, coverageStatus, dataAsOf, projections: { pending, running, dead } }`. Per-DAO `data`: `{ scope: "dao", daoId, daoName, coverageStatus, voteCoverageStatus, latestSuccessfulSync, dataAsOf }`.

```bash
curl -s https://agent-api.degov.ai/v2/meta/data-status
curl -s "https://agent-api.degov.ai/v2/meta/data-status?daoId=ens-dao"
```

#### `GET /v2/daos`

DAO directory. No payment.

Params:

| Param            | Type                   | Notes                                          |
| ---------------- | ---------------------- | ---------------------------------------------- |
| `hasVoteData`    | `true`/`false`         | filter by vote data presence                   |
| `hasForumData`   | `true`/`false`         | filter by forum data presence                  |
| `coverageStatus` | string                 | e.g. `ready`                                   |
| `limit`          | int, 1–100, default 50 |                                                |
| `cursor`         | string                 | opaque page cursor from `meta.page.nextCursor` |

Item shape: `{ daoId, name, hasVoteData, hasForumData, coverageStatus, voteCoverageStatus, proposalCounts: { total, active }, participation: { uniqueVoters, totalVotes, totalVotingPower }, latestActivity: { proposalAt, voteAt, forumAt } }`. Numeric strings are decimal strings.

```bash
curl -s "https://agent-api.degov.ai/v2/daos?hasVoteData=true&limit=50"
```

#### `GET /v2/daos/:daoId`

DAO summary. No payment.

Params: none (path: `daoId`).

`data`: `{ daoId, name, coverageStatus, voteCoverageStatus, proposalCounts: { total, active, pending, closed }, outcomes: { passed, failed, executed, canceled, unknown }, participation: { uniqueVoters, totalVotes, totalVotingPower }, sourceTypes: string[], latestActivity: { proposalAt, voteAt, forumAt } }`.

```bash
curl -s https://agent-api.degov.ai/v2/daos/ens-dao
```

### Standard ($0.005 each)

#### `GET /v2/proposals`

Filterable, sortable proposal list. Paid (standard).

Params:

| Param             | Type                   | Notes                                                              |
| ----------------- | ---------------------- | ------------------------------------------------------------------ |
| `daoId`           | string                 | filter by DAO                                                      |
| `provider`        | string                 | filter by source provider (e.g. `snapshot`, `degov-square`)        |
| `proposerId`      | string                 | filter by proposer                                                 |
| `lifecycleStatus` | CSV                    | `active`, `pending`, `closed`, `unknown`                           |
| `outcome`         | CSV                    | `passed`, `executed`, `failed`, `canceled`, `unknown`              |
| `timeField`       | string                 | `createdAt`, `startAt`, `endAt`, `updatedAt` (default `updatedAt`) |
| `from` / `to`     | RFC 3339               | window on `timeField`; max 365 days                                |
| `sort`            | string                 | `updatedDesc` (default), `createdDesc`, `endingSoon`               |
| `limit`           | int, 1–100, default 25 |                                                                    |
| `cursor`          | string                 | page cursor                                                        |

Item shape: `{ proposalKey, identity: { daoId, provider, externalId }, title, sourceUrl, lifecycleStatus, outcome, endAt, coverageStatus }`.

```bash
curl -s "https://agent-api.degov.ai/v2/proposals?daoId=ens-dao&lifecycleStatus=active&sort=endingSoon&limit=25"
```

#### `GET /v2/proposals/resolve`

External reference → canonical `proposalKey`. Paid (standard). Use only when you have a URL/title/external id and no key yet.

Params: exactly one of `url`, `title`, or `externalId` (required), plus optional `daoId`, `provider`, and `limit` (1–20, default 5).

`data`: `{ candidates: [{ proposalKey, identity: { daoId, provider, externalId }, title, match: { type, matchedFields } }] }`. `match.type` is deterministic (`exact`/`url`/`title`/`external_id`-style), not a probability.

```bash
curl -s "https://agent-api.degov.ai/v2/proposals/resolve?url=https://snapshot.org/proposal/0x123...&daoId=ens-dao"
```

#### `GET /v2/events`

Event-time governance feed (proposal created / voting started / ended / ending soon / executed / updated, forum discussion active). Paid (standard). `from` and `to` are **required**; window max 90 days.

Params:

| Param           | Type                    | Notes                                                                                                                                                                     |
| --------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `from` / `to`   | RFC 3339                | required                                                                                                                                                                  |
| `daoId`         | string                  | optional                                                                                                                                                                  |
| `eventTypes`    | CSV                     | `proposal_created`, `proposal_voting_started`, `proposal_voting_ended`, `proposal_voting_ending_soon`, `proposal_executed`, `proposal_updated`, `forum_discussion_active` |
| `timeBasis`     | string                  | `eventTime` (default) or `discoveredTime`                                                                                                                                 |
| `importanceMin` | int 0–100               | minimum importance                                                                                                                                                        |
| `limit`         | int, 1–200, default 100 |                                                                                                                                                                           |
| `cursor`        | string                  |                                                                                                                                                                           |

Item shape: `{ eventId, eventType, eventTimeMs, daoId, itemType, title, url, importanceScore, proposalKey? | topicKey? }`.

```bash
curl -s "https://agent-api.degov.ai/v2/events?from=2026-08-01T00:00:00Z&to=2026-08-07T00:00:00Z&eventTypes=proposal_created,proposal_voting_ended&limit=200"
```

#### `GET /v2/signals`

Curated governance signals (proposal result, deadline reminders, governance radar, forum activity). Paid (standard). `from`/`to` required; window max 90 days.

Params:

| Param         | Type                   | Notes                                                                                                                                     |
| ------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `from` / `to` | RFC 3339               | required                                                                                                                                  |
| `daoId`       | string                 | optional                                                                                                                                  |
| `signalTypes` | CSV                    | `proposal_created`, `proposal_deadline_reminder`, `proposal_vote_ended`, `proposal_result`, `forum_discussion_active`, `governance_radar` |
| `timeBasis`   | string                 | `eventTime` (default) or `discoveredTime`                                                                                                 |
| `priorityMin` | int 0–100              | minimum priority                                                                                                                          |
| `surface`     | string                 | `agent` (default), `atlas_latest`, `atlas_priority`, `telegram_realtime`                                                                  |
| `limit`       | int, 1–100, default 50 |                                                                                                                                           |
| `cursor`      | string                 |                                                                                                                                           |

Item shape: `{ signalId, signalType, priority: { score, band }, actionability, daoId, title, summary, sourceUrl, severity, proposalKey? | topicKey? }`.

```bash
curl -s "https://agent-api.degov.ai/v2/signals?from=2026-08-01T00:00:00Z&to=2026-08-07T00:00:00Z&signalTypes=proposal_result,governance_radar&surface=agent"
```

#### `GET /v2/forum-topics`

Forum topic list. Paid (standard).

Params:

| Param                       | Type                   | Notes                                                 |
| --------------------------- | ---------------------- | ----------------------------------------------------- |
| `daoId`                     | string                 | optional                                              |
| `provider`                  | string                 | optional                                              |
| `governanceRelated`         | `true`/`false`         | narrow to governance-relevant threads                 |
| `updatedFrom` / `updatedTo` | RFC 3339               | window; max 365 days                                  |
| `minReplies`                | int                    | minimum reply count                                   |
| `sort`                      | string                 | `updatedDesc` (default), `createdDesc`, `repliesDesc` |
| `limit`                     | int, 1–100, default 25 |                                                       |
| `cursor`                    | string                 |                                                       |

Item shape: `{ topicKey, identity, title, summary, url, author, category, tags, relevanceScore, replies, posts, likes, views, createdAt, updatedAt }` (counts as decimal strings).

```bash
curl -s "https://agent-api.degov.ai/v2/forum-topics?daoId=uniswap&governanceRelated=true&sort=repliesDesc&limit=25"
```

### Plus ($0.01 each)

#### `GET /v2/proposals/:proposalKey`

Proposal detail (body text, proposer, choices, quorum, lifecycle). Paid (plus). `proposalKey` must come from a list/resolve/event/signal result.

`data`: `{ proposalKey, identity, title, bodyText, proposerId, sourceUrl, discussionUrl, lifecycleStatus, outcome, choices, quorumRaw, startAt, endAt, related: { voteSummary, votes, evidence } }`.

```bash
curl -s "https://agent-api.degov.ai/v2/proposals/<proposalKey>"
```

#### `GET /v2/proposals/:proposalKey/votes/summary`

Vote totals, quorum progress, per-choice breakdown. Paid (plus).

`data`: `{ proposal: { proposalKey, title }, totals: { votes, uniqueVoters, votingPower } | null, quorum: { raw, progress, reached } | null, choices: [{ key, label, votes, votingPower }], coverageStatus, readiness }`.

```bash
curl -s "https://agent-api.degov.ai/v2/proposals/<proposalKey>/votes/summary"
```

#### `GET /v2/proposals/:proposalKey/votes`

Vote rows. Paid (plus).

Params: `order` (`power` default | `time`), `limit` (1–500, default 100), `cursor`.

Item shape: `{ voteId, voterIdentity, voterAddress, choiceKey, choice, votingPower, votedAt, transactionHash }`.

```bash
curl -s "https://agent-api.degov.ai/v2/proposals/<proposalKey>/votes?order=power&limit=100"
```

#### `GET /v2/proposals/:proposalKey/evidence`

Optional research/audit bundle: provenance, source references, intelligence status, quality flags, limitations. Paid (plus). Use for citation/audit/security answers only — ordinary proposal explanations should skip it.

`data`: `{ proposal: { proposalKey, title, sourceUrl }, provenance: [{ field, source, provider, observedAt }], intelligence: { status, warnings }, qualityFlags: string[], warnings: string[] }`.

```bash
curl -s "https://agent-api.degov.ai/v2/proposals/<proposalKey>/evidence"
```

#### `GET /v2/forum-topics/:topicKey`

Forum topic detail. Paid (plus). Same shape as the list item.

```bash
curl -s "https://agent-api.degov.ai/v2/forum-topics/<topicKey>"
```

#### `GET /v2/daos/:daoId/timeline`

Monthly activity timeline. Paid (plus).

Params: `metric` (`proposals_created` | `votes_cast`, required), `fromMonth`/`toMonth` (YYYY-MM, max 240 months).

`data`: `[{ month, count }]` (shape per metric).

```bash
curl -s "https://agent-api.degov.ai/v2/daos/ens-dao/timeline?metric=proposals_created&fromMonth=2026-01&toMonth=2026-08"
```

#### `GET /v2/daos/:daoId/voters`

DAO voter ranking. Paid (plus).

Params: `limit` (1–100, default 25), `cursor`.

Item shape: `{ rank, voterIdentity, totalVotingPower, voteCount, proposalCount }`.

```bash
curl -s "https://agent-api.degov.ai/v2/daos/ens-dao/voters?limit=25"
```

#### `GET /v2/voters/:voterIdentity`

Voter profile across DAOs. Paid (plus).

`data`: `{ voterIdentity, daoCount, voteCount, proposalCount, totalVotingPower, daos: [{ daoId, voteCount, proposalCount, totalVotingPower, firstVoteAt, lastVoteAt }] }`.

```bash
curl -s "https://agent-api.degov.ai/v2/voters/<voterIdentity>"
```

#### `GET /v2/voters/:voterIdentity/votes`

Voter vote history. Paid (plus).

Params: `daoId`, `from`/`to` (RFC 3339, max 365 days), `limit` (1–100, default 50), `cursor`.

Item shape: `{ proposal: { proposalKey, title }, choiceKey, votingPower, votedAt, transactionHash }`.

```bash
curl -s "https://agent-api.degov.ai/v2/voters/<voterIdentity>/votes?limit=50"
```

## v1 → v2 migration table (for users of the previous skill version)

| v1 (frozen, removed)              | v2 replacement                                                                     |
| --------------------------------- | ---------------------------------------------------------------------------------- |
| `GET /v1/activity`                | `GET /v2/proposals` / `GET /v2/events` / `GET /v2/signals`                         |
| `GET /v1/governance-events`       | `GET /v2/events` (event-time feed)                                                 |
| `GET /v1/daos/:daoId/brief`       | `GET /v2/daos/:daoId` + `GET /v2/proposals?daoId=...`                              |
| `GET /v1/items/:kind/:externalId` | `GET /v2/proposals/resolve` → `GET /v2/proposals/:proposalKey` (or `forum-topics`) |
| `GET /v1/system/freshness`        | `GET /v2/meta/data-status`                                                         |
| `GET /v1/meta/pricing`            | `GET /v2/meta/pricing`                                                             |

## Implementation notes

- Decimal amounts (`uniqueVoters`, `totalVotingPower`, `votes`, `replies`, ...) are strings; do not parse to float for display.
- `ServingProposal`-sourced ids are never exposed; keys are the only stable handles.
- The v2 cache is revision-bound: responses may be served from memory cache with `readiness.currentRevision`; a stale cursor means the serving revision advanced — re-run the list.
