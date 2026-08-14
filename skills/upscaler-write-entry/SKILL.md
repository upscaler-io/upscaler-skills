---
name: upscaler-write-entry
description: Use when the user asks to create, add, insert, update, populate, or fill an entry (row, item) inside an existing Upscaler register (`rg_*`), i.e. writing a register item (`i_*`). Triggers on phrases like "create an entry in register rg_…", "add a row to the risk register", "populate a new supplier entry", "create a sample/dummy/test item in a register", "insert a row into the Process Register", "update entry i_… set a field to a value". Handles label-to-schema-key resolution, dummy/sample value generation, top-level file uploads, and files nested in `form-table` columns via the dotted `--file "Table.Column=path"` flag. Do NOT use for Upscaler records (`r_*` instances / `rd_*` definitions); "complete record r_…", advancing a record's tasks, or changing its status route to upscaler-run-record. Do NOT use to author a NEW register DEFINITION (use upscaler-author-asset), or to answer read-only questions (use upscaler-ask).
license: MIT
compatibility: Requires Upscaler MCP server (preferred) OR the `upscaler` CLI (`pip install upscaler-cli && upscaler login`). Write permission on the target register's Organization.
---

# Upscaler entry create / update

Writes entries (rows) into an **already-existing** register. The register definition (`rg_*`) and its fields are assumed to exist; this skill does not create new register definitions. For that, route to `upscaler-author-asset`.

This skill is **write-capable**. Every mutation goes through a **propose-then-confirm** UX: compose the payload, show it to the user, wait for confirmation, then send. Never mutate silently. Words like "sample", "dummy", "test", or "demo" in the user's prompt scope the *values* (use throwaway data), not the *process* (still render the proposal and wait). Auto-mode bias toward action does not override this rule; the skill is more specific than the global preference.

**Agent writes never finalize (HITL contract).** An entry this skill creates lands with status **DRAFT**, pending human review in up-app. An update to a **COMPLETED** entry lands as a **pending revision**: the live values stay untouched until a human applies the revision in up-app. Never claim an entry is live, final, or completed after a write. Report a create as "saved as a draft for review" and an update to a COMPLETED entry as "proposed a revision". Pass an optional note summarizing the change for the reviewer (CLI `--note`, or `data.note` on `upscaler_manage_entry` / the `note` parameter on the item tools).

## Platform connection (MCP → CLI → setup)

Run the connection-priority probe from [`../../references/upscaler-access.md`](../../references/upscaler-access.md) before any retrieval or mutation:

1. **MCP first:** scan for `upscaler_get_asset`, `upscaler_list`, and `upscaler_manage_entry`. File requests also require `upscaler_manage_file`; if the connector lacks it, explain that its file surface must be updated rather than silently mixing MCP and CLI.
2. **CLI fallback:** otherwise use `upscaler --json get …`, `upscaler --json list …`, `upscaler --json entry create|update|upload-file`. Confirm authentication via `upscaler status`. Global flags such as `--profile` and `--json` are accepted before or after the subcommand.
3. **Setup prompt:** if neither tier is available, print the setup message from the shared reference and stop.

Record the chosen tier once per session and stay on it.

## When to use

- "Create an entry in register `rg_xxx`."
- "Add a sample / dummy / test row to the Risk Register."
- "Populate a new supplier entry with these fields: …"
- "Update entry `i_xxx`, set Owner to Alice and Status to Open."
- "Fill in the demo entry, including the file upload fields."
- "Insert a row into the Process Register."

## When NOT to use

- "Complete record `r_…`", "advance / set the status of this record", "tick off the tasks on `r_…`." A `r_*` is a **record instance** (its parent is a `rd_*` record definition), not a register item (`i_*`). This skill writes register entries only and does not complete or transition records. → `upscaler-run-record` owns the record flow (task order, per-task filling, task completion); it shares this skill's form-filling core.
- "Create a new register called X." → `upscaler-author-asset` (you are authoring an asset definition, not a row).
- "Draft a new record definition / incident record template." → `upscaler-author-asset` (authoring an `rd_*`, not writing an `i_*`).
- "How many open risks do we have?" → `upscaler-ask` (read-only query).
- "Build me an evidence pack for A.5.15." or "Bind a Test on requirement A.5.15 to this record definition (`rd_*`)." → neither is a register write, and neither is covered by this library. Say so and stop rather than improvising.

## The contract you are writing against

