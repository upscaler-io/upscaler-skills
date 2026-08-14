# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) as carried in `.codex-plugin/plugin.json`.

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

### Changed

- **Repository split.** This library was previously distributed as part of `upscaler-io/agent-skills` under the plugin name `upscaler-platform`, alongside five workflow skills that are not part of this release. Existing installs of `upscaler-platform` should be replaced with `upscaler-skills`.
- `upscaler-ask` no longer routes unconditionally to workflows this library does not cover. Its new "Workflows outside this library" section treats them as optional: if a skill covering the workflow is loaded in the session, route to it; otherwise answer the read-only part of the request and stop.
- `upscaler-write-entry`'s "When NOT to use" list now marks evidence-pack and Test-binding requests as out of scope rather than routing them elsewhere.
- `references/personas.md` lists only the skills that ship in this repo.
- `scripts/build_bundle.py` derives the bundle name from `.codex-plugin/plugin.json` instead of hard-coding it, so the zip name tracks the plugin name.

### Removed

- `references/posture-collection.md`, whose only consumers are not part of this release.
