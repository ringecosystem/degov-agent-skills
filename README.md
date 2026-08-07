# DeGov Agent Skills

Reusable agent skills for DAO governance research and proposal security analysis. These skills enable AI agents to answer DAO governance questions with evidence instead of guesses — using the Degov Agent API as the primary data source, web search as a follow-up, and the MetaMask agent wallet (`mm`) for x402 payments on paid endpoints.

## Skills

| Skill                                                                  | Description                                                                                                                                                                                                                                                                                                                                                                               |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`dao-governance-research`](./skills/dao-governance-research/SKILL.md) | DAO governance research via the Degov Agent API v2: endpoint routing, paid-call consent, x402 payment ceremony with the MetaMask agent wallet, and answer formatting. Routes to `references/` (endpoint cards, pricing, errors, x402 protocol, payment setup) and `workflows/` (discovery, recent activity, explain proposal, security review, evidence, payment setup, troubleshooting). |
| [`dao-governance-security`](./skills/dao-governance-security/SKILL.md) | Proposal security analysis: a rubric for checking malicious or unexpectedly risky proposal actions, funds flow, permissions, proposer/process anomalies, execution risk, uncertainty, and recommended user actions.                                                                                                                                                                       |

## Installation

```bash
npx skills add ringecosystem/degov-agent-skills
```

## Development

```bash
pnpm install
pnpm run format:check
pnpm run validate:dao-governance-security
pnpm run test:x402-compat
pnpm run smoke:dao-governance-research        # offline checks
pnpm run smoke:dao-governance-research:free   # live free endpoints
pnpm run smoke:dao-governance-research:paid   # live paid-offer check (zero cost)
```

Set `DEGOV_AGENT_API_BASE_URL` to point live checks at a staging instance (e.g. `http://127.0.0.1:8310`).