Three facts drive every step below. Internalise them before composing a payload:

1. **`data.values` keys are the schema field `key`, verbatim.** Most registers use `ff_*` ids; some legacy/seeded registers use the human field name as the key (a single register can mix both). Read `data.schema.fields[].key` and use it exactly. The merge endpoint stores keys verbatim, so a key the schema does not list (a typo, or an invented `ff_*`) becomes a permanent ghost key with no delete operation. Never hand-craft a key.
2. **`entry update --file FIELD=PATH` uploads to a top-level file field; the dotted form `--file "Table.Column=PATH"` reaches a file column nested in a `form-table`.** Both go through one CLI call: it fetches the schema, resolves the field (or table + column), uploads, splices the value, and retries on version conflict.
3. **Every value write is a draft, never a finalization.** A create leaves the new entry in status DRAFT for human review. An update to a PENDING or DRAFT entry merges values and the entry stays (or becomes) DRAFT. An update to a COMPLETED entry is stashed as a pending revision; the live values and COMPLETED status are untouched until a human applies the revision in up-app, and a later draft save replaces the previous pending revision. Attach a reviewer note with each write: CLI `--note "..."` on `entry create` / `entry update`, or `data.note` in the `upscaler_manage_entry` payload (the item tools expose it as a `note` parameter). The note should summarize what was filled in or changed, so the reviewer can act on it without re-deriving your reasoning.

## Workflow

### 1. Resolve the register and fetch its schema

If the user gave you an `rg_*` ID, use it directly. Otherwise resolve by title first:

- **MCP:** `upscaler_search_nodes({ query: "<register name>", asset_types: ["register"] })` then `upscaler_get_asset({ asset_id: "<rg_id>", format: ["schema"] })`.
- **CLI:** `upscaler --json asset find --title "<register name>" --type register_definition` then `upscaler --json get <rg_id> --format schema`.

`asset find --type` takes the **raw backend enum** (`register_definition`, not the `register` alias that `upscaler_search_nodes` accepts); the alias returns zero hits on the CLI. Resolve, then stop if `asset find` returns zero or more than one hit (a bogus or wrong-Organization id `get` succeeds with empty content, so do not rely on `get` as a guard).

From the schema, read the full field map: fields are at `data.schema.fields[]`, each with a `key` / `label` / `type` / `required`. Every `table` field has `columns[]` (each column has its own `key` / `label` / `type`; a nested file column is `type: "file_upload"`). The literal type strings are `textarea`, `date`, `time`, `select`, `radio`, `checkbox`, `lookup`, `record_link`, `member`, `table`, `file_upload` (not `text_area` / `date_picker` / `time_picker`), plus the camelCase outlier `frameworkRequirementPicker`. **Both** the top-level field `key`s and the nested `columns[].key`s matter.

### 2. Propose values, confirm, then build the schema-keyed payload

Load and follow the value-shape and context-derivation rules in [`../../references/form-filling.md`](../../references/form-filling.md). Then present a concise table of labels, types, proposed human-readable values, and sources **before** sending anything. Include the reviewer note you plan to send with the write. Sample, dummy, and demo requests still require confirmation.

After confirmation, map each value to its exact schema `key`; do not assume every key begins `ff_*`. Build the JSON payload yourself because entry create/update has no label-resolution flag. Omit calculated and auto-increment fields, shape multi-valued fields exactly as the schema says, and preserve bare column keys inside table rows.

If the register has automations, warn that the saved row or display title may change after the write. Verification must compare the final stored values and title rather than the request byte-for-byte.

### 3. Upload any files, then write the entry

#### 3a. Top-level `file_upload` fields

The entry must exist before a file is attached. On create, send the confirmed non-file values first, capture the new `i_*`, then attach files.

**MCP:** call `upscaler_manage_file` with `action: "presign_upload"`, `file_name`, `content_type`, and the target `asset_id`. Submit the bytes as a multipart POST to `data.url` using every returned `data.fields` value. Build the canonical file item `{uid, name, type, size, addedAt}`, preserving the returned `uid`; read the entry's current file list, append this item if its UID is absent, and persist the complete list with `upscaler_manage_entry({operation:"update", entry_id:"i_*", data:{values:{"<schema-key>":[...]}}})`. The MCP tool presigns but does not stream bytes or attach the file value for you.

**CLI:** use the upload sugar, which performs the presign, S3 POST, and values splice:

```bash
# Sugar form, one file, one field.
upscaler --profile <p> entry upload-file --entry-id <i_*> --field "<Label or ff_*>" --path /tmp/dummy.pdf

# Repeatable form, multiple files into the same field in one mutation.
upscaler --profile <p> entry update --entry-id <i_*> \
  --file "Attachments=/tmp/report.pdf" \
  --file "Attachments=/tmp/log.csv"
```

Both CLI forms preserve the existing list and append new file items. Sequential `entry upload-file` calls are safe; batching multiple `--file` flags is simply fewer writes. Retries are UID-idempotent.

The file bytes upload immediately, but the spliced file value follows the draft contract like any other value write: on a fresh or DRAFT entry it lands in the draft values; on a COMPLETED entry it lands in the pending revision and the live file list is unchanged until a human applies the revision.

If the user asked for dummy files, create valid, minimal content in `/tmp/` with an accurate extension and MIME type. Ask when real document content or a particular format matters.

#### 3b. `file_upload` columns nested inside a `table` field

**CLI:** use the dotted form of `--file`:

```bash
upscaler --profile <p> entry update --entry-id <i_*> \
  --file "<TableLabel>.<ColumnLabel>=/tmp/report.pdf"
# or with raw keys, written as <table_key>.<bare_col_id>:
upscaler --profile <p> entry update --entry-id <i_*> \
  --file "ff_table.ff_col=/tmp/report.pdf"
```

The CLI fetches the schema, resolves the table and column (label match is case-insensitive), uploads the file, and appends one new table row containing `{uid, name, type, size, addedAt}`. Multiple `--file` flags batch into one mutation and one new row. Missing paths fail before upload, and version-conflict retries are UID-idempotent.

**MCP:** use the same presign-and-POST sequence as step 3a. Read the current table list, append one row keyed by the bare column ID—`{"ff_col":[<file-item>]}`, not the schema's dotted `ff_table.ff_col`—and update the full table value with `upscaler_manage_entry`. Preserve all prior rows and their server-managed row keys.

The CLI performs the bare-column reduction for you. With either tier, a dotted inner key persists but renders as an empty table cell, so step 4 compares the result with a known-good row.

### 4. Compose and send the create / update

**CLI:** the `--data` payload must be wrapped in `{"values": {...}}`. The CLI passes `--data` through as the request body's `data` field, and the merge endpoint reads values from `data.values.<key>`. A bare `--data '{"ff_xxx": "v"}'` with top-level `ff_*` keys is rejected before sending. Wrap regardless of the schema's key style.

For **create** (entry does not exist yet; the new entry lands as a DRAFT for review):

```bash
upscaler --profile <p> entry create \
  --definition-id <rg_*> \
  --data '{"values": {"<ff_title>": "Sample item", "<ff_owner>": "Alice", "<ff_status>": "Open"}}' \
  --note "Drafted a sample item with owner Alice, status Open"
```

For **update** (entry exists, `i_*` in hand; on a COMPLETED entry this lands as a pending revision, live values untouched):

```bash
upscaler --profile <p> entry update \
  --entry-id <i_*> \
  --data '{"values": {"<ff_status>": "Closed"}}' \
  --note "Proposed setting Status to Closed"
```

Scalar and table values both go through `--data`; there is no `--field` scalar sugar on `entry create` / `entry update` (the `--field` flag exists only on `entry upload-file`, where it names a file field). The `values` dict must be keyed by the exact schema `key` for each field (read it from the schema, verbatim). For anything containing a table value, use `--data @payload.json` so you control the keys exactly (and remember the `values` wrapper).

**MCP:** use `upscaler_manage_entry({operation:"create", definition_id:"rg_*", data:{values:{...}, note:"..."}})` or `upscaler_manage_entry({operation:"update", entry_id:"i_*", data:{values:{...}, note:"..."}})`. The same `data.values` wrapper and exact schema-key rules apply; the reviewer note travels as `data.note`.

After the write, **confirm the draft values landed by reading them back** — verify with `list entries --include-values`, **not** `get <i_*>`. A single `get <i_*>` immediately after a create returns the entry with `values: null` (the register is event-sourced; the per-item `get` projection does not hydrate values right after the write), so a `get`-based check produces a false "the write didn't land". `list entries --include-values` reflects the new values immediately.

