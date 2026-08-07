---
name: dao-governance-security
description:
  Load this skill when users ask whether a DAO governance proposal is safe, malicious, risky,
  unexpectedly permissive, or worth supporting from a security perspective. Use it to analyze
  proposal actions, funds flow, contract calls, permissions, proposer reputation, process anomalies,
  execution risk, evidence, uncertainty, and recommended user actions.
metadata:
  version: 0.2.0
---

# DAO Governance Proposal Security Skill

## When to use this skill

Use this skill when the user asks for a security-oriented analysis of a DAO governance proposal,
vote, executable payload, Snapshot/Tally/Agora proposal, forum post, multisig transaction, or
onchain governance action.

Invoke it for questions such as:

- "Is this proposal safe to vote for?"
- "Could this governance proposal be malicious?"
- "Analyze the executable actions in this Tally proposal."
- "Does this proposal transfer funds or grant permissions?"
- "What are the security risks if this passes?"
- "Summarize any red flags in this DAO proposal before I vote."

Do not use this skill as a substitute for a professional audit, formal legal advice, or a definitive
exploit proof unless the evidence supports that level of confidence. The goal is to help the user
identify concrete risks, missing information, and safe next steps.

## Security posture

Be skeptical, evidence-first, and explicit about uncertainty. This framework is designed to catch
malicious or unexpected proposal actions, including token/native-asset movement, permission grants,
contract upgrades, and governance-setting changes. A governance proposal can look harmless in prose
while executable actions transfer assets, upgrade contracts, change permissions, or call arbitrary
targets. Conversely, not every large transfer or upgrade is malicious. Judge risk from the
combination of proposal text, executable payload, recipients, permissions, proposer history, process
context, and timing.

Prefer this mindset:

- Treat the proposal text as a claim, not as proof.
- Treat executable actions as the source of truth when they exist.
- Decode contract calls and value transfers before giving a low-risk conclusion.
- Separate confirmed facts from inferences and missing data.
- Recommend human/security-team review when execution can move funds, grant powerful roles, upgrade
  core contracts, or cannot be decoded.

## Required inputs and evidence

Start by collecting the minimum evidence needed to analyze the proposal. Ask for missing links only
when they cannot be retrieved from the prompt or public sources.

Useful inputs:

- DAO name and network/chain.
- Proposal URL, proposal ID, Snapshot/Tally/Agora/Governor link, forum link, or transaction hash.
- Proposal title, body, and exact executable actions if available.
- Voting status, execution ETA/deadline, quorum/threshold, and current vote totals.
- Proposer address/ENS/profile and any sponsor/delegate information.
- Target contract addresses, calldata, ETH/native value, token amounts, recipients, and operation
  type (`call`, `delegatecall`, `upgrade`, `setRole`, `transfer`, etc.).
- Source links used to support the analysis.

Evidence sources to prefer:

- Official governance UI, forum, Snapshot, Tally, Agora, or DAO docs.
- Block explorers with verified contract source, ABI, token transfer views, and transaction
  simulation traces.
- DAO treasury dashboards and official multisig/governor addresses.
- Prior proposals by the same proposer or affecting the same contracts.
- Degov Agent API via the `dao-governance-research` skill when recent proposal discovery or context
  is needed. Use its
  [proposal-security.md](../dao-governance-research/workflows/proposal-security.md) for the
  data-fetch call chain (resolve → proposal detail → vote summary → evidence).
- The v2 proposal evidence bundle (`GET /v2/proposals/:proposalKey/evidence` via the
  `dao-governance-research` skill, plus tier): provenance, source references, intelligence quality
  flags, and limitations — useful for evidence-first checks and for classifying uncertainty (see the
  severity `Unknown` definition).

Never ask the user to paste private keys, seed phrases, admin credentials, or non-public secrets.

## Severity definitions

Assign one overall risk level and one severity for each finding. Use the highest credible severity
among findings as the default overall risk, then adjust for uncertainty and mitigations.

