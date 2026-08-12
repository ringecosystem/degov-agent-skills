# Pricing and budget

## Source of truth

`GET /v2/meta/pricing` (free) returns the live route table. Always use it for budget guidance; never
hardcode prices in answers.

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

## Tier summary

| Tier     | Price source             | Endpoints                                                                                                                                                              |
| -------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| free     | no payment               | `meta/pricing`, `meta/data-status`, `daos`, `daos/:daoId`                                                                                                              |
| standard | live pricing route table | `proposals`, `proposals/resolve`, `events`, `signals`, `forum-topics`                                                                                                  |
| plus     | live pricing route table | `daos/:daoId/timeline`, `proposals/:proposalKey` (+ votes/summary, votes, evidence), `forum-topics/:topicKey`, `daos/:daoId/voters`, `voters/:voterIdentity` (+ votes) |

## Budget guidance

- Ask the user how much they are willing to spend. Only after they choose the paid API path, check
  `mm wallet balance --chain-ids 8453` (Base USDC in the MetaMask agent wallet) to ensure the
  planned cost fits the available balance.
- Sum the live route price for every call in the planned resource set.
- Tell the user the expected cost **before** the first paid call, and let the wallet balance guide
  the cap.
- An unpaid paid-endpoint request costs nothing: the API returns `402` and no settlement happens.
