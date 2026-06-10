# Example: Critical-risk treasury drain and admin grant

This synthetic example demonstrates how `dao-governance-security` should escalate when a proposal's prose claims a modest payment but decoded actions move a materially different amount to a suspicious recipient and grant dangerous permissions to an unknown address from a new proposer.

## Proposal input

- DAO: ExampleDAO
- Chain / governance system: Ethereum Governor + timelock
- Proposal: `EXD-99`, "Pay final website maintenance invoice"
- Status: queued for execution in 10 hours after a short emergency vote
- Proposer: `0x9999999999999999999999999999999999999999`, new proposer with no prior ExampleDAO proposal history and no verified delegate profile
- Proposal text: pay 25,000 USDC to the known web vendor multisig for completed website maintenance
- Decoded executable actions:
  1. Treasury call sends 2,500,000 USDC to `0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`, an unknown EOA not listed in the forum post or vendor registry
  2. Timelock call grants `DEFAULT_ADMIN_ROLE` on the treasury controller to `0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`, an unverified contract deployed two days ago
- Evidence links: official governance UI, forum post, decoded calldata view, treasury recipient registry, block explorer pages for recipient/proposer

## Expected structured analysis output

```markdown
## Governance proposal security analysis: EXD-99 — Pay final website maintenance invoice

Overall risk: Critical
Confidence: High
Recommendation: oppose / do not execute yet

### Bottom line

The decoded executable payload materially contradicts the proposal text. The proposal claims a 25,000 USDC vendor payment, but action 1 sends 2,500,000 USDC to an unknown EOA, and action 2 grants `DEFAULT_ADMIN_ROLE` over the treasury controller to an unverified recently deployed contract. This should be treated as a potential treasury drain and governance-control compromise unless the DAO security team proves the payload is legitimate before execution.

### Risk summary

- Highest-risk issue: executable actions transfer 100x the stated USDC amount and grant treasury admin control to an unknown contract
- Sensitive effects: large fund transfer, dangerous role grant, suspicious recipient, suspicious new proposer, emergency process
- Main uncertainty: whether the proposer account or payload source was compromised
- Recommended posture: oppose, request cancellation/veto, and escalate to DAO security contacts before timelock execution

### Proposal and evidence reviewed

- DAO: ExampleDAO
- Chain / governance system: Ethereum Governor + timelock
- Proposal status: queued for execution in 10 hours
- Sources:
  - Governance UI: synthetic example link
  - Forum post: synthetic example link
  - Decoded calldata: synthetic example link
  - Treasury recipient registry: synthetic example link
  - Proposer/recipient explorer pages: synthetic example link
- Key assumption(s): the decoded calldata view is complete and corresponds to the queued proposal payload

### Executable actions checked

| #   | Target                         | Function / action                   | Value / token amount | Recipient / beneficiary                                          | Risk note                                                     |
| --- | ------------------------------ | ----------------------------------- | -------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------- |
| 1   | ExampleDAO Treasury            | `transferToken(USDC, to, amt)`      | 2,500,000 USDC       | Unknown EOA `0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`         | Amount is 100x the proposal text and recipient is not listed. |
| 2   | ExampleDAO Treasury Controller | `grantRole(DEFAULT_ADMIN_ROLE, to)` | none                 | Unverified contract `0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb` | Grants dangerous treasury admin permission.                   |

### Findings

#### Critical: USDC amount and recipient contradict the proposal text

- Evidence: proposal text says 25,000 USDC to the web vendor multisig, while decoded action 1 sends 2,500,000 USDC to `0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`.
- Why it matters: this would move 100x the disclosed amount to an address that is not tied to the stated vendor, creating immediate treasury-loss risk.
- Affected action(s): action 1, ExampleDAO Treasury USDC transfer.
- Confidence: High
- Recommended follow-up: ask the governor/timelock operators or security council to cancel or veto before execution and require a corrected payload.

#### Critical: Proposal grants treasury admin authority to an unverified contract

- Evidence: decoded action 2 calls `grantRole(DEFAULT_ADMIN_ROLE, 0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb)` on the treasury controller.
- Why it matters: `DEFAULT_ADMIN_ROLE` can usually grant or revoke other roles and may enable future treasury control beyond this proposal.
- Affected action(s): action 2, Treasury Controller role grant.
- Confidence: High
- Recommended follow-up: do not execute until the target contract source, ownership, role semantics, and necessity are independently verified; cancellation is appropriate if undocumented.

#### High: New proposer and emergency process amplify the payload risk

- Evidence: proposer `0x9999999999999999999999999999999999999999` has no prior ExampleDAO proposal history, and the proposal used a short emergency vote with execution in 10 hours.
- Why it matters: a sensitive payload from an untrusted proposer with limited review time increases the likelihood of social-engineering or compromised-process risk.
- Affected action(s): proposal process and both executable actions.
- Confidence: Medium
- Recommended follow-up: verify proposer identity through official delegate channels and ask why emergency handling was used for a routine invoice.

### Funds, recipients, and permissions

The payload sends 2,500,000 USDC to an unknown EOA instead of the stated 25,000 USDC vendor payment. It also grants `DEFAULT_ADMIN_ROLE` over the treasury controller to an unverified recently deployed contract. No benign interpretation should be accepted without direct confirmation from official DAO security channels and a replacement payload.

### Proposer and process review

The proposer is new, lacks a verified delegate profile, and submitted high-impact executable actions through a shortened emergency process. The recipient and admin-grant beneficiary do not match the forum post or recipient registry in the synthetic evidence. These process and identity anomalies raise the risk of the already-dangerous payload.

### Uncertainties and assumptions

- The example does not prove intent; it proves that the executable effects are inconsistent with the stated invoice payment and could drain funds or compromise treasury permissions.
- The current treasury balance is not included; if the treasury has less than 2,500,000 USDC, execution may fail, but the attempted transfer remains a critical red flag.
- The ownership and code of the admin-grant contract are not verified; this uncertainty increases risk rather than reducing it.

### Recommended user actions

- Oppose the proposal and warn other voters/delegates with the decoded action evidence.
- Escalate immediately to the DAO security council, guardian, vetoer, timelock operators, or multisig signers before the 10-hour execution window closes.
- Request cancellation or veto, plus a corrected proposal that uses the documented vendor multisig, disclosed amount, and no unrelated admin grant.
- Monitor the timelock queue and treasury events for attempted execution or replacement payloads.
```
