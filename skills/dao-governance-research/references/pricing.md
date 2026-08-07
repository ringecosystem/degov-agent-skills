# Pricing and budget

## Source of truth

`GET /v2/meta/pricing` (free) returns the live route table. Always use it for budget guidance; never hardcode prices in answers.

```json
{
  "data": {
    "token": "USDC",
    "network": "eip155:8453",
    "routes": [
      {
        "routeId": "v2.proposals.list",
        "method": "GET",
        "path": "/v2/proposals",
        "tier": "standard",
        "paid": true,
        "price": "0.005"
      }
    ]
  },
  "meta": { "requestId": "req-xxx", "generatedAt": "..." }
}
```

- `tier`: `free` (no payment) / `standard` / `plus`.
- `price`: decimal string in USD per call, or `null` for free routes.
- `network`: payment network for x402 — currently `eip155:8453` (Base, USDC).

## Tier summary (verify against live pricing)

| Tier     | Typical price | Endpoints                                                                                                                                                              |
| -------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| free     | —             | `meta/pricing`, `meta/data-status`, `daos`, `daos/:daoId`                                                                                                              |
| standard | $0.005        | `proposals`, `proposals/resolve`, `events`, `signals`, `forum-topics`                                                                                                  |
| plus     | $0.01         | `daos/:daoId/timeline`, `proposals/:proposalKey` (+ votes/summary, votes, evidence), `forum-topics/:topicKey`, `daos/:daoId/voters`, `voters/:voterIdentity` (+ votes) |

## Budget guidance

- Ask the user how much they are willing to spend, or check the wallet balance first: `mm wallet balance --chain-ids 8453` (Base USDC in the MetaMask agent wallet).
- Multiply the number of planned paid calls by the route price. Example: one standard list ($0.005) + two plus details ($0.01 × 2) ≈ $0.025.
- Tell the user the expected cost **before** the first paid call, and let the wallet balance guide the cap.
- An unpaid paid-endpoint request costs nothing: the API returns `402` and no settlement happens.
