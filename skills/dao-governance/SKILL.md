---
name: dao-governance
description: Use when users ask DAO research questions. Answer with Degov Agent API data first, then use web search when API coverage is insufficient.
---

# DAO Governance Skill

Use this skill to answer DAO governance questions with Degov Agent API data first, then fall back to web search only when API coverage is insufficient.

## Setup

Default managed wallet path:
- `~/.agents/state/dao-governance/wallet.json`

Initialize the local wallet:

```bash
cd skills/dao-governance/scripts
pnpm install
export DEGOV_AGENT_WALLET_PASSPHRASE="choose-a-strong-passphrase"
pnpm exec tsx degov-client.ts wallet init
pnpm exec tsx degov-client.ts wallet address
```

Then fund that Base address with USDC.

Optional API override:

```bash
export DEGOV_AGENT_API_BASE_URL="http://127.0.0.1:3310"
```

## Research workflow

1. Read the user question and infer what they really want.
2. Identify the likely DAO or DAO group first.
3. Choose the smallest useful set of API endpoints.
4. Batch the API queries, gather all results, then synthesize them.
5. Follow links from the API data when you need deeper context.
6. Use web search only when the API or linked materials are not enough.

### Query planning for vague questions

Users often ask broad or fuzzy questions.
Do not answer too early.

First decide:
- which DAO or DAO family the user is probably asking about
- whether they want discovery, recent activity, a DAO summary, or one specific item
- what time range is implied

Examples:
- "What has Spark been doing lately?"
  Infer DAO: `spark`
  Likely endpoints: `brief spark`, `activity --dao spark`, maybe `freshness`

- "What are the biggest DAO governance stories this week?"
  Infer DAO scope: multi-DAO
  Likely endpoints: `daos`, `activity --hours 168 --limit ...`, then `brief` for the most important DAOs

- "Can you explain this ENS proposal?"
  Infer DAO: `ens`
  Likely endpoints: `item ...` if an ID is given, otherwise `activity --dao ens` and `brief ens`

### Endpoint selection rules

Use the API intentionally:
- `daos`: discover which DAOs exist in coverage
- `activity`: scan recent actions across one DAO or many DAOs
- `brief <dao-id>`: get compact context before writing the answer
- `item <proposal|forum_topic> <external-id>`: drill into one proposal or forum topic
- `freshness`: check whether the data is recent enough to trust

### Batch retrieval rule

When a question needs more than one API call:
- decide the query plan first
- run the needed API calls as a batch
- collect all results
- only then write the answer

Do not stream raw intermediate payloads to the user.

### Source follow-up rule

Degov Agent API is the first layer, not the last layer.
Its results often include source URLs.

When those URLs are important to the answer:
- open or search the linked forum/proposal materials
- confirm the meaning of the proposal or discussion
- use the source text to improve the explanation

If the API results are missing, stale, or too shallow:
- use web search
- prefer official DAO forums, Snapshot pages, governance portals, and official announcements
- say clearly when you are using the web in addition to Degov Agent API

## Answer style

The API is a data source, not the final user experience.
Do not give users raw JSON unless they explicitly ask for it.

Write as if the user is a middle school student:
- use simple words
- explain DAO and governance ideas in plain language
- avoid dense technical wording unless needed
- when you must use a technical term, explain it in one short sentence

Make the answer detailed enough to be useful:
- one-line answers are not acceptable
- explain what happened, why it matters, and which DAO it affects
- include timeframe when relevant

Use bullets carefully:
- bullets are good for listing proposals, actions, or takeaways
- do not turn the whole answer into a long wall of bullets
- prefer a short opening paragraph, then a few clear bullets, then a short wrap-up if helpful

## Response format

For normal research questions, aim for this structure:

1. A short plain-language summary paragraph.
2. `Key points` with 3-5 bullets when there are several findings.
3. A short `Why it matters` explanation when the topic is complex.
4. A brief source note saying whether the answer came from Degov Agent API, the web, or both.

