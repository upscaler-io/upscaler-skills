# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

Public distribution point for the **core** Claude Code agent skills that integrate with the Upscaler platform. Users clone or copy entries from `skills/` into `~/.claude/skills/` or `.claude/skills/`. This repo is **not** an application — it is a curated library. Changes land as skill additions, edits to skill content, or tooling that validates skills.

Several compliance workflows are deliberately out of scope (evidence assembly, design-doc gap review, framework setup, management review, status reporting). Nothing in this repo may depend on a skill outside it being installed.

## Library shape: hub-and-spoke

The skills form a hub-and-spoke. `upscaler-ask` is the entry point that answers compliance-manager questions and **routes** to a specialist skill when the user's intent is a workflow rather than a question. The core spokes are `upscaler-author-asset`, `upscaler-write-entry`, and `upscaler-run-record`. Treat this shape as load-bearing: new workflow skills become new spokes that `upscaler-ask` routes to; new question categories extend the hub. `upscaler-write-entry` and `upscaler-run-record` share one form-filling core (`references/form-filling.md`); changes to value shapes or context-derivation rules go there, not into either skill.

Five workflow shapes are deliberately **out of scope**: evidence assembly, design-doc gap review, framework setup, management review, and status reporting. `skills/upscaler-ask/SKILL.md` handles them in its "Workflows outside this library" section, written so an externally supplied skill can take over: if one covering the workflow is loaded in the session, route to it; if not, answer the read-only part of the request and stop rather than half-building the artifact. Keep that section generic, so **this repo never needs editing when such a skill appears**.

Every skill follows the **MCP → CLI → setup** connection priority: prefer Upscaler MCP tools (names match `upscaler_*`), fall back to the `upscaler` CLI with `--json`, and print the verbatim setup message and stop when neither is available. The shared pattern lives at `references/upscaler-access.md` — link to it rather than duplicating the prose. Do not mix tiers in one workflow.

## Repository layout

- `skills/<skill-name>/SKILL.md` — the skill entry point. YAML frontmatter (`name`, `description`, optional `license`, `compatibility`, `metadata`) tells the agent when to trigger the skill; markdown body tells the agent how to execute. Supporting files (`scripts/`, `references/`, `assets/`, data) live alongside.
- `skills/upscaler-author-asset/` is the one skill large enough to route its own detail, and the pattern is worth copying. Its `references/` are **numbered by load order**: `01-asset-types.md` and `07-validation-checklist.md` are always read (first and last), and the middle files load by asset category (`03` for documents, `02` + `04` for registers, `02` + `05` for records, `02` + `06` for courses). The routing table lives at the bottom of its `SKILL.md`; extend that table when adding a reference rather than inlining prose. Alongside it: `examples/sample-register-all-blocks.md` (one register exercising every block type) and `scripts/generate_field_id.py`, which mints and `--check`s base62 `ff_<28 chars>` field IDs. Field IDs must be base62: the platform's `select_values` regex silently drops a hyphenated key, so a hand-invented ID projects to nothing.
- `references/` — **repo-root shared references** loaded on demand by every skill via relative path (`../../references/<file>.md`). Lives outside `skills/` because the validator iterates every directory under `skills/` and expects a `SKILL.md` in each; non-skill folders there would fail validation.
  - `references/upscaler-access.md` — MCP → CLI → setup connection priority, tool/command mapping, verbatim setup message. Update whenever the platform's tool surface changes.
  - `references/personas.md` — three target personas (compliance manager, engineer/PM, author) and how each skill calibrates output. Compliance manager is the primary persona; auditor is **not** a target persona.
  - `references/form-filling.md` — the form-filling core shared by `upscaler-write-entry` (register entries) and `upscaler-run-record` (record tasks): schema-first key resolution, per-type value shapes, deriving values from the parent asset and its referenced assets, read-back tolerances.
