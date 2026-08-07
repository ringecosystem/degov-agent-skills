# Workflow: proposal security review (bridge to dao-governance-security)

Goal: fetch the data a security analysis needs, then hand the judgment to the `dao-governance-security` skill. The security skill owns the rubric (severity, findings, output format); this workflow owns the data-fetch call chain.

## Steps

1. Resolve the proposal key ([explain-proposal.md](explain-proposal.md) steps 1–2).

2. Fetch detail (plus): `GET /v2/proposals/<proposalKey>` — `bodyText`, `proposerId`, `sourceUrl`, `discussionUrl`, `lifecycleStatus`, `outcome`, `choices`.

3. Fetch vote summary (plus) for quorum/participation context: `GET /v2/proposals/<proposalKey>/votes/summary`.

4. **Evidence bundle** (plus) when available — provenance, source references, intelligence quality flags, limitations:

```bash
curl -s "https://agent-api.degov.ai/v2/proposals/<proposalKey>/evidence"
```

The evidence bundle is an optional audit/citation aid: it does not decode calldata or replace the security skill's own verification (block explorers, simulation, proposer history).

5. Load `dao-governance-security` and produce its required analysis format, using the fetched data as evidence plus the sources it names.

## Boundaries

- The API provides proposal text, metadata, and votes — not decoded onchain actions. For executable payloads, use the linked source (Snapshot/Tally/Agora/explorer) and follow the security skill's decoding requirements.
- If the evidence bundle reports `intelligence.status: "unavailable"` or quality warnings, treat it as _absence of a dossier_, not as a clean bill of health.
- Paid calls here are plus tier ($0.01 each); mention the expected cost when the user is budget-conscious (consent flow first).
