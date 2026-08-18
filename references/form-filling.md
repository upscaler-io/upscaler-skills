# Form-filling core (registers and records)

Shared reference for the write-capable skills that fill Upscaler forms: `upscaler-write-entry` (register entries, `i_*` rows in an `rg_*`) and `upscaler-run-record` (record instances, `r_*` created from an `rd_*`). Load this file before proposing or composing any values payload. The schema is authoritative: use every field's exact `key`, `type`, `required`, `multiple`, `value_format`, options, and table columns.

## The two container shapes

| | Register entry | Record |
| --- | --- | --- |
| Definition | `rg_*` (one flat field list) | `rd_*` (one field list **per task**, `td_*`) |
| Instance | `i_*` | `r_*` (with task instances `t_*`) |
| Values shape | flat: `values.<key>` | flat per task on writes and on `tasks[].values`; the values-bearing **list** reads back nested `values.<taskDefinitionId>.<key>` (completed tasks only) |
| Create payload | `{"values": {...}}` | `{"title": ...}` only, then draft each task separately |
| Update path | `entry update --entry-id i_*` / `upscaler_manage_entry(operation:"update", entry_id)` | per task: `entry save-draft --task-id t_* --note "…"` / `upscaler_manage_entry({operation:"save_task_draft", entry_id, task_id, data:{values, note}})` |

A bare record-level `{"values": {...}}` (no task nesting) is rejected on records. A `taskValues` wrapper on a register entry is equally wrong. Identify the container from the definition prefix first.

**Agent writes never finalize (HITL contract).** Exactly one mutation was removed from the agent surface: `completeTask`. Everything else still works and is simply *rerouted* into a draft. A record `create` may carry `taskValues` keyed by `td_*`, and a record `update` may carry a `task_id`; both are dispatched to `saveTaskDraft`, drafting each task in record order and synthesizing a reviewer note when you omit one. Every such write leaves the task in DRAFT for a human to complete in the Upscaler app. Register entries follow the same spirit through their own mutation, `saveItemDraft` (agents get no `appliedDraftId` or `expectedVersion`, and cannot apply or discard a draft): a create carrying values lands as DRAFT, a title-only create stays PENDING, and an update to a COMPLETED entry is stashed as a pending revision instead of changing live values. Both containers share one lifecycle, `PENDING → DRAFT → COMPLETED`. Never report a task, record, or entry as completed, closed, or live after a write.

Drafts validate loosely on purpose: values are checked for type and shape only, and required fields may stay open, because the required pass belongs to the human at completion. Stage what you have and name the gaps in the note. One exception: a register-entry **create** through `upscaler_manage_entry(operation:"create")` runs the required-field pass fail-closed before creating the item, so a create payload must satisfy every required field even though later draft updates need not.

## Field resolution (schema first)

Fetch the definition schema before composing anything: `upscaler --json get <rg_*|rd_*> --format schema` (MCP: `upscaler_get_asset({asset_id, format: ["schema"]})`).

- **`data.values` keys are the schema field `key`, verbatim.** Most definitions use `ff_*` ids, but canonical seeded definitions may use human-readable, label-like keys, and a single definition can mix both. Never assume either style; read `fields[].key` and copy it exactly. The merge endpoint stores keys verbatim, so a typo or invented key becomes a permanent ghost with no delete operation.
- The literal field type strings are `text`, `textarea`, `number`, `date`, `time`, `select`, `radio`, `checkbox`, `lookup`, `record_link`, `member`, `table`, `file_upload`, `auto_increment`, `assessment`, `asset_picker`, `diagram`, plus the camelCase outlier `frameworkRequirementPicker`.
- Every `table` field has `columns[]`. The schema reports a column key as dotted (`ff_table.ff_col`) but stored row cells are keyed by the **bare** last segment (`ff_col`). A dotted inner key persists yet renders as an empty cell.
- On **records**, write a table field under its **bare** machine key (e.g. `Checklist`), the same key the web editor renders. Current schema surfaces report it bare (with columns as `<table>.<col>`, reducing to bare per the rule above). If a schema ever reports the field's key with a `values.<td_*>.` prefix (a server defect fixed 2026-07-19), strip the prefix before writing; a prefixed key is stored verbatim as an unrendered ghost that blanks the visible table. If the bare key is then rejected as an "unknown field key", the server predates the fix: stop and route the table rows to the web UI instead of writing the prefixed form. Note that a task write replaces the task's whole values map, so always resend every field, including existing table rows.
- A **record definition's** schema is a per-task list: each task definition (`td_*`) carries its own fields. Do not pass `--resolve-labels` when listing against an `rd_*`; the flag needs a flat `schema.fields` list, which a per-task record schema does not provide, so keys come back unrelabelled (a silent no-op, not an error).
- For `select`/`radio` options, prefer the inline schema options. The dynamic `field_options` operation is for option-resolved fields (`lookup`, `record_link`, `member`); checkbox options are inline only.

