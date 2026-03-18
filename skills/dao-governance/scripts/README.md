# dao-governance scripts

TypeScript CLI helpers for querying `degov-agent-api` with automatic x402 payments.

## Quick start

```bash
cd skills/dao-governance/scripts
pnpm install
export DEGOV_AGENT_WALLET_PASSPHRASE="choose-a-strong-passphrase"
pnpm exec tsx degov-client.ts wallet init
pnpm exec tsx degov-client.ts wallet address
```

Fund the displayed Base address with USDC, then test:

```bash
pnpm exec tsx degov-client.ts wallet balance
pnpm exec tsx degov-client.ts daos
```

By default, the CLI targets the deployed API at `https://agent-api.degov.ai`.
Set `DEGOV_AGENT_API_BASE_URL` only when you want to use a local or alternate API.

## Free and paid APIs

Free:

- `GET /health`
- `GET /v1/meta/pricing`
- `GET /v1/daos`

Paid:

- `GET /v1/activity`
- `GET /v1/daos/:daoId/brief`
- `GET /v1/items/:kind/:externalId`
- `GET /v1/system/freshness`

## Wallet storage

The generated wallet is stored outside git:

- default: `~/.agents/state/dao-governance/wallet.json`
- override with `DEGOV_AGENT_WALLET_PATH`

New wallets are encrypted at rest. For non-interactive use, set:

- `DEGOV_AGENT_WALLET_PASSPHRASE`

## Budget guide

`budget --usd ...` fetches live pricing from `degov-agent-api`.
If the pricing metadata endpoint is unavailable, the CLI falls back to the current default pricing table.

## Commands

```bash
pnpm exec tsx degov-client.ts wallet init
pnpm exec tsx degov-client.ts wallet address
pnpm exec tsx degov-client.ts wallet balance
pnpm exec tsx degov-client.ts budget --usd 1
pnpm exec tsx degov-client.ts daos
pnpm exec tsx degov-client.ts activity --hours 24 --limit 10
pnpm exec tsx degov-client.ts brief ens
pnpm exec tsx degov-client.ts item proposal <id>
pnpm exec tsx degov-client.ts freshness
pnpm exec tsx degov-client.ts health
```

`health`, `budget`, and `daos` work without a funded wallet.
`activity`, `brief`, `item`, and `freshness` require the x402 wallet to be initialized and funded.