- `docs/skill-template/` — copy this directory as the starting point for every new skill. Keep it in sync with the current format. Lives outside `skills/` because its placeholder `name` is not a real skill.
- `scripts/build_chatgpt_skills.py` — stdlib-only packager for ChatGPT's per-skill upload flow (Settings → Skills → "Upload from your computer"). Stages each skill, inlines the repo-root shared references it links under `references/shared/`, rewrites the `../../references/…` links, and zips to `dist/chatgpt/<skill>.zip` (gitignored). Re-run after any change to a skill or a shared reference; the zips are build artifacts, never edit them.
- `scripts/build_bundle.py` — stdlib-only packager for the whole library as one installable bundle, `dist/upscaler-skills.zip` (gitignored). Keeps the repo shape, so `skills/` sits next to the repo-root `references/` and every `../../references/…` link still resolves without rewriting; carries both plugin manifests so an unzipped copy installs as a local Claude Code or Codex plugin. Repo-root `scripts/`, `.github/`, and OS/editor noise are left out; the allow-list is `BUNDLE_ENTRIES`. The bundle name and version are both read from `.codex-plugin/plugin.json`, the only manifest carrying semver, so the zip name tracks a rename automatically.
- `scripts/build_editor_bundles.py` — stdlib-only packager for the two agents with no Agent Skills loader. Emits `dist/editors/cursor-rules.zip` (one `.mdc` per skill under `.cursor/rules/`, frontmatter converted to Cursor's `description`/`globs`/`alwaysApply`) and `dist/editors/gemini-context.zip` plus a standalone `dist/editors/GEMINI.md` (every skill concatenated). Both flatten the skill, so every `../../references/…` and skill-local link is rewritten to a bundled copy under `upscaler-skills-refs/`; the build then re-reads each archive and fails if any rewritten link does not resolve inside it.
- `scripts/validate_skills.py` — stdlib-only validator aligned with the [Agent Skills spec](https://agentskills.io/specification). Parses frontmatter in every `skills/*/SKILL.md`, enforces required fields, name/description constraints, and directory match. Also lints `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `.codex-plugin/plugin.json` if present. Run locally with `python3 scripts/validate_skills.py`; CI runs the same script.
- `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` — Claude Code plugin manifest and marketplace catalog. Together they make this repo installable via `/plugin marketplace add upscaler-io/upscaler-skills` and via `npx skills add upscaler-io/upscaler-skills` (Vercel skills.sh discovers the same files). The bundled plugin is named `upscaler-skills`, the marketplace `upscaler`. Plugin uses `source: "./"` so the repo root doubles as the plugin directory; `skills/` under the root is auto-discovered. No `version` field — git SHA versioning means every commit ships an update.
- `.codex-plugin/plugin.json` — OpenAI Codex CLI plugin manifest ([format](https://developers.openai.com/codex/plugins/build)). Same `upscaler-skills` plugin name, with `skills: "./skills/"` pointing back at the shared skills directory. Codex requires a semver `version` field (unlike Claude's manifest), so bump it on each release. No accompanying Codex marketplace catalog: Codex's marketplace.json constrains `source.path` to be inside the marketplace root, which doesn't fit a single-plugin-as-repo layout. Users install via `codex plugin marketplace add upscaler-io/upscaler-skills` then `codex plugin install upscaler-skills`, or fall back to `npx skills add` / direct copy into `~/.codex/skills/` or `.agents/skills/`.
- `.github/workflows/validate.yml` — runs the validator on every push/PR. Update validator + workflow together when the skill format evolves.
- `.github/workflows/package.yml` — builds every distributable package on push, PR, and manual dispatch, and publishes them to a GitHub Release on a `v*` tag. Two jobs: `build` runs with a read-only token, `release` is the only one granted `contents: write` and is gated on the tag. A tag whose version disagrees with `.codex-plugin/plugin.json` fails the build rather than shipping a mislabelled release. Release asset names are stable across versions so `releases/latest/download/<asset>` keeps working; add a new packager here **and** to the staging step when a new agent needs one.
- `llms.txt` — `llms.txt` index for LLM discovery. Lists every skill, the shared references, install routes, and the API tiers. Update alongside any rename, new skill, or breaking change.

## Common commands

```bash
# Validate every skill in skills/
python3 scripts/validate_skills.py

# Validate a single skill directory (skips the three manifest lints;
# only the argument-less run checks plugin.json / marketplace.json)
python3 scripts/validate_skills.py skills/upscaler-author-asset

# Scaffold a new skill from the template
cp -r docs/skill-template skills/my-new-skill

# Package skills as self-contained zips for ChatGPT upload (output: dist/chatgpt/)
python3 scripts/build_chatgpt_skills.py

# Package the whole library as one installable bundle (output: dist/upscaler-skills.zip)
python3 scripts/build_bundle.py
python3 scripts/build_bundle.py --force   # package a spec-invalid tree anyway

# Package Cursor rules and the Gemini context file (output: dist/editors/)
python3 scripts/build_editor_bundles.py
python3 scripts/build_editor_bundles.py cursor   # one target only ("cursor" | "gemini")
```

`build_bundle.py` runs the validator itself and refuses to package a failing tree without `--force`. The other two packagers do not validate, so run `validate_skills.py` before trusting their output.

No build step, no package manager. The validator is the full pre-commit check; the only tests in the repo are the `upscaler-ask` evals below, which cost real money and are not part of that check.

### Skill evals (`upscaler-ask` only)

`skills/upscaler-ask/evals/` holds two harnesses over one shared 23-query set (`trigger_eval.json`: 15 positives across every answer category, 8 tricky near-miss negatives).

- **Trigger accuracy**, via skill-creator's `run_eval.py`, measures the `description:` frontmatter in isolation by writing it into a throwaway slash-command alias. It is only meaningful *before* the skill is installed: with the real `upscaler-ask` loaded alongside its spokes, Claude picks the real skill over the test alias and every positive records a FAIL (the baseline run scored 8/23 for exactly this reason). Use it for pre-install description A/B testing, never to measure a live install. Skill-creator's `run_loop.py` inherits the same limitation.
- **Tool-call cost**: `python3 skills/upscaler-ask/evals/tool_call_cost.py [--limit N] [--out DIR]` spawns real `claude -p` runs and records trigger rate, tool calls per query, duration, and cost. Budget roughly $15 to $25 and 45 to 75 minutes for the full 15 positives; use `--limit 3` to smoke-test. Tool calls per query is the efficiency signal (a list-and-count question should land near 6 to 10; a category consistently past 15 means its recipe is too vague and the agent is exploring).

**Trap:** the cost harness defaults its output directory to `skills/upscaler-ask-workspace/`, a non-skill directory *inside* `skills/`. The validator iterates every directory there and demands a `SKILL.md`, so its presence makes `validate_skills.py` (and therefore CI and `build_bundle.py`) fail with `upscaler-ask-workspace: missing SKILL.md`. It is not gitignored either. Always pass `--out` somewhere outside `skills/`, or delete the workspace before validating.

## Authoring guidance for skills

- **Frontmatter `description` is the trigger signal.** Claude matches the user's intent against this string to decide whether to load the skill. List concrete trigger phrases ("when user asks to...", "mentions X", "wants to Y") and the skill's domain. Vague descriptions cause either over-triggering or silence.
- **Skill directory name must equal the `name` frontmatter field.** The validator enforces this.
- **Keep `SKILL.md` short; push detail into `references/`.** Claude reads the entire `SKILL.md` on every invocation, so long skills burn context. Link out to reference docs the skill can read on demand.
- **Every skill opens with a "Platform connection (MCP → CLI → setup)" block** that links to `references/upscaler-access.md` (via `../../references/upscaler-access.md` from inside a skill directory). Do not inline the long version or restate the full tool mapping; reference the shared doc. Skills that are pure local authoring (e.g. `upscaler-author-asset`) note that the connection is only needed when publishing back.
- **MCP-first / CLI-fallback, never mixed.** When showing example commands, present the MCP tool name and the CLI command side-by-side (bulleted or in a two-column table) so the skill works on either tier without forking the prose.
- **Read-only skills must declare it and not call write tools.** `upscaler_manage_*`, `upscaler entry create`, `upscaler todo create`, etc. are off-limits for `upscaler-ask`. Write workflows route to `upscaler-author-asset` (drafting assets), `upscaler-write-entry` (register entries), or `upscaler-run-record` (record tasks). Write-capable skills must use a propose-then-confirm UX and never mutate silently.
- **Cite by `upscaler:<asset_id>`** in every fact the skill emits about an Upscaler item. Never fabricate an asset ID; if retrieval returned nothing, say so.
- **`upscaler-ask` routes before answering** when the user's intent is workflow-shaped (draft a policy, add a register row, complete a record). New spoke skills must declare the routing trigger in their `description:` and be added to the routing table in `skills/upscaler-ask/SKILL.md`.
- **Never assume an out-of-scope skill is installed.** If a workflow is outside this library, the correct behaviour is to answer the read-only part and say the rest is out of scope. Never fabricate the output of a skill that is not present.
- **Executables belong in `scripts/`** with clear entry points. Prefer shell/Python over heavier stacks to minimize user install friction.
- **Skills target the public API surface of Upscaler (MCP, CLI, REST).** They should not hard-code internal endpoints or credentials.

## Before landing changes

1. Run `python3 scripts/validate_skills.py`.
2. If you changed the skill schema, update `docs/skill-template/`, the validator, `CONTRIBUTING.md`, and this file together, they drift silently otherwise.
3. Add the skill to the table in `README.md`, the list in `AGENTS.md`, and the index in `llms.txt`.
4. Log the change under `[Unreleased]` in `CHANGELOG.md`. If the change is a **breaking rename or removal**, mark it as a "Breaking change" entry and add a one-line breaking-change notice under the skill table in `README.md`.
5. **Releasing.** `.github/workflows/package.yml` fails any `v*` tag whose version disagrees with `.codex-plugin/plugin.json` (the only manifest carrying semver), so bump that version on **every** release, not just breaking ones, and promote the `[Unreleased]` entries under the new version before tagging.
6. If the change touches the platform connection pattern (new MCP tools, new CLI commands, new auth flow), update `references/upscaler-access.md` once rather than editing each skill.
7. If you added a new spoke skill, also update the routing table in `skills/upscaler-ask/SKILL.md` so the hub knows when to hand off to it.
8. New skills ship through the bundled `upscaler-skills` plugin automatically (because `.claude-plugin/marketplace.json` uses `source: "./"`). No marketplace edit needed unless you're splitting a skill into its own plugin.
