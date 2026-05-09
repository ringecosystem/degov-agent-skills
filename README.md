# degov-agent-skills

Reusable agent skills for DeGov governance research.

This repository packages the `dao-governance` skill and its helper CLI so agents can answer DAO governance questions with evidence instead of guesses. The skill is designed for external use: it explains when to use Degov Agent API data, when to fall back to web sources, and how to ask for consent before paid API calls.

## What is included

- `skills/dao-governance/SKILL.md`: the agent-facing governance research guide.
- `skills/dao-governance/scripts/`: a TypeScript helper CLI for Degov Agent API calls and payment-wallet management.

## What the skill does

The `dao-governance` skill helps agents:

- discover covered DAOs through free public endpoints
- use Degov Agent API as the primary evidence source when recent governance data matters
- use web search as a secondary source when API coverage is missing, stale, or too shallow
- ask the user before making paid x402 API calls
- turn API results into clear, source-aware explanations instead of raw JSON dumps

The default API endpoint is:

```text
https://agent-api.degov.ai
```

## Public API model

Free endpoints are available for basic discovery:

- `GET /health`
- `GET /v1/meta/pricing`
- `GET /v1/daos`

Paid research endpoints use x402 payments on Base USDC and should only be called after user consent:

- `GET /v1/activity`
- `GET /v1/governance-events`
- `GET /v1/daos/:daoId/brief`
- `GET /v1/items/:kind/:externalId`
- `GET /v1/system/freshness`

## Wallet safety

The helper CLI creates a dedicated local wallet for small API payments. It does not ask users to paste private keys into chat.

Default local wallet state is stored outside the repository:

```text
~/.agents/state/dao-governance/wallet.json
```

Keep wallet files, passphrases, `.env` files, logs, generated state, and other secrets out of version control.

## Using the CLI helper

From the helper directory:

```bash
cd skills/dao-governance/scripts
pnpm install
pnpm exec tsx degov-client.ts help
```

Common commands:

```bash
pnpm exec tsx degov-client.ts daos
pnpm exec tsx degov-client.ts budget --usd 1
pnpm exec tsx degov-client.ts wallet init
pnpm exec tsx degov-client.ts wallet address
pnpm exec tsx degov-client.ts wallet balance
pnpm exec tsx degov-client.ts transfer <to-address> <amount-usdc>
pnpm exec tsx degov-client.ts activity --hours 24 --limit 10
pnpm exec tsx degov-client.ts governance-events --hours 24 --limit 200
pnpm exec tsx degov-client.ts brief ens
pnpm exec tsx degov-client.ts item proposal <id>
pnpm exec tsx degov-client.ts freshness
pnpm exec tsx degov-client.ts health
```
