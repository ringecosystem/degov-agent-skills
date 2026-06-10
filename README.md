# degov-agent-skills

Reusable agent skills for DeGov governance research and proposal security analysis.

This repository packages DAO governance skills so agents can answer governance questions with evidence instead of guesses and assess proposal security risks before users vote or execute. The skills are designed for external use: they explain when to use Degov Agent API data, when to fall back to web sources, how to ask for consent before paid API calls, and how to analyze governance proposals for malicious or unexpectedly risky actions.

## What is included

- `skills/dao-governance/SKILL.md`: the agent-facing governance research guide.
- `skills/dao-governance-security/SKILL.md`: the proposal security-analysis rubric for evaluating executable actions, funds flow, permissions, proposer/process anomalies, uncertainty, and recommended user actions.
- `skills/dao-governance/scripts/`: a TypeScript helper CLI for Degov Agent API calls and payment-wallet management.
- `scripts/tests/`: repository-owned validation and smoke-test entry points used by CI and local checks.

## What the skills do

The `dao-governance` skill helps agents:

- discover covered DAOs through free public endpoints
- use Degov Agent API as the primary evidence source when recent governance data matters
- use web search as a secondary source when API coverage is missing, stale, or too shallow
- ask the user before making paid x402 API calls
- turn API results into clear, source-aware explanations instead of raw JSON dumps

The `dao-governance-security` skill helps agents:

- decode and compare governance proposal actions against the proposal text
- check token/ETH amounts, recipients, allowances, upgrades, roles, ownership, and governance setting changes
- assess proposer identity, reputation, vote/process anomalies, execution and cross-chain risk
- classify findings with clear severity levels from Critical through Unknown
- produce a required final analysis format with evidence, assumptions, uncertainties, and concrete recommended user actions

## Proposal security examples and validation

The security skill includes synthetic example analyses that can be used for local review without querying live APIs:

- `skills/dao-governance-security/examples/benign-operational-budget.md`: a low-risk operational treasury transfer where proposal text, decoded action, recipient, amount, proposer history, and process context line up.
- `skills/dao-governance-security/examples/risky-treasury-drain-and-admin-grant.md`: a critical-risk proposal where decoded actions contradict the prose, move an incorrect amount to a suspicious recipient, come from a suspicious proposer, and grant a dangerous permission.

Run the deterministic validator from the repository root:

```bash
pnpm run validate:dao-governance-security
```

The validator checks that `skills/dao-governance-security/SKILL.md` is loadable as a skill, that its required final-analysis sections are present, and that both examples follow the structured output contract. The same check is included in the offline smoke test:

```bash
pnpm run smoke:dao-governance
```

The default API endpoint is:

```text
https://agent-api.degov.ai
```

## Public API model

Free endpoints are available for basic discovery:

- `GET /health`
- `GET /v1/meta/pricing`
- `GET /v1/daos`

Paid research endpoints use x402 payments on Base USDC and should only be called after user consent:

- `GET /v1/activity`
- `GET /v1/governance-events`
- `GET /v1/daos/:daoId/brief`
- `GET /v1/items/:kind/:externalId`
- `GET /v1/system/freshness`

## Wallet safety

The helper CLI creates a dedicated local wallet for small API payments. It does not ask users to paste private keys into chat.

Default local wallet state is stored outside the repository:

```text
~/.agents/state/dao-governance/wallet.json
```

Keep wallet files, passphrases, `.env` files, logs, generated state, and other secrets out of version control.

## Repository checks and formatting

Repository-wide checks are exposed from the repository root. The root formatter scans the repository recursively for Prettier-supported files while respecting `.prettierignore` and `.gitignore`:

```bash
pnpm run format
pnpm run format:check
pnpm run validate:dao-governance-security
pnpm run smoke:dao-governance
```

The dao-governance helper package keeps local checks scoped to the governance skill. Run these from the skill directory; the package itself lives in `scripts/`:

```bash
cd skills/dao-governance
pnpm --dir scripts run format
pnpm --dir scripts run format:check
pnpm --dir scripts run check
```

## Using the CLI helper

From the skill directory:

```bash
cd skills/dao-governance
pnpm --dir scripts install
pnpm --dir scripts exec tsx degov-client.ts help
```

Common commands:

```bash
pnpm --dir scripts exec tsx degov-client.ts daos
pnpm --dir scripts exec tsx degov-client.ts budget --usd 1
pnpm --dir scripts exec tsx degov-client.ts wallet init
pnpm --dir scripts exec tsx degov-client.ts wallet address
pnpm --dir scripts exec tsx degov-client.ts wallet balance
pnpm --dir scripts exec tsx degov-client.ts transfer <to-address> <amount-usdc>
pnpm --dir scripts exec tsx degov-client.ts activity --hours 24 --limit 10
pnpm --dir scripts exec tsx degov-client.ts governance-events --hours 24 --limit 200
pnpm --dir scripts exec tsx degov-client.ts brief ens
pnpm --dir scripts exec tsx degov-client.ts item proposal <id>
pnpm --dir scripts exec tsx degov-client.ts freshness
pnpm --dir scripts exec tsx degov-client.ts health
```
