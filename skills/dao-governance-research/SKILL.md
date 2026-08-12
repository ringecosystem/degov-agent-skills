---
name: dao-governance-research
description:
  Load this skill when users ask about Web3 DAO governance. Route covered, structured governance
  research to the Degov Agent API (v2), and use official web sources for conceptual questions,
  primary-source verification, or gaps in API coverage. Paid endpoints use x402 payments signed by
  the MetaMask agent wallet (mm).
metadata:
  version: 1.0.0
---

# DAO Governance Research Skill

## When to use this skill

Use this skill when the user is asking about Web3 DAO governance and the answer depends on accurate,
recent governance information. The main goal is to avoid hallucinating DAO activity, proposal
details, or governance timelines. Use the Degov Agent API (v2) for covered, structured governance
data. Use official web sources when the question is conceptual, the API does not cover it, or
primary-source verification is more useful. The goal is reliable evidence, not forcing every
governance question through the API.

Invoke this skill for questions such as:

- "What has ENS been doing lately?"
- "What are the biggest DAO governance stories this week?"
- "Can you explain this ENS proposal?"
- "What's the Uniswap governance mechanism?"
- "How do I participate in Arbitrum governance?"

The Degov Agent API is a plain REST API. This skill documents its surface (endpoints, parameters,
envelopes, errors) and how to pay for paid endpoints with x402 via the MetaMask agent wallet. There
is no Degov CLI: assemble HTTP calls directly from the endpoint cards in
[api-v2.md](references/api-v2.md).

## Prerequisites

| Path                                                                       | Requirements                                                        | Install                                                                                                                             |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Free endpoints (`meta/pricing`, `meta/data-status`, `daos`, `daos/:daoId`) | None                                                                | —                                                                                                                                   |
| Paid endpoints (standard/plus tiers)                                       | `mm` CLI + MetaMask agent-wallet skill + Base USDC in the mm wallet | `npm install -g @metamask/agent-wallet` and `npx skills add metaMask/agent-skills` (details in [payment.md](references/payment.md)) |
| Web-only fallback                                                          | None                                                                | —                                                                                                                                   |

Paid calls require a MetaMask agent wallet account because x402 payment authorizations are signed by
`mm`. The MetaMask skill is the canonical documentation for `mm` and includes the `x402_pay.py`
payment ceremony script; this skill composes with it instead of re-implementing payments. If the
user has no MetaMask account or declines the paid path, use web search only (see the consent flow
below).

Default API endpoint: `https://agent-api.degov.ai`. For development against an alternate deployment,
use any base URL override the agent environment supports (for example
`DEGOV_AGENT_API_BASE_URL=http://127.0.0.1:8310` for a local staging instance).

## Preflight (when relevant)

Do not run a fixed preflight for every question. Check only what the selected path needs:

1. **Coverage/freshness** — use `GET /v2/meta/data-status` when recency or completeness matters.
   Treat `backfilling`/`stale` as a limitation to disclose, not an automatic failure. Use
   `GET /health` only to diagnose connectivity or service errors.
2. **Paid-path readiness** — after the user chooses a paid API path, run `mm doctor` and require
   both `authenticated: true` and `initialized: true`; confirm Base is supported with
   `mm chains list --json` (look for chain id `8453`). If `mm doctor` fails, follow the MetaMask
   skill's login/onboarding workflows, or fall back to web-only.

## Endpoint routing

Match the user's intent to an endpoint, then read the endpoint card in
[api-v2.md](references/api-v2.md) before constructing the request (live prices:
[pricing.md](references/pricing.md)). All requests return the v2 envelope `{ data, meta }`; errors
return `{ error: { code, message }, meta }` (see [errors.md](references/errors.md)). Paid endpoints
return `402` with a `PAYMENT-REQUIRED` header until paid (see [x402.md](references/x402.md) and the
payment ceremony below).

