# AGENTS.md

This repository is the external home for DeGov agent skills. Its main purpose is to package reusable agent knowledge for DAO governance research and proposal security analysis, with a focus on making answers evidence-based, source-aware, risk-aware, and safe around paid API access.

## Repository map

- `README.md`: public repository overview, usage summary, and safety guidance.
- `skills/dao-governance-research/SKILL.md`: the user-facing governance research skill. It defines when to use DeGov governance data, how to choose between API and web sources, how to ask for paid-call consent, and how to write answers. It routes to `references/` (endpoint cards, pricing, errors, x402 protocol, payment setup) and `workflows/` (repeated multi-step patterns).
- `skills/dao-governance-research/references/`: endpoint contract cards for the v2 API, pricing/budget guidance, error handling, the x402 payment protocol, and MetaMask agent wallet payment setup.
- `skills/dao-governance-research/workflows/`: repeatable user journeys (discovery, recent activity, explain proposal, proposal security review, evidence/citations, payment setup, troubleshooting).
- `skills/dao-governance-security/SKILL.md`: the user-facing proposal security skill. It defines a concrete rubric for checking malicious or unexpected proposal actions, funds flow, permissions, proposer/process anomalies, execution risk, uncertainty, and final analysis format.
- `skills/dao-governance-security/examples/`: synthetic benign and risky proposal analyses used for reviewer inspection and local validation.
- `scripts/tests/validate-dao-governance-security.py`: deterministic stdlib validator for the security skill frontmatter, required output template, and example structured analyses.
- `scripts/tests/test_x402_compat.py`: deterministic fixture test locking the Degov API x402 offer contract against the MetaMask agent-wallet payment script requirements.
- `scripts/tests/smoke-test-dao-governance-research.py`: repeatable repository-level smoke tests. It defaults to deterministic local checks; live free and zero-cost paid-offer checks are explicit opt-ins.
- `.github/workflows/ci.yml`: repository CI for Markdown formatting, Python validation helpers, and the smoke tests.

## Core purpose

The `dao-governance-research` skill helps agents answer Web3 DAO governance questions without inventing facts. It documents the Degov Agent API (v2) as the primary evidence source for supported DAO data, then uses web search as a secondary layer when API data is missing, stale, too shallow, or needs source verification. The skill ships no CLI and no local wallet: agents assemble HTTP calls directly from the endpoint cards, and paid calls are settled with x402 payments signed by the MetaMask agent wallet (`mm`), composing with the MetaMask agent-wallet skill for the payment ceremony.

The `dao-governance-security` skill helps agents evaluate whether a specific governance proposal is malicious, unexpectedly risky, or safe enough to support from a security perspective. It focuses on executable actions, token/native-asset movement, contract calls, permissions, proposer reputation, process anomalies, execution risk, uncertainty, and user-facing recommendations.

The intended user experience is not a raw API dump or a vague risk label. Agents should turn governance data into clear explanations that identify what happened, why it matters, which DAO it affects, what risks were found, what sources support the answer, and what the user should do next.

## Degov Agent API model (v2)

The default API endpoint is `https://agent-api.degov.ai`.

All v2 endpoints return the uniform envelope `{ data, meta }`. `meta` carries `requestId`, `generatedAt`, `dataAsOf`, `readiness` (`ready|backfilling|stale|unavailable`), and `page` (`limit`, `hasMore`, `nextCursor`) on list endpoints. Errors return `{ error: { code, message, details? }, meta }` with stable codes (`VALIDATION_ERROR` 400, `PAYMENT_REQUIRED` 402, `CURSOR_INVALID` 400, `CURSOR_STALE` 409, `NOT_FOUND` 404, `RATE_LIMITED`/`QUOTA_EXCEEDED` 429, ...).

Free endpoints:

- `GET /v2/meta/pricing`
- `GET /v2/meta/data-status`
- `GET /v2/daos`
- `GET /v2/daos/:daoId`

Standard endpoints (paid, currently $0.005):

- `GET /v2/proposals`
- `GET /v2/proposals/resolve`
- `GET /v2/events`
- `GET /v2/signals`
- `GET /v2/forum-topics`

Plus endpoints (paid, currently $0.01):

- `GET /v2/daos/:daoId/timeline`
- `GET /v2/proposals/:proposalKey`
- `GET /v2/proposals/:proposalKey/votes/summary`
- `GET /v2/proposals/:proposalKey/votes`
- `GET /v2/proposals/:proposalKey/evidence`
- `GET /v2/forum-topics/:topicKey`
- `GET /v2/daos/:daoId/voters`
- `GET /v2/voters/:voterIdentity`
- `GET /v2/voters/:voterIdentity/votes`

