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
- `~/.codex/memories/degov-agent-skills/dao-governance-wallet.json`

## Setup

```bash
cd skills/dao-governance/scripts
pnpm install
node degov-client.js wallet init
```

Optional API override:

```bash
export DEGOV_AGENT_API_BASE_URL="http://127.0.0.1:3311"
```

## Wallet Flow

1. Initialize the local wallet:

```bash
node degov-client.js wallet init
```

2. Show the funding address:

```bash
node degov-client.js wallet address
```

3. Fund that address with USDC on Base mainnet.

4. Check wallet balance:

```bash
node degov-client.js wallet balance
```

5. Start querying the API:

```bash
node degov-client.js daos
node degov-client.js activity --hours 24 --limit 10
node degov-client.js brief ens
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
node degov-client.js wallet init
node degov-client.js wallet address
node degov-client.js wallet balance
node degov-client.js budget --usd 1
node degov-client.js daos
node degov-client.js activity --hours 48 --limit 10
node degov-client.js brief ens
node degov-client.js item proposal <id>
node degov-client.js freshness
node degov-client.js health
```

## Guardrails

- Do not ask users to paste private keys.
- Use the local managed wallet for API payments.
- If the wallet is unfunded, instruct the user to fund the displayed address on Base with USDC.
- State when information came from Degov Agent API versus the web.
- Do not fabricate governance activity, proposals, or dates.