Good example qualities:
- easy to read
- not too short
- not overloaded with bullets
- clear enough for a younger student to follow

Avoid:
- raw API payload dumps
- unexplained abbreviations
- overly dry or robotic wording
- giant bullet lists with no narrative

## Example workflows

### Example 1: vague multi-DAO question

User:
"What are the most important DAO governance updates this week?"

Good workflow:
1. Treat this as a multi-DAO request.
2. Query `activity` for the last 7 days.
3. Identify the most active or important DAOs from that result.
4. Query `brief` for the top DAOs to add context.
5. If a proposal looks important, follow the linked source material.
6. Write a plain-language summary instead of showing the raw API output.

### Example 2: vague single-DAO question

User:
"What has ENS been doing recently?"

Good workflow:
1. Infer the DAO is `ens`.
2. Query `activity --dao ens`.
3. Query `brief ens`.
4. If one proposal or forum post matters a lot, inspect the linked material.
5. Explain the recent actions in simple language.

### Example 3: specific item question

User:
"Can you explain proposal X to me?"

Good workflow:
1. Find the item ID or infer it from recent DAO activity.
2. Query `item`.
3. Read linked source material if the API summary is too thin.
4. Explain:
   what the proposal wants
   who it affects
   why people may support or oppose it
   what happens next

## Example answer style

Example:

"Here is the simple version: ENS has mainly been working on one budget-related proposal and one governance discussion recently. The proposal is about how money should be used, while the discussion is about how ENS should organize itself. So the big idea is that ENS is not just talking about technical upgrades, it is also deciding how to manage its community and resources.

Key points:
- One recent proposal focuses on funding work inside the ENS ecosystem.
- A governance discussion is looking at rules or structure, not just day-to-day operations.
- These topics matter because they affect how ENS makes decisions in the future.

Why it matters:
If a DAO changes how it spends money or how it makes decisions, that can shape the whole project for a long time.

Source note:
This answer is based mainly on Degov Agent API data, plus follow-up reading of the linked governance pages when needed."

## More answer examples

### Example A: weekly roundup

User:
"What were the biggest DAO governance updates this week?"

Good answer shape:

"Here is the simple version: this week, the biggest DAO stories were mostly about spending plans, voting decisions, and rule changes. The most important updates were not random small chats. They were the kinds of decisions that can change how a DAO uses money or makes future choices.

Key points:
- One DAO focused on a budget or funding proposal.
- Another DAO had a governance discussion about rules, structure, or voting.
- A few DAOs were active, but only some updates looked important enough to matter beyond one small group.

Why it matters:
When a DAO changes its budget or decision rules, that can affect the whole project, not just one proposal.

Source note:
This summary is based mainly on Degov Agent API activity data, plus linked governance pages when needed."

### Example B: single DAO recent activity

User:
"What has Arbitrum been doing lately?"

Good answer shape:

"Arbitrum has recently been focused on governance work rather than just technical development. In simple terms, that means people in the community are talking about how decisions should be made, what should get support, and what priorities matter most right now.

Key points:
- There has been recent proposal or forum activity connected to Arbitrum governance.
- The discussion is more about direction and decision-making than just routine updates.
- The most important items are the ones that could affect funding, rules, or future planning.

Why it matters:
For a DAO like Arbitrum, governance activity helps show where the community wants the project to go next.

Source note:
This answer is based on Degov Agent API DAO brief and recent activity data, with source-link follow-up when needed."

### Example C: explain one proposal simply

User:
"Can you explain this proposal like I'm new to crypto?"

Good answer shape:

"Yes. The simple version is that this proposal is a plan the community is being asked to approve or reject. It usually asks for one of three things: money, a rule change, or a change in project priorities.

Key points:
- What the proposal wants
- Who would be affected if it passes
- Why supporters think it is useful
- Why critics may be unsure

Why it matters:
DAO proposals are important because they are one of the main ways a community makes real decisions.

Source note:
This explanation should use Degov Agent API item data first, then the linked proposal page for extra context."

