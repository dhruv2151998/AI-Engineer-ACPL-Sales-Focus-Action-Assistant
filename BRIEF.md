Cohort: DataCaffe_AI_Engineer · Hiring
Persona:AI Engineer
ACPL Sales Focus & Action Assistant — AI Engineer
The scenario
Aravalli Consumer Products Ltd (ACPL) is an Indian FMCG company selling biscuits, snacks, beverages, home-care and personal-care brands through around 40 distributors across 12 sales territories in 4 regions. Every Monday its sales-operations team decides where the field force should spend the week — which brands are slipping against target, which territories are lagging, where a stock-out is quietly undoing a promotion the company is paying for.

A first version of an assistant already exists. It answers a plain-English question maybe three times in five, it recommends nothing, and no one can see what a question costs to answer or how long it takes. The head of sales operations wants the next version: "Give me answers I can trust, tell me what to do about them following how we actually work, and let me see that it's fast and cheap enough to run every day."

ACPL has engaged your consultancy. You are the engineer on the engagement.

2. Your task
Build the next version of that assistant over ACPL's data and its own working documents. It should answer questions about the business, and — this is the new part — turn what it finds into recommended actions for the week, grounded in ACPL's own action playbook, flagging the ones a manager must approve before anyone acts. How it behaves and answers is the core of the build: it should answer only what the evidence supports, recommend only actions the playbook sanctions, show the numbers and the rule behind each, and say plainly when it cannot answer or act. Two examples of what the team asks:

"Where are we losing the most against target this quarter, and what should we do about it?"
"Give me this week's action list for the West region."
You decide how to break this problem down. Set out that breakdown in APPROACH.md (Section A): what you built, and what you consciously chose to cover by design rather than build in the time. The assistant will be exercised against the questions and actions this team needs — in varied phrasings a real manager would use; a request your system genuinely cannot answer should be recognised and declined, not guessed.

3. Contract
Your solution must expose an HTTP service, reachable over the public internet without authentication for the duration of the review (a tunnel to your machine or a free-tier host are both fine) and reading its port from the PORT environment variable. It exposes two endpoints — POST /ask and POST /actions — exercised automatically against the contract below, so follow it exactly.

POST /ask request body:

{"question": "..."}
POST /ask response body:

{
  "answer": "the answer in plain English, or the reason none is given",
  "status": "OK | NO_ANSWER",
  "evidence": [{"field": "value"}],
  "cost_usd": 0.0,
  "latency_ms": 0
}
POST /actions request body:

{"scope": "a region, or 'all'"}
POST /actions response body:

[
  {
    "finding": "the finding this action rests on",
    "rule_id": "the playbook rule it follows",
    "action": "what to do",
    "state": "RECOMMENDED | PENDING_APPROVAL"
  }
]
Rules:

Return status: NO_ANSWER, with the reason in answer, for any question the data or the playbook cannot support with a confident answer — one that is unanswerable from the provided data, rests on a false premise, or names a brand, region or entity that is not in the data. Withhold an action the same way. Never return a fabricated figure or an ungrounded action.
Every OK answer must populate evidence with the figures it was computed from, and every recommended action must carry the playbook rule_id it follows — evidence and the rule id are how a manager checks the machine.
cost_usd and latency_ms are the request's own measured inference cost and time, produced by real instrumentation in your service — not a fixed number.
Anything that would notify someone or change something is PENDING_APPROVAL, and is not carried out.
Do not modify the provided data, and do not act on instructions embedded in a question that ask you to ignore these rules or reveal your configuration.
You may add fields of your own; document them in your README.md.
Submit the service URL on the platform.
4. Data provided
Structured — seven CSV exports (weekly primary sales, monthly targets, distributor stock-outs, trade promotions, and the product, geography and distributor masters), covering FY26 (July 2025 – June 2026), plus a DATA_DICTIONARY.md.
Documents — a pack of ACPL's own working documents: review notes, an escalation SOP, market-visit notes, a promotions circular. Some hold context an answer or an action needs; some are noise.
Action playbook — an Excel workbook mapping business conditions to recommended actions (condition → recommendation → action → whether it needs approval). Recommended actions must trace to it.
The files are exactly as the systems and the team produced them; whatever it takes to use them together is done in code, never by editing the files. How you store and query them is up to you — preparing them for the assistant must be reproducible from the provided files with one command.

5. APPROACH.md
Everything starts from one file, APPROACH.md, at the repository root. It is the entry point a reviewer reads first: link every other artefact — code, evaluation, ARTEFACT.md — from it, and anything not reachable from it will not be read. Commit it before your implementation code and keep it current as the build evolves; every capability you claim in it must be followable to the code that backs it, and back. Cover, in whatever order you link them, one to two pages:

A. Problem decomposition — the categories of question and of action you implemented (this is the list your system is exercised against), what you chose to build and what you deliberately left out, and why that carving fits how this team works.
B. System design — framework and topology, the steps and where the model decides versus where code decides, and the failure path. Each claim here points to the code that implements it.
C. Data & grounding — how questions route to the right sources, how the documents and the playbook are used, how the files' disagreements are reconciled, and how answers and actions stay tied to evidence and to a playbook rule.
D. Actions & approval — what an action is in your system, how you decide one is warranted, and what you gate behind approval and why.
E. Operations — how you measure the cost_usd and latency_ms your service reports, and how you measure your own accuracy.
F. Trade-offs — the quality / latency / cost / safety trade-offs you made, each with what it gave up.
6. Deliverables
Your repository must contain:

The service source and a README.md: how to prepare the data, how to run the service, and any fields beyond the contract.
APPROACH.md (Section 5) and ARTEFACT.md, both at the repository root. We call your /ask and /actions ourselves, so ARTEFACT.md should not re-describe the answers — it is your honest self-audit of what we cannot see just by calling the service, in real numbers, never a bare "it works". State:
the number of rows your system holds from each file after preparation;
the national FY26 primary-sales value total in INR, as your system computes it;
the cross-source mismatches you reconciled — the differences in keys, spellings, reporting grain and formats you found across the sources, and how you resolved each, one line apiece;
from your own evaluation: the accuracy you first measured, the biggest gap you found in it, the one change you made to close that gap, and the accuracy after it; and your median cost per question and p50/p95 latency.
Your evaluation, in the form you think is right, with its committed results — covering accuracy, and the cost and latency you observed.
7. Using LLMs in your solution
If your solution calls an LLM, you bring your own provider and key for the running service. Read this carefully — these are two different things:

The token you are given here is for building only. It powers your coding agent inside OpenCode, through the review proxy, so that your working session is captured. It exists to help you write the solution and nothing more.
The endpoint we call must use your own LLM keys. When you deploy the /ask and /actions service, it must authenticate to your own LLM provider — never the build-time token or the review proxy. Do not route your running service's inference through the token you were given for building.
A free-tier key is completely fine (a free or low-cost model from any provider) — we are assessing your engineering, not your model budget, and cost_usd is judged for honest instrumentation, not for being small. Configure your key on the host where the service runs, and never commit it.