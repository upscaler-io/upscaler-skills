# 03 — Document authoring

Documents are stored as a **Slate JSON tree** and round-tripped as Markdown. The body may contain prose, headings, lists, tables, code blocks, callouts, embeds, Mermaid diagrams, and **attachment blocks** (`image`, `file`, `data-table`, `data-chart`). They do **not** contain `<form-*>` field widgets — those are register/record-only. When authoring for `asset create --values-type markdown`, output one continuous Markdown document; attachments are added separately (see "Attaching images and files" below). For richer pre-populated trees, submit Slate JSON via `--values-type slateJson`.

> **Notice:** Subtype section templates below are sensible defaults aligned with common compliance and documentation practice. The live Upscaler platform is the authoritative source for the current default shape and may evolve these templates over time.

## Heading grammar

- Exactly one `# H1` — the document title, first line of the output.
- Major sections use numbered `## N. Title` (`## 1. Purpose`, `## 2. Scope`, ...).
- Subsections use numbered `### N.M Title` (`### 1.1 Lawful Basis`, `### 1.2 Scope`, ...).
- Do not skip levels (no H2 → H4).
- Do not use `####` or deeper.

## Structural rules

- Insert `---` between `##` sections **only**. Never between `#` and the first `##`. Never after the last `##` section's content. Never inside a section.
- No YAML frontmatter, no metadata block (version, owner, effective date) — the platform adds that automatically.
- Do not end output with trailing `---` or trailing blank lines.

## Allowed block types

| Block | Syntax |
| --- | --- |
| Heading | `## N. Title`, `### N.M Title` |
| Paragraph | Plain text separated by blank lines |
| Bulleted list | `- Item` — **flat lists only in markdown writes.** The markdown deserialiser does not support nesting: an indented child item (any marker, 2- or 4-space indent) is promoted to top level AND the parent line is merged with its first child into one corrupted line (`* Parent* Child`). Verified 2026-08-10 on a clean document. Nested lists render fine when built in the web editor and serialise correctly on read — but they will not survive any markdown write, including a read-modify-write of a document that already contains them (see "Updating an existing document"). Where sub-structure is needed in authored markdown, restructure as flat bullets under a bolded lead-in, a table, or `<ul><li>` HTML inside a table cell (which does survive). |
| Numbered list | `1. Item`, `2. Item` |
| Table | Standard Markdown `|` table |
| Blockquote | `> text` — plain quote block |
| Callout / note | GFM alert blockquote: first line `> [!NOTE]` / `> [!TIP]` / `> [!IMPORTANT]` / `> [!WARNING]` / `> [!CAUTION]`, body on following `> ` lines. Deserialises to the `note` block with `options.type` info / question / info / warning / error respectively. Round-trips as `<note type="..." data-content="...">`, which is also hand-authorable and additionally accepts `type="success"`, `type="default"`, and a `title` attribute. Note: `> **Note**: text` does **not** create a callout — it stores a plain quote block. |
| Bold | `**text**` |
| Italic | `*text*` |
| Inline code | `` `text` `` |
| Code block | Fenced ` ``` ` block with an info string, e.g. ` ```bash `. Any info string is accepted **except** `yaml` and `mermaid`, which are reserved (` ```mermaid ` becomes a Mermaid diagram; ` ```yaml ` is consumed by the data-table processor and never becomes a code block — to show YAML as code, use no info string or `text`). Highlighted languages: css, html, java, javascript, jsx, markdown, php, python, sql, tsx, typescript, bash; other strings are stored verbatim without highlighting. Do not write `paintext` — that literal is an editor-internal UI value, not an authoring identifier. |
| External embed | `<embed url="https://..." title="..."></embed>` (hand-authorable; bare `<embed>` element, **not** `<format-embed>`). `url` is required — asset create fails validation without it. Optional `card` attribute (`0`, `1`, or `"small"`). Rendered via Iframely. |
| Thematic break | `---` (between `##` sections only) |
| Asset link | `[Title](/document_definition/DOCUMENT_ID)` |
| Mermaid diagram | ` ```mermaid ... ``` ` fenced block (≤10 nodes) |
| Image attachment | `<format-image fileUid="<uid>" fileName="...">` (hand-authorable). Round-trips as `![filename](./_attachments/<uid>.<ext>)`. |
| File attachment | `<format-file fileList='[{...}]'>` (hand-authorable). Round-trips as `[📎 filename](./_attachments/<uid>.<ext>)`. |
| Data-table embed | Read-side round-trip output only: fenced ` ```yaml ` block with a `table:` root key. **Not hand-authorable** — yaml fences in submitted markdown are silently dropped. The fence carries the block options: `sourceType` (`item` = register, `record` = record definition), `sourceId`, `columns` (v2 `dataIndex` paths start with `values`, e.g. `["values","ff_abc"]`), and optionally `filter`, `dataFilterString`, `sorter`, `paginationSize` (`default` \| `small`). |
| Data-chart embed | Read-side round-trip output only: fenced ` ```yaml ` block with a `chart:` root key (options: `chartType`, `sourceType` / `sourceId` as per data-table, `xAxis: {dataIndex}`, `yAxis: [{dataIndex, aggregate}]`). Not hand-authorable. |

