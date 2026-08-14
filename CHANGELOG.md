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

- **Repository split.** This library was previously distributed as part of `upscaler-io/agent-skills` under the plugin name `upscaler-platform`. Five advanced workflow skills moved to [`upscaler-adv-skills`](https://github.com/upscaler-io/upscaler-adv-skills): `upscaler-prep-evidence`, `upscaler-review-design`, `upscaler-setup-framework`, `upscaler-prep-management-review`, and `upscaler-report-status`. Existing installs of `upscaler-platform` should be replaced with `upscaler-skills` (plus `upscaler-adv-skills` for the advanced set).
- `upscaler-ask` no longer routes unconditionally to the advanced spokes. Its new "Workflows outside this library" section treats them as optional: route if the skill is loaded, otherwise answer the read-only part of the request and stop. Installing `upscaler-adv-skills` restores full routing through that repo's `upscaler-adv-routing` overlay skill.
- `upscaler-write-entry`'s "When NOT to use" list now names the advanced skills as separately shipped rather than as installed siblings.
- `references/personas.md` lists only the skills that ship in this repo, and points at `upscaler-adv-skills` for the rest.
- `scripts/build_bundle.py` derives the bundle name from `.codex-plugin/plugin.json` instead of hard-coding it, so the zip name tracks the plugin name.

### Removed

- `references/posture-collection.md` — moved to `upscaler-adv-skills`, where its only two consumers now live.
