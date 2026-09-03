# Degov Agent API V2 reference

Base URL: `https://agent-api.degov.ai`.

The machine-readable source of truth is `GET /openapi.json`. It contains the public route set, input
and output schemas, real examples, and `x-payment-info` for paid operations. Prefer it over this
summary if the two ever differ.

## Public boundary

The public V2 API exposes governance data only:

- DAOs and their available governance resource families
- proposals and exact proposal resolution
- proposal votes and normalized summaries when supported
- governance-related forum topics
- DAO participants and voter history

Operational health, ingestion status, internal event/signal feeds, timelines, evidence bundles, and
V1 routes are not part of the public contract. Do not probe or depend on undocumented paths.

## Access and payment

`GET /v2/daos` and `GET /v2/daos/{daoId}` are free. The other routes below are paid and accept
either an x402 payment or a DeGov partner token in `x-degov-api-token`.

For x402, make the request without fabricating payment fields, inspect the returned
`PAYMENT-REQUIRED` challenge, and delegate payment to the wallet capability. Read current prices
from the operation's `x-payment-info` in `/openapi.json` or from the challenge; do not hardcode
them.

## Response envelopes

A detail response contains only `data`:

```json
{
  "data": {
    "daoId": "uniswapgovernance-eth",
    "name": "Uniswap"
  }
}
```

A list response contains `data` and `page`:

```json
{
  "data": [],
  "page": {
    "hasMore": false,
    "nextCursor": null
  }
}
```

Public responses do not expose a generation time, coverage label, readiness state, or serving
revision. DAO, proposal, forum-topic, and vote-summary records include `dataAsOf`: the latest source
observation included in that published record. It is useful provenance, but it does not prove that
every provider or related resource is current. Verify time-sensitive claims through the returned
official source URL.

Errors normally use:

```json
{
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "Unknown query field",
    "details": { "fields": ["unknown"] }
  },
  "requestId": "req-123"
}
```

## Pagination and windows

- List `limit` values are integers from 1 through 100 and default to 25.
- `nextCursor` is non-null only when `hasMore` is true. Pass it back unchanged to the same endpoint
  with the same filters and sort.
- Never inspect, construct, shorten, or reuse a cursor for another request shape.
- Pagination is a live keyset traversal: unrelated publications do not expire a cursor, but records
  inserted or updated while paging can move between pages. Restart when a point-in-time full scan is
  required.
- Proposal creation, forum activity, and voter-history windows are at most 365 days.
- `...From` bounds are inclusive and `...To` bounds are exclusive.

## Public identifiers

- `daoId` is a stable public slug, such as `uniswapgovernance-eth`. Obtain it from the DAO directory
  rather than guessing from the display name.
- `proposalId` is an opaque value beginning with `p1_`. Obtain it from proposal list, proposal
  resolution, or voter history, and pass it back unchanged.
- `topicId` begins with `t1_` and is useful for caching or deduplication. There is no public topic
  detail route.
- `voterId` is the normalized public voter identity. EVM addresses are lowercase; another provider
  may use a different non-blank identity string.

## Free routes

### `GET /v2/daos`

Lists DAOs alphabetically by public `daoId`.

| Name     | Type   | Meaning                                      |
| -------- | ------ | -------------------------------------------- |
| `query`  | string | Case-insensitive substring of DAO name or id |
| `limit`  | int    | 1-100, default 25                            |
| `cursor` | string | Cursor from the preceding matching DAO page  |

```bash
curl -sS "https://agent-api.degov.ai/v2/daos?query=Uniswap&limit=25"
```

Example item:

```json
{
  "daoId": "uniswapgovernance-eth",
  "name": "Uniswap",
  "sources": ["discourse", "snapshot"],
  "availableData": ["proposals", "votes", "forumTopics"],
  "proposalCounts": { "total": 197, "active": 0 },
  "participation": { "voterCount": 30710, "voteCount": 313022 },
  "latestActivity": {
    "proposalCreatedAt": "2026-07-21T23:15:24.000Z",
    "forumLastPostedAt": "2026-07-10T09:08:39.987Z"
  },
  "dataAsOf": "2026-09-03T09:42:18.000Z"
}
```

`participation` is either the published complete vote totals or `null`. Timestamps inside
`latestActivity` can also be `null`. `availableData` is a resource-availability signal, not a
freshness guarantee.

Use `query` to resolve a natural-language DAO name; ask the user when multiple matches remain.

### `GET /v2/daos/{daoId}`

Returns one DAO item with the same fields as the directory.

