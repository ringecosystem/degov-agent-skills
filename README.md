# DeGov Agent Skills

Reusable agent skills for DAO governance research and proposal security analysis. These skills
enable AI agents to answer DAO governance questions with evidence instead of guesses — using the
Degov Agent API for covered structured data, official web sources for primary-source context and
coverage gaps, and the MetaMask agent wallet (`mm`) for x402 payments on paid endpoints.

## Skills

| Skill                                                                  | Description                                                                                                                                                                                                                               |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`dao-governance-research`](./skills/dao-governance-research/SKILL.md) | DAO governance research using the Degov Agent API for covered structured data and official web sources for verification, context, and coverage gaps. Payment authorization and signing are delegated to the configured wallet capability. |
| [`dao-governance-security`](./skills/dao-governance-security/SKILL.md) | Proposal security analysis: a rubric for malicious or risky actions, funds flow, permissions, proposer/process anomalies, execution risk, uncertainty, and recommended user actions.                                                      |

## Installation

```bash
npx skills add ringecosystem/degov-agent-skills
```
