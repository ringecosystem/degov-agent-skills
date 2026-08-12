# Degov Agent API troubleshooting

Use this guide only after a request fails or returns data that cannot support the answer. Do not run
a fixed preflight for every governance question.

## Response failures

API errors normally use this envelope:

```json
{
  "error": { "code": "VALIDATION_ERROR", "message": "...", "details": {} },
  "meta": { "requestId": "req-xxx", "generatedAt": "..." }
}
```

| Status or code                               | Meaning                                                                 | Recovery                                                                    |
| -------------------------------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `400 VALIDATION_ERROR`                       | Invalid parameter, enum, CSV value, or date window                      | Re-read [api.md](api.md) and correct the request                            |
| `400 RESOLVE_INPUT_REQUIRED`                 | Proposal resolver has no usable identifier                              | Supply exactly one URL, title, or external ID                               |
| `402 PAYMENT_REQUIRED`                       | The resource requires payment                                           | Delegate the response to the `metamask-agent-wallet` skill                  |
| `404 DAO_NOT_FOUND`                          | Unknown or uncovered DAO ID                                             | Use the DAO directory to resolve the current ID                             |
| `404 PROPOSAL_NOT_FOUND` / `TOPIC_NOT_FOUND` | Opaque key is invalid or no longer available                            | Obtain the key again from a list, event, signal, or resolver response       |
| `409 CURSOR_INVALID` / `CURSOR_STALE`        | Cursor does not match the resource, filters, limit, or serving revision | Drop the cursor and restart pagination only if another page is still needed |
| `422 COVERAGE_UNAVAILABLE`                   | The requested domain is not covered                                     | Continue with official web sources and disclose the gap                     |
| `429 RATE_LIMITED`                           | Request rate is too high                                                | Respect `Retry-After`; do not retry a payment blindly                       |
| `500 INTERNAL_ERROR`                         | Unexpected service failure                                              | Preserve `requestId`, retry later if useful, and use web sources meanwhile  |
| `503 DATA_UNAVAILABLE`                       | Projection or serving data is unavailable                               | Check data status, then use web sources if the outage affects the answer    |

## Payment failures

The governance skill does not implement payment authorization or signing. Pass the complete `402`
response to the wallet capability and follow its standard x402 workflow. If payment cannot proceed,
use official web sources where possible and state that structured Degov API data was unavailable.

Do not manually construct payment headers, signatures, or retries in this skill.

## Freshness and coverage

- `ready`: use the data normally.
- `backfilling`: data may be incomplete; disclose the limitation when material.
- `stale`: verify time-sensitive claims against primary sources.
- `unavailable`: do not infer missing results; switch to official web sources.

An empty list is not automatically an error. Check the DAO ID, filters, time field, time range, and
coverage status before concluding that no activity exists.

## Response-shape checks

- Preserve high-precision decimal strings instead of converting them to floating point.
- Use `meta.page.nextCursor` only when `hasMore` is true.
- Never reuse a cursor across different resources, limits, or filters.
- Treat proposal keys, topic keys, and voter identities as opaque values.
- A long opaque path value that produces `414 URI Too Long` is a server-routing problem; keep the
  request ID and report it instead of shortening or reconstructing the key.

## Connectivity

Use `GET /health` only when diagnosing connectivity or service availability. A successful health
response does not establish data coverage or freshness; use the data-status resource for that.
