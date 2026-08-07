# Payment setup — MetaMask agent wallet

The paid path uses the **MetaMask agent wallet** (`mm` CLI) as the only payment backend. Local key
management is gone: keys and signing stay in the MetaMask wallet; this skill only documents the
composition. The MetaMask agent-wallet skill is the canonical `mm` reference — load it
(`npx skills add metaMask/agent-skills`) and follow its onboarding/login workflows for anything not
covered here.

## Install (one-time)

```bash
npm install -g @metamask/agent-wallet
npx skills add metaMask/agent-skills
```

Check the version: `mm --version` should report `@metamask/agent-wallet/<version>`; this skill is
pinned to `mmCliVersion` in its frontmatter (warn the user once on mismatch).

## Account setup

- `mm login` — sign in with MetaMask Mobile (QR) or browser (Google/Email). The user needs a
  MetaMask account.
- `mm init` — select a wallet mode (`server-wallet` or `byok`) and, for server-wallet, a trading
  mode (`guard` or `beast`).
- `mm doctor` — readiness gate: both `authenticated: true` and `initialized: true` before any paid
  call.

Never type passwords or mnemonics into chat or inline flags; use the `MM_PASSWORD` / `MM_MNEMONIC`
environment variables instead (see the MetaMask skill's credential rules).

## Funding and balances

- The API settles in USDC on **Base** (chain id `8453`). Fund the mm wallet's Base address with
  USDC.
- Balance: `mm wallet balance --chain-ids 8453`
- Add funds: `mm wallet add-fund` (shows a QR code and the address).
- Withdraw unused USDC: `mm transfer <to-address> <amount> --chain-id 8453` — confirm recipient and
  amount with the user first.

## Spending policy and automation

- `guard` mode may require manual approval (and possibly MFA) for signing; x402 authorization
  windows are short (`maxTimeoutSeconds` in the offer), so slow approvals can expire. For
  automated/agent-driven flows prefer `beast` mode or BYOK with `MM_PASSWORD` set, per the MetaMask
  skill's guidance.
- Policy changes (guard → beast) can require MFA; tightening (beast → guard) applies immediately.

## Per-call cost control

- Check `/v2/meta/pricing` (free) before spending; every paid call costs $0.005 (standard) or $0.01
  (plus) unless pricing changes.
- A `402` response costs nothing — only settling pays.

## Troubleshooting quick map

| Symptom                                                              | Fix                                                                                                                            |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `mm` commands return `AUTH_FAILED` / "No CLI refresh token"          | `mm login`                                                                                                                     |
| `NOT_INITIALIZED` "Project not initialized"                          | `mm init`                                                                                                                      |
| Balance shows 0 on Base                                              | Fund the Base address (`mm wallet add-fund`), USDC on chain 8453                                                               |
| `402` after payment                                                  | Verify the settlement header; do not pay twice — see [x402.md](x402.md) and [errors.md](errors.md)                             |
| Offer rejected by `x402_pay.py` (domain/network/assetTransferMethod) | Report it; degov offers are standard x402 v2 (verified 2026-08) — rejection usually means a changed API or stale skill version |
