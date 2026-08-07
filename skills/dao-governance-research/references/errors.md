# Errors

Every v2 endpoint returns failures through one envelope:

```json
{
  "error": { "code": "VALIDATION_ERROR", "message": "...", "details": {} },
  "meta": { "requestId": "req-xxx" }
}
```

## Error codes

| HTTP | Code                              | Meaning                                                               | Handling                                                                                            |
| ---- | --------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| 400  | `VALIDATION_ERROR`                | Bad parameter, enum, or CSV value                                     | Fix the request per `api-v2.md`; read `details` when present                                        |
| 400  | `WINDOW_TOO_LARGE`                | `from`/`to` window exceeds the endpoint max (90/365 days, 240 months) | Narrow the window                                                                                   |
| 400  | `CURSOR_INVALID`                  | Malformed or foreign cursor                                           | Drop the cursor and re-run                                                                          |
| 401  | `UNAUTHORIZED`                    | Missing/invalid auth (not normally seen on the public x402 path)      | —                                                                                                   |
| 402  | `PAYMENT_REQUIRED`                | Paid endpoint called without payment                                  | Run the x402 payment ceremony (SKILL.md) and retry once with the signature header                   |
| 403  | `FORBIDDEN`                       | Authenticated but not allowed (partner scope paths)                   | —                                                                                                   |
| 404  | `NOT_FOUND`                       | Unknown `daoId`, `proposalKey`, `topicKey`, or `voterIdentity`        | Re-resolve the key (list/resolve) — keys are versioned and can expire across serving revisions      |
| 409  | `PAYMENT_CONFLICT`                | Payment/settlement conflict                                           | Do not retry blindly; inspect the settlement                                                        |
| 409  | `CURSOR_STALE`                    | The serving revision advanced; cursor bound to an old snapshot        | Re-run the list without a cursor (or with a fresh one); never reuse filters+cursor across revisions |
| 422  | `CANDIDATE_BUDGET_EXCEEDED`       | Internal candidate budget (signals pipeline)                          | Retry with narrower filters or later                                                                |
| 429  | `RATE_LIMITED` / `QUOTA_EXCEEDED` | Too many requests / monthly quota                                     | Back off and retry later                                                                            |
| 500  | `INTERNAL_ERROR`                  | Server error                                                          | Retry once; if persistent, report                                                                   |

## Non-envelope HTTP errors

- `414 URI Too Long`: Fastify rejects route params longer than its default `maxParamLength` (100 chars). v2 `proposalKey`/`topicKey` values are opaque and ~190 chars, so key-param routes (`proposals/:proposalKey`, `.../votes/summary`, `.../votes`, `.../evidence`, `forum-topics/:topicKey`) can return 414. **Known API-side issue** (reproduced on staging 2026-08-07; no payment is made when this happens); expected fix is a higher `maxParamLength` in the API server. Until it ships, retry later or use the list/resolve endpoints.

## 402 anatomy

A paid endpoint without payment returns `402` with:

- Header `PAYMENT-REQUIRED`: base64 x402 v2 challenge — `{ x402Version: 2, accepts: [{ scheme: "exact", network: "eip155:8453", amount, asset, payTo, maxTimeoutSeconds, extra: { name, version, assetTransferMethod: "eip3009" } }] }`.
- Body: `{ error: "Payment required", paymentRequired: { scheme, network, amount, asset, payTo } }`.

`amount` is in atomic units (USDC has 6 decimals; e.g. `5000` = $0.005). `payTo` is the API's receiver — confirm it with the user before paying. See `x402.md` for the full ceremony.

## Retry guidance

- 402: pay once, retry once with the signature header. Never auto-retry a payment, and never re-pay an already-settled resource (a successful retry returns the resource plus a `PAYMENT-RESPONSE` settlement header).
- 409 `CURSOR_STALE`: re-run the list fresh; the cost of one standard call may be incurred again — mention it if the user is budget-conscious.
- 429: exponential backoff, then ask the user before continuing.
