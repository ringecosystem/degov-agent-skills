# Workflow: troubleshooting

Decision tree for failed API calls and payment problems.

## API-level failures

| Symptom                                                                          | Cause                                                                                 | Fix                                                                                                                           |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `400 VALIDATION_ERROR`                                                           | Bad param/enum/CSV                                                                    | Re-read the endpoint card in [api-v2.md](../references/api-v2.md); check `details`                                            |
| `400 WINDOW_TOO_LARGE`                                                           | Window > 90/365 days, timeline > 240 months                                           | Narrow `from`/`to` or `fromMonth`/`toMonth`                                                                                   |
| `400 CURSOR_INVALID`                                                             | Cursor malformed or from another filter set                                           | Drop the cursor; re-run                                                                                                       |
| `404 NOT_FOUND` (key)                                                            | Key expired/versioned away                                                            | Re-resolve via list or `proposals/resolve`                                                                                    |
| `409 CURSOR_STALE`                                                               | Serving revision advanced                                                             | Re-run the list without a cursor; note the extra standard-tier call                                                           |
| `429 RATE_LIMITED` / `QUOTA_EXCEEDED`                                            | Too many requests                                                                     | Back off; ask the user before continuing                                                                                      |
| `500 INTERNAL_ERROR`                                                             | Server issue                                                                          | Retry once; if persistent, report                                                                                             |
| `414 URI Too Long` on `proposals/:proposalKey` / `forum-topics/:topicKey` routes | Old deployment with default `maxParamLength` (100) rejecting the ~190-char opaque key | The fix is shipped (degov-agent-api, 2026-08): retry against a current deployment; if it persists, use list/resolve endpoints |
| Empty/stale-looking data                                                         | `meta.dataAsOf` old, `coverageStatus` `backfilling`/`stale`                           | Check `meta/data-status`; say the data may lag; use web follow-up                                                             |

## Payment failures

| Symptom                         | Cause                                                                          | Fix                                                                                                                                       |
| ------------------------------- | ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `402` with `PAYMENT-REQUIRED`   | Normal for paid endpoints                                                      | Run the payment ceremony ([SKILL.md](../SKILL.md) → Payment ceremony)                                                                     |
| `x402_pay.py` rejects the offer | Script requires domain name/version in `extra`, `eip3009`, exact scheme, https | Degov offers satisfy all of these (verified 2026-08); if rejection persists, the API or skill version changed — report, do not hand-patch |
| `mm` says `AUTH_FAILED`         | Not logged in                                                                  | `mm login` (user action)                                                                                                                  |
| `mm` says `NOT_INITIALIZED`     | No wallet mode set                                                             | `mm init` (user action)                                                                                                                   |
| Payment signed but still `402`  | Envelope/settlement mismatch, or authorization expired                         | Check `PAYMENT-RESPONSE`; never re-pay blindly — see [errors.md](../references/errors.md)                                                 |
| `PAYMENT_CONFLICT` 409          | Settlement conflict                                                            | Inspect the settlement; do not auto-retry                                                                                                 |
| Balance 0 on Base               | USDC not on chain 8453                                                         | `mm wallet add-fund`, fund the Base address                                                                                               |

## Environment failures

| Symptom                      | Cause                   | Fix                                                                                              |
| ---------------------------- | ----------------------- | ------------------------------------------------------------------------------------------------ |
| Base URL unreachable         | Wrong endpoint          | Production: `https://agent-api.degov.ai`; staging: local override (e.g. `http://127.0.0.1:8310`) |
| MetaMask skill not installed | Missing prerequisite    | `npx skills add metaMask/agent-skills`, or use web-only mode                                     |
| `mmCliVersion` mismatch      | CLI upgraded/downgraded | Warn the user; `npm install -g @metamask/agent-wallet@<pinned>` if alignment is wanted           |

## Escalation

If the same failure repeats after the fix, stop and report the exact request, response envelope, and
error code instead of looping.
