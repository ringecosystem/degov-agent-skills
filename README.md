# degov-agent-skills

Reusable agent skills for DeGov governance research and proposal security analysis.

This repository packages DAO governance skills so agents can answer governance questions with evidence instead of guesses and assess proposal security risks before users vote or execute. The skills are designed for external use: they explain when to use Degov Agent API data, when to fall back to web sources, how to ask for consent before paid API calls, and how to analyze governance proposals for malicious or unexpectedly risky actions.

## What is included

- `skills/dao-governance-research/SKILL.md`: the agent-facing governance research guide. It documents the Degov Agent API v2 surface (endpoint routing table, prerequisites, preflight, paid-call consent flow) and points to:
  - `skills/dao-governance-research/references/`: endpoint cards (`api-v2.md`), pricing, errors, x402 payment protocol, and MetaMask payment setup.
  - `skills/dao-governance-research/workflows/`: repeatable multi-step patterns (discovery, recent activity, explain proposal, proposal security review, evidence/citations, payment setup, troubleshooting).
- `skills/dao-governance-security/SKILL.md`: the proposal security-analysis rubric for evaluating executable actions, funds flow, permissions, proposer/process anomalies, uncertainty, and recommended user actions, plus synthetic example analyses in `skills/dao-governance-security/examples/`.
- `scripts/tests/`: repository-owned validation and smoke-test entry points used by CI and local checks.

There is no Degov CLI and no local wallet in this repository. Agents call the REST API directly using the endpoint cards, and paid calls are settled with x402 payments signed by the MetaMask agent wallet (see below).

## What the skills do

The `dao-governance-research` skill helps agents:

- discover covered DAOs through free v2 endpoints
- use Degov Agent API v2 as the primary evidence source when recent governance data matters
- use web search as a secondary source when API coverage is missing, stale, or too shallow
- ask the user before making paid x402 API calls
- turn API results into clear, source-aware explanations instead of raw JSON dumps

The `dao-governance-security` skill helps agents:

- decode and compare governance proposal actions against the proposal text
- check token/ETH amounts, recipients, allowances, upgrades, roles, ownership, and governance setting changes
- assess proposer identity, reputation, vote/process anomalies, execution and cross-chain risk
- classify findings with clear severity levels from Critical through Unknown
- produce a required final analysis format with evidence, assumptions, uncertainties, and concrete recommended user actions

## Degov Agent API model (v2)

The default API endpoint is:

```text
https://agent-api.degov.ai
```

All v2 endpoints return the uniform envelope `{ data, meta }` (RFC 3339 timestamps, decimal strings, opaque `proposalKey`/`topicKey` handles, revision-bound cursor pagination, readiness status).

Free endpoints (no payment):

- `GET /v2/meta/pricing`
- `GET /v2/meta/data-status`
- `GET /v2/daos`
- `GET /v2/daos/:daoId`

Standard endpoints (small x402 fee, currently $0.005 per call):

- `GET /v2/proposals`
- `GET /v2/proposals/resolve`
- `GET /v2/events`
- `GET /v2/signals`
- `GET /v2/forum-topics`

Plus endpoints (currently $0.01 per call):

- `GET /v2/daos/:daoId/timeline`
- `GET /v2/proposals/:proposalKey`
- `GET /v2/proposals/:proposalKey/votes/summary`
- `GET /v2/proposals/:proposalKey/votes`
- `GET /v2/proposals/:proposalKey/evidence`
- `GET /v2/forum-topics/:topicKey`
- `GET /v2/daos/:daoId/voters`
- `GET /v2/voters/:voterIdentity`
- `GET /v2/voters/:voterIdentity/votes`

The v1 endpoints (`/v1/activity`, `/v1/governance-events`, `/v1/daos/:daoId/brief`, `/v1/items/...`, `/v1/system/freshness`) are frozen and removed from this documentation; a v1 → v2 migration table lives in `skills/dao-governance-research/references/api-v2.md`.

## Payments

Paid calls use x402 payments on Base in USDC. Keys and signing live in the **MetaMask agent wallet**; this repository never manages private keys. Prerequisites for the paid path (one-time):

```bash
npm install -g @metamask/agent-wallet
npx skills add metaMask/agent-skills
```

The user signs in with `mm login`, initializes with `mm init`, and funds the wallet's Base address with USDC. The payment ceremony composes with the MetaMask agent-wallet skill's `x402_pay.py` (`inspect` → user confirmation → `pay`); degov's x402 offers are standard v2 (verified against staging) and payable by that script as-is. See `skills/dao-governance-research/references/x402.md` and `references/payment.md`.

Every paid call requires user consent first, and every payment requires confirmation of asset, amount, network, payTo, and resource URL. Users without a MetaMask account can still get web-only answers.

## Validation

Repository checks are exposed from the repository root (Python standard library plus prettier for Markdown):

```bash
pnpm install
pnpm run format:check
pnpm run validate:dao-governance-security
pnpm run test:x402-compat
pnpm run smoke:dao-governance-research
```

The offline smoke test validates the research skill frontmatter, references/workflows presence, absence of stale TypeScript files, the security-skill validator, and the x402 offer compatibility fixture. Live opt-ins:

```bash
pnpm run smoke:dao-governance-research:free    # free endpoints (health, data-status, daos)
pnpm run smoke:dao-governance-research:paid    # also asserts a live 402 offer is MetaMask-payable (zero cost)
```

Set `DEGOV_AGENT_API_BASE_URL` to point the live checks at a staging instance (for example `http://127.0.0.1:8310`).