A table-of-contents block (`toc`) exists in the editor but cannot be authored in Markdown: no Markdown or custom-element syntax deserialises to it. To pre-place one, submit Slate JSON via `--values-type slateJson` with `{ "type": "toc", "children": [{ "text": "" }] }`; otherwise treat it as editor-insert-only.

To pre-populate a `data-table` or `data-chart`, use the Workflow B slateJson path with a **complete** options object — write validation rejects incomplete blocks (data-table: `sourceType` + `sourceId` + at least one column, each with `dataIndex` and `title`; data-chart: `chartType` + `sourceType` + `sourceId` + `xAxis` + `yAxis` entries with `dataIndex` and `aggregate`). Caveat: the write-path validator accepts only `chartType: pie | column | line` — `bar` / `area` exist in the editor UI but fail slateJson writes. The yAxis aggregation key is `aggregate` (SUM / AVERAGE / MIN / MAX).

## Language conventions

- **policy**: use "shall" for mandatory requirements.
- **procedure**: use imperative steps ("Open the console", "Review the output").
- **guideline**: use "should" for recommendations, "may" for optional.
- **plan**: use future-tense objectives ("will deliver", "will review").
- Define acronyms on first use.
- Use `[ORGANIZATION_NAME]` as a placeholder for the tenant's name.
- Active voice; sentences under 25 words where possible.

## Section templates by subtype

These are the default section structures. Stay within the count range from `01-asset-types.md` (policy 5–9, procedure 6–10, guideline 4–7, plan 5–9); add or merge sections to fit — do not skip numbering.

### policy (default 7 sections)

1. Purpose — why the policy exists
2. Scope — who / what it applies to
3. Definitions — key terms
4. Policy Statements — requirements (use "shall")
5. Roles and Responsibilities — who does what
6. Compliance and Exceptions — enforcement + exception process
7. Review and Maintenance — review cadence and change process

### procedure (default 8 sections)

1. Purpose — what the procedure accomplishes
2. Scope — when and where it applies
3. Definitions — key terms
4. Prerequisites — required inputs, access, tools
5. Procedure Steps — numbered actionable steps
6. Responsibilities — RACI matrix if complex
7. Records and Evidence — what to retain
8. References — related documents

### guideline (default 5 sections)

1. Purpose — what guidance this provides
2. Scope — who should follow it
3. Guidance by Topic — organised recommendations
4. Best Practices — recommended approaches
5. References — related resources

### plan (default 7 sections)

1. Purpose and Objectives — what the plan achieves
2. Scope — what is covered
3. Approach / Strategy — how objectives will be met
4. Timeline / Phases — key milestones
5. Resources Required — people, tools, budget
6. Success Criteria — how success is measured
7. Review Points — when to assess progress

## Worked example — policy

```markdown
# Data Protection Policy

## 1. Purpose

### 1.1 Scope of policy

This policy establishes [ORGANIZATION_NAME]'s requirements for lawful, transparent, and secure personal data processing, ensuring compliance with ISO 27001 A.18.1 and the UK GDPR.

### 1.2 Applicability

This policy applies to:

- All employees, contractors, temporary workers, and agency staff
- Data owners, data stewards, and department heads
- The Data Protection Officer (DPO) and senior leadership
- Third-party processors acting on behalf of [ORGANIZATION_NAME]

---

## 2. Definitions

- **Personal Data** — any information relating to an identified or identifiable natural person.
- **Special Category Data** — personal data revealing racial or ethnic origin, political opinions, religious beliefs, health, or biometric identifiers.
- **Processing** — any operation performed on personal data, including collection, storage, use, disclosure, and deletion.

---

## 3. Policy Statements

### 3.1 Lawful basis

[ORGANIZATION_NAME] shall identify and document a lawful basis under UK GDPR Article 6 for every processing activity before it begins.

### 3.2 Data minimisation

Personal data shall be adequate, relevant, and limited to what is necessary for the stated purpose. Collection of additional fields "in case they are useful" is prohibited.

### 3.3 Retention

Personal data shall be retained only for as long as required for the stated purpose and in line with the Records Retention Schedule. On expiry, data shall be securely deleted or irreversibly anonymised.

---

## 4. Roles and Responsibilities

| Role | Responsibility |
| --- | --- |
| Data Protection Officer | Advise on compliance, monitor processing, act as liaison with the ICO |
| Data Owners | Define lawful basis and retention for their datasets |
| All Staff | Report suspected personal-data breaches within 24 hours |

---

## 5. Compliance and Exceptions

Non-compliance with this policy may result in disciplinary action. Exceptions shall be requested in writing to the DPO and reviewed annually.

---

## 6. Review and Maintenance

This policy shall be reviewed every 12 months, or sooner following a material change in law, organisational structure, or processing activity. Changes shall be approved by the Information Security Steering Group.
```

