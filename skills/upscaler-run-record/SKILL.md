---
name: upscaler-run-record
description: Use when the user asks to create, fill in, progress, complete, or close an Upscaler record instance (`r_*`), or to instantiate one from a record definition (`rd_*`) - audit records, incident records, meeting minutes, management review records, or any multi-task workflow form. Triggers on phrases like "complete record r_…", "create a new incident record", "fill in the audit record", "advance this record", "complete the Findings task", "tick off the tasks on r_…", "close out this record". Owns the whole record flow - task order, per-task form filling, draft-saving with a reviewer note, verification. Agents save drafts only; a human reviews and completes each task in the app. Do NOT use for register entries (`i_*` rows in an `rg_*` - use upscaler-write-entry) or for authoring a NEW record definition (use upscaler-author-asset).
license: MIT
compatibility: Requires Upscaler MCP server (preferred) OR the `upscaler` CLI >= 0.3.0 (`pip install upscaler-cli && upscaler login`); `entry save-draft` does not exist before 0.3.0. Write permission on the record's Organization.
---

# Upscaler record runner

Creates record instances (`r_*`) from an existing record definition (`rd_*`) and drives them through their task flow: fill each task's form, save it as a **draft** with a reviewer note, and verify, in the order the definition's workflow dictates. The record definition is assumed to exist; authoring a new `rd_*` routes to `upscaler-author-asset`.

**Agents never complete tasks.** The agent surface is human-in-the-loop: every task write lands as a DRAFT that a human assignee reviews (the draft banner in the Upscaler app shows your note and prefilled values) and completes themselves. Even when the user says "complete the task", what you can deliver is a draft ready for their one-click completion; say so in your report and never claim a task or record was completed.

This skill shares its **form-filling core** with `upscaler-write-entry`: the same schema-first key resolution, value shapes, and context-derivation rules, defined once in [`../../references/form-filling.md`](../../references/form-filling.md). What this skill adds on top is **record-flow awareness**: tasks, task order, per-task value nesting, and draft-saving.

This skill is **write-capable**. Every mutation goes through a **propose-then-confirm** UX: compose the task's values, show them, wait for confirmation, then save the draft. Never mutate silently. "Sample" / "dummy" / "test" / "demo" in the prompt scopes the *values*, not the *process*: still render the proposal and wait.

## Platform connection (MCP → CLI → setup)

Run the connection-priority probe from [`../../references/upscaler-access.md`](../../references/upscaler-access.md) before any retrieval or mutation:

1. **MCP first:** scan for `upscaler_get_asset`, `upscaler_list`, and `upscaler_manage_entry` (its operations are `create`, `update`, `save_task_draft`, `delete`; `task_id` is required for `save_task_draft` and for record updates). There is no standalone `upscaler_save_task_draft` MCP tool — drafts go through `upscaler_manage_entry`.
2. **CLI fallback:** otherwise use `upscaler --json get …`, `upscaler --json list …`, and `upscaler entry create|update|save-draft|upload-file`. Confirm authentication via `upscaler status`.
3. **Setup prompt:** if neither is available, print the setup message from the shared reference and stop.

Record the chosen tier once per session and stay on it.

## The record model

- An `rd_*` **record definition** holds ordered **task definitions** (`td_*`), each with its own field list. The definition's schema (`get <rd_*> --format schema`) is therefore a per-task list, not one flat field set.
- An `r_*` **record instance** holds one **task instance** (`t_*`) per task definition. Values nest per task: `values.<taskDefinitionId>.<key>`.
- Most records are **sequential**: task N stays locked until task N−1 is completed. A draft save does not advance the flow; respect the definition order when drafting.
- **Task completion is human-only.** There is no agent-facing completion command and no direct "set record status" command. To move a record forward, save a draft on each task (values + a required note) and hand off: the assignee reviews the draft banner in the Upscaler app and completes the task. A record closes only through those human completions.

## When to use

- "Create a new incident record and fill in the first task."
- "Complete record `r_xxx`." / "Tick off the remaining tasks on `r_xxx`." (You draft every remaining task; the human completes them.)
- "Instantiate the Internal Audit record for Q3 and fill the header."
- "Complete the Findings task on the audit record with these results: …"
- "Run a meeting-minutes record for today's ISMS steering meeting."
- "Complete a Supplier Agreement Review / Supplier Monitoring Activity Review record." Supplier reviews are ordinary records here: ground the checklist values in the tenant's own Supplier Due Diligence Policy through the shared derivation pipeline (governing-documents search fallback included), and **perform the review activity itself** (Step 4), including public web research on the supplier and comparison against the previous review.