| Level    | Meaning                                                                                                                                                               | Typical triggers                                                                                                                                                                                                                                                                |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Critical | Strong evidence of malicious behavior or a change that can directly cause irreversible loss, takeover, censorship, or protocol-wide compromise if executed.           | Undisclosed treasury drain; arbitrary `delegatecall`; granting admin/upgrade roles to unknown address; upgrading core implementation to unverified code; changing governor/timelock controls to bypass checks; calldata does something materially different from proposal text. |
| High     | Material security or governance risk that could cause major asset loss, loss of control, or hard-to-reverse damage, but intent or exploitability is not fully proven. | Large transfer to weakly justified recipient; powerful permission grant with incomplete rationale; upgrade with limited review; emergency action with weak process; suspicious proposer plus sensitive action; execution path cannot be fully decoded for a high-impact target. |
| Medium   | Meaningful risk that needs attention but is limited in scope, reversible, or mitigated by process controls.                                                           | Moderate fund movement; parameter changes with market/security impact; ambiguous recipient ownership; missing simulation for non-core call; process irregularities that do not obviously change outcome.                                                                        |
| Low      | Minor issue or ordinary operational risk with clear evidence, low blast radius, and no sensitive permissions.                                                         | Small budget transfer to known recipient; routine parameter update; well-documented action matching proposal text; known proposer and normal process.                                                                                                                           |
| Info     | Context that is useful but not itself a risk.                                                                                                                         | Proposal is non-executable; recipient matches verified DAO multisig; timelock provides review window; contract source is verified.                                                                                                                                              |
| Unknown  | Evidence is insufficient to classify safely. Use this when key payload, target, recipient, chain, or source data is unavailable.                                      | Missing calldata; unverified target contract; inaccessible proposal; no reliable source for proposer identity; conflicting source data.                                                                                                                                         |

Do not mark a proposal Low merely because no exploit is obvious. If the executable payload is
unavailable or undecoded and the proposal is executable, use Unknown or higher depending on
potential impact.

## Analysis workflow

### 1. Scope the proposal

Identify:

- DAO, chain, proposal ID, source links, and voting/execution status.
- Whether the proposal is executable onchain, offchain signaling only, or tied to a multisig/manual
  implementation.
- Who can execute it and when: governor, timelock, multisig, bridge executor, foundation, delegate,
  or third-party relayer.
- Claimed intent in the proposal body.

Security questions:

- Is the proposal text complete enough to explain the executable actions?
- Is the proposal urgent or using an emergency path?
- Is there a timelock or post-vote cancellation path if issues are found?

### 2. Normalize every proposed action

Create a table of all actions before judging risk. For each action capture:

- Action index/order.
- Target address and target name if known.
- Function name and decoded parameters.
- Native ETH/token value sent.
- Token contract, amount, decimals, and USD estimate when relevant.
- Recipient/beneficiary address and known identity.
- Operation type (`call`, `delegatecall`, upgrade, role grant/revoke, ownership transfer, parameter
  change, bridge/message send).
- Whether target contract source/ABI is verified.
- Evidence link for the decoded action.

Red flags:

- Hidden extra actions not mentioned in the proposal text.
- `delegatecall`, arbitrary executor modules, multicalls, fallback calls, or raw calldata that
  cannot be decoded.
- Calls to newly deployed, unverified, proxy, or upgradeable contracts without clear rationale.
- Ordering that grants permission first and then uses it for unrelated actions.

### 3. Check token, ETH, and treasury movement

For each transfer or spend:

- Verify token address, symbol, decimals, amount, and recipient.
- Compare amount against proposal text, budget request, prior grants, and DAO treasury size when
  possible.
- Check whether recipient is a known multisig, vendor, contributor, bridge, escrow, or unknown EOA.
- Check whether the recipient address exactly matches the address in official docs/forum posts.
- Look for approvals, unlimited allowances, sweeps, rescue functions, or transfers of
  LP/NFT/governance tokens that may imply control.

Red flags:

- Amount in calldata differs from prose, especially by decimal-place errors.
- Recipient is an unknown EOA, newly created address, address with mixer/exploit history, or address
  not listed in the proposal.
- Unlimited token approvals or allowance changes to untrusted spenders.
- Transfers of governance tokens, LP positions, vesting ownership, bridge escrow assets, or
  timelock-controlled assets.
