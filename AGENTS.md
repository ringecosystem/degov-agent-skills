# AGENTS.md

This repository is the external skill home for DeGov-related agent skills. It currently contains one primary skill, `dao-governance`, plus a small TypeScript CLI used by that skill to query `degov-agent-api` and make x402-paid API calls through a dedicated local wallet.

## Repository map

- `README.md`: high-level repository overview and current skill behavior.
- `skills/dao-governance/SKILL.md`: the actual Hermes/Codex-style skill document loaded when a user asks about Web3 DAO governance.
- `skills/dao-governance/scripts/`: TypeScript CLI helpers for wallet management, free API calls, and x402-paid API calls.
- `skills/dao-governance/scripts/degov-client.ts`: command-line entry point for the Degov Agent API.
- `skills/dao-governance/scripts/wallet-store.ts`: local wallet creation, encryption, migration, balance lookup, and secret-file handling.
- `.github/workflows/ci.yml`: CI validation for formatting and TypeScript compilation.

## What this codebase does

The `dao-governance` skill is intended to make agents answer DAO governance questions with evidence instead of guessing. It uses `degov-agent-api` as the primary source for recent governance data, then falls back to or supplements with web search when API coverage is missing, stale, or too thin.

The bundled CLI defaults to the production API:

```bash
https://agent-api.degov.ai
```

It supports these main commands from `skills/dao-governance/scripts`:

```bash
pnpm exec tsx degov-client.ts health
pnpm exec tsx degov-client.ts daos
pnpm exec tsx degov-client.ts budget --usd 1
pnpm exec tsx degov-client.ts wallet init
pnpm exec tsx degov-client.ts wallet address
pnpm exec tsx degov-client.ts wallet balance
pnpm exec tsx degov-client.ts activity --hours 24 --limit 10
pnpm exec tsx degov-client.ts brief ens
pnpm exec tsx degov-client.ts item proposal <id>
pnpm exec tsx degov-client.ts freshness
```

Free endpoints should be used before paid endpoints when they are enough. Paid endpoints require a dedicated local Base wallet funded with USDC and must only be used after the user agrees to the paid Degov Agent API path.

## Dependency and validation commands

Most validation runs from the scripts package:

```bash
cd skills/dao-governance/scripts
pnpm install
pnpm run format:check
pnpm run typecheck
pnpm exec tsx degov-client.ts help
```

Use the combined package check when appropriate:

```bash
cd skills/dao-governance/scripts
pnpm run check
```

Before opening a PR, also run repository-level git checks from the worktree root:

```bash
git status --short --branch
git diff --check
git diff --stat origin/main...HEAD
```

If formatting changes are needed, run:

```bash
cd skills/dao-governance/scripts
pnpm run format
```

## Coding and documentation conventions

- Prefer clear, maintenance-oriented comments only when the intent is not obvious.
- Keep user-facing skill guidance plain and explicit; do not dump raw API payloads in normal answers.
- Do not hardcode pricing estimates in documentation when live pricing is available through `budget` or `/v1/meta/pricing`.
- Do not ask users to paste private keys. The CLI must manage a dedicated local wallet instead.
- Keep wallet and passphrase files outside the repository. Defaults are under `~/.agents/state/dao-governance/`.
- Preserve the free-vs-paid decision flow in `SKILL.md`: use free endpoints when sufficient, and ask before paid calls.
- When changing API behavior or CLI commands, update all related docs together: root `README.md`, `skills/dao-governance/SKILL.md`, and `skills/dao-governance/scripts/README.md`.

## Security and paid-call guardrails

- Treat wallet files, private keys, passphrases, API tokens, and `.env` files as secrets.
- Never commit generated wallet material or passphrase files.
- Paid calls should be intentional and visible to the user.
- The skill should present a simple choice before paid use:
  1. Use Degov Agent API
  2. Use web search only
- If the user declines paid API use, proceed with web search and do not keep pushing wallet setup.
