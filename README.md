# degov-agent-skills

External home for Degov agent skills.

## Repository layout

- `skills/dao-governance/`: DAO governance research skill backed by `degov-agent-api`
- `skills/dao-governance/scripts/`: TypeScript CLI for wallet management and paid API calls

## Current skill behavior

The `dao-governance` skill:
- uses `degov-agent-api` as the primary evidence source
- pays for `/v1/*` requests with x402 on Base mainnet USDC
- creates a dedicated local wallet instead of asking users for a raw private key
- stores that wallet outside git at `~/.agents/state/dao-governance/wallet.json`

## Development setup

```bash
cd skills/dao-governance/scripts
pnpm install
export DEGOV_AGENT_WALLET_PASSPHRASE="choose-a-strong-passphrase"
pnpm exec tsx degov-client.ts wallet init
pnpm exec tsx degov-client.ts wallet address
```

Then fund the displayed Base address with USDC and call the API:

```bash
export DEGOV_AGENT_API_BASE_URL="http://127.0.0.1:3310"
pnpm exec tsx degov-client.ts wallet balance
pnpm exec tsx degov-client.ts daos
```

## Installed skill path

During local development, the latest skill should also be synced into:

```bash
~/.agents/skills/dao-governance
```

See:
- `skills/dao-governance/SKILL.md`
- `skills/dao-governance/scripts/README.md`
