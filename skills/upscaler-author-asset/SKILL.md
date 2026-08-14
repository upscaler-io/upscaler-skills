---
name: upscaler-author-asset
description: Use when the user asks to author, draft, generate, scaffold, or create an Upscaler asset definition — OR to update, revise, amend, or edit an EXISTING one — including a policy, procedure, guideline, plan, risk/asset/supplier/improvement/audit register, audit record, meeting minutes, incident record, or compliance/product/onboarding training course. Triggers on phrases like "Upscaler policy", "create a risk register", "draft an incident record", "author compliance training", "generate a procedure document", "build an onboarding course", "write an Upscaler asset", "update the testing procedure to cover X", "revise our secure development policy", "draft the document updates", "apply these changes to d_…", or any request mentioning the Upscaler platform together with an asset type. Updating an existing document is higher risk than creating one: follow the read-modify-write flow in references/03. Do NOT use for generic document writing, ordinary Markdown, or non-Upscaler content.
license: MIT
compatibility: Requires Python 3.10+ to run scripts/generate_field_id.py for unique field IDs.
---

# Upscaler asset definition authoring

This skill teaches you how to generate **valid** Upscaler asset definitions, Markdown (and Markdown+HTML) output that the Upscaler platform will accept without schema errors. The platform validates block options on every write and silently drops what it does not recognise; getting these rules wrong means either a rejected write or, worse, a silently broken asset (see the enforcement tiers under "Universal rules").

## Platform connection (MCP → CLI → setup)

Authoring happens locally and does not require a live Upscaler connection. If the user asks to **publish** the result back into the platform, follow the shared priority:

1. **MCP first:** if a tool whose name matches `upscaler_*` (commonly `upscaler_manage_asset` or `upscaler_manage_entry`) is present, call it to create or update. Always inspect the schema first via `upscaler_get_asset({ asset_id: "<definition-id>", format: ["schema"] })`.
2. **CLI fallback:** otherwise use `upscaler asset create --type <document_definition|register_definition|record_definition|course_definition> --data @file.json` for definitions, or `upscaler entry create --definition-id <id> --data @file.json` for register entries. Confirm the session is authenticated via `upscaler status`. Show the user your proposed payload and get explicit confirmation before any write, then preview with `--dry-run` where supported (`asset`/`entry` `{create,update,delete}`). Your own propose-then-confirm is mandatory: `--json` suppresses the CLI's interactive confirm prompt, so a write runs immediately once issued.
3. **Setup prompt:** if neither is available, print the setup message from [`../../references/upscaler-access.md`](../../references/upscaler-access.md) and stop. Do not author-and-publish blind.

Follow the shared auth recovery rules: refresh an expired session when possible, ask for login only when unauthenticated or refresh fails, and distinguish auth failures from usage errors that also exit `2`. Do not switch tiers to hide an error.

**Updating an existing document is not "create with extra steps."** `d_*` markdown writes silently replace the document's shared working copy (viewers see the published version until someone clicks Publish in the UI; the CLI can only read the working copy, never the published body), accept no version check (last write wins), and the CLI read-back is lossy: nested lists come back flattened/merged even when stored correctly, and bold runs serialised as `**text **` degrade to literal asterisks if written back. Before any `update-content` on an existing document, follow the read-modify-write procedure in `references/03-document-authoring.md` → "Updating an existing document": strip the fetched frontmatter, normalise `**…: **` bolds, and verify by diff plus a web-UI check (never by grepping for your added text).

The shared tool mapping, connection probe, auth rules, and setup message live in [`../../references/upscaler-access.md`](../../references/upscaler-access.md). Category-specific publish flows live in references `03`–`06`.

## Scope

The Upscaler platform recognises **4 asset categories** and **15 subtypes**:

- **Document** — `policy`, `procedure`, `guideline`, `plan`
- **Register** — `risk_register`, `asset_register`, `supplier_register`, `improvement_register`, `audit_register`
- **Record** — `audit_record`, `meeting_minutes`, `incident_record`
- **Course** — `compliance_training`, `product_training`, `onboarding_course`

Read [`references/01-asset-types.md`](references/01-asset-types.md) first — it has the canonical count ranges and detection-keyword table.