## Updating an existing document (read-modify-write)

Revising a live `d_*` document is **higher risk than creating a new one**: the write replaces the whole body, so parser limitations damage content you did not touch. Four platform behaviours drive the procedure below (all verified 2026-08-10 against production):

1. **Markdown writes land in the document's shared WORKING COPY, silently.** Viewers keep seeing the last published version until someone clicks **Publish** in the web editor — but `get` AND `get --draft` both return the working copy, so **the CLI cannot show you what viewers currently see**; only the web UI document page shows the published body ("This asset contains unpublished changes" banner = they diverge). Two consequences: a CLI write is not immediately viewer-visible (safer than it looks), and CLI-based verification can never prove what is published (blinder than it looks). Any designer's UI session shares the same working copy your write just replaced.
2. **Last write wins, and there is no usable version signal.** Documents accept no `expectedVersion`, and the `version:` field in the fetched frontmatter is a **fetch timestamp, not a content version** — it changes on every `get`. To detect concurrent edits, hash the body with the `version:` line stripped and compare before writing.
3. **`get` returns YAML frontmatter that must NOT be written back.** The platform manages frontmatter itself; if the fetched frontmatter is included in the write, it is rendered as visible body text (a junk `## assetId: …` block under the title). Strip everything up to and including the closing `---` of the leading YAML block.
4. **Nested lists survive the WRITE but not the CLI READ-BACK.** The deserialiser stores nesting correctly (list-item → [paragraph, nested list]) and the web UI renders it properly; it is the read-side markdown serialiser that flattens nesting and prints parent+first-child merged on one line (`* Parent* Child`). So a corrupted-looking `get` after a nested-list write does NOT prove the stored tree is damaged — check the web UI before attempting any repair. It DOES mean round-trip editing is lossy in one specific way, see 5.
5. **Bold runs serialised as `**text **` (space inside the closing marker) die on round-trip.** The old serialiser emits that form; CommonMark cannot re-parse it as bold, so a fetched-and-rewritten body turns those runs into literal `**` glyphs in the document. Before writing a fetched body back, normalise every `**…: **` to `**…:** ` (move the space outside) — and grep the body for `\*\*[^*]+ \*\*` (excluding table-row false positives like `**A** | **B**`) until it is clean.

Procedure:

```bash
# 1. Snapshot the Slate tree FIRST — this is your only rollback source.
upscaler get <d_*> --format json > snapshot-slate.json

# 2. Fetch the markdown body and strip the leading YAML frontmatter block.
upscaler get <d_*> --json   # extract .data.json.text, drop through the closing '---'

# 3. Gate: count nested list items in the body.
grep -cE '^\s+[-*] ' body.md
#    If > 0, STOP — a markdown write will flatten them and merge parents into
#    children. Make the edit in the web editor, or write via --values-type
#    slateJson using the snapshot from step 1 as the base tree.

# 4. Apply edits with unique-anchor replacement (assert each old string occurs
#    exactly once), not wholesale regeneration.

# 5. Re-fetch immediately before writing; hash-compare (version: line stripped)
#    against the body you edited to rule out a concurrent edit.

# 6. Write, then VERIFY BY DIFF: fetch the live body and diff it against what
#    you intended to store. Do not verify by grepping for your new text —
#    presence checks confirm what you added and are blind to what the parser
#    destroyed elsewhere in the document.
```

Propose-then-confirm applies doubly here: show the user a diff of old vs new **before** the write, and warn explicitly that the change publishes immediately to every viewer group on the document.

## Attaching images and files

