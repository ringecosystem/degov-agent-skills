# Workflow: first-time payment setup

Goal: get a new environment ready for paid Degov API calls (one-time). The user performs the MetaMask account steps; the agent prepares everything else.

## Prerequisites check

```bash
mm --version                      # @metamask/agent-wallet/<version>; compare to SKILL.md mmCliVersion
mm doctor                         # authenticated: true, initialized: true
mm chains list --json             # chain id 8453 (Base) present
```

## Steps

1. **Install** (agent can do this):

```bash
npm install -g @metamask/agent-wallet
npx skills add metaMask/agent-skills
```

2. **Account setup (user-operated)** — the agent stops here and hands over:

```bash
mm login      # MetaMask Mobile QR or browser
mm init       # wallet mode (server-wallet | byok) + trading mode (guard | beast)
```

Never ask the user to paste a private key or mnemonic into chat; use `MM_PASSWORD`/`MM_MNEMONIC` env vars if BYOK.

3. **Fund Base USDC** (user action): `mm wallet add-fund` → send USDC to the displayed Base address (chain 8453). Small test amounts are enough.

4. **Verify**:

```bash
mm wallet balance --chain-ids 8453
curl -s https://agent-api.degov.ai/v2/meta/pricing      # confirm live prices
```

5. **First paid call** (agent): follow the payment ceremony in SKILL.md — `x402_pay.py inspect` → show the user asset/amount/network/payTo → confirm → `pay`. Verify the settlement transaction hash and that the resource body came back.

## Notes

- A `402` response itself costs nothing; only settling pays.
- If the user has no MetaMask account or declines, use the web-only path and say the answer may be less accurate.
- For agent-driven automation, prefer `beast` trading mode or BYOK so x402 signing does not stall on manual approvals (short authorization windows).