- Native ETH value attached to a call that is not documented.

### 4. Decode contract calls and permissions

For each non-transfer call, determine what power it changes or exercises:

- Governor/timelock settings: voting delay, voting period, proposal threshold, quorum, veto,
  guardian, cancellation, execution delay.
- Access control: `grantRole`, `revokeRole`, `setPendingAdmin`, `acceptAdmin`, `transferOwnership`,
  `setOwner`, `setGuardian`, `setManager`.
- Upgradeability: proxy admin changes, implementation upgrades, beacon upgrades, diamond cuts,
  module installs, plugin changes.
- Treasury controls: spender approvals, payment streams, vesting admin, safe module/guard changes,
  bridge controller changes.
- Oracle/risk parameters: price feed, collateral factor, liquidation threshold, debt ceiling,
  interest rate model, pause flags.
- Cross-chain controls: bridge executor, messenger target, remote chain ID, aliased sender,
  retryable ticket, payload hash.

Red flags:

- Admin/owner/upgrader role moves to an unknown address or contract.
- Proposal disables timelock, veto, pause, guardian, quorum, or other safety controls without a
  strong reason.
- Upgrade target source code is unverified, new, unaudited, or not linked in the proposal.
- A parameter change creates obvious insolvency, oracle manipulation, liquidation, governance
  capture, or censorship risk.
- Cross-chain payload cannot be mapped to its remote execution effects.

### 5. Compare proposal text with executable reality

Explicitly check whether the proposal's human-readable description matches the executable actions.

Classify each mismatch:

- Benign omission: minor implementation detail, no added authority or value movement.
- Material omission: relevant security or treasury effect omitted from prose.
- Contradiction: executable action differs from or reverses the stated intent.
- Undecodable: cannot determine whether it matches.

Escalate severity when a mismatch affects funds, permissions, upgrades, vote mechanics, or execution
controls.

### 6. Assess proposer identity and reputation

Evaluate proposer risk without overclaiming. Use identity evidence, not vibes.

Check:

- Address age, ENS/profile, delegate page, forum account, and prior proposal history.
- Whether the proposer is a known delegate, core team, foundation, service provider, multisig, or
  new/unknown account.
- Prior successful proposals and whether they were controversial, canceled, failed, or flagged.
- Forum discussion quality: did the proposer answer technical questions and provide
  addresses/calldata?
- Any obvious impersonation: similar ENS/name, newly registered domain, mismatched social links,
  copied proposal text.

Red flags:

- New proposer with no history submitting high-impact executable actions.
- Proposer/sponsor identity differs across forum, Snapshot, Tally, and execution payload.
- Proposal uses urgency, vague threats, or social pressure to reduce review time.
- Linked docs or domains are newly created, unofficial, or typo-squatted.

### 7. Check governance process anomalies

Analyze whether the process itself increases risk:

- Proposal posted without normal forum temperature check, RFC, audit, or review stage.
- Short voting window, low participation, vote ending soon, or unusual execution timing.
- Quorum barely reached through late whale votes, self-delegation, flash-loaned voting power, or
  vote buying allegations.
- Proposal bundles unrelated actions, making safe parts inseparable from risky parts.
- Proposal uses emergency powers, optimistic governance, veto bypass, or multisig execution outside
  normal process.
- Changes were edited after discussion without clear changelog.
- Same or similar proposal was previously rejected/canceled but reintroduced with less scrutiny.

Process anomalies usually raise risk by one level when paired with sensitive executable actions.

### 8. Assess execution and operational risk

Even non-malicious proposals can be dangerous if execution is brittle.

Check:

- Whether simulation succeeds at the expected block and chain.
- Whether target contracts are paused, deprecated, migrated, or already changed.
- Whether action ordering creates temporary unsafe states.
- Whether slippage, oracle freshness, bridge finality, or cross-chain replay can affect outcome.
- Whether execution depends on offchain work by a multisig, foundation, service provider, or bridge
  relayer.
- Whether rollback is possible and who controls it.

Red flags:

- Simulation fails or cannot be run for an executable high-impact proposal.
- Proposal assumes balances, roles, or contract state that may not hold at execution.
- Cross-chain execution creates delayed or partially applied state.
- No rollback path for core upgrades or permission transfers.

### 9. Handle uncertainty explicitly

When evidence is missing, do not fill gaps with confident language. State what is unknown, why it
matters, and how to resolve it.

Use uncertainty categories:

- Missing data: proposal/payload/source unavailable.
- Undecoded payload: calldata, ABI, proxy implementation, or cross-chain message unknown.
- Identity uncertainty: proposer or recipient cannot be linked to a trusted entity.
- State uncertainty: current balances, roles, or simulation result not verified.
- Intent uncertainty: action is powerful but rationale may be legitimate.

If uncertainty affects core funds or permissions, recommend delaying support until the uncertainty
is resolved.

## Finding checklist

Use this checklist to ensure coverage. A final analysis does not need to show every checklist item,
but the answer should reflect that each category was considered.

- [ ] Proposal text and source links reviewed.
- [ ] Executable actions identified, decoded, and compared with prose.
- [ ] Token/native value amounts, decimals, recipients, and allowances checked.
- [ ] Contract targets, ABIs, source verification, proxies, and upgrades checked.
- [ ] Permissions, ownership, roles, timelocks, guardians, and governance settings checked.
- [ ] Proposer/sponsor identity, reputation, and prior activity checked.
- [ ] Voting status, deadlines, quorum, vote concentration, and process path checked.
- [ ] Execution/simulation, cross-chain effects, ordering, rollback, and operational dependencies
      checked.
- [ ] Unknowns, assumptions, and evidence limits documented.
- [ ] Recommended user action is concrete and proportional to the risk.

## Final output format

Use this structure for user-facing analysis. Keep it readable, but do not omit required sections.
Render it as normal Markdown: required fields, headings, tables, and bullets must start at column 0
(except intentionally nested bullets). Do not indent the whole response or analysis block by four
spaces, because that turns the output into a Markdown code block and hides the required structure.

```text
## Governance proposal security analysis: <proposal title or ID>

Overall risk: <Critical | High | Medium | Low | Info | Unknown>
Confidence: <High | Medium | Low>
Recommendation: <support / oppose / abstain / wait for clarification / escalate to security review / do not execute yet>

### Bottom line

<2-4 sentences explaining the main risk judgment in plain language. Mention the highest-impact finding and the most important uncertainty.>

### Risk summary

- Highest-risk issue: <one-line summary or "none identified">
- Sensitive effects: <fund transfers / approvals / role grants / upgrades / governance setting changes / none found / not verified>
- Main uncertainty: <most important missing or undecoded evidence>
- Recommended posture: <support / oppose / abstain / wait / escalate, with one short reason>

### Proposal and evidence reviewed

- DAO: <name>
- Chain / governance system: <chain, governor, Snapshot/Tally/Agora/forum/etc.>
- Proposal status: <draft/active/passed/queued/executed/unknown>
- Sources:
  - <source title>: <URL>
- Key assumption(s): <assumptions needed because evidence is incomplete>

### Executable actions checked

| #   | Target         | Function / action  | Value / token amount | Recipient / beneficiary | Risk note    |
| --- | -------------- | ------------------ | -------------------- | ----------------------- | ------------ |
| 1   | <address/name> | <decoded function> | <amount or none>     | <recipient or none>     | <short note> |

If no executable actions exist or they could not be found, say so explicitly and explain how that affects risk.

### Findings

#### <Severity>: <finding title>

- Evidence: <specific source, calldata, address, amount, vote/process fact, or quote>
- Why it matters: <security impact or user impact>
- Affected action(s): <action index, contract, recipient, role, or process step>
- Confidence: <High | Medium | Low>
- Recommended follow-up: <specific verification or mitigation>

### Funds, recipients, and permissions

<Concise summary of asset movement, recipients, approvals, role grants, ownership changes, upgrades, and governance setting changes. Include "none found" only if actually checked.>

### Proposer and process review

<Identity/reputation notes, proposal history, forum discussion, vote timing, quorum, anomalies, or "not verified" if unavailable.>

### Uncertainties and assumptions

- <Unknown or assumption, why it matters, and how to resolve it>

### Recommended user actions

- <Vote/abstain/wait/escalate action>
- <Questions to ask proposer or DAO security council>
- <Execution/timelock monitoring action if relevant>
```