| User intent                                                      | Endpoint(s)                                                                                             | Tier            |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | --------------- |
| Is the API healthy / how fresh is the data                       | `GET /v2/meta/data-status`                                                                              | free            |
| Live pricing and per-endpoint prices                             | `GET /v2/meta/pricing`                                                                                  | free            |
| Which DAOs are covered                                           | `GET /v2/daos` (filters: `hasVoteData`, `hasForumData`, `coverageStatus`)                               | free            |
| DAO summary / proposal counts / participation                    | `GET /v2/daos/:daoId`                                                                                   | free            |
| What a DAO has been doing (recent proposals, by time window)     | `GET /v2/proposals` (`daoId`, `timeField`, `from`, `to`, `sort`)                                        | standard        |
| What happened in governance this week / today                    | `GET /v2/events` (`from`+`to` required, `eventTypes`) or `GET /v2/signals` (`from`+`to`, `signalTypes`) | standard        |
| Explain a specific proposal (by URL/title/external id)           | `GET /v2/proposals/resolve` → `GET /v2/proposals/:proposalKey`                                          | standard → plus |
| Proposal vote totals / per-vote rows                             | `GET /v2/proposals/:proposalKey/votes/summary` / `.../votes`                                            | plus            |
| Citation/audit bundle for a proposal (provenance, quality flags) | `GET /v2/proposals/:proposalKey/evidence`                                                               | plus            |
| Recent forum discussion                                          | `GET /v2/forum-topics` (`daoId`, `governanceRelated`, `sort`) → `GET /v2/forum-topics/:topicKey`        | standard → plus |
| DAO activity trend over months                                   | `GET /v2/daos/:daoId/timeline` (`metric`, `fromMonth`, `toMonth`)                                       | plus            |
| Top voters / a voter's profile and vote history                  | `GET /v2/daos/:daoId/voters` → `GET /v2/voters/:voterIdentity` → `GET /v2/voters/:voterIdentity/votes`  | plus            |

Multi-step user journeys live in `workflows/` — [discovery.md](workflows/discovery.md) (DAO
discovery), [recent-activity.md](workflows/recent-activity.md) (what happened this week),
[explain-proposal.md](workflows/explain-proposal.md) (explain a specific proposal),
[proposal-security.md](workflows/proposal-security.md) (security review data fetch, bridging to the
`dao-governance-security` skill), [evidence.md](workflows/evidence.md) (citation/audit bundles),
[payment-setup.md](workflows/payment-setup.md) (first-time payment onboarding),
[troubleshooting.md](workflows/troubleshooting.md) (failure decision tree). Load the matching
workflow when the request is a pattern rather than a single endpoint.

## Paid-call consent flow

Before entering a paid API workflow, ask whether the user wants that path. Keep the choice short and
include the estimated total cost from `/v2/meta/pricing` when the query plan is known:

> This request needs paid DeGov API data. It uses x402 fees in USDC on Base, signed by your MetaMask
> agent wallet. The planned calls are estimated to cost <amount from `/v2/meta/pricing`>.
>
> Choose one:
>
> 1. Use Degov Agent API
> 2. Use web search only

- If the user chooses `1`: ensure the paid-path prerequisites (mm CLI, MetaMask skill, Base USDC)
  are met, then continue with the API-backed workflow.
- If the user chooses `2`: continue with web search and say clearly that the answer uses web sources
  instead of the Degov Agent API.
- If the user has already agreed earlier in the conversation and the wallet is ready, do not repeat
  the full explanation for every follow-up question.
- New calls beyond the agreed query plan require a new cost estimate and consent; calls already
  covered by the agreed plan do not require repeating the two-option prompt.
- Do not repeatedly push wallet setup after the user declines.

## Payment ceremony (x402 via MetaMask agent wallet)

Paid endpoints respond `402 Payment Required` with a base64 `PAYMENT-REQUIRED` header (x402 v2) and
a JSON body containing the payment requirement. The degov offers are standard x402 v2:
`scheme: exact`, network `eip155:8453`, USDC on Base, EIP-3009 (`assetTransferMethod: eip3009`),
with the EIP-712 domain name/version included in `extra`.

