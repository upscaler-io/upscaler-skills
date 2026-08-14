# 07 — Pre-submit validation checklist

Run this checklist **before returning** any generated asset definition. Every item must be satisfied. Items are enforced at different tiers: block-level items (whitelist membership, required attributes, parseable JSON values) are checked by the platform's `validateBlocks` on write; structural conventions (counts, heading style, language register) are not checked at publish but mirror the ranges the platform's own AI generator enforces, so treat them as mandatory self-checks. See "Universal rules" in `SKILL.md` for the full enforcement-tier model.

## Universal checks (all categories)

1. **Category and subtype are valid.** Check `01-asset-types.md`. Category must be one of `document | register | record | course`. Subtype must be one of the listed values for that category.
2. **Count is within the subtype range.** Same table in `01-asset-types.md`. Sections / tasks / lessons must fall within `[min, max]`. The publish path does not enforce this (a 4-section policy still publishes), but the ranges match the platform generator's own hard limits, so fix any out-of-range count before returning: "3 sections for a policy" (min is 5) and "11 sections for a procedure" (max is 10) must both be corrected.
3. **No YAML frontmatter, no metadata block.** Do not emit version, effective date, owner, review date. The platform supplies this.
4. **No trailing blank lines, no trailing `---`.** Output ends on the last content line.
5. **Every `<form-*>` element is from the 17-element whitelist** in `02-form-elements.md`. Reject invented names. `form-framework-requirement-picker` is a real platform block, not an invented name, but it still fails this check: the markdown deserialiser silently drops it on save, so strip it and warn the user before re-submitting a definition that contains it.
6. **Every form field `name` matches `^ff_[A-Za-z0-9]{28}$`** (base62 only — no underscore, no hyphen). Run `python3 scripts/generate_field_id.py --check <id>` if unsure. Never hand-craft IDs. An id with characters outside `[A-Za-z0-9_]` (e.g. a hyphen) is silently dropped by `select_values`, so the field stops resolving even though create succeeds.
7. **Every form field `name` is unique** across the entire asset.
8. **Every HTML attribute value is quoted.** `required="true"`, never `required=true`, never `required="True"`, never bare `required`.
9. **Rating `form-radio` uses the fixed colour scale.** `green → cyan → gold → orange → volcano` (or `magenta` for the very top).
10. **Yes/No `form-radio` uses `optionType="button"`** with Yes=`volcano`, No=`green`.
11. **`form-checkbox` `values` is a JSON array of plain strings**, not objects.
12. **`form-select` and `form-radio` `values`** use **single-quoted** JSON (`values='[...]'`), never double-quoted.

## Document checks

13. Exactly one `# H1` — the document title, first line.
14. All `##` are numbered: `## 1. Name`, `## 2. Name`, …
15. All `###` are numbered: `### 1.1 Name`, `### 1.2 Name`, …
16. No heading level is skipped (no H2 → H4).
17. `---` appears between `##` sections only. Not between `#` and first `##`. Not after the last `##`.
18. **No `<form-*>` field widgets** in documents (those are register/record-only). Image, file, and data-table attachment blocks ARE permitted — they're Slate-native and attached via `upscaler asset upload-file` after publish; see `03-document-authoring.md`. The markdown-authorable content blocks (`quote`, `code-block`, `mermaid`, `divider`, `grid`, `note`, `embed`) are also permitted; `toc` and `data-chart` cannot be authored in markdown.
18a. **No hand-authored image/file URLs.** `![alt](./local-path.svg)` and similar are silently stripped on save (the markdown round-trips as `![alt]()`). Attachments must come from the upload path.
18b. **`<format-image>` / `<format-file>` are the only authorable HTML attachment tags.** Valid in any asset category. Other `<format-*>` tags are dropped. Full grammar in `02-form-elements.md` → "Attachment elements".
18c. **No nested/indented list items** (`grep -E '^\s+[-*] '` must return nothing). The markdown deserialiser flattens nesting and merges each parent bullet with its first child into one corrupted line. Flat lists only; restructure sub-items as flat bullets under a bolded lead-in, a table, or `<ul><li>` inside a table cell.
19. Language register matches the subtype:
    - `policy` uses "shall" for mandatory requirements.
    - `procedure` uses imperatives.
    - `guideline` uses "should" / "may".
    - `plan` uses future-tense objectives.

## Update-in-place checks (writes to an EXISTING asset)

These apply on top of the document checks whenever the write targets an existing `d_*` rather than a create. Full procedure in `03-document-authoring.md` → "Updating an existing document".

