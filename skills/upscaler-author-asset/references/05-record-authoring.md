# 05 — Record authoring

Records are **multi-page workflow forms** where each page is a **task**. The Upscaler platform stores a record_definition as `{title, description, taskDefinitions: [...]}` — tasks are structured state, **not** boundaries parsed out of a single Markdown blob.

This means the skill's output is not "one markdown file with `# Task N:` separators." It is:

1. A **definition shell** (title + optional description) — one JSON payload.
2. **One Markdown body per task** — each task's body is its own `##`-headed Markdown file containing `<form-*>` elements.

The agent publishes by running a small sequence of `upscaler` CLI calls (or `upscaler_manage_asset` MCP calls). See "Publish flow" below for the exact recipe.

> **Notice:** Subtype task structures and field sets below are sensible defaults aligned with ISO 27035 / NIST SP 800-61 and common audit practice. The live Upscaler platform is the authoritative source for the current default shape and may evolve these templates over time.

## Per-task body structure

Each task body is a continuous Markdown document with `##` section headings and `<form-*>` elements, exactly like a register body. **There is no `# H1` and no `# Task N:`** — the task title lives in the structured payload, not in the body.

```markdown
## Section Heading

---

<form-* ...></form-*>

<form-* ...></form-*>

## Next Section

---

<form-* ...></form-*>
```

Rules:

- Only `##` is allowed inside a task body. Never `#`, never `###` or deeper.
- Each section: `## Heading`, blank line, `---`, blank line, first field. `---` only between heading and first field.
- Fields are `<form-*>` elements from `02-form-elements.md`.
- **Field IDs are unique across the entire record** (not just within one task). Use a fresh `scripts/generate_field_id.py` call for every field across every task body.
- Factual, objective language. Past tense for completed actions, present tense for ongoing status.
- Stay within the task count range from `01-asset-types.md`: audit 2–4, meeting 2–3, incident 3–5.

## Workflow types

| Type | Meaning |
| --- | --- |
| `sequential` | Tasks execute strictly in order (T1 → T2 → T3). Default — applied automatically by the publish flow. |
| `parallel` | After a fork, multiple tasks run concurrently and all must complete before the next sequential step. Requires custom `--data` for `set-task-condition`. |
| `sequential_parallel` | Mix of sequential and parallel segments. Requires custom conditions. |

When the user needs anything other than `sequential`, confirm the fork/join points before drafting — it changes the conditions you have to emit.

## Auto-increment prefixes

| Subtype | Typical prefix |
| --- | --- |
| `audit_record` | `AUD-` |
| `incident_record` | `INC-` |

Meeting minutes typically don't use auto-increment.

## Subtype templates

### audit_record (default 3 tasks, ~16 fields)

| Task | Title | Fields | Purpose |
| --- | --- | --- | --- |
| 1 | Audit Header | ~9 | Capture metadata, scope, methodology |
| 2 | Findings | ~2 | Log findings table + supporting evidence |
| 3 | Conclusion | ~5 | Overall assessment, opinion, sign-off |

Key fields by task:
- **Task 1** — Audit Number (`form-auto-increment`, `AUD-`), Audit Title (`form-text`), Audit Type (`form-radio`: Internal / External / Surveillance), Audit Start/End Date (`form-date-picker`), Lead Auditor (`form-member`), Auditee/Department (`form-text`), Scope and Objectives (`form-text-area`), Methodology (`form-text-area`).
- **Task 2** — Findings Table (`form-table` with columns: Finding ID, Description, Severity, ISO Clause, Evidence, Recommendation, Management Response, Due Date, Status), Supporting Evidence Notes (`form-text-area`).
- **Task 3** — Overall Assessment (`form-text-area`), Audit Opinion (`form-radio`: Conforming / Minor Non-Conformance / Major Non-Conformance), Follow-Up Actions (`form-text-area`), Follow-Up Date (`form-date-picker`), Sign-Off (`form-member`).

### meeting_minutes (default 2 tasks, ~13 fields)

| Task | Title | Fields | Purpose |
| --- | --- | --- | --- |
| 1 | Meeting Details | ~8 | Metadata, attendees, roles |
| 2 | Agenda & Actions | ~5 | Agenda, decisions, action items |

Key fields:
- **Task 1** — Meeting Title (`form-text`), Meeting Date (`form-date-picker`, `defaultToday="true"`), Meeting Time (`form-time-picker`), Location (`form-text`), Attendees (`form-member`, `multiple="true"`), Chair (`form-member`), Minute Taker (`form-member`), Apologies (`form-member`, `multiple="true"`).
- **Task 2** — Agenda Items (`form-table`: Item Number, Topic, Discussion Summary, Presenter), Decisions Made (`form-text-area`), Action Items (`form-table`: Action, Assigned To, Due Date, Status), Next Meeting Date (`form-date-picker`), Next Meeting Topics (`form-text-area`).

### incident_record (default 4 tasks, ~40+ fields)

| Task | Title | Fields | Purpose |
| --- | --- | --- | --- |
| 1 | Raise & Assess Incident | ~30 (6 sections) | Raise, communicate, initial response, assess, contain, eradicate |
| 2 | BCP Execution | ~10 | Execute business continuity procedures |
| 3 | Lessons Learned | ~10 (4 sections) | Post-incident review |
| 4 | Close Incident Report | ~3 | Formal closure |

