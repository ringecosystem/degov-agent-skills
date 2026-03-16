---
name: dao-governance
description: Use when users ask DAO research questions. Answer with Degov Agent API data first, then use web search when API coverage is insufficient.
---

# DAO Governance Skill

Use this skill to answer DAO governance questions with Degov Agent API data first, then fall back to web search only when API coverage is insufficient.

## Setup

Default managed wallet path:
- `~/.agents/state/dao-governance/wallet.json`

Initialize the local wallet:

```bash
cd skills/dao-governance/scripts
pnpm install
export DEGOV_AGENT_WALLET_PASSPHRASE="choose-a-strong-passphrase"
pnpm exec tsx degov-client.ts wallet init
pnpm exec tsx degov-client.ts wallet address
```

Then fund that Base address with USDC.

Optional API override:

```bash
export DEGOV_AGENT_API_BASE_URL="http://127.0.0.1:3310"
```

## Research workflow

1. Use `health` if you need to confirm the backend is up.
2. Use `daos` to discover DAO coverage.
3. Use `activity` for recent multi-DAO governance activity.
4. Use `brief <dao-id>` for compact DAO context.
5. Use `item <proposal|forum_topic> <external-id>` only when you need item-level detail.
6. Use web search only when the API is stale, incomplete, or unavailable.

## Commands

```bash
pnpm exec tsx degov-client.ts wallet init
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
