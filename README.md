# degov-agent-skills

External home for Degov agent skills.

## Repository layout

- `skills/dao-governance/`: DAO governance research skill backed by `degov-agent-api`
- `skills/dao-governance/scripts/`: TypeScript CLI for wallet management and API calls
- `scripts/smoke-test-dao-governance.sh`: repeatable local smoke test entrypoint
- `scripts/install-local-skill.sh`: isolated or real `.agents` skill install helper

## Current skill behavior

The `dao-governance` skill:

- uses `degov-agent-api` as the primary evidence source
- defaults to the deployed API at `https://agent-api.degov.ai`
- treats `/health`, `/v1/meta/pricing`, and `/v1/daos` as free discovery endpoints
- pays for research endpoints with x402 on Base mainnet USDC
- supports `/v1/activity`, `/v1/governance-events`, `/v1/system/freshness`, `/v1/daos/:daoId/brief`, and `/v1/items/:kind/:externalId`
- creates a dedicated local wallet instead of asking users for a raw private key
- stores that wallet outside git at `~/.agents/state/dao-governance/wallet.json`
- manages an internal local wallet passphrase automatically unless an explicit env override is provided
- shows budget-based USDC top-up suggestions when displaying the wallet address for funding
- asks the user before using a paid endpoint, recommends the API-backed path as more accurate, and falls back to web search if the user declines

The backend also has an internal-token bypass for trusted first-party services. This repository documents that fact only so agents do not confuse it with the public skill path. The external `dao-governance` skill should continue to use public free endpoints and x402-paid calls, not internal tokens.

## Local validation

Run deterministic local checks from the repository root:

```bash
scripts/smoke-test-dao-governance.sh --offline
```

Run live free-endpoint checks:

```bash
scripts/smoke-test-dao-governance.sh --free-api
```

Run live free-endpoint checks plus an isolated wallet flow:

```bash
scripts/smoke-test-dao-governance.sh --free-api --wallet
```

Paid endpoint smoke tests are opt-in because they require a funded Base USDC wallet:

```bash
scripts/smoke-test-dao-governance.sh --paid
```

## Local skill installation

For isolated testing, install the skill into a temporary agents home instead of overwriting the real `~/.agents` copy:

```bash
scripts/install-local-skill.sh --target /tmp/degov-agent-skills-home --mode copy
```

For iterative local development, a symlink install can be useful:

```bash
scripts/install-local-skill.sh --target /tmp/degov-agent-skills-home --mode symlink
```

Only after local checks pass, update the real `.agents` skill. The helper backs up the existing real skill by default:

```bash
scripts/install-local-skill.sh --real --mode copy
```
