# dao-governance scripts

CLI helpers for querying `degov-agent-api` with automatic x402 payments.

## Quick start

```bash
cd skills/dao-governance/scripts
pnpm install
node degov-client.js wallet init
node degov-client.js wallet address
```

Fund the displayed Base address with USDC, then test:

```bash
export DEGOV_AGENT_API_BASE_URL=http://127.0.0.1:3311
node degov-client.js wallet balance
node degov-client.js daos
```

## Wallet storage

The generated wallet is stored outside git:
- default: `~/.codex/memories/degov-agent-skills/dao-governance-wallet.json`
- override with `DEGOV_AGENT_WALLET_PATH`

## Budget guide

Per 1 USDC:
- `daos`: about 200 requests
- `activity`: about 200 requests
- `freshness`: about 200 requests
- `brief`: about 50 requests
- `item`: about 50 requests