The read-back check applies to creates and to updates of PENDING/DRAFT entries, where the values merge into the entry (status DRAFT). **An update to a COMPLETED entry is different by design:** the live values are intentionally unchanged, so an unchanged read-back is the expected outcome, not a failed write. Confirm a pending revision from the mutation response instead, and tell the user the revision is waiting for review in up-app.

- **CLI:** `upscaler --profile <p> --json list entries --definition-id <rg_*> --include-values --limit 200`, then find the row whose `_id` matches the new `i_*` and check its `values`. Read raw keys here: do **not** pass `--resolve-labels`, which rewrites `ff_*` keys to human labels and hides the key shape you are checking.
- **MCP:** `upscaler_list({ type: "entries", definition_id: "<rg_*>", include_values: true })`, then match the new `i_*` in `data.items`.

**"Values present" is necessary but not sufficient.** A row stored under the wrong key is "present" yet invisible. Two extra checks before you report success:

1. **Diff the new row's keys against a known-good row.** For any `table` / nested-file write, pull an existing populated row from the same register and confirm your new row uses the **same** key shape — bare `ff_col` inside the table list, not the dotted `ff_table.ff_col`. A plain "did values land" check passes for both, but only the bare-keyed row renders.
2. **Check the asset-level title, not just the field value.** Register automations can stamp or rename the row's display title on create/upload, so the field value and the displayed title may diverge. Read the entry's `title`, not only the title field's value, before quoting it back to the user.

Apply the read-back tolerances in [`../../references/form-filling.md`](../../references/form-filling.md); historical wrappers, absent unanswered keys, and unrecomputed calculated fields are not automatically failed writes.

(The `entry create` response already echoes the populated `values` too — but treat `list entries` as the independent ground truth.) Cite the result as `[<entry title>](upscaler:<i_*>)` in your response, and phrase the outcome per the HITL contract: "saved as a draft for review" for a create or a draft merge, "proposed a revision (pending review in up-app)" for an update to a COMPLETED entry. Never state that the entry is live, final, or completed.

## Anti-patterns

