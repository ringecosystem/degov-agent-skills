---
name: dao-governance-research
description:
  Load this skill when users ask about Web3 DAO governance. Use the Degov Agent API as the primary
  source for covered governance facts and recent activity, then use official web sources when API
  coverage is missing, stale, or insufficient.
metadata:
  version: 1.0.0
---

# DAO Governance Research

## Purpose

Use this skill when a question depends on accurate, recent DAO governance information. The Degov
Agent API is the primary source for covered structured data. Official governance sites, forums,
Snapshot, Tally, Agora, DAO documentation, and block explorers provide primary-source verification
and context.

Use web sources directly for conceptual questions or participation instructions that do not need
structured API data. When API coverage is missing, stale, or too shallow, continue with official web
sources and disclose that limitation without treating the web as an inferior fallback.

Default API base URL: `https://agent-api.degov.ai`.

## Research flow

1. Identify the DAO, governance system, requested time range, and whether the user wants discovery,
   recent activity, a specific proposal, forum discussion, voter analysis, or security context.
2. Use the free DAO directory and DAO detail endpoints first when they can resolve the DAO or show
   which public resource families are available.
3. Select the smallest set of API resources that can answer the question. Use
   [api.md](references/api.md) for current paths, parameters, response shapes, and limits.
4. Follow pagination only while additional results materially improve the answer. Treat keys and
   cursors as opaque values returned by the API; never construct or parse them.
5. Open relevant source URLs from API results when primary text, outcome, quorum, execution details,
   or currentness needs confirmation. The public V2 response does not expose pipeline health or a
   data-freshness timestamp.
6. If API data is unavailable or insufficient, continue with official web sources and state what
   evidence was not available.
7. Turn the evidence into a direct answer rather than returning raw JSON.

## Capability routing

| User intent                                       | API capability                                  |
| ------------------------------------------------- | ----------------------------------------------- |
| Discover covered DAOs or resolve a DAO            | DAO directory and DAO detail                    |
| Check available public data families              | DAO detail `availableData`                      |
| Review recent proposals                           | Proposal list filtered by DAO, status, and time |
| Resolve a proposal from an exact URL or source ID | Proposal resolution followed by proposal detail |
| Explain a proposal                                | Proposal detail                                 |
| Analyze known turnout or vote concentration       | Vote summary and vote rows                      |
| Inspect recent governance forum discussion        | Forum topic list                                |
| Rank DAO participants or review voter behavior    | DAO participant and voter resources             |
| Confirm outcome, quorum, execution, or freshness  | Official source linked by the API               |

For a broad request, begin with a DAO, proposal, or forum list and drill into only the most relevant
items. For a specific proposal, resolve an exact supplied URL or source identity when necessary,
fetch the detail, and add vote resources only when they affect the answer. The resolver does not
accept titles; use a narrowed proposal list or official search when the user supplies only a title.

## Payments

Some API resources require x402 payment. When a request returns `402 Payment Required`, load the
`metamask-agent-wallet` skill and follow its standard x402 workflow. The wallet capability owns user
authorization, spending controls, offer inspection, signing, settlement verification, and retry
safety. Do not reproduce or override those policies in this skill.

If the wallet capability is unavailable or the payment is not authorized, continue with official web
sources where possible and disclose that structured Degov API data was not used.

Current payment metadata is published on each paid operation in `/openapi.json` and in the
`PAYMENT-REQUIRED` challenge. Do not hardcode prices in this skill.

## Evidence rules

- Treat API data as evidence, not final prose.
- Prefer primary sources for proposal intent, executable actions, deadlines, and official process.
- Distinguish confirmed facts from interpretation and missing information.
- Preserve exact dates and time zones when timing affects the answer.
- Do not describe API results as complete, fresh, or current solely because the request succeeded;
  verify time-sensitive claims against an official source.
- `availableData` describes public resource availability, not freshness. If it conflicts with a
  successful endpoint response, disclose the ambiguity instead of guessing.
- `rawChoice` is provider-shaped JSON. Map simple scalar choice ids through proposal `choices`, but
  do not invent semantics for arrays or objects when the proposal does not describe its vote type.
- Do not infer proposal contents, outcomes, vote totals, or dates from titles alone.
- For proposal security questions, gather the available proposal, vote, provenance, and source
  context, then apply the `dao-governance-security` skill.

## Answer style

Answer in the depth and format the user requested. By default:

1. Lead with the plain-language conclusion.
2. Summarize the most important proposals, actions, or takeaways.
3. Explain why they matter when that context is useful.
4. Include the relevant time range and source links.
5. State material coverage, freshness, or evidence limitations.

Do not return raw API payloads unless the user asks for them.

## Troubleshooting

Use [troubleshooting.md](references/troubleshooting.md) for API validation, pagination, freshness,
payment, connectivity, and response-shape failures.

## Final checklist

- The DAO and requested scope are correctly identified.
- The selected resources are sufficient but not excessive.
- Opaque proposal ids and cursors came from API responses.
- Important claims are supported by API evidence or relevant primary sources.
- Missing, potentially stale, or conflicting evidence is disclosed.
- Payment behavior, when needed, was delegated to the wallet capability.
- The answer is useful prose rather than an API dump.
