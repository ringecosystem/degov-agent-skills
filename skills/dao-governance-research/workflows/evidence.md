# Workflow: evidence and citations

Goal: produce a citation/audit-oriented answer (research reports, security write-ups, provenance checks) using the v2 evidence bundle. Plus tier — apply the paid-call consent flow first.

## When to use

- The user asks for sources/provenance behind a proposal's data.
- A security or research answer needs quality flags and explicit limitations.
- You need to state _what is known vs. not known_ about a proposal's records.

Do **not** call this for ordinary "explain this proposal" answers — the detail endpoint already carries the source links.

## Steps

1. Obtain the key ([explain-proposal.md](explain-proposal.md) steps 1–2).

2. Fetch the bundle:

```bash
curl -s "https://agent-api.degov.ai/v2/proposals/<proposalKey>/evidence"
```

3. Interpret:

- `provenance[]` — which serving field came from which source/provider and when observed.
- `qualityFlags` — e.g. `registry_body_available`, `registry_quorum_available`; absent flag = not verifiable via the registry.
- `warnings` — e.g. non-`ready` coverage status.
- `intelligence` — persisted dossier status; `unavailable` with a warning means **no dossier exists**, which is not the same as "clean".

4. Combine with the detail/votes data and the named external sources; cite them explicitly.

## Output

State provenance and limitations in the answer, e.g. "proposal body and quorum are available in the registry; no persisted intelligence dossier exists; coverage was ready as of <time>". Do not inflate certainty — the bundle's `warnings` are part of the evidence.