- **Writing a display label as a `values` key without checking the schema** (e.g. `{"Support documents": [...]}`). The merge endpoint stores literal keys. A typo becomes a permanent ghost with no delete operation. Always resolve the label to the exact `fields[].key` first; that key may be `ff_*` or a human-readable machine key.
- **Keying a `table` row cell by the dotted column key from the schema** (e.g. `{"ff_table": [{"ff_table.ff_col": [...]}]}`). The schema reports columns as `ff_table.ff_col`, but the store and UI key cells by the **bare** `ff_col` (the last dot-segment). A dotted inner key stores fine and passes a "did it land" check, yet the row renders empty. Use the bare `ff_col` in hand-built `--data` rows; `--file` already reduces to bare for you.
- **Declaring success on "values present" without a key-shape diff.** A row under the wrong key is present but invisible. For table/file writes, compare the new row's keys against a known-good row in the same register, and read the asset-level `title` (automations may rename it), before reporting done.
- **Sending bare `ff_*` keys to `entry create --data` / `entry update --data` without the `{"values": {...}}` wrapper.** The CLI now **rejects** a bare top-level `ff_*` payload with a usage error and exits before sending — wrap every payload in `{"values": {...}}`. (Non-`ff_` label keys still pass through unwrapped, so wrap regardless.)
- **Treating "sample" / "dummy" / "test" / "demo" in the prompt as consent to skip the proposal table.** Those words scope the *values* (use throwaway data); they do not scope the *process* (still render the proposal and wait for explicit go-ahead).
- **Verifying a write with `get <i_*>`.** A per-item `get` right after a create returns `values: null` (the register is event-sourced; the item-`get` projection lags), so it falsely reads as "nothing landed". Confirm with `list entries --definition-id <rg_*> --include-values` and match the new `i_*` instead.
- **Rebuilding a file field from only the new upload.** The stored value is a list. Preserve existing items and append by UID; the CLI does this automatically, while the MCP flow must do it explicitly.
- **Reaching for `upscaler files presign` directly.** It is a low-level escape hatch that *requires* `--asset-id` (it does not 422 for a missing asset_id — that claim was wrong). You almost never need it: `entry update --file FIELD=PATH` covers top-level files and `--file "Table.Column=PATH"` covers nested form-table columns.
- **Pointing a bare `entry update --file <ColumnLabel>=PATH` at a nested table column.** The resolver only matches that against *top-level* file fields and reports "no file field named …". Use the dotted form `--file "<TableLabel>.<ColumnLabel>=PATH"` (or `ff_table.ff_col=PATH`) so the CLI resolves the column and splices the table row for you.
- **Claiming an entry is live, final, or completed after a write.** Agent writes never finalize. A create is "saved as a draft for review"; an update to a COMPLETED entry is "proposed a revision". A human finalizes in up-app.
- **Reading an unchanged COMPLETED entry as a failed write.** An update to a COMPLETED entry stashes a pending revision and leaves live values untouched by design. Confirm from the mutation response; do not retry the write because `list entries` still shows the old values.
- **Skipping the reviewer note.** The note (`--note` / `data.note` / the tools' `note` parameter) is what the reviewer sees first. Send one that summarizes the change unless the user explicitly declines.
- **Mutating without confirmation.** Always show the user the planned payload first; wait for explicit go-ahead.
- **Inventing field keys.** Machine keys live in the schema response. Never hand-craft one for an existing register or assume it begins `ff_*`.
- **Writing a value into a calculated field.** The schema does not expose the `calculated` flag, so detect them from context (a score/total/rating derived from other fields; the user says it is computed) and omit them. A written value persists verbatim (misleading) until the next UI edit overwrites it; an omitted one cannot fail validation, because calculated fields are exempt from `required`.
- **Writing a scalar into a multi-valued field (or vice versa).** Multiple-mode selects and checkboxes take arrays even for one selection; radios and single-mode selects take bare strings. The merge endpoint stores the wrong shape without complaint and the UI then fails to render it — read `multiple` / `value_format` from the schema per field.
- **Sending `expectedVersion` from a stale read.** For `mergeItemValues` updates, fetch the entry immediately before the write and pass the returned version, or omit it on the very first write and let the server set it.

## Examples

**User:** "Use the dev profile. Create a sample item in register `rg_2o0kTkmNlnVTWZrfh0G2Zj52qgaB`. Please create dummy files for file upload fields."

**Skill should:**

1. Run the connection probe. Find `upscaler` on PATH, confirm `upscaler --profile dev status` is authenticated.
2. `upscaler --profile dev --json get rg_2o0kTkmNlnVTWZrfh0G2Zj52qgaB --format schema` to read every field and every `columns[].key`.
3. Generate dummy `/tmp/*.pdf` (and `/tmp/*.csv` etc.) for each `file_upload` field, top-level and nested.
4. Show the user a one-table proposal: every field, its type, the proposed dummy value, plus the reviewer note to be sent.
5. On confirmation: `entry create` with a `{"values": {...}}` payload keyed by the schema `key`s for scalar / select / table fields and a `--note` summarizing what was drafted, then `entry update --file "<Label>=PATH"` for top-level files and `entry update --file "<TableLabel>.<ColumnLabel>=PATH"` for files in `form-table` columns.
6. Confirm via `list entries --definition-id <rg_*> --include-values` (match the new `i_*`, no `--resolve-labels`). For the `Support documents` table, diff the new row's keys against an existing populated row (expect bare `ff_col`, not `ff_table.ff_col`), and read the entry's `title` in case an automation restamped it. Then cite it as `[Sample item](upscaler:i_*)`, saved as a draft for review; do not report it as live or completed.

**User:** "Set the Status of `i_xyz` to Closed and clear its Owner."

**Skill should:** fetch the schema for the parent register once, resolve `Status` and `Owner` to their `ff_*` keys, show the user the planned payload (`{"values": {"ff_status": "Closed", "ff_owner": null}}`) and a reviewer note, and on confirmation send `upscaler entry update --entry-id i_xyz --data '...' --note "Proposed closing the item and clearing its owner"`. If `i_xyz` is PENDING/DRAFT, confirm the merged draft via `list entries --include-values` (match `i_xyz`), not a per-item `get`. If `i_xyz` is COMPLETED, the write lands as a pending revision: live values stay unchanged, so confirm from the mutation response and report "proposed a revision, pending review in up-app", never "Status is now Closed".

## References

Read the shared form-filling core [`../../references/form-filling.md`](../../references/form-filling.md) when composing or verifying field values (it is shared with `upscaler-run-record`, which handles record instances `r_*`). The connection and platform contract is in [`../../references/upscaler-access.md`](../../references/upscaler-access.md), especially "Schema-first writes", "Listing entries with values (avoid N+1)", and "Pitfalls".