## When NOT to use

- "Add a row / entry to a register (`rg_*` / `i_*`)." → `upscaler-write-entry`. An `i_*` is a flat register row, not a task-structured record.
- "Draft / author a new record definition or template." → `upscaler-author-asset` (that is authoring an `rd_*`, not running one).
- "What's the status of record X?" (pure lookup, no mutation intended) → `upscaler-ask`.

## Workflow

### 1. Resolve the record: instance, definition, or title

- **Given `r_*`:** fetch it (`upscaler --json get <r_*>` / `upscaler_get_asset`). Read its parent definition from `userRecordDefinitionId` (an `rd_*`), its task instances (`t_*`, each tied to a `td_*`), each task's status, and any values already filled.
- **Given `rd_*`:** you are creating a fresh instance; go to step 2.
- **Given a title** ("the Internal Audit record"): resolve it, MCP `upscaler_search_nodes({query, asset_types: ["record_definition"]})`, CLI `upscaler --json asset find --title "<title>" --type record_definition`. On both tiers `record` means record *instances* (`r_*`), never the definition — use it only when hunting for an existing instance by title. Stop and ask if the lookup returns zero or more than one hit. Determine from context whether the user wants a new instance or an existing one; when unsure, list existing instances with MCP `upscaler_list({type:"entries", definition_id:"<rd_*>"})` or CLI `upscaler --json list entries --definition-id <rd_*>`.

### 2. Read the definition schema and map the flow

`upscaler --json get <rd_*> --format schema` (MCP: `upscaler_get_asset({asset_id, format: ["schema"]})`). This yields each task definition in order with its field list: `key`, `label`, `type`, `required`, options, table columns. Build a small flow map: task order, which tasks are already complete or drafted (for an existing `r_*`), and which task is next.

