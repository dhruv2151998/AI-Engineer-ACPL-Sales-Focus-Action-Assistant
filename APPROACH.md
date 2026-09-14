# Approach

Links: [README](./README.md) · [ARTEFACT](./ARTEFACT.md) · [AI usage log](./ai_log.md)

## A. Problem decomposition
Implemented question categories: sales value/units by brand/region/month;
target achievement %; stockout incidence; promotion presence. Implemented
action categories: supply-constraint escalation, promo-effectiveness
review, and external-cause flagging, per the 8 playbook rules (`DataSet/action_playbook.xlsx`, parsed by `scripts/parse_playbook.py`).
Deliberately not built: multi-brand/multi-region batch queries in one
call, arbitrary free-text date ranges beyond month/quarter, and any
notify/execute action (all actions are returned as data only, per contract).
These cuts match how the team actually works week-to-week: one brand or
region at a time, monthly cadence, human-approved actions.

## B. System design
FastAPI service (`src/service/main.py`) calling Groq's Llama 3.1 8B
Instant via the OpenAI-compatible API for two narrow LLM tasks only:
(1) structured intent extraction from the question, (2) evidence-
constrained answer phrasing with an explicit premise-validity check
(`src/service/ask.py`). Everything else — entity validation against
`dim_sku`/`dim_geo`, the SQL aggregation, playbook rule matching, and the
approval gate — is deterministic Python/SQL, never the model's judgment
(`scripts/prepare_data.py`, `scripts/parse_playbook.py`). Failure path:
unresolved entity, unsupported metric, zero query rows, or a false premise
all short-circuit to NO_ANSWER before any answer is generated.

## C. Data & grounding
7 CSVs + the playbook loaded into SQLite (`data/warehouse.db`) via
`scripts/prepare_data.py`, one reproducible command. Cross-source
mismatches (region casing/suffix variants, column-name differences,
date-format differences, sales-vs-target grain mismatch) identified in
`docs/data_profile.md` and resolved in code, logged line-by-line in
`docs/mismatches.md` — source files are never edited. Supporting documents
loaded as tagged text (`scripts/load_documents.py`); each evidence array
is built directly from deterministic query results, and every action
carries its `rule_id` straight from the parsed playbook table.

## D. Actions & approval
An action is a playbook rule whose condition evaluates true against
real, computed findings (achievement %, stockout days, promotion uplift)
for the requested scope — never an LLM-generated suggestion. Approval
gating (`RECOMMENDED` vs `PENDING_APPROVAL`) is read directly from the
playbook's `needs_approval` column. The service performs no side effects
in either state — nothing is ever notified or executed, matching the
contract's requirement that anything which would act stays pending.

## E. Operations
`cost_usd` is computed from real token usage returned by Groq's API
(`usage.prompt_tokens`/`completion_tokens`) times published per-token
rates ($0.05/1M input, $0.08/1M output for Llama 3.1 8B Instant).
`latency_ms` wraps the full request handler with `time.perf_counter()`.
Accuracy was measured via a hand-run guardrail test set (see ARTEFACT.md)
covering answerable, unknown-entity, false-premise, and injection cases.

## F. Trade-offs
Chose a small/fast/cheap Groq model over a larger reasoning model —
trades some nuance for latency/cost predictability. Chose keyword-tagged
document lookup over embedding search — trades recall on paraphrased
document queries for zero added build time/cost. Given a ~2-hour build
window, the evaluation set is small (single-digit test count) rather
than a large automated suite — trades statistical confidence for meeting
the deadline; this is the top item to expand with more time. SQLite over
a hosted DB — irrelevant concurrency trade-off since all data is read-only.