Required sections are: `Overall risk`, `Confidence`, `Recommendation`, `Bottom line`,
`Risk summary`, `Proposal and evidence reviewed`, `Executable actions checked`, `Findings`,
`Uncertainties and assumptions`, and `Recommended user actions`.

## Examples and local validation

Use the synthetic examples in [examples/](examples/) to understand the expected shape of a completed
analysis and to regression-check future edits:

- [benign-operational-budget.md](examples/benign-operational-budget.md) shows a low-risk operational
  transfer where decoded actions, amount, recipient, proposer history, and process context match the
  proposal text.
- [risky-treasury-drain-and-admin-grant.md](examples/risky-treasury-drain-and-admin-grant.md) shows
  a critical-risk payload with a malicious or contradictory action, incorrect amount, suspicious
  recipient, suspicious proposer, and dangerous permission grant.

Run the deterministic local validator after editing this skill or its examples:

```bash
python3 .github/scripts/validate-dao-governance-security.py
```

The validator checks that this file is loadable as a skill, the required final output sections are
still present, and both examples follow the structured analysis format.

## Recommendation rules

Map the analysis to user action clearly:

- Critical: Recommend opposing, canceling, vetoing, or halting execution. Escalate immediately to
  DAO security contacts, delegates, guardians, or the timelock/multisig operators. Provide the
  concrete evidence that justifies urgency.
- High: Recommend waiting, opposing, or requiring security review before support/execution. Ask for
  decoded payload, audits, simulations, recipient verification, or narrowed permissions.
- Medium: Recommend conditional support only after specified clarifications or mitigations. Monitor
  execution and ask targeted questions.
- Low: Support may be reasonable from a security perspective, but still note non-security governance
  or financial considerations that were out of scope.
- Info: No security judgment needed; explain the informational context.
- Unknown: Do not recommend support as "safe". Recommend waiting for missing data, decoding
  payloads, verifying identities, or getting a trusted review.

## Common pitfalls

1. **Trusting prose over calldata.** Always decode and compare executable actions when available.
2. **Ignoring token decimals.** A decimal mistake can turn a small payment into a massive transfer
   or make an amount appear harmless.
3. **Treating known proposer identity as proof of safety.** Reputable proposers can make mistakes,
   be compromised, or submit bundled actions they do not fully understand.
4. **Calling a proposal safe when payloads are missing.** Missing executable details should lower
   confidence and often produce Unknown risk.
5. **Missing permissions hidden in operational actions.** Treasury transfers are obvious; role
   grants, Safe modules, proxy admins, bridge executors, or oracle parameter changes can be more
   dangerous.
6. **Overstating malicious intent.** Say "the action would allow X" or "this is inconsistent with
   the proposal text" unless evidence supports intent.
7. **Forgetting execution context.** A passed offchain Snapshot may still require multisig
   execution; an onchain proposal may have a timelock where action is still possible.
8. **Ignoring cross-chain effects.** Governance payloads may execute on another chain through
   bridge/messenger contracts, so local calldata is not always the whole effect.
9. **Indenting the final analysis as a code block.** The required fields, headings, tables, and
   bullets must render as Markdown. Do not prefix every line with four spaces when generating or
   batching analyses.

## Verification checklist before answering

- [ ] I can identify the proposal, DAO, status, and source links I used.
- [ ] I decoded or explicitly could not decode the executable actions.
- [ ] I checked asset amounts, recipients, permissions, upgrades, and governance settings.
- [ ] I compared executable reality with proposal text.
- [ ] I considered proposer reputation and process anomalies without making unsupported accusations.
- [ ] I assigned severity using the definitions above.
- [ ] I separated evidence, assumptions, and unknowns.
- [ ] I gave concrete recommended user actions, not just a vague risk label.