## Deriving values from context (parent asset and referenced assets)

Proposed values should come from the workspace, not from imagination. Before proposing, mine these sources in order (cheapest first) and cite what you used:

1. **The parent definition itself.** The definition's `description`, each field's `guidance` and `placeholder` text, section headings, and option lists encode what the author expects in each field. For records, the task titles and section headings describe the workflow stage the values must reflect (e.g. a "Containment" section wants past-tense factual actions, not plans).
2. **Sibling instances as exemplars.** Pull one known-good populated row from the same definition (MCP: `upscaler_list({type:"entries", definition_id:"<id>", include_values:true, limit:5})`; CLI: `upscaler --json list entries --definition-id <id> --include-values --limit 5`) and mirror its key shapes, value formats, and tone. This is also the ground truth for table-row key shape and for whether the tenant stores label-like keys.
3. **Referenced assets, per field type.** These fields point at other assets; resolve the reference and offer real targets:
   - `lookup` points at a target register. List that register's entries with the paired `upscaler_list({type:"entries", definition_id:"<rg_*>"})` / `upscaler --json list entries --definition-id <rg_*>` recipe and propose `{value: "<i_*>", label: "<row title>"}` objects built from real rows. Never invent an `i_*`.
   - `record_link` points at records. List the target `rd_*` the same way and resolve real `r_*` ids.
   - `member` requires ids from the member directory (MCP: `upscaler_list({type:"members", limit:100})` — 100 is the tool's hard cap, page with `offset`; CLI: `upscaler --json list members --limit 200`). Member ids are unprefixed nanoids (only groups carry `g_`); copy them verbatim. Ask when the intended person is unclear.
   - `frameworkRequirementPicker` takes real installed-framework requirement ids (MCP: `upscaler_manage_framework({action:"get_installed", framework_id:"<id>"})`; CLI: `upscaler --json framework get-installed <id>`). Normally omit; write only on explicit OWNER/ADMIN request.
4. **Governing documents (the "not enough clues" fallback).** The policy or procedure the definition operationalizes (usually an ancestor or sibling in the asset hierarchy, or bound to the same framework requirement) supplies terminology, review frequencies, checklist wording, and thresholds. This source is not optional: when sources 1-3 leave a required field, a checklist row, or a narrative ungrounded, run a document search before leaving the field blank or asking the user. Search near the definition's parent first (MCP: `upscaler_search_documents({query:"<topic>", parent_id:"<parent>"})`; CLI: `upscaler --json search "<topic>" --parent-id <parent>`), then widen to a global search (drop `parent_id`) if the scoped search returns nothing. A field may stay blank only after both searches come back empty, and the proposal must say the search found nothing rather than presenting the blank silently.
5. **The user's own material.** Anything the user pasted or pointed at wins over derived context, but still gets normalized to the schema's value shapes below.
6. **Earlier tasks on the same record, when filling a later task.** Read already-completed task values before drafting the next task so the record remains one consistent narrative. This source applies only to `r_*` records, not register entries.

If a reference cannot be resolved (empty target register, no matching member), leave the field unanswered and say so in the proposal. An honest blank beats a fabricated id: unresolvable ids are rejected or, worse, stored and rendered broken.

## Value shapes by field type

| Field type | Value to write |
| --- | --- |
| `text`, `textarea` | A string. Keep generated prose short; trim user content to the UI's 18,000-character limit. |
| `number` | A number. Honour schema `min` / `max`; generated samples should be plain integers because precision and step are not exposed. |
| `date` | `YYYY-MM-DD`, including week/month/quarter/year-style UI pickers. |
| `time` | `HH:mm:ss` in 24-hour time; bare `HH:mm` is invalid. |
| `radio`, single `select` | One visible option-text string. |
| multiple `select` | An array of visible option-text strings, even for one selection. Multiple is the platform default, so read `multiple` / `value_format`. |
| `checkbox` | An array of inline `options[].value` strings (e.g. `["Yes"]`, never the bare string). Do not query dynamic field options for checkbox. |
| `member` | `{"value": "<member-or-group id>", "label": "<name>"}` (array when `multiple`) — the canonical stored shape for both containers. A bare id string is accepted only because the agent layer resolves it against the field's options, and fails with `VALUE_VALIDATION_ERROR` when it cannot. Ask if the intended person is unclear. |
| `lookup` | `{"value": "i_*", "label": "<row title>"}`, or an array of these when `multiple`. |
| `record_link` | `{"value": "r_*", "label": "<record title>"}`, or an array of these when `multiple` — same shape as `lookup`; read `multiple` from the schema. |
| `frameworkRequirementPicker` | Normally omit. When explicitly requested by an OWNER/ADMIN, write an array of `{"frameworkId": "...", "requirementId": "..."}` using real installed-framework ids. |
| `file_upload` | Use the owning skill's file workflow (`entry update --file` / `entry upload-file` / presign-and-POST). Never write a hand-built file item without a real uploaded `uid`. On **records**, pass `--task-id`: the CLI reads the task's current values, splices the uploaded file in, and sends the result through `saveTaskDraft`, so the attachment lands in the draft like any other value. |

Omit `auto_increment` fields. Omit calculated fields as well: the agent schema does not expose their calculated flag, so use context cues such as totals, scores, ratings, or an explicit user statement. Calculated fields are exempt from required validation and are recomputed by the web editor.

Writes must never carry the `upscaler:` URI prefix; that is this library's citation convention only. On option-resolved fields (`lookup`, `record_link`, `member`, `select`, `radio`, `checkbox`) it fails membership and rejects with VALUE_VALIDATION_ERROR; on `text`/`textarea` it is stored verbatim and silently pollutes the field, so strip it before composing, not after a rejection.

## Table values

A table value is the complete list of rows to retain; replacing the value does not merge individual rows. Each row is keyed by the bare column id (`ff_col`), even though the schema reports the dotted `ff_table.ff_col`. A dotted inner key persists but renders empty.

Do not invent a row `key`. The server creates one for a new row. When replacing existing rows, preserve each existing server-managed `key` to retain row identity. Because schema `minRows` / `maxRows` are not exposed, keep generated tables to one or two rows unless the user asks for more.

## Proposal and read-back

Before confirmation, show labels, types, and human-readable proposed values (and where each derived value came from). After confirmation, map them to the exact schema keys; never infer a key. Warn that automations may change the saved display title or fields after the write.

During verification:

- **Register entries: verify with a values-bearing list, not a per-item `get`.** MCP `upscaler_list({type:"entries", definition_id:"<rg_*>", include_values:true})` or CLI `upscaler --json list entries --definition-id <rg_*> --include-values`, then match the new `i_*`. A per-item `get` right after a create returns `values: null` (the projection lags the event-sourced write) and falsely reads as "nothing landed".
- **Record task drafts: verify with the plain record read, `upscaler --json get <r_*>`.** A draft save writes the values onto the task itself, so match the `t_*` under `tasks[]`, confirm its `status` is `DRAFT`, and diff its `values` against the payload you sent. Those values are **flat for that task** (`tasks[].values.<key>`), not nested under the task-definition id. `--draft` is **not** the draft read: it requests the unpublished working copy of a *definition* (meaningful on an `rd_*` schema read), never a task's staged values. The values-bearing list keeps reporting the record's **committed** values (usually empty, or the pre-draft state) until a human completes the task, and `get <r_*> --format schema` returns `current_value: null` for every field; reading either as the verification and finding nothing is the expected result of a *successful* draft save, not a failed write. Do not pass `--resolve-labels` when the definition is an `rd_*`.
- **Register pending revisions have no agent-readable surface.** An update to a COMPLETED entry stashes the proposal where only the Upscaler app can read it (an editor-gated `itemDraft` query that neither MCP nor the CLI exposes), and the mutation response echoes the entry's unchanged **live** values. An error-free call is the whole receipt: report that the revision awaits review and stop, rather than hunting for a read that confirms it.
- Compare table cell keys with a known-good row and expect bare column ids.
- The nested `values.<taskDefinitionId>.<key>` shape appears **only** in the values-bearing list, and only for tasks a human has completed; `get <r_*>` never returns a record-level values object. Flatten the nested shape before diffing against your payload.
- Treat an absent key as unanswered, not as an empty stored value.
- Historical rows may contain `{value, label}` wrappers or legacy `DD/MM/YYYY` dates; normalize these only for comparison.
- Calculated fields may remain empty on a fresh CLI/MCP write until the form is edited in the UI.
- Verify the instance's display title as well as its values, because automations may rename it.