## Workflow

1. **Detect the category and subtype.** Use the keyword table in `01-asset-types.md`. If the user's intent is ambiguous, ask them to confirm before drafting — the wrong subtype means the wrong section template and the wrong count range.
2. **Plan the structure.** Pick a section / task / lesson count inside the subtype's allowed range. Propose titles and purposes to the user before generating full content.
3. **Load the relevant reference files.** See "Reading order" below.
4. **Draft in the correct content format.** Per-category format is documented in `03-06`.
5. **Self-validate** against every item in [`references/07-validation-checklist.md`](references/07-validation-checklist.md) before returning the output.

## The four content formats

| Category | Content format                                                                                                       |
| -------- | -------------------------------------------------------------------------------------------------------------------- |
| Document | Slate-backed Markdown — prose, headings, lists, pipe tables (→ `grid`), blockquotes (→ `quote`), fenced code (→ `code-block`; ` ```mermaid ` fences → `mermaid`; ` ```yaml ` fences are silently dropped), `---` (→ `divider`), GFM alert callouts (`> [!NOTE]` etc. → `note`), and `<note>` / `<embed>` custom elements, plus `image` / `file` / `data-table` attachment blocks (attached post-create; see `03-document-authoring.md`). `toc`, `data-table`, and `data-chart` cannot be authored in markdown. **No** `<form-*>` field widgets. |
| Register | Markdown `##` sections + `<form-*>` elements. Single-page.                                                           |
| Record   | One Markdown body **per task** (`##` sections + `<form-*>` elements); tasks are structured state, added via separate mutations, **not** parsed out of a single blob. See `05-record-authoring.md`. |
| Course   | Draft bundle with `# Lesson N:` boundaries; live courses are a `cd_*` shell plus separate lesson definitions, so split the bundle before publishing. Each lesson contains `##` sections + **mandatory** `<form-assessment>`. |

## Universal rules

Treat every rule below as mandatory, but know the consequence tier when one slips:

- **Enforced — the create/update is rejected.** On every markdown write the backend converts to Slate and runs `validateBlocks`; any issue throws `Content validation failed`. This covers: missing/empty `name` on any field; `form-select` / `form-radio` `values` that do not parse to a non-empty JSON array (double-quoting the JSON truncates the attribute, so the single-quote rule is enforced indirectly); `form-checkbox` values that are not all plain strings; malformed `form-assessment` `questions` (a stray apostrophe collapses the attribute to a string and the write is rejected). Exception: course lesson bodies are converted without validation at write time; their errors surface later, at release publish, as "Can not add asset with errors".
- **Silent degradation — the write succeeds but the data misbehaves.** Nested list items in any markdown write are flattened to top level AND each parent bullet is merged with its first child into one corrupted line — this destroys pre-existing nesting on a read-modify-write, not just newly authored lists (flat lists only; see `03-document-authoring.md` → "Updating an existing document"); `ff_` ids with characters outside `[A-Za-z0-9_]` (e.g. hyphens) are dropped by the read-side `select_values` projection; unknown `<form-*>` / `<format-*>` tag names are dropped at parse time; hand-authored file/image URLs do not survive; authored `fileList` entries are stripped to `uid`/`name`/`type`/`size`/`addedAt`.
- **House style — never enforced by the platform; follow it for consistency.** The colour scale, auto-increment prefix format, `---` placement, heading numbering and H1 rules, one-assessment-per-lesson with ≥3 MCQs, no YAML frontmatter, no trailing content.

The rules:

- **Documents have exactly one `# H1`.** Records and courses have **no asset-level H1** — their title lives in platform metadata. For records, each task body is its own Markdown blob with no `#` headings at all (only `##`). For courses, `# Lesson N:` is a page boundary within the asset body, not an asset title.
- **Inside a document, `##` headings are numbered (`## 1. Purpose`, `## 2. Scope`) and `###` are numbered (`### 1.1 Lawful basis`).** Do not skip levels. Only `##` is allowed inside records and courses (no `###` or deeper).
- **Field IDs use `ff_` + 28 base62 chars from `[A-Za-z0-9]`** (no underscore, no hyphen). Generate them with `scripts/generate_field_id.py` (see below). This format and the uniqueness rule are self-enforced authoring rules: the platform's option validator only checks that `name` is a non-empty string, but an id with characters outside `[A-Za-z0-9_]` (e.g. a hyphen) is silently dropped by the `select_values` projection, so the field stops resolving even though create succeeds. Never hand-craft. Every field ID is unique across the entire asset.
- **Every HTML attribute value is a quoted string.** `required="true"` — never `required=true`, never bare `required`, never `required="True"`.
- **`form-select` / `form-radio` `values` use single-quoted JSON.** `values='[{"text":"A","color":null}]'` — never `values="[..]"`.
- **`form-checkbox` `values` is a JSON array of plain strings**, not objects.
- **Rating scale colour sequence is fixed**: `green → cyan → gold → orange → volcano` (or `magenta` for the very top). Yes/No: Yes=`volcano`, No=`green`.
- **`---` appears only between a heading and its first content block.** Never after fields, never at the end of a section, never at the end of the asset.
- **Every course lesson has exactly one `<form-assessment>` with ≥3 MCQs, each with 3 answers and exactly one `isCorrect: true`** (this skill's authoring convention; the platform itself supports multiple correct answers, graded by exact-set match). Assessment attributes use **single** quotes (`name='ff_...'`, `questions='[...]'`). **No apostrophes** inside `label` strings — they break the single-quoted attribute.
- **Auto-increment prefixes are 3–4 uppercase letters + `-`.** `RSK-`, `AUD-`, `IMP-`, `INC-`. Set `addLeadingZeros="true"`.
- **No YAML frontmatter or metadata block** in the asset body. The platform adds version, owner, dates automatically.
- **No trailing blank lines or trailing `---`** at the end of the output.

## Count ranges (authoring guidance)

These are recommended ranges. The platform does **not** enforce a count validator (`validateBlocks` only checks per-block options), so a 4-section policy still publishes — but staying in range keeps assets well-shaped and consistent with the section templates in `03-document-authoring.md`.

| Subtype                | Unit     | Min | Max |
| ---------------------- | -------- | --- | --- |
| `policy`               | sections | 5   | 9   |
| `procedure`            | sections | 6   | 10  |
| `guideline`            | sections | 4   | 7   |
| `plan`                 | sections | 5   | 9   |
| `risk_register`        | sections | 3   | 5   |
| `asset_register`       | sections | 3   | 5   |
| `supplier_register`    | sections | 3   | 4   |
| `improvement_register` | sections | 3   | 5   |
| `audit_register`       | sections | 3   | 4   |
| `audit_record`         | tasks    | 2   | 4   |
| `meeting_minutes`      | tasks    | 2   | 3   |
| `incident_record`      | tasks    | 3   | 5   |
| `compliance_training`  | lessons  | 3   | 6   |
| `product_training`     | lessons  | 3   | 10  |
| `onboarding_course`    | lessons  | 2   | 6   |

Registers additionally need 10–20+ total fields, 3–5 of them required.

## Form elements — the 17-element whitelist

These are the only `<form-*>` names this skill may author. Never invent others. One additional name exists in the platform, `form-framework-requirement-picker` ("Linked Requirements"): you may see it when reading a definition serialised from the platform, but never emit it and never round-trip it — the markdown deserialiser does not accept it, so any markdown submitted with that tag silently drops the block.

- `form-text` — single-line text
- `form-text-area` — multi-line text (optional `markdown="true"`)
- `form-number` — numeric input
- `form-date-picker` — date selection
- `form-time-picker` — time selection
- `form-select` — dropdown, single or multi
- `form-radio` — single-choice button group
- `form-checkbox` — multi-choice (string values)
- `form-auto-increment` — sequential IDs with prefix
- `form-member` — person / group picker
- `form-upload` — file upload
- `form-table` — embedded table with typed columns (placeholder-ref tier)
- `form-lookup` — reference another register (placeholder-ref tier)
- `form-recordlink` — link to record definitions (placeholder-ref tier)
- `form-asset-picker` — platform asset picker (placeholder-ref tier)
- `form-assessment` — **courses only**, one per lesson, ≥3 MCQs
- `form-diagram` — never emit

Calculated fields are not a block: they are the `calculated` / `formula` / `calculatorMode` / `matrix` options on `form-text`, `form-number`, `form-select`, `form-radio`, and `form-checkbox`. A `<form-calculated>` tag does not exist and would be silently dropped.

Full attribute grammar, required/optional attrs, one example and one pitfall per element live in [`references/02-form-elements.md`](references/02-form-elements.md).

## Attachment elements — `<format-image>` and `<format-file>`

A parallel HTML custom element family for embedding image and file attachments inline in markdown. Valid in **any** asset category (document, register, record, course). Only `format-image` and `format-file` are recognised; other `<format-*>` tags are silently dropped. Grammar and Slate output shapes are in `references/02-form-elements.md` → "Attachment elements".

## Field ID generation

Run `scripts/generate_field_id.py` once per field:

```bash
python3 scripts/generate_field_id.py        # one ID
python3 scripts/generate_field_id.py 10     # ten IDs
python3 scripts/generate_field_id.py --check ff_btHrCEEWqKfq5zO7Konyy2DfGTTE
```

If script execution is not available in your environment, produce the ID inline matching the regex `^ff_[A-Za-z0-9]{28}$` — 28 characters exactly, drawn uniformly from `A-Z`, `a-z`, `0-9` (base62; no `_`, no `-`). Never reuse an ID within an asset.

## Anti-patterns (do NOT do these)

- Skipping heading levels (H2 → H4) or using unnumbered `##`/`###` in documents.
- Inventing new `<form-*>` names (only the 18 above are recognised).
- Hand-crafting field names like `ff_risk_owner` or `risk-owner` — must be a fresh 28-char nanoid.
- Reusing the same `name` across fields.
- Putting `<form-*>` field widgets in a document (those are register/record-only). Image and file attachments are fine — they live as Slate blocks attached via `upscaler asset upload-file`; see `references/03-document-authoring.md`.
- Hand-authoring image/file URLs that look like local paths (e.g. `![alt](./diagram.svg)`). The platform strips any URL that doesn't resolve to an attached file, leaving `![alt]()`. Attachments use platform-assigned UIDs and the URL form is not authorable in markdown.
- For images and files with a platform-assigned uid in hand, the supported hand-authorable form is `<format-image>` / `<format-file>` (see `references/02-form-elements.md` → "Attachment elements"). Do not invent other `<format-*>` tags; only `format-image` and `format-file` are recognised.
- Producing a course lesson without an assessment, or with fewer than 3 questions.
- Using double quotes on `<form-assessment>` attributes (the JSON has double quotes inside — single quotes outside).
- Writing apostrophes inside assessment `label` strings (`"the user's data"` breaks; rewrite as `"the data of the user"` or `"user data"`).
- Section / task / lesson count outside the subtype's recommended range (publish does not reject it, but the ranges match the platform generator's own limits — see Count ranges above).
- Trailing `---` at the end of a document / register / record / course.
- Adding YAML frontmatter or a metadata block (version, owner, effective date) to the asset body.
- Using `required=true` or bare `required` — HTML attributes are strings in double quotes.
- Using `values="[...]"` (double-quoted) for `form-select` or `form-radio` — must be single-quoted.
- Using object values for `form-checkbox` — they are plain strings.

## Reading order

After reading this file, load the references relevant to the user's request:

- **Any category** — `references/01-asset-types.md` (always) and `references/07-validation-checklist.md` (always, as the final check).
- **Document** (`policy`, `procedure`, `guideline`, `plan`) — add `references/03-document-authoring.md`. Add `references/02-form-elements.md` if you need the `<format-image>` / `<format-file>` attachment syntax; documents must not contain `<form-*>` field widgets.
- **Register** (`risk_register`, `asset_register`, `supplier_register`, `improvement_register`, `audit_register`) — add `references/02-form-elements.md` and `references/04-register-authoring.md`.
- **Record** (`audit_record`, `meeting_minutes`, `incident_record`) — add `references/02-form-elements.md` and `references/05-record-authoring.md`.
- **Course** (`compliance_training`, `product_training`, `onboarding_course`) — add `references/02-form-elements.md` and `references/06-course-authoring.md`.

Do not load reference files the current request does not need — each reference is self-contained.