To pay, compose with the MetaMask agent-wallet skill (its [x402.md](references/x402.md) and
`scripts/x402_pay.py`):

1. Load the metamask-agent-wallet skill and locate its `x402_pay.py` script.
2. `python3 <skill-dir>/scripts/x402_pay.py inspect <paid-url>` — prints the payment requirement(s)
   as JSON (asset, amount, network, `payTo`, resource). Verify it matches the approved plan. Show it
   to the user when it differs from the estimate or when the user asks to inspect it.
3. After the paid path and cost are approved, run
   `python3 <skill-dir>/scripts/x402_pay.py pay <paid-url> --confirm` — signs an EIP-3009
   authorization with `mm wallet sign-typed-data`, retries with the `PAYMENT-SIGNATURE` header, and
   prints the settlement (transaction hash) plus the resource body.
4. Verify the settlement appears in the response headers (`PAYMENT-RESPONSE`) and the data is
   usable; report the tx hash with a Base explorer link when relevant.

Rules: one payment attempt per resource, never auto-retry a payment, never pay outside the user's
approved query plan and cost, and do not re-pay a resource that already settled. If `x402_pay.py` is
unavailable or the MetaMask skill is not installed, do not improvise a payment — use web-only mode
or ask the user to install the MetaMask skill first.

## Standard workflow for answering questions

### Query planning for vague questions

For broad or fuzzy questions, first decide:

- which DAO or DAO family the user is probably asking about (use `GET /v2/daos` when a short name is
  ambiguous; some production DAO ids include suffixes, for example ENS is `ens-dao`, not `ens`);
- whether the user wants discovery, recent activity, event-time events, a DAO summary, or one
  specific item;
- what time range is implied;
- whether free endpoints can answer enough before you move to paid endpoints.

Examples:

- "What has Spark been doing lately?" → `GET /v2/proposals?daoId=spark&sort=updatedDesc`, maybe
  `GET /v2/daos/spark`, then `GET /v2/events?daoId=spark&from=...&to=...` for timing.
- "What are the biggest DAO governance stories this week?" →
  `GET /v2/events?from=<168h ago>&to=<now>&limit=200` when event timing matters, or
  `GET /v2/signals?from=...&to=...&limit=100` for curated signals; then
  `GET /v2/proposals/:proposalKey` for the most important ones.
- "Can you explain this ENS proposal?" → `GET /v2/proposals/resolve?url=<link>` (or `?title=` /
  `?externalId=`) to get a `proposalKey`, then `GET /v2/proposals/:proposalKey` and optionally
  `.../votes/summary`.

### Endpoint selection rules

Use the API intentionally:

- `daos` / `daos/:daoId`: discovery and DAO context (free).
- `proposals`: recent proposals with filters; use `sort=endingSoon` for deadlines,
  `lifecycleStatus=active` for open proposals, `timeField`+`from`+`to` for time windows.
- `events`: event-time feed for a specific window — proposal created/voting started/ended/ending
  soon/executed, forum discussion active. Prefer it for "what happened today/this week" and
  deadline-sensitive questions. `from` and `to` are required.
- `signals`: curated governance signals (proposal result, deadline reminders, governance radar) with
  `priorityMin`/`surface` filters; use for "biggest stories" and watch-style questions.
- `proposals/resolve`: only when you have a URL/title/external id and no key yet; returns
  deterministic `match.type` + `matchedFields`, not a confidence score.
- `proposals/:proposalKey`, `.../votes/summary`, `.../votes`: drill into one proposal. Obtain the
  key from a list/resolve/event/signal result — never construct or parse it.
- `proposals/:proposalKey/evidence`: for citation/audit/security answers that need provenance,
  references, or quality flags. Skip it when proposal detail and primary sources are sufficient.
