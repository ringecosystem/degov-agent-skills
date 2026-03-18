# degov-agent-skills

External home for Degov agent skills.

## Repository layout

- `skills/dao-governance/`: DAO governance research skill backed by `degov-agent-api`
- `skills/dao-governance/scripts/`: TypeScript CLI for wallet management and paid API calls

## Current skill behavior

The `dao-governance` skill:

- uses `degov-agent-api` as the primary evidence source
- defaults to the deployed API at `https://agent-api.degov.ai`
- pays for `/v1/*` requests with x402 on Base mainnet USDC
- creates a dedicated local wallet instead of asking users for a raw private key
- stores that wallet outside git at `~/.agents/state/dao-governance/wallet.json`
- manages an internal local wallet passphrase automatically unless an explicit env override is provided
- shows budget-based USDC top-up suggestions when displaying the wallet address for funding
- asks the user before using a paid endpoint, recommends the API-backed path as more accurate, and falls back to web search if the user declines
