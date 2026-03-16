---
name: dao-governance
description: Use when users ask DAO research questions. Answer with Degov Agent API data first, then use web search when API coverage is insufficient.
---

# DAO Governance Skill

Use this skill to answer DAO governance questions with Degov Agent API data as the primary source.

## What Changed

This skill no longer requires users to provide a private key.
It manages a dedicated payment wallet locally and stores it outside git.

Default wallet file:
- `~/.agents/state/dao-governance/wallet.json`

## Setup

```bash
cd skills/dao-governance/scripts
pnpm install
export DEGOV_AGENT_WALLET_PASSPHRASE="choose-a-strong-passphrase"
pnpm exec tsx degov-client.ts wallet init
```

Optional API override:

```bash
export DEGOV_AGENT_API_BASE_URL="http://127.0.0.1:3311"
```

## Wallet Flow

1. Initialize the local wallet:

```bash
pnpm exec tsx degov-client.ts wallet init
```

2. Show the funding address:

```bash
pnpm exec tsx degov-client.ts wallet address
```

3. Fund that address with USDC on Base mainnet.

4. Check wallet balance:

```bash
pnpm exec tsx degov-client.ts wallet balance
```

If you already have a legacy wallet file from earlier testing under `.codex`, migrate it into the new managed location:

```bash
pnpm exec tsx degov-client.ts wallet migrate
```

5. Start querying the API:

```bash
pnpm exec tsx degov-client.ts daos
pnpm exec tsx degov-client.ts activity --hours 24 --limit 10
pnpm exec tsx degov-client.ts brief ens
```

## Pricing Guide

Approximate request budget per 1 USDC:
- `GET /v1/daos`: 200 requests
- `GET /v1/activity`: 200 requests
- `GET /v1/system/freshness`: 200 requests
- `GET /v1/daos/:daoId/brief`: 50 requests
- `GET /v1/items/:kind/:externalId`: 50 requests

Example:
- 1 DAO list + 5 activity queries + 10 DAO briefs costs about `0.23 USDC`

## Data Workflow

1. Check API health with `/health` if needed.
2. Use `/v1/daos` to discover DAO coverage.
3. Use `/v1/activity` for recent cross-DAO activity.
4. Use `/v1/daos/:daoId/brief` for compact DAO context.
5. Use `/v1/items/:kind/:externalId` only for items you plan to cite.
6. Fall back to web search only when API coverage is weak or stale.

## Commands

```bash
pnpm exec tsx degov-client.ts wallet init
pnpm exec tsx degov-client.ts wallet migrate
pnpm exec tsx degov-client.ts wallet address
pnpm exec tsx degov-client.ts wallet balance
pnpm exec tsx degov-client.ts budget --usd 1
pnpm exec tsx degov-client.ts daos
pnpm exec tsx degov-client.ts activity --hours 48 --limit 10
pnpm exec tsx degov-client.ts brief ens
pnpm exec tsx degov-client.ts item proposal <id>
pnpm exec tsx degov-client.ts freshness
pnpm exec tsx degov-client.ts health
```

## Guardrails

- Do not ask users to paste private keys.
- Use the local managed wallet for API payments.
- Require a wallet passphrase for encrypted local storage.
- If the wallet is unfunded, instruct the user to fund the displayed address on Base with USDC.
- State when information came from Degov Agent API versus the web.
- Do not fabricate governance activity, proposals, or dates.
