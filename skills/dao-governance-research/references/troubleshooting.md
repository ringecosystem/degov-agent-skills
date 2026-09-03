# Degov Agent API V2 troubleshooting

Use this guide after a request fails or the returned fields cannot support the user's claim. Do not
run a fixed preflight before every governance question.

## First checks

1. Compare the request with `GET /openapi.json`; it is the source of truth for public paths,
   parameters, request bodies, and response shapes.
2. Confirm that a `daoId`, `proposalId`, `topicId`, `voterId`, and cursor came from the API rather
   than being guessed or decoded.
3. Preserve the response `requestId` when reporting an unexpected server failure.
4. Do not probe operational, internal, removed, or undocumented routes to decide whether public
   governance data is usable.

## Error responses

Most API errors use this envelope:

```json
{
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "The requested time window is too large",
    "details": {}
  },
  "requestId": "req-123"
}
```

| Status / code                 | Meaning                                                     | Recovery                                                        |
| ----------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------- |
| `400 INVALID_ARGUMENT`        | Unknown, malformed, conflicting, or out-of-range input      | Correct the request from `/openapi.json`; do not guess          |
| `401 UNAUTHORIZED`            | A protected internal path was requested without authority   | Stop; use only the documented public route set                  |
| `402 Payment Required`        | The public resource requires payment                        | Delegate the full challenge to the wallet capability            |
| `404 NOT_FOUND`               | The requested public DAO, proposal, or voter was not found  | Reacquire the public id from a list or exact resolver           |
| `404 DATA_NOT_AVAILABLE`      | The resource exists but that normalized data is unavailable | Use another public resource or the official source; disclose it |
| `409 CURSOR_EXPIRED`          | Published data changed since the cursor was issued          | Restart pagination only when another page still matters         |
| `429 RATE_LIMITED`            | Too many requests                                           | Respect `Retry-After`; avoid blind paid retries                 |
| `500 INTERNAL_ERROR`          | Unexpected service failure                                  | Preserve `requestId`; retry later or use an official source     |
| `503 TEMPORARILY_UNAVAILABLE` | The public serving view cannot currently answer             | Use an official source and disclose the API outage              |

Fastify can also return `413` for an oversized JSON body and `415` for a non-JSON resolver request.

## Payment failures

Do not construct payment signatures or retry paid requests manually. Pass the complete 402 response,
including its `PAYMENT-REQUIRED` header, to the `metamask-agent-wallet` capability. Let it handle
offer inspection, authorization, signing, settlement, and replay protection.

If the wallet capability is unavailable or payment is not authorized, continue with official web
sources where possible and say that structured Degov API data was not used.

## Empty, unavailable, and ambiguous data

- An empty list means no records matched the request in the current published view. It does not by
  itself prove that the source has never had matching records.
- DAO `availableData` describes public resource availability, not freshness. A missing family and a
  successful family endpoint conflict should be disclosed rather than silently choosing one.
- `DATA_NOT_AVAILABLE` from vote summary does not mean "zero votes". Vote rows may still exist for a
  ballot mechanism that cannot currently be normalized.
- Zero totals from a successful vote summary are evidence of zero published votes, but the API does
  not expose a data-as-of timestamp. Use the official proposal page if currentness matters.
- A null forum `excerpt` means the API cannot summarize the discussion. Open `source.url` rather
  than guessing from the title.

## Vote interpretation

- Preserve `votingPower` and `knownVotingPower` as decimal strings.
- `rawChoice` can be a scalar, array, or object. Map only a simple scalar through proposal
  `choices[].id`.
- If `choices` is null or the raw ballot is complex, state that the selection cannot be interpreted
  from the public API alone. Do not assume that numeric values always mean For/Against/Abstain.
- The API does not currently expose vote transaction hashes; use the proposal's official source for
  transaction-level verification.

## Pagination

- Use `nextCursor` only when `hasMore` is true.
- Pass the cursor back unchanged to the same route, filters, sort, and limit.
- Do not reuse, decode, edit, shorten, or synthesize a cursor.
- On `CURSOR_EXPIRED`, discard prior pages only if a consistent full traversal is required;
  otherwise keep the evidence already used and explain the limited window.

## Currentness

Public V2 intentionally omits pipeline health, serving revisions, coverage labels, and operational
status. It also currently omits a consumer-facing data-as-of timestamp. A successful request is not
proof that source ingestion is current. For "now", "latest", deadlines, execution, or other
time-sensitive claims, verify the relevant `source.url` and state the evidence time in the answer.