```bash
curl -sS "https://agent-api.degov.ai/v2/daos/uniswapgovernance-eth"
```

An unknown slug returns `404 NOT_FOUND`.

## Paid routes

The curl examples below show request construction only. Without a partner token or x402 payment,
they intentionally return `402 Payment Required`.

### `GET /v2/daos/{daoId}/participants`

Ranks voters who have an effective latest vote in the DAO.

| Name     | Type   | Meaning                                                 |
| -------- | ------ | ------------------------------------------------------- |
| `sort`   | enum   | `votedProposalCountDesc` or `latestEffectiveVoteAtDesc` |
| `limit`  | int    | 1-100, default 25                                       |
| `cursor` | string | Cursor from the preceding page                          |

Default sort: `votedProposalCountDesc`.

```bash
curl -sS \
  "https://agent-api.degov.ai/v2/daos/uniswapgovernance-eth/participants?sort=votedProposalCountDesc&limit=5"
```

Example item:

```json
{
  "voterId": "0x06c4865ab16c9c760622f19a313a2e637e2e66a2",
  "address": "0x06c4865ab16c9c760622f19a313a2e637e2e66a2",
  "votedProposalCount": 152,
  "earliestEffectiveVoteAt": "2021-05-27T13:01:20.000Z",
  "latestEffectiveVoteAt": "2025-08-26T01:25:19.000Z"
}
```

`address` and either timestamp can be `null`.

### `GET /v2/proposals`

Lists proposals using title search and exact structured filters.

| Name          | Type       | Meaning                                                      |
| ------------- | ---------- | ------------------------------------------------------------ |
| `query`       | string     | Case-insensitive substring of proposal title                 |
| `daoId`       | string     | Exact public DAO slug                                        |
| `provider`    | string     | Exact, case-sensitive provider returned by the API           |
| `proposerId`  | string     | Exact normalized proposer identity                           |
| `status`      | repeatable | `pending`, `active`, or `closed`; repeat for multiple values |
| `createdFrom` | date-time  | Inclusive proposal creation lower bound                      |
| `createdTo`   | date-time  | Exclusive proposal creation upper bound                      |
| `sort`        | enum       | `createdDesc` or `votingEndsAtAsc`                           |
| `limit`       | int        | 1-100, default 25                                            |
| `cursor`      | string     | Cursor from the preceding page                               |

Default sort: `createdDesc`.

```bash
curl -sS \
  "https://agent-api.degov.ai/v2/proposals?query=cirBTC&daoId=aavedao-eth&status=active&status=pending&sort=votingEndsAtAsc&limit=10"
```

Example item:

```json
{
  "proposalId": "p1_<opaque>",
  "daoId": "aavedao-eth",
  "title": "[ARFC] Onboard cirBTC on Aave v3 Core and Aave V4 Core",
  "proposerId": "0x66a28531e6f390a8cd44ab0c57a0f1aeb7e673ff",
  "source": {
    "provider": "snapshot",
    "externalId": "0xe7ce...",
    "url": "https://snapshot.org/#/aavedao.eth/proposal/0xe7ce...",
    "discussionUrl": "https://governance.aave.com/t/arfc-onboard-cirbtc-on-aave-v3-core-and-aave-v4-core/25128/4"
  },
  "status": "active",
  "outcome": "unknown",
  "createdAt": "2026-09-01T09:58:40.000Z",
  "votingStartsAt": "2026-09-02T09:58:40.000Z",
  "votingEndsAt": "2026-09-05T09:58:40.000Z",
  "dataAsOf": "2026-09-03T09:42:18.000Z"
}
```

`proposerId`, `discussionUrl`, `status`, and the three governance timestamps can be `null`.
`outcome` is `passed`, `failed`, `executed`, `canceled`, `no_quorum`, or `unknown`; an active
proposal normally has `unknown`. Search matches titles only, not proposal bodies.

### `POST /v2/proposals/resolve`

Resolves exactly one proposal from either its canonical URL or complete source identity. The JSON
body is a discriminated union; extra fields are rejected.

By URL:

```bash
curl -sS -X POST \
  -H "content-type: application/json" \
  --data '{"by":"url","url":"https://snapshot.org/#/uniswapgovernance.eth/proposal/0x5ae3426216321df66a67eb677874b725f80e51888ad2da72b382b21669c554ee"}' \
  "https://agent-api.degov.ai/v2/proposals/resolve"
```

By source identity:

```bash
curl -sS -X POST \
  -H "content-type: application/json" \
  --data '{"by":"source_id","daoId":"uniswapgovernance-eth","provider":"snapshot","externalId":"0x5ae3426216321df66a67eb677874b725f80e51888ad2da72b382b21669c554ee"}' \
  "https://agent-api.degov.ai/v2/proposals/resolve"
```

The response `data` is one proposal-list item. A title is not a supported resolver input.

### `GET /v2/proposals/{proposalId}`

Returns the proposal-list fields plus body, normalized choices, quorum, and source update time.

```bash
curl -sS "https://agent-api.degov.ai/v2/proposals/p1_<opaque>"
```

Additional fields:

```json
{
  "body": "## Summary\n\nThe proposal asks the DAO to...",
  "choices": [
    { "id": "1", "label": "For" },
    { "id": "2", "label": "Against" },
    { "id": "3", "label": "Abstain" }
  ],
  "quorumRequired": "40000000",
  "sourceUpdatedAt": "2026-07-26T20:15:24.000Z"
}
```

`body`, `choices`, `quorumRequired`, and `sourceUpdatedAt` can be `null`. Choice ids are provider
safe: Snapshot choices are normally one-based, while DeGov Square Governor choices use `0` Against,
`1` For, and `2` Abstain. The contract does not expose executable actions or a separate
authoritative execution-state object; use `source.url` for those claims.

### `GET /v2/proposals/{proposalId}/vote-summary`

Returns totals for proposals whose ballot choices can be normalized.

```bash
curl -sS "https://agent-api.degov.ai/v2/proposals/p1_<opaque>/vote-summary"
```

Example `data`:

```json
{
  "proposalId": "p1_<opaque>",
  "choices": [
    {
      "id": "1",
      "label": "For",
      "voteCount": 117,
      "knownVotingPower": "5347713.994141648005204052"
    },
    { "id": "2", "label": "Against", "voteCount": 0, "knownVotingPower": "0" }
  ],
  "totals": {
    "voteCount": 118,
    "knownVotingPower": "5349527.584801537875704052"
  },
  "quorum": {
    "requiredVotingPower": "40000000",
    "progressPercent": "13.373819462004",
    "reached": false
  },
  "dataAsOf": "2026-07-26T04:54:01.000Z"
}
```

Voting power is a decimal string and must not be converted to a binary floating-point number. A
`quorum` value of `null` means no usable provider requirement is available; nullable progress and
reached fields mean attainment could not be calculated safely. Governor quorum follows its
`COUNTING_MODE` membership instead of counting Against votes automatically. A
`404 DATA_NOT_AVAILABLE` response means a normalized summary is unavailable; it does not mean the
proposal does not exist.

### `GET /v2/proposals/{proposalId}/votes`

Lists effective latest votes for one proposal, with at most one current vote per voter.

| Name     | Type   | Meaning                        |
| -------- | ------ | ------------------------------ |
| `sort`   | enum   | `powerDesc` or `timeDesc`      |
| `limit`  | int    | 1-100, default 25              |
| `cursor` | string | Cursor from the preceding page |

Default sort: `powerDesc`.

```bash
curl -sS \
  "https://agent-api.degov.ai/v2/proposals/p1_<opaque>/votes?sort=powerDesc&limit=5"
```

Example item:

```json
{
  "voter": {
    "voterId": "0x8d07d225a769b7af3a923481e1fdf49180e6a265",
    "address": "0x8d07d225a769b7af3a923481e1fdf49180e6a265"
  },
  "choiceId": "1",
  "choiceLabel": "For",
  "rawChoice": 1,
  "votingPower": "2301703.801449782",
  "votedAt": "2026-07-26T04:54:01.000Z",
  "transactionHash": null
}
```

`address`, `choiceId`, `choiceLabel`, `votingPower`, `votedAt`, and `transactionHash` can be `null`.
Use `choiceId`/`choiceLabel` when present. `rawChoice` preserves any provider JSON value, including
a complex ballot for which the API deliberately leaves the normalized choice fields null.

### `GET /v2/forum-topics`

Lists governance-related forum topics.

| Name              | Type      | Meaning                                                  |
| ----------------- | --------- | -------------------------------------------------------- |
| `query`           | string    | Case-insensitive substring of forum-topic title          |
| `daoId`           | string    | Exact DAO slug                                           |
| `provider`        | string    | Exact provider                                           |
| `lastPostedFrom`  | date-time | Inclusive latest-post lower bound                        |
| `lastPostedTo`    | date-time | Exclusive latest-post upper bound                        |
| `minCommentCount` | int       | Minimum posts after the opening topic post               |
| `sort`            | enum      | `lastPostedAtDesc`, `createdDesc`, or `commentCountDesc` |
| `limit`           | int       | 1-100, default 25                                        |
| `cursor`          | string    | Cursor from the preceding page                           |

