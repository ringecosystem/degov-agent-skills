# dao-governance compatibility notes

Last checked against `degov-agent-api` main commit `b9547be`.

## Current public API facts

Free endpoints:

- `GET /health`
- `GET /v1/meta/pricing`
- `GET /v1/daos`

Paid x402 endpoints:

- `GET /v1/activity`
- `GET /v1/governance-events`
- `GET /v1/system/freshness`
- `GET /v1/daos/:daoId/brief`
- `GET /v1/items/:kind/:externalId`

Payment network:

- Base mainnet, CAIP-2 `eip155:8453`
- USDC asset address `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- Pricing should be read dynamically from `GET /v1/meta/pricing`. As of the checked backend commit, pricing metadata includes `governanceEvents`; the CLI still falls back to the `activity` price for older deployments that do not expose a dedicated governance-events metadata key.

## Important schema and workflow notes

`/v1/activity` returns recently updated proposal/forum-topic items. Item detail lookup should use:

- `item.evidenceRef.kind`
- `item.evidenceRef.externalId`

`/v1/governance-events` returns event-time records for a supplied window. It is the better source for deadline- or event-oriented reporting because it models events such as:

- `proposal_created`
- `proposal_voting_started`
- `proposal_voting_ending_soon`
- `proposal_voting_ended`
- `proposal_updated`
- `forum_topic_created`
- `forum_discussion_active`

At the HTTP level it requires:

- `start_ms`
- `end_ms`

Optional filters:

- `dao_id`
- `limit`
- `event_types`

## Internal-token bypass

The backend supports a trusted first-party internal bypass. This is not a public user setup path for this skill. External agents should use free public endpoints and x402-paid requests after user consent.

## Local validation evidence

The following checks were run during the May 2026 alignment pass:

- `pnpm install --frozen-lockfile`
- `pnpm run format:check`
- `pnpm run typecheck`
- `pnpm exec tsx degov-client.ts help`
- `pnpm exec tsx degov-client.ts health`
- `pnpm exec tsx degov-client.ts budget --usd 1`
- `pnpm exec tsx degov-client.ts daos`
- isolated wallet `init`, `address`, and `balance` using `/tmp/degov-agent-skills-test`

Observed free API result: production `daos` returned 28 DAO items.

Paid endpoint smoke testing is intentionally opt-in because it requires a funded Base USDC wallet.