19a. **Pre-write body captured** (`upscaler get <d_*> --json`, body extracted). Writes replace the shared working copy with no version check; note `--format json` returns markdown, not the Slate tree, and the CLI can never read the published body — only the web UI shows it.
19b. **Fetched YAML frontmatter stripped** from the body being written. Writing it back renders it as visible body text.
19c. **Broken bold runs normalised**: every `**…: **` (space inside the closing marker, as the platform serialiser emits) rewritten to `**…:** ` before writing back, else those runs become literal `**` glyphs. Check `grep -E '\*\*[^*]+ \*\*'` is clean (ignore `**A** | **B**` table false positives).
19d. **Concurrent-edit check done**: re-fetch immediately before writing and hash-compare bodies with the `version:` line stripped (it is a fetch timestamp, not a content version).
19e. **Post-write verification is a DIFF of live vs intended PLUS a web-UI render check.** The CLI read-back shows nested lists flattened/merged even when they are stored and rendered correctly — do not "repair" based on CLI output alone, and do not trust grep-for-added-text as verification.
19f. **Publish step accounted for.** The write leaves the document in "unpublished changes" state; viewers see the old version until a designer clicks Publish in the editor. Tell the user this explicitly.

## Register checks

20. One `# H1` — the register title.
21. Each section starts `## N. Title`, blank line, `---`, blank line, first field.
22. `---` appears only between `##` and the first field — never after fields.
23. Total field count is 10–20+ (at least 3–5 required).
24. Every field has `guidance` (2–4 sentences, never a single word). Every field type that takes `placeholder` also has one; `form-radio`, `form-checkbox`, and `form-recordlink` take no `placeholder` — do not author it on them (the platform stores it but never renders or validates it), and do not fail registers that omit it there.
25. Auto-increment prefix uses 3–4 uppercase letters + `-` (e.g. `RSK-`, `IMP-`, `AUD-`).

## Record checks

26. **One Markdown body per task**, not a single blob with `# Task N:` boundaries. Each task body file contains **no `#` headings at all** — only `##`. Task titles live in the definition payload, not in any body.
27. The publish payload is a definition shell (`{title, description?}`) plus an ordered list of task titles and matching body files — ready to feed into `asset create` + N × (`asset add-task` + `asset set-task-values`).
28. Inside each task body, only `##` headings are used (no `#`, no `###`).
29. Sections inside a task body follow `## Heading` → blank → `---` → blank → field pattern.
30. **Field IDs are unique across the entire record** (not per-task).
31. Language is factual and objective. Past tense for completed actions, present tense for ongoing status.
32. Workflow type (`sequential` / `parallel` / `sequential_parallel`) matches the agreed plan, with matching `set-task-condition` calls planned for every task that has a non-open condition.

## Course checks

33. **No asset-level `# H1`.** The course title is in platform metadata.
34. Each lesson boundary is `# Lesson N: Title` and titles match the agreed plan.
35. Inside a lesson, only `##` headings are used.
36. Section order within a lesson: Training video → Learning objectives → content sections → (optional hands-on exercise) → **Assessment**.
37. **Exactly one `<form-assessment>` per lesson**, and it is the last section.
38. Each assessment has **≥3 questions**; each question has **exactly 3 answers** with **exactly one `isCorrect: true`** (this skill's authoring convention, matching the platform's own course-generator style; the platform validator only type-checks `questions`/`answers`/`isCorrect` and fully supports multiple correct answers, graded by exact-set match — do not flag existing multi-correct assessments as invalid).
39. Assessment attributes use **single quotes**: `name='ff_...'`, `title='Lesson N: Assessment'`, `required='true'`, `questions='[...]'`.
40. **No apostrophes anywhere inside `label` strings.** (`"the organisation"`, not `"the organisation's"`.) Scan with a regex or visually.
41. Assessment `name` is a fresh `ff_` + 28-char ID; unique across the entire course.
42. Question `id`s are sequential `q1`, `q2`, … and answer `id`s are `a1`, `a2`, `a3` — **not** generated field IDs.
43. Only `form-assessment` is used as a form element in courses. No `form-text`, `form-select`, etc.
44. Every lesson starts with a `[Video placeholder: topic]`.

## Quick scan commands

```bash
# Count field IDs and check for duplicates
grep -oE 'ff_[A-Za-z0-9]{28}' output.md | sort | uniq -d

# Check ID format (flags any id with a non-base62 char or wrong length)
grep -oE 'name="ff_[^"]*"' output.md | grep -v -E 'name="ff_[A-Za-z0-9]{28}"'

# Check single-quoted assessment attributes
grep -n 'form-assessment' output.md | grep -v "name='"

# Check for apostrophes inside assessment label strings
grep -oE '"label":"[^"]*'\''[^"]*"' output.md

# Nested-list gate (18c / 19c) — must return 0
grep -cE '^\s+[-*] ' output.md
```

If any command above produces output, fix the issue before returning the asset.
