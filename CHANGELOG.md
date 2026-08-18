# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) as carried in `.codex-plugin/plugin.json`.

## [Unreleased]

## [1.1.0] - 2026-08-18

### Added

- README "Related projects" section linking [`upscaler-cli`](https://github.com/upscaler-io/upscaler-cli). The CLI that every skill falls back to when MCP is not configured is now open source under MIT, so the fallback path has readable source and its own issue tracker.
- `references/upscaler-access.md` gains a "HITL write contract" section and mapping rows for the draft surface (`upscaler_manage_entry` with `operation:"save_task_draft"` / `entry save-draft`, and the plain record read that verifies a task draft). The HITL tool swap had been documented only inside the two write skills, so the shared reference (the single source of truth for the tool mapping) still described the pre-HITL surface.
- `upscaler-ask` gains an entry status vocabulary covering `PENDING → DRAFT → COMPLETED`. Its register recipes tally entries by status, and the HITL draft-states release both adds `PENDING` as the birth state of a non-imported entry and re-projects history so never-completed entries reclassify from `DRAFT` to `PENDING`. The note says to count only COMPLETED rows as live register data, and that non-editors see neither PENDING nor DRAFT, so the same question returns different counts for different callers.
- `upscaler-write-entry` gains an "Errors an agent may see" section (`DRAFT_NOT_AVAILABLE`, `VALUE_VALIDATION_ERROR`), matching the one `upscaler-run-record` already carried, plus a note that `HITL_FINALIZED` does not apply to register entries.
- `upscaler-run-record` documents `TASK_SKIPPED`: a skipped task rejects a draft save just as a completed one does.
- The plugin manifests and `llms.txt` no longer advertise "record completion": all distribution-facing descriptions now say agents draft records and a human completes each task, matching the HITL contract the skills themselves teach.

### Changed

- The CLI setup hint in `references/upscaler-access.md` no longer tells users to set `server_url` before logging in. The CLI now defaults to Upscaler's production API, so `pip install upscaler-cli && upscaler login` is the whole setup. Pointing at a different host is presented as the self-hosted case instead, which stops the printed hint from implying a step most users do not need.
- The MCP option in the setup message now gives real connect instructions: the actual Claude Code command (`claude mcp add --transport http upscaler https://ai.upscaler.app/mcp`) and the server endpoint URL for any other MCP client. The previous text printed a command that does not exist (`/mcp add upscaler`) and linked a docs URL that never resolved.
- Support is a single channel: the issue-template contact link and a new README "Support" section route platform questions to support@upscaler.io, and skill matters to this repo's issues.
- Internal codenames removed from user-facing prose (the platform web app is now called "the Upscaler app"), and the LICENSE copyright holder corrected to Upscaler Limited.

### Fixed

- `upscaler-run-record` verified a saved task draft with `get <r_*> --draft`. That flag only switches an `rd_*` **schema** read to the unreleased working copy of the definition; on an `r_*` it is ignored. The draft is read from the plain record JSON instead, where the task carries `status: DRAFT` and its own `values`. Step 7 now says so, and the worked example no longer verifies a draft with the committed-values list.
- `upscaler-write-entry` told the agent to confirm a pending revision "from the mutation response". The response echoes the entry's live values, which a revision deliberately leaves unchanged, so it reads as a failed write. An error-free call is now documented as the whole receipt, since the stashed proposal has no agent-readable surface.
- `references/form-filling.md` still sent agents to `get <r_*> --draft` and still described a register create as landing DRAFT unconditionally. The shared core now carries the same corrected record read-back as `upscaler-run-record`, adds the register pending-revision case, and distinguishes a values-carrying create (DRAFT) from a title-only create (PENDING, the birth state of a non-imported entry).
- `upscaler-ask` claimed `upscaler-run-record` "completes their tasks", the one capability the HITL draft-states release removed. It now says the spoke drafts tasks for a human to complete, and that no write-capable spoke finalizes.
- `upscaler-write-entry` told agents to send `expectedVersion` on `mergeItemValues`. Agent value writes go through `saveItemDraft`, deliberately separate from the human apply path, and expose neither `expectedVersion` nor `appliedDraftId`. The anti-pattern now names `mergeItemValues` / `setItemValues` / `discardItemDraft` as the reviewer's mutations and says not to reach for them.
- `compatibility:` on both write skills now states a floor of `upscaler` CLI >= 0.3.0, the release where `entry complete-task` was removed and `entry save-draft` added.
- **Source-verified sweep of every skill against the platform and CLI codebases.** The wrong-as-written items, all corrected:
  - `upscaler_save_task_draft` was documented as a callable MCP tool in five places; it does not exist on the MCP surface (the native function is deliberately unregistered). The only agent path is `upscaler_manage_entry({operation:"save_task_draft", …})`.
  - `--filter "<Label>=<value>"` examples in `upscaler-ask` and the access reference: `--filter` does no label resolution (only `--select-value` does), so a label predicate silently matches nothing. Examples now use the raw `ff_*` key and say to resolve the label from the schema first.
  - `upscaler-ask` called `--select-value` labels case-sensitive in one place and case-insensitive in another; the CLI casefolds, so case-insensitive is correct.
  - `upscaler_search_nodes({asset_types:["record"]})` in `upscaler-run-record` resolved record *instances* while the surrounding recipe needed the `rd_*` definition; now `record_definition`. The access reference's alias list (`record` is a first-class enum, not an alias) is fixed to the real three-entry alias map.
  - `form-lookup` `filterParentId` examples emitted an array of plain id strings, which the platform validator rejects outright ("Source [0] must be an object."); now the `{label, key, value}` object shape, matching `recordDefinitions`.
  - `<note type="default">` is not a legal note type (the enum is `info | question | success | warning | error`); the stale `chartType: pie | column | line` restriction was lifted platform-side on 2026-08-03 (`bar` / `area` now pass).
  - The nested-list story was backwards: nesting is stored correctly on write and corrupted by the markdown *read-back*, so the flat-list gate matters for read-modify-write, not greenfield writes. The `_attachments/<uid>` round-trip form is export-bundle-only; CLI reads emit plain `![<name>](<name>)`. The "Slate snapshot" rollback step in the update procedure asked for a read no agent surface provides and now snapshots the markdown body instead.
  - `record_link` values are `{value, label}` objects (array only when `multiple`), not "an array of record ids"; the member `{value, label}` shape is canonical for both containers, not records-only.
  - The access reference contradicted `form-filling.md` on `field_options`: select/radio options are always inlined and `field_options` returns an empty list for them.
  - The platform option validator requires a non-empty `title` on nearly every field (not just `name`), and validation warnings reject writes just like errors; the enforced-tier lists and checklist now say so.
- Precision notes added from the same sweep: `TASK_SKIPPED` and `VALUE_VALIDATION_ERROR` are agent-envelope codes (a backend-side value rejection surfaces as `VALIDATION_ERROR`, now documented); pending register revisions are readable by the Upscaler app's editor-gated `itemDraft` query, just never by agents; a values-carrying entry **create** runs the required-field pass fail-closed, unlike later draft updates; an item draft save notifies the register definition's creator; the field-type enumeration gains `auto_increment`, `assessment`, `asset_picker`, `diagram`; `upscaler_list` caps `limit` at 100; the self-closing-tag and attribute-quoting rules are house style, not parser rules; `get` prefix routing coverage and the CLI's default server constant are stated as shipped.

## [1.0.0] - 2026-08-14

First release of `upscaler-skills` as a standalone repository.

### Added

- Four core skills, carried over from `upscaler-io/agent-skills` at the point of the split:
  - `upscaler-ask` — compliance-manager Q&A hub, framework-agnostic, read-only, routes to the spokes below.
  - `upscaler-author-asset` — authoring and read-modify-write updates of Upscaler asset definitions (policies, procedures, registers, record definitions, courses).
  - `upscaler-write-entry` — create and update register entries (`i_*`) inside an existing register (`rg_*`).
  - `upscaler-run-record` — create record instances (`r_*`) from a record definition (`rd_*`) and drive their task flow end to end.
- Shared references `references/upscaler-access.md` (MCP → CLI → setup connection priority), `references/form-filling.md` (form-filling core shared by `upscaler-write-entry` and `upscaler-run-record`), and `references/personas.md`.
- Claude Code plugin (`upscaler-skills` in the `upscaler` marketplace), OpenAI Codex CLI plugin manifest, ChatGPT per-skill packager, and single-bundle packager.
- `scripts/build_editor_bundles.py`, a stdlib-only packager for the two supported agents that have no Agent Skills loader. Produces `dist/editors/cursor-rules.zip` (one agent-requested `.mdc` rule per skill, laid out to unzip straight into `.cursor/rules/`) and `dist/editors/gemini-context.zip` plus a standalone `GEMINI.md`. Flattening a skill breaks its `../../references/…` and skill-local links, so both bundles carry every linked file under `upscaler-skills-refs/` with the links rewritten — in the SKILL.md body and inside bundled support files, which carry their own links. The reference root derives from the plugin name so a second Upscaler bundle unzipped into the same project cannot overwrite a shared reference that differs between them. The build then re-reads each archive and fails on any relative link that does not resolve.
- `.github/workflows/package.yml`. Builds the offline bundle, the ChatGPT per-skill zips, the Cursor rules, and the Gemini context file on every push, pull request, and manual dispatch, and publishes them to a GitHub Release on a `v*` tag. Splits build from publish so only the tag-gated release job holds a write-scoped token, and fails a tag whose version disagrees with `.codex-plugin/plugin.json`. Release asset names are stable across versions, so `releases/latest/download/<asset>` keeps resolving.

### Changed

- **Repository split.** This library was previously distributed as part of `upscaler-io/agent-skills` under the plugin name `upscaler-platform`, alongside five workflow skills that are not part of this release. Existing installs of `upscaler-platform` should be replaced with `upscaler-skills`.
- `upscaler-ask` no longer routes unconditionally to workflows this library does not cover. Its new "Workflows outside this library" section treats them as optional: if a skill covering the workflow is loaded in the session, route to it; otherwise answer the read-only part of the request and stop.
- `upscaler-write-entry`'s "When NOT to use" list now marks evidence-pack and Test-binding requests as out of scope rather than routing them elsewhere.
- `references/personas.md` lists only the skills that ship in this repo.
- `scripts/build_bundle.py` derives the bundle name from `.codex-plugin/plugin.json` instead of hard-coding it, so the zip name tracks the plugin name.
- README documents Cursor and Gemini CLI as package downloads with stable `releases/latest/download/` URLs, replacing the hand-conversion instructions those two agents previously needed.

### Removed

- `references/posture-collection.md`, whose only consumers are not part of this release.
