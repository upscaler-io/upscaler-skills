# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) as carried in `.codex-plugin/plugin.json`.

## [Unreleased]

### Added

- README "Related projects" section linking [`upscaler-cli`](https://github.com/upscaler-io/upscaler-cli). The CLI that every skill falls back to when MCP is not configured is now open source under MIT, so the fallback path has readable source and its own issue tracker.

### Changed

- The CLI setup hint in `references/upscaler-access.md` no longer tells users to set `server_url` before logging in. The CLI now defaults to Upscaler's production API, so `pip install upscaler-cli && upscaler login` is the whole setup. Pointing at a different host is presented as the self-hosted case instead, which stops the printed hint from implying a step most users do not need.

### Fixed

- `upscaler-run-record` verified a saved task draft with `get <r_*> --draft`. That flag only switches an `rd_*` **schema** read to the unreleased working copy of the definition; on an `r_*` it is ignored. The draft is read from the plain record JSON instead, where the task carries `status: DRAFT` and its own `values`. Step 7 now says so, and the worked example no longer verifies a draft with the committed-values list.
- `upscaler-write-entry` told the agent to confirm a pending revision "from the mutation response". The response echoes the entry's live values, which a revision deliberately leaves unchanged, so it reads as a failed write. An error-free call is now documented as the whole receipt, since the stashed proposal has no agent-readable surface.

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