- `forum-topics`: forum discussion scanning; `governanceRelated=true` narrows to governance-relevant
  threads.
- `timeline`, `voters`: trend and voter analysis.

Before using a paid endpoint, apply the paid-call consent flow above.

### Cursor pagination

List endpoints paginate with `limit` + `cursor` (see [errors.md](references/errors.md) for
`CURSOR_INVALID` / `CURSOR_STALE`). The `meta.page` object in responses carries `limit`, `hasMore`,
and `nextCursor`. When you need more than one page, follow `nextCursor`; bind filters to the request
and do not reuse a cursor across different filter sets. If a cursor comes back stale (409), re-run
the list without a cursor.

### Batch retrieval rule

When a question needs more than one API call: decide the query plan first, run the necessary calls,
collect all results, only then write the answer. Do not stream raw intermediate payloads to the user
unless they explicitly ask for them.

### Source follow-up rule

The Degov Agent API is the first layer, not the last layer. Its results often include source URLs.
When those URLs are important to the answer: open or search the linked forum or proposal materials,
confirm meaning/scope/timing, and use the source text to improve the explanation. If the API results
are missing, stale, or too shallow: use web search, prefer official DAO forums, Snapshot pages,
governance portals, Tally pages, and official announcements, and say clearly when you are using the
web in addition to the Degov Agent API. If a paid endpoint would help but the user does not want to
use the Degov Agent API service: continue with web search instead of pushing wallet setup again, and
say the answer may be less accurate or complete.

## Answer style and formatting

The API is a data source, not the final user experience. Do not give users raw JSON unless they
explicitly ask for it. Match the user's requested depth and format. By default:

- use simple words; explain DAO and governance ideas in plain language;
- answer directly, adding what happened and why it matters when that context helps;
- include the timeframe when relevant; use exact dates when timing is important.

For research summaries, a useful default shape is:

1. A plain-language paragraph that gives the main answer immediately.
2. A few concise bullets for the most important proposals, actions, or takeaways.
3. The most relevant source links at the end.

Keep the answer easy to scan. Cite the most relevant source links and distinguish API-derived facts
from primary-source interpretation when that distinction matters. Do not invent unsupported facts.

## Answer checklist

1. Did I figure out which DAO or DAO group the user probably means?
2. Did I choose the right v2 endpoints (including `events`/`signals` for event-time windows) and
   gather enough results before answering?
3. Did I follow `nextCursor` when pagination was needed, and handle a stale cursor correctly?
4. Did I use linked source materials or web follow-up when the API alone was too thin?
5. Did I answer in the depth and format the user requested instead of copying raw API output?
6. Are the important claims supported by relevant links or clearly identified API data?
7. If a paid endpoint was needed, did I ask the user whether they wanted to use the Degov Agent API
   service before making paid calls?
8. Did the actual payment requirement stay within the approved query plan and estimated cost, and
   did I avoid double-paying a settled resource?

## Guardrails

- Do not ask users to paste private keys, seed phrases, or credentials. Keys and signing live in the
  MetaMask agent wallet.
- Before entering a paid workflow, present the planned calls and estimated total cost, then offer
  the simple API-or-web choice. Do not claim the paid path is inherently more accurate for every
  question.
- Pay only calls covered by the approved plan and cost. If the inspected offer differs, show the
  asset, amount, network, `payTo`, and resource URL and get approval again. One payment attempt per
  resource; never auto-retry or double-pay.
- If the user declines the paid API path, proceed with web search instead of repeatedly asking.
- Turn API data into a user-friendly explanation instead of pasting raw responses; state when
  information came from the Degov Agent API versus the web.
- Do not fabricate governance activity, proposals, or dates.
- Use `GET /v2/meta/pricing` for live pricing; do not hardcode prices.
- The v2 API is the only supported surface; v1 endpoints are frozen and not documented here (see the
  migration table in [api-v2.md](references/api-v2.md)).