Key sections within Task 1:
- **Incident Overview** — Incident Number, Raised By (`form-member`), Date/Time Raised (`form-date-picker`/`form-time-picker`), Incident Response Lead (`form-member`), IRT Members (`form-member` multi), Incident Type (`form-select` multi: Data Breach / Service Outage / Malicious Attack / Theft or Loss), Incident Description (`form-text-area` markdown), Criticality (`form-select`: Low / Medium / High).
- **Incident Communication** — Management Notification, Business Operations Disrupted (`form-radio` solid Yes/No), BC Team Notification, Third-Parties for Resolution (`form-table`), Third-Parties for Notification (`form-table`), Communications Team Notification.
- **Initial Response Information** — First Responder, Date/Time First Noticed, Initial Description (`form-text-area` markdown), Initial Actions Taken (`form-text-area` markdown), Supporting Evidence (`form-upload` multi).
- **Incident Assessment** — Incident Ongoing (`form-radio` solid Yes/No), Ongoing Incident Actions, Incident Cause, Information Impacted, Affected Infrastructure, Security Controls in Place, Affected Services, Affected Departments, Impact Duration, Supporting Documentation.
- **Containment** — Containment Activities, Person(s) Responsible, Approved By.
- **Eradication and Recovery** — Eradication Activities, Person(s) Responsible, Approved By, Required Change Requests (`form-recordlink`).

## Worked example — meeting_minutes Task 1 body

This is the **body of one task**, ready to feed to `upscaler asset set-task-values --values-file <this file> --values-type markdown`. There is no `# Task 1: …` header — the title is set via `add-task --title "Meeting Details"`.

```markdown
## Meeting Details

---

<form-text name="ff_1YOEsJIKOE6zhYJPlBABZy4nSIuj" title="Meeting Title"
  required="true" placeholder="E.g. Q1 ISMS Steering Committee"
  guidance="Enter the official title of the meeting."></form-text>

<form-date-picker name="ff_S3eYWoHXeYV7Vd8k1aKa7nL1YHdu" title="Meeting Date"
  required="true" placeholder=""
  guidance="Calendar date the meeting was held."
  defaultToday="true"></form-date-picker>

<form-time-picker name="ff_XP4EJ51HSSBofpp2cu8AIKZOsNxo" title="Meeting Time"
  required="true" placeholder=""
  guidance="Start time in 24-hour format."
  use12Hours="false" defaultNow="true"></form-time-picker>

<form-text name="ff_rIiotuvQFduAwTu0wuH1UARWMUg2" title="Location"
  required="false" placeholder="E.g. Boardroom A / Zoom"
  guidance="Physical or virtual meeting location."></form-text>

<form-member name="ff_H1MXOgpwOYKgdCnXfU5jJgLe2dFM" title="Attendees"
  required="true" placeholder=""
  guidance="Members present at the meeting."
  multiple="true" includeGroups="false"></form-member>
```

## Publish flow (batched by default)

Authoring produces:

- **`record.json`** — the definition plus ordered `tasks[]` payload.
- **`task-1.md`**, **`task-2.md`**, ... — one body file per task. Each is pure Markdown (`##` sections + `<form-*>` elements).
- **`tasks.json`** *(optional working file)* — task titles and source-body paths used to assemble `record.json`.

For the default sequential workflow, read each task body and serialize it into one payload:

```json
{
  "title": "Meeting Minutes",
  "description": "Captures meeting details, decisions, and actions.",
  "sequential": true,
  "tasks": [
    {"title": "Meeting Details", "values": "## Meeting Details\n\n---\n\n<form-text ...>", "valuesType": "markdown"},
    {"title": "Agenda & Actions", "values": "## Agenda & Actions\n\n---\n\n<form-table ...>", "valuesType": "markdown"}
  ]
}
```

Then preview and create in one call:

```bash
upscaler --profile <name> asset create --type record_definition --data @record.json --dry-run
upscaler --profile <name> asset create --type record_definition --data @record.json
```

The implementation adds every task body and, when `sequential` is true (the default), wires task N to unlock after task N−1. The response includes each assigned `taskDefinitionId`; no follow-up calls are needed for the normal sequential case.

For `parallel` / `sequential_parallel`, later edits, or recovery after a partial legacy workflow, use the granular `asset add-task`, `asset set-task-values`, and `asset set-task-condition` commands. Confirm the fork/join condition AST with the user before those writes.

### MCP equivalents

If `upscaler_manage_asset` is available, prefer the same single create payload:

| CLI | MCP |
| --- | --- |
| `asset create --type record_definition --data @record.json` | `upscaler_manage_asset({operation: "create", asset_type: "record_definition", data: {title, description, sequential, tasks}})` |
| `asset add-task --title <T>` | `upscaler_manage_asset({operation: "add_task_definition", asset_id, data: {title}})` |
| `asset set-task-values --values-file <md>` | `upscaler_manage_asset({operation: "set_task_definition_values", asset_id, data: {taskDefinitionId, values, valuesType: "markdown"}})` |
| `asset set-task-condition --data @cond.json` | `upscaler_manage_asset({operation: "set_task_definition_condition", asset_id, data: {taskDefinitionId, condition}})` |

## Common mistakes

- Wrapping the per-task body in `# Task N:` headings, or concatenating all tasks into one Markdown blob. **The platform does not parse `# Task N:` into workflow nodes** — create task structure with the batch `tasks[]` payload or granular `add-task` mutations.
- Reusing field IDs across tasks (IDs must be unique across the entire record).
- Putting the record title as `# H1` inside any task body — it lives in the definition shell's `title` field, not in any body.
- Using `###` headings — only `##` is allowed inside a task body.
- `---` after fields or between tasks — only between `## heading` and the first field.
- Using granular `add-task` calls and assuming they sequence automatically. Batch create with `sequential: true` wires them; granular additions need explicit conditions.
- Subjective / first-person language ("I noticed", "we will") — records must be factual and objective.
- Forgetting `optionType="button"` on Yes/No radios or status radios.