Key contract points:

- `proposalKey` / `topicKey` are opaque server-generated handles returned by lists, resolve, events, and signals. Clients never construct or parse them; follow-up endpoints accept only the key.
- `resolve` is an external-reference boundary (URL/title/external id → key) and is optional when a list already returned a key.
- Evidence (`proposals/:proposalKey/evidence`) is an optional research/audit bundle (provenance, citations, quality flags, limitations) — not part of ordinary proposal answers.
- Cursors are bound to endpoint, filter hash, and serving revision; a `CURSOR_STALE` (409) means re-run the list without a cursor.
- Numeric amounts are decimal strings; timestamps are RFC 3339.
- v1 endpoints are frozen and not documented here. `references/api-v2.md` has the v1 → v2 migration table.

## Payment model (MetaMask agent wallet)

Paid endpoints respond `402` with a `PAYMENT-REQUIRED` header (x402 v2, exact scheme, EIP-3009, USDC on Base `eip155:8453`) until paid. Keys and signing live in the MetaMask agent wallet; the repository never stores wallet secrets. The paid path requires, as documented prerequisites:

- `mm` CLI: `npm install -g @metamask/agent-wallet` (version pinned as `mmCliVersion` in the research skill frontmatter)
- MetaMask agent-wallet skill: `npx skills add metaMask/agent-skills`
- A signed-in, initialized wallet (`mm login`, `mm init`) with Base USDC

The payment ceremony composes with the MetaMask skill's `x402_pay.py` (`inspect` → user confirmation → `pay`). Degov's x402 offers are standard v2 and payable by that script as-is (verified against staging; the `test_x402_compat.py` fixture locks the offer contract in CI).

## Paid-call consent rules

Before any paid endpoint is used, the agent should present the user with a simple choice:

1. Use Degov Agent API
2. Use web search only

If the user chooses the API path, ensure the payment prerequisites are met (mm CLI, MetaMask skill, Base USDC) and continue. Every payment requires confirmation of asset, amount, network, `payTo`, and resource URL before signing; one payment attempt per resource, never auto-retry a payment. If the user declines paid API use, continue with web search and clearly state that the answer is based on web sources instead of Degov Agent API data. Do not repeatedly push wallet setup after the user declines.

## Answering DAO governance questions

The skill should encourage a short planning step before answering:

- Identify the likely DAO or DAO family.
- Decide whether the user wants discovery, recent activity, event-time events, a DAO summary, or one specific item explanation.
- Decide whether free API data is enough before considering paid endpoints.
- Use linked source URLs or web follow-up when API output needs verification or context.

Good answers should be plain-language, source-aware, and detailed enough to be useful. Avoid raw JSON, vague claims, and long undifferentiated bullet lists.

## Documentation conventions

When public API behavior, payment behavior, or paid-call rules change, keep the related documentation synchronized:

- Root `README.md`
- `skills/dao-governance-research/SKILL.md`
- `skills/dao-governance-research/references/` (endpoint cards, pricing, errors, x402, payment)
- `skills/dao-governance-research/workflows/` (user journeys)
- `skills/dao-governance-security/SKILL.md` when security-analysis behavior, severity definitions, or output expectations change
- This `AGENTS.md` file when the shared repository knowledge changes
- `scripts/tests/` when the offline contract checks change (frontmatter expectations, x402 fixture, smoke coverage)

Prefer durable repository knowledge here. Avoid personal workflow instructions, branch conventions, review preferences, or developer-specific process notes.

## Security guardrails

- Never ask users to paste private keys. Keys and signing live in the MetaMask agent wallet.
- Never commit wallet files, passphrases, API tokens, `.env` files, generated runtime state, or copied local skill caches.
- Do not hardcode paid API pricing in long-lived docs when live pricing is available (`/v2/meta/pricing` is the source of truth).
- Every x402 payment requires user confirmation of asset, amount, network, `payTo`, and resource URL; one payment attempt per resource, never auto-retry.
- Keep payment wallets funded with small amounts only; do not encourage transferring large balances.
- Treat API data as evidence, not as final prose. The agent remains responsible for explaining context and uncertainty clearly.
- Keep this repository focused on the external skill contract; do not document private service-side implementation paths.