Attachment blocks live in the Slate tree with platform-managed UIDs. The URL form `./_attachments/<uid>.<ext>` requires a uid that the platform assigns at upload time, so it is **not** hand-authorable. Three workflows are viable.

### Workflow A — authored markdown plus post-create upload (most common)

1. `asset create --type document_definition --data @body.json --values-type markdown` — submit the body without any attachment URLs. Use a short inline placeholder where the image or file will appear, e.g. `*[Workflow diagram attached after publish]*`.
2. Open the document in the Upscaler editor and insert an Image block or File block at the placeholder location; this creates a Slate block with an `options.name`.
3. `upscaler asset upload-file --asset-id <doc> --field <options.name> --path <local>` populates the block with the local file. (Step 2 + 3 can also be done together in the editor's UI by drag-and-drop.)

### Workflow B — Slate JSON with pre-uploaded UIDs (advanced)

`asset create --values-type slateJson --data @body.json` where `body.json` is a Slate tree like:

```json
[
  {"type":"image","fileName":"diagram.svg","status":"uploaded","fileUid":"<uid>","children":[{"text":""}]},
  {"type":"file","options":{"name":"attachments"},"fileList":[{"uid":"<uid>","name":"checklist.md","type":"text/markdown","size":1234,"addedAt":"<ISO-8601 UTC>"}],"children":[{"text":""}]}
]
```

UIDs come from a prior upload step. Only worth this path when scripting batch uploads. Three details on the file block:

- `options.name` is the only key `upscaler asset upload-file --field` / `update-content --file` match on — a file block authored without it can never be targeted by the CLI later.
- `addedAt` is optional but is one of the five persisted `fileList` fields (`uid`/`name`/`type`/`size`/`addedAt`) and drives the 15-minute "uploading vs error" grace window when the S3 object is not yet visible; the CLI's own uploader always writes it.
- A `status` value in authored entries is stripped on write and recomputed from S3 on read, so including it is harmless but has no effect.

### Workflow C — inline `<format-*>` with pre-uploaded uids

Use this for scripted attachments and whenever you need to attach an **image**. `upscaler asset upload-file` and `update-content --file` only walk Slate `type: "file"` blocks; they ignore image blocks, so images can only be wired in via Workflow C (or the editor).

Hand-authored shape, once you hold the uids:

```html
<format-image fileUid="<uid>" fileName="diagram.svg"></format-image>

<format-file fileList='[{"uid":"<uid>","name":"checklist.md","type":"text/markdown","size":1234,"status":"done"}]'></format-file>
```

Same syntax is valid in registers, records, and courses. Full grammar and caveats live in `02-form-elements.md` → "Attachment elements".

Do **not** add a bare `name="..."` attribute to `<format-file>` hoping to make it CLI-addressable: the deserialiser hoists attributes to the **top level** of the Slate node, so `name` would not land in `options.name` and `--field` would not find it. If you need a CLI-targetable named block from this path, use a JSON `options` attribute — `<format-file options='{"name":"attachments"}' fileList='...'></format-file>` (attribute values starting with `{` are JSON-parsed) — or use Workflow B / the editor.

#### Getting uids: prefer the CLI

For **named file blocks** (`<format-file>` / `<format-image>` whose `options.name` you control), use the CLI — no scripting needed. It presigns, uploads to S3, and splices the uid into the named block for you:

```bash
# Upload into a named file block on an existing document_definition.
upscaler asset upload-file --asset-id <d_*> --field "<block name>" --path /abs/diagram.svg
# Or batch with update-content (validates Slate file blocks by options.name):
upscaler asset update-content --asset-id <d_*> --file "<block name>=/abs/checklist.md"
```

Note: `upscaler files presign` is a low-level escape hatch that **requires** `--asset-id` (it is a required option — it does *not* 422 for a missing asset_id; that earlier claim was wrong). You only need the scripted route below for cases the CLI sugar does not cover (e.g. minting a uid to hand-place in an inline image tag). The scripted workflow:

1. Create (or pick) the target `document_definition` so you have an `asset_id`.
2. For each attachment, `POST /api/v1/files/presign` with `{file_name, content_type, asset_id}` → returns `{uid, url, fields}`.
3. `POST` the file bytes to S3 as multipart form-data, merging `fields` into the form and putting the bytes under `file`.
4. `POST /api/v1/assets` with `operation: "update_content"`, the body markdown containing the `<format-image>` / `<format-file>` tags, and `valuesType: "markdown"`.

```python
import asyncio, json, sys
from pathlib import Path

# Point at the editable install of the SDK on this machine.
sys.path.insert(0, "/path/to/upscaler/packages/up-sdk/src")
import httpx
from src.auth.token_store import TokenStore
from src.client import UpscalerClient
from src.config import CLIConfig

ASSET_ID = "d_..."           # existing document_definition id
PROFILE = "dev"
SVG = Path("/abs/diagram.svg")
MD = Path("/abs/checklist.md")

async def presign(client, name, ctype):
    return await client.request(
        "POST", "/api/v1/files/presign",
        json={"file_name": name, "content_type": ctype, "asset_id": ASSET_ID},
    )

async def s3_post(envelope, path, ctype):
    files = {"file": (path.name, path.read_bytes(), ctype)}
    async with httpx.AsyncClient(verify=False, timeout=60.0) as s3:
        resp = await s3.post(envelope["url"], data=envelope["fields"], files=files)
        resp.raise_for_status()

async def main():
    cfg = CLIConfig(profile=PROFILE)
    client = UpscalerClient(
        cfg.resolve_server_url(None),
        TokenStore(profile=PROFILE),
        verbose=False,
        verify_ssl=cfg.resolve_verify_ssl(),
    )

    svg_env = (await presign(client, SVG.name, "image/svg+xml"))["data"]
    await s3_post(svg_env, SVG, "image/svg+xml")
    md_env = (await presign(client, MD.name, "text/markdown"))["data"]
    await s3_post(md_env, MD, "text/markdown")

    md_file_list = json.dumps([{
        "uid": md_env["uid"], "name": MD.name,
        "type": "text/markdown", "size": MD.stat().st_size, "status": "done",
    }])
    body = f'''# My Document

## 1. Purpose

Body prose.

<format-image fileUid="{svg_env["uid"]}" fileName="{SVG.name}"></format-image>

<format-file fileList='{md_file_list}'></format-file>
'''

    await client.request(
        "POST", "/api/v1/assets",
        json={
            "operation": "update_content",
            "asset_id": ASSET_ID,
            "data": {"values": body, "valuesType": "markdown"},
        },
    )

asyncio.run(main())
```

Verify with `upscaler get <asset_id> --format markdown` — image attachments round-trip as `![<name>](<name>)`, file attachments as `[📎 <name>](<name>)`. If either renders as `![]()` the uid did not resolve; re-check the presign `asset_id` and the S3 POST response.

### Markdown serialisation reference

When `upscaler get <doc> --format markdown` round-trips a Slate document, attachment blocks render as:

| Slate `type` | Round-trip output | Hand-authorable input |
| --- | --- | --- |
| `image` | `![filename](./_attachments/<uid>.<ext>)` | `<format-image fileUid="<uid>" fileName="...">` |
| `file` | `[📎 filename](./_attachments/<uid>.<ext>)` | `<format-file fileList='[{...}]'>` |
| `data-table` | Fenced ` ```yaml ` block with a `table:` root key (columns, sourceType, sourceId) | — |
| `data-chart` | Fenced ` ```yaml ` block with a `chart:` root key (chartType, sourceType, sourceId, axes) | — |

**Do not hand-author the URL forms.** The platform strips URLs that don't resolve to known uploaded files, leaving an empty `![alt]()`. Use Workflow A, B, or C. (The web editor does have a from-URL image form, `{ type: "image", href }`, created when pasting `<img>` HTML in the UI, but it is not reachable from markdown: `![alt](url)` deserialises to a dead `url` field the editor never renders, and any URL-form image serialises back as `![alt]()`, so only uploaded `fileUid` images survive the markdown round-trip.)

## Common mistakes

- Nested/indented list items in any markdown write — the deserialiser flattens them and merges each parent into its first child (`* Parent* Child`). Flat lists only; see "Allowed block types".
- Round-tripping a fetched document (frontmatter and all) back through `update-content` — strip the leading YAML block first, gate on nested lists, and diff after writing. See "Updating an existing document".
- Two `# H1` headings in one document (only the title is H1).
- Numbered `## H2` but unnumbered `### H3` — numbering must be consistent.
- A trailing `---` at the end of the document.
- `<form-*>` field widgets in a document — those belong in registers/records only. Slate `image`, `file`, and `data-table` attachment blocks are fine.
- Hand-authoring `![alt](./diagram.svg)` or any local-path image URL — the platform strips unknown URLs. Use Workflow A, B, or C instead.
- Inventing new `<format-*>` tags; only `format-image` and `format-file` are recognised, anything else is silently dropped.
- Tables used for layout instead of structured comparison.
- YAML frontmatter or a metadata block — the platform supplies this.