Keys follow the shared contract: use `fields[].key` verbatim. Canonical seeded definitions often use short label-like machine keys instead of `ff_*`; never assume either style. **One exception:** table fields are written under their **bare** machine key; if a schema reports one with a `values.<td_*>.` prefix (a server defect fixed 2026-07-19), strip the prefix, and if the bare key is then rejected, stop and route the table rows to the web UI (see the shared core's field-resolution rules).

### 3. Derive values from the parent asset and its references

Load [`../../references/form-filling.md`](../../references/form-filling.md) and follow its complete "Deriving values from context" order, including the record-only rule to read earlier completed tasks before drafting a later one. Unresolvable references stay blank and are called out in the proposal. Never invent an `i_*`, member id, or `t_*`/`td_*`.

### 4. Perform the task's documented activity, then draft

Many record tasks capture **evidence of an activity**: a review, a verification, a check. The task's `guidance` text, the definition description, and the governing policy (source 4 of the shared derivation order) say what that activity is. Fill the form with the results of actually performing the activity this session, not with paperwork that assumes it happened:

- If the activity examines sources outside the workspace (a supplier's published terms, DPA, privacy policy, trust or status page, a certification registry, a regulation), fetch those sources now with the available web tools. Cite every external finding with its full URL and retrieval date (`YYYY-MM-DD`). If web access is unavailable in the session, leave the affected fields to the user and say why.
- Use the latest completed sibling instance as the **baseline**: compare today's findings against it and surface what changed (new or lapsed certifications, changed terms, new sub-processors, incidents, ownership changes) in the observation and narrative fields, instead of copying the old answers forward.
- Do not infer from absence. "No public disclosure found at <URL> on <date>" is a finding; "no breaches" is fabrication.
- Findings that warrant new workspace assets (for example a risk to raise in the Risk Register) are proposed separately and routed to `upscaler-write-entry`; never bundle them into the task submission.

### 5. Propose per task, then confirm

Present one proposal table per task: field label, type, proposed value, and the source it was derived from. A draft save does **not** close the task, and partial values are accepted (type/shape validation only; required fields may stay open for the reviewer), so you may stage what you have; call out any fields left blank so the note and the proposal agree. Still wait for explicit confirmation before writing: a draft save notifies the task's assignees.

To preview without writing, use the active tier: **CLI:** `upscaler entry save-draft --task-id <t_*> --note "<summary>" --dry-run` fetches and displays the task fields. **MCP:** there is no mutation dry-run; render the proposal from the record-definition schema already fetched in Step 2 and do not call the write tool until the user confirms.

### 6. Write

**Fresh record:** create it with `title` only, capture the new `r_*` and each created task's `t_*` from the response, then draft task by task. This is the clearest flow because each task gets its own proposal, confirmation, and purpose-written note.

```bash
upscaler --profile <p> entry create --definition-id <rd_*> --data '{"title": "INC-042 - Phishing incident 2026-07-18"}'
```

A create may also carry `taskValues` keyed by task-definition id, which drafts those tasks in record order in one call. It is **not** a completion path: each task is dispatched to `saveTaskDraft`, and a reviewer note is synthesized per task when `data.note` is omitted. Prefer it only when the user has already confirmed every task's values together; a synthesized note is weaker than one you write. Validation stops at the first task that fails, and tasks drafted before it keep their drafts.

```json
{"title": "INC-042 - Phishing incident 2026-07-18",
 "taskValues": {"<td_task1>": {"<key>": "value"}, "<td_task2>": {"<key>": "value"}}}
```

**Draft a task (the common path):** `entry save-draft` stages the values plus a **required `--note`** on the task; the task moves to DRAFT and the assignee finalizes it in the app. The `--entry-id` is auto-detected from the task if omitted.

```bash
upscaler --profile <p> entry save-draft --task-id <t_*> \
  --note "<what was filled in, sources used, what is left open>" \
  --data '{"values": {"<key>": "value"}}'
```

**The note is load-bearing.** It is the reviewer's summary: say what you filled in, where the values came from, and anything left open or uncertain. A meaningful note is required; do not pass boilerplate like "draft".

**MCP:** `upscaler_manage_entry({operation: "save_task_draft", entry_id: "<r_*>", task_id: "<t_*>", data: {values: {...}, note: "<summary>"}})`. Record creation is `upscaler_manage_entry({operation: "create", definition_id: "<rd_*>", data: {title: "..."}})`. For **item entries** (register rows, `upscaler-write-entry` territory) the tools keep their names and the note rides inside the data payload as `data.note`; the same holds for the CLI's REST envelope, where `--note` is folded into `data.note`.

A bare record-level `{"values": {...}}` with no task nesting is rejected; register-style flat payloads do not fit records.

**File-upload fields stage into the draft like any other value**, provided you pass `--task-id`. The CLI reads the task's current values, uploads the bytes, splices the file item in, and sends the result through `saveTaskDraft` (last-writer-wins, so no `expectedVersion` is needed on records). Note `entry upload-file` takes `--path`, not `--file`:

```bash
upscaler --profile <p> entry upload-file --entry-id <r_*> --task-id <t_*> \
  --field "<file field name>" --path ./evidence.pdf

# or fold files and values into one draft save:
upscaler --profile <p> entry update --entry-id <r_*> --task-id <t_*> \
  --data '{"values":{"<key>":"value"}}' --file "<File label>=./evidence.pdf" \
  --note "<summary>"
```

Because a task write replaces the whole values map, the CLI's read-splice-send sequence is what preserves the other fields; do not hand-build a file array from only the new upload. If either tier cannot resolve the file field, stop and ask the user to attach it in the web UI rather than guessing a key.

**Errors an agent may see:**

- `HITL_FINALIZED`: the task was already completed by a human. Leave it unchanged and ask the assignee to make the edit; drafts can only be saved on tasks a human has not completed.
- `TASK_SKIPPED`: the task was skipped by the flow, so it is not a draft target either. Do not try to revive it by drafting; report it as skipped and move to the next open task. (This code is minted by the MCP error envelope; on the CLI the same rejection surfaces as the raw backend error about task status.)
- `HITL_AGENT_COMPLETE_REMOVED`: you called the removed `complete_task` MCP operation. This is the *only* gated mutation: a create with `taskValues` and an update with a `task_id` both route to `saveTaskDraft` and are fine. The error names `save_task_draft`; switch to it and retry as a draft. (The deleted `entry complete-task` CLI command never reaches the server — it fails locally with `No such command 'complete-task'`.)
- `VALIDATION_ERROR`: a value passed the agent-side shape check but the backend rejected it ("Invalid task values"). Treat it exactly like `VALUE_VALIDATION_ERROR`: re-read the schema and fix the offending value shape.

### 7. Verify

**Read the task back from the record JSON.** A draft save writes the values onto the task and flips that task to `DRAFT`, so the plain record read is the verification surface:

```bash
upscaler --profile <p> --json get <r_*>
```

(MCP: `upscaler_get_asset({asset_id:"<r_*>", format:["json"]})`.) Match the `t_*` under `tasks[]`, confirm its `status` shows **DRAFT** (never completed; agents cannot complete), and diff its `values` against the payload you sent. The values are **flat for that task** (`tasks[].values.<key>`), not nested under the task-definition id. Read the record `title` and `status` from the same payload (the record itself stays PENDING until a human completes its tasks). Apply the read-back tolerances from the shared core. Cite the result as `[<record title>](upscaler:<r_*>)`.

**`--draft` is not the draft read.** That flag requests the unpublished working copy of a *definition* (meaningful on an `rd_*` schema read); it never returns a task's staged values. A HITL task draft is read through the record JSON above.

**Do not verify a draft with `list entries --include-values`.** That list reports *committed* values only, so it keeps showing the record's pre-draft state (usually empty) until a human completes the task. Reserve the values-bearing list for records a human has already completed, and never pass `--resolve-labels` with an `rd_*` (the per-task schema has no flat field list, so keys silently come back unrelabelled).

Then report the flow position: which tasks are drafted awaiting review, which tasks a human has completed, and which task is next. State explicitly that the drafts await human review in the Upscaler app; never report a task or the record as completed or closed by you.

## Anti-patterns

- **Treating a record like a register row.** Flat `{"values": {...}}` payloads and writes without a `task_id` are rejected; `--resolve-labels` against an `rd_*` silently does nothing. The task nesting is load-bearing.
- **Claiming completion.** Agents save drafts; humans complete. Never say a task or record "has been completed" after a draft save, and never call a legacy completion surface to force it (it rejects with `HITL_AGENT_COMPLETE_REMOVED`).
- **Boilerplate notes.** The required note is the reviewer's brief. "Draft" or "filled in" wastes the reviewer's one glance; summarize the values, their sources, and the gaps.
- **Reading an empty values list as a failed draft save.** `list entries --include-values` reports *committed* values, which a draft deliberately leaves untouched. Verify with the record JSON (`get <r_*>`, `tasks[].values`); do not re-send the write because the list still looks empty.
- **Skipping ahead in a sequential flow.** Draft tasks in definition order and report the next task, so the human can complete them in sequence; a draft on a later task cannot unlock anything.
- **Assuming `ff_*` keys.** Canonical seeded record definitions frequently use label-like machine keys. Read `fields[].key` per task, verbatim.
- **Inventing `td_*` / `t_*` ids.** Task definition ids come from the `rd_*` schema; task instance ids come from the created record. Never fabricate either.
- **Drafting later tasks blind.** Read the values already stored in earlier tasks first; a record is one narrative, and contradictory tasks read as fabricated evidence.
- **Rolling a periodic review forward without re-performing it.** Copying the previous instance's answers and asserting "unchanged" without fetching the sources is fabricated evidence. Perform the documented activity (Step 4), or leave the field to the user and say what was not checked.
- **Mutating without confirmation, or "sample data" shortcuts.** Same contract as `upscaler-write-entry`: propose, confirm, then write.

## Examples

**User:** "Create a meeting-minutes record for today's ISMS steering committee and fill in the details: chaired by Dana, minutes by me."

**Skill should:** resolve the Meeting Minutes `rd_*` by title; read its schema (2 tasks); resolve Dana and the user against `list members`; propose Task 1 values (title, date `defaultToday`, chair, minute-taker) with sources shown; on confirmation `entry create` with title only, then `entry save-draft --task-id <t_task1> --note "Prefilled attendees and date from the request; agenda left open"` with the Task 1 values; verify via `get <r_*>` (`tasks[]`: Task 1 `status: DRAFT`, values match); report that Task 1 is drafted awaiting review, Task 2 (Agenda & Actions) is next, and offer to draft it.

**User:** "Complete the remaining tasks on `r_abc` with the retro notes I pasted."

**Skill should:** `get r_abc`; find its `rd_*` and per-task status; read already-completed task values for context; map the pasted notes onto the next unlocked task's fields (shared-core value shapes); propose; on confirmation `entry save-draft --entry-id r_abc --task-id <t_*> --note "<summary of what was mapped from the retro notes>" --data '{"values": {...}}'`; verify, then repeat for each remaining task in order, one confirmation each; close by reporting every task is drafted and the assignee completes them in the Upscaler app.

## References

- [`../../references/form-filling.md`](../../references/form-filling.md): the shared form-filling core (key resolution, value shapes, context derivation, read-back tolerances). Load before proposing values.
- [`../../references/upscaler-access.md`](../../references/upscaler-access.md): connection priority, tool/command mapping, auth recovery, citation contract.
