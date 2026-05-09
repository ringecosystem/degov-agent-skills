# AGENTS.md

This repository is the external home for DeGov agent skills. Its main purpose is to package reusable agent knowledge for DAO governance research, with a focus on making answers evidence-based, source-aware, and safe around paid API access.

## Repository map

- `README.md`: short repository overview, current behavior summary, and local validation/install commands.
- `skills/dao-governance/SKILL.md`: the user-facing agent skill. It defines when to use DeGov governance data, how to choose between API and web sources, how to ask for paid-call consent, and how to write answers.
- `skills/dao-governance/API_COMPATIBILITY.md`: concise compatibility notes from the latest `degov-agent-api` main-branch alignment pass.
- `skills/dao-governance/scripts/README.md`: operator-facing notes for the bundled CLI helper.
- `skills/dao-governance/scripts/degov-client.ts`: TypeScript CLI for Degov Agent API access, including DAO discovery, budgets, activity, event-time governance events, briefs, item lookup, freshness, and health checks.
- `skills/dao-governance/scripts/wallet-store.ts`: local Base wallet storage, encryption, migration, passphrase handling, and USDC balance lookup.
- `scripts/smoke-test-dao-governance.sh`: repeatable local smoke tests. It defaults to deterministic local checks; live free, wallet, and paid checks are explicit opt-ins.
- `scripts/install-local-skill.sh`: installs `skills/dao-governance` into an isolated agents home or backs up and updates the real `~/.agents` copy.
- `.github/workflows/ci.yml`: repository CI for documentation/script formatting, shell syntax, TypeScript compilation, and CLI startup.

## Core purpose

The `dao-governance` skill helps agents answer Web3 DAO governance questions without inventing facts. It treats `degov-agent-api` as the primary evidence source for supported DAO data, then uses web search as a secondary layer when API data is missing, stale, too shallow, or needs source verification.

The intended user experience is not a raw API dump. Agents should turn governance data into clear explanations that identify what happened, why it matters, which DAO it affects, and what sources support the answer.

## Degov Agent API model

The CLI defaults to the production API:

```text
https://agent-api.degov.ai
```

The skill distinguishes between free discovery endpoints and paid research endpoints.

Free endpoints:

- `GET /health`
- `GET /v1/meta/pricing`
- `GET /v1/daos`

Paid endpoints:

- `GET /v1/activity`
- `GET /v1/governance-events`
- `GET /v1/daos/:daoId/brief`
- `GET /v1/items/:kind/:externalId`
- `GET /v1/system/freshness`

`/v1/governance-events` is the event-time feed used by Realtime Signal-style workflows. It requires `start_ms` and `end_ms`, with optional `dao_id`, `limit`, and `event_types` filters. Use it when timing semantics matter more than a generic last-updated activity feed.

Use free endpoints when they are enough. Use paid endpoints only after the user explicitly chooses the Degov Agent API path.

The backend also supports an internal-token paid API bypass for trusted first-party runtime services. That mechanism is intentionally not part of the public external skill path and must not be documented as something ordinary agents or users should configure.

## CLI capabilities

`degov-client.ts` provides these capability groups:

- Wallet management: initialize a dedicated local wallet, show its address, and check Base USDC balance.
- Budget guidance: fetch live pricing and estimate how many API calls a given USDC budget can cover.
- DAO discovery: list covered DAOs without requiring payment.
- Governance research: fetch recent activity, event-time governance events, DAO briefs, specific proposal/forum items, and system freshness.
- Health checks: confirm the configured API is reachable.

The CLI is a helper for agents and operators. It should not replace the answer-writing guidance in `SKILL.md`.

## Wallet and runtime state

Paid API calls use x402 payments on Base with USDC. The repository must never contain wallet secrets or runtime payment state.

Default local state locations are outside git:

- Wallet file: `~/.agents/state/dao-governance/wallet.json`
- Wallet passphrase file: `~/.agents/state/dao-governance/wallet-passphrase`

Environment overrides:

- `DEGOV_AGENT_API_BASE_URL`: alternate API base URL.
- `DEGOV_AGENT_WALLET_PATH`: alternate wallet file path.
- `DEGOV_AGENT_WALLET_PASSPHRASE`: explicit passphrase for non-interactive use.
- `DEGOV_AGENT_WALLET_PASSPHRASE_PATH`: alternate passphrase file path.

Keep local-only agent state, runtime files, passphrases, `.env` files, logs, generated wallets, `node_modules`, and `.hermes/` out of version control.

## Paid-call consent rules

Before any paid endpoint is used, the agent should present the user with a simple choice:

1. Use Degov Agent API
2. Use web search only

If the user chooses the API path, the agent can initialize or reuse the local wallet and explain how to fund the displayed Base address with USDC if the balance is insufficient.

If the user declines paid API use, continue with web search and clearly state that the answer is based on web sources instead of Degov Agent API data.

Do not repeatedly push wallet setup after the user declines.

## Answering DAO governance questions

The skill should encourage a short planning step before answering:

- Identify the likely DAO or DAO family.
- Decide whether the user wants discovery, recent activity, event-time governance events, a DAO brief, or one specific item explanation.
- Decide whether free API data is enough before considering paid endpoints.
- Use linked source URLs or web follow-up when API output needs verification or context.

Good answers should be plain-language, source-aware, and detailed enough to be useful. Avoid raw JSON, vague claims, and long undifferentiated bullet lists.

## Documentation conventions

When API behavior, CLI commands, wallet behavior, paid-call rules, or testing/install flows change, keep the related documentation synchronized:

- Root `README.md`
- `skills/dao-governance/SKILL.md`
- `skills/dao-governance/scripts/README.md`
- This `AGENTS.md` file when the shared repository knowledge changes

Prefer durable repository knowledge here. Avoid personal workflow instructions, branch conventions, review preferences, or developer-specific process notes.

## Local validation conventions

Use the root smoke-test wrapper for repeatable checks:

```bash
scripts/smoke-test-dao-governance.sh --offline
scripts/smoke-test-dao-governance.sh --free-api
scripts/smoke-test-dao-governance.sh --free-api --wallet
```

Paid checks are opt-in:

```bash
scripts/smoke-test-dao-governance.sh --paid
```

Use `scripts/install-local-skill.sh` to test skill installation in an isolated target before updating the real `~/.agents` copy.

## Security guardrails

- Never ask users to paste private keys.
- Never commit wallet files, passphrases, API tokens, `.env` files, generated runtime state, or copied local skill caches.
- Do not hardcode paid API pricing in long-lived docs when live pricing is available.
- Keep payment wallets dedicated to small API fees only; do not encourage transferring large balances.
- Treat API data as evidence, not as final prose. The agent remains responsible for explaining context and uncertainty clearly.