Default sort: `lastPostedAtDesc`.

```bash
curl -sS \
  "https://agent-api.degov.ai/v2/forum-topics?query=Aave%20V4&daoId=aavedao-eth&sort=commentCountDesc&limit=5"
```

Example item:

```json
{
  "topicId": "t1_<opaque>",
  "daoId": "aavedao-eth",
  "source": {
    "provider": "discourse",
    "externalId": "24293",
    "url": "https://governance.aave.com/t/arfc-aave-v4-activation-on-ethereum-mainnet/24293"
  },
  "title": "[ARFC] Aave V4 Activation on Ethereum Mainnet",
  "excerpt": null,
  "author": "alice",
  "category": { "id": "4", "name": "Governance" },
  "tags": [],
  "commentCount": 45,
  "likeCount": 112,
  "viewCount": 6949,
  "createdAt": "2026-03-13T18:00:12.676Z",
  "lastPostedAt": "2026-09-01T09:37:38.182Z",
  "dataAsOf": "2026-09-03T09:42:18.000Z"
}
```

`excerpt`, `author`, `category`, and either governance timestamp can be `null`. There is no
topic-detail endpoint. Search matches titles only. Open `source.url` when the user asks what the
discussion actually says and the excerpt is insufficient.

### `GET /v2/voters/{voterId}`

Returns one voter's participation totals across public active DAOs.

```bash
curl -sS \
  "https://agent-api.degov.ai/v2/voters/0x06c4865ab16c9c760622f19a313a2e637e2e66a2"
```

Example `data`:

```json
{
  "voterId": "0x06c4865ab16c9c760622f19a313a2e637e2e66a2",
  "address": "0x06c4865ab16c9c760622f19a313a2e637e2e66a2",
  "daoCount": 41,
  "votedProposalCount": 2223,
  "earliestEffectiveVoteAt": "2021-05-05T14:41:56.000Z",
  "latestEffectiveVoteAt": "2025-08-26T01:25:19.000Z"
}
```

`address` and either timestamp can be `null`.

### `GET /v2/voters/{voterId}/votes`

Lists the voter's effective latest votes, newest first.

| Name        | Type      | Meaning                         |
| ----------- | --------- | ------------------------------- |
| `daoId`     | string    | Optional exact DAO slug         |
| `votedFrom` | date-time | Inclusive vote-time lower bound |
| `votedTo`   | date-time | Exclusive vote-time upper bound |
| `limit`     | int       | 1-100, default 25               |
| `cursor`    | string    | Cursor from the preceding page  |

```bash
curl -sS \
  "https://agent-api.degov.ai/v2/voters/0x06c4865ab16c9c760622f19a313a2e637e2e66a2/votes?daoId=uniswapgovernance-eth&limit=5"
```

Example item:

```json
{
  "proposalId": "p1_<opaque>",
  "daoId": "uniswapgovernance-eth",
  "proposalTitle": "Establish Uniswap Governance as DUNI, a Wyoming DUNA",
  "proposalUrl": "https://snapshot.org/#/uniswapgovernance.eth/proposal/0xf9f9...",
  "choiceId": "1",
  "choiceLabel": "For",
  "rawChoice": 1,
  "votingPower": "1",
  "votedAt": "2025-08-26T01:25:19.000Z",
  "transactionHash": null
}
```

`choiceId`, `choiceLabel`, `votingPower`, `votedAt`, and `transactionHash` can be `null`. Interpret
`rawChoice` with the same caution as proposal vote rows when the normalized choice is unavailable.

## Known contract limits

- `dataAsOf` is per-record provenance, not a global freshness or pipeline-health guarantee.
- DAO name/id and proposal/forum title substring search are available; body and full-text search are
  not.
- Proposal outcome and quorum are exposed, but executable actions and a separate authoritative
  execution-state object are not.
- Forum topic detail is not exposed; excerpts and authors can be absent.
- Vote rows expose normalized choices and source transaction hashes when they can be represented,
  while preserving provider-shaped `rawChoice` for unsupported ballots.
- Some ballot mechanisms return `DATA_NOT_AVAILABLE` from vote summary even when vote rows exist.

These limits are reasons to open official source URLs and state uncertainty, not reasons to fill
missing facts with inference.
