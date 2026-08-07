# DeGov Agent Skills

Reusable agent skills for DAO governance research and proposal security analysis. These skills
enable AI agents to answer DAO governance questions with evidence instead of guesses — using the
Degov Agent API as the primary data source, web search as a follow-up, and the MetaMask agent wallet
(`mm`) for x402 payments on paid endpoints.

## Skills

| Skill                                                                  | Description                                                                                                                                                                                                                                                                                                          |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`dao-governance-research`](./skills/dao-governance-research/SKILL.md) | DAO governance research via the Degov Agent API v2: endpoint routing, paid-call consent, x402 payment ceremony, and answer formatting. Includes `references/` (endpoint cards, pricing, errors, x402, payment) and `workflows/` (discovery, activity, explain, security review, evidence, payment, troubleshooting). |
| [`dao-governance-security`](./skills/dao-governance-security/SKILL.md) | Proposal security analysis: a rubric for malicious or risky actions, funds flow, permissions, proposer/process anomalies, execution risk, uncertainty, and recommended user actions.                                                                                                                                 |

## Installation

```bash
npx skills add ringecosystem/degov-agent-skills
```
