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
export DEGOV_AGENT_API_BASE_URL=http://127.0.0.1:3311
pnpm exec tsx degov-client.ts wallet balance
pnpm exec tsx degov-client.ts daos
```

## Wallet storage

The generated wallet is stored outside git:
- default: `~/.agents/state/dao-governance/wallet.json`
- override with `DEGOV_AGENT_WALLET_PATH`

New wallets are encrypted at rest. For non-interactive use, set:
- `DEGOV_AGENT_WALLET_PASSPHRASE`

<<<<<<< HEAD
The CLI still discovers the legacy `.codex` wallet path from earlier testing. To move it into the new managed location and encrypt it:

```bash
pnpm exec tsx degov-client.ts wallet migrate
```

=======
>>>>>>> f76e1bf (refactor: move dao governance client to typescript)
## Budget guide

Per 1 USDC:
- `daos`: about 200 requests
- `activity`: about 200 requests
- `freshness`: about 200 requests
- `brief`: about 50 requests
- `item`: about 50 requests

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