### Example D: compare two DAOs

User:
"How are ENS and Uniswap different right now?"

Good answer shape:

"ENS and Uniswap may both be DAOs, but they can be busy with very different kinds of decisions. One may be talking more about governance structure or community coordination, while the other may be more focused on treasury use, protocol direction, or incentives.

Key points:
- What ENS has been discussing recently
- What Uniswap has been discussing recently
- One clear difference in focus
- One similarity in how both communities make decisions

Why it matters:
Comparing two DAOs helps users understand that not all governance activity means the same thing.

Source note:
Use Degov Agent API activity plus DAO briefs for both DAOs, then follow source links if a comparison needs more detail."

### Example E: what should I pay attention to

User:
"What should I pay attention to in DAO governance today?"

Good answer shape:

"The best things to pay attention to are the updates that can actually change how a DAO works. In simple terms, that usually means budget proposals, rule changes, major votes, or discussions that could lead to new plans.

Key points:
- Look for proposals about money or treasury use.
- Look for changes to voting rules or governance structure.
- Look for repeated discussion around the same issue, because that can signal a bigger shift.
- Ignore tiny updates unless they connect to a larger decision.

Why it matters:
The goal is not to read everything. The goal is to notice the few updates that can shape the project in a big way.

Source note:
Use recent Degov Agent API activity first, then linked governance pages for confirmation."

### Example F: when the API is not enough

User:
"Can you tell me the full story behind this governance fight?"

Good answer shape:

"I can explain the main issue, but the API summary alone may not be enough for the full story. To answer well, I should first use Degov Agent API to find the key proposal or forum thread, then read the linked source material to understand the arguments on both sides.

Key points:
- Start with the API to find the important item.
- Use the linked forum or proposal page to understand the dispute.
- Explain both sides in simple language.
- Tell the user clearly when the answer uses web or source-page follow-up.

Source note:
This kind of answer should usually combine Degov Agent API with linked source reading or web research."

### Example G: short answer that is still useful

User:
"Is this proposal important?"

Good answer shape:

"Yes, it looks important if it changes money, voting rules, or long-term project direction. A proposal is usually less important if it only covers a small operational detail.

The main thing to check is:
- does it change spending
- does it change governance rules
- does it affect many community members

If the answer to one or more of those is yes, then it is probably worth paying attention to.

Source note:
Judge this using Degov Agent API item data first, then the linked source page if needed."

## Answer checklist

Before replying, quickly check:

1. Did I figure out which DAO or DAO group the user probably means?
2. Did I choose the right API endpoints and gather enough results before answering?
3. Did I use linked source materials or web follow-up when the API alone was too thin?
4. Did I explain the answer in simple language instead of copying raw API output?
5. Is the answer detailed enough to be useful, not just one line?
6. Did I avoid too many bullets and keep the structure easy to read?
7. Did I clearly say whether the answer came from Degov Agent API, the web, or both?
8. Did I avoid making up facts, dates, proposal details, or conclusions?

## Commands

```bash
pnpm exec tsx degov-client.ts wallet init
pnpm exec tsx degov-client.ts wallet address
pnpm exec tsx degov-client.ts wallet balance
pnpm exec tsx degov-client.ts budget --usd 1
pnpm exec tsx degov-client.ts daos
pnpm exec tsx degov-client.ts activity --hours 48 --limit 10
pnpm exec tsx degov-client.ts brief ens
pnpm exec tsx degov-client.ts item proposal <id>
pnpm exec tsx degov-client.ts freshness
pnpm exec tsx degov-client.ts health
```

## Guardrails

- Do not ask users to paste private keys.
- Use the local managed wallet for API payments.
- Require a wallet passphrase for encrypted local storage.
- Use `budget` when you need the current API pricing table.
- If the wallet is unfunded, instruct the user to fund the displayed address on Base with USDC.
- Turn API data into a user-friendly explanation instead of pasting raw responses.
- State when information came from Degov Agent API versus the web.
- Do not fabricate governance activity, proposals, or dates.
