# Upscaler Skills (core)

This repository publishes the core open-source agent skills for the [Upscaler](https://upscaler.io) platform. Each directory under `skills/` is a self-contained skill that follows the [Agent Skills specification](https://agentskills.io/specification).

Advanced workflow skills live in a separate repository, [`upscaler-adv-skills`](https://github.com/upscaler-io/upscaler-adv-skills).

## For agents working in this repo

When adding, editing, or validating skills:

- One skill per directory under `skills/<skill-name>/`.
- The directory name must match the `name:` field in `SKILL.md` frontmatter. Names are lowercase, kebab-case, matching `[a-z0-9][a-z0-9-]*`, at most 64 characters, with no consecutive hyphens and no trailing hyphen.
- `description:` is the trigger. Write it as the list of user intents where the agent should load this skill. Keep it under 1024 characters. See https://agentskills.io/skill-creation/optimizing-descriptions for guidance.
- Keep `SKILL.md` under 500 lines and ~5000 tokens. Move longer material into `references/` and tell the agent _when_ to load each reference file.
- Optional frontmatter fields (`license`, `compatibility`, `metadata`) are encouraged where they help users understand requirements.
- Run `python3 scripts/validate_skills.py` before committing. CI runs the same check.
- The skeleton for new skills lives at `docs/skill-template/`. Copy it into `skills/<name>/` to start.
- `.claude-plugin/plugin.json` (plugin manifest) and `.claude-plugin/marketplace.json` (marketplace catalog) keep this repo installable as a Claude Code plugin and via `npx skills add`. `.codex-plugin/plugin.json` makes the same repo installable as an OpenAI Codex CLI plugin (manifest format: https://developers.openai.com/codex/plugins/build). New skills under `skills/` ship through the bundled `upscaler-skills` plugin automatically on both surfaces — no manifest edit needed.
- **Do not add advanced workflow skills here.** Evidence packs, design-doc gap reviews, framework setup, management-review packs, and status reports belong in `upscaler-adv-skills`.
- **Do not reintroduce hard routing to the advanced spokes.** `skills/upscaler-ask/SKILL.md` has a "Workflows outside this library" section that handles them as optional. Extend that section rather than adding rows to the main routing table.

## Available skills

- `skills/upscaler-ask/`: hub. Compliance-manager Q&A entry point. Answers questions about controls, evidence, risks, policies, and training in concise prose with citations; routes to a specialist skill when a workflow is implied.
- `skills/upscaler-author-asset/`: spoke. Author Upscaler asset definitions (policies, procedures, registers, records, courses) that pass platform validation, and apply read-modify-write updates to existing documents.
- `skills/upscaler-write-entry/`: spoke (write-capable). Create or update an entry (`i_*`) inside an existing register (`rg_*`): field resolution, sample-value generation, top-level and nested form-table file uploads; propose-then-confirm before every write.
- `skills/upscaler-run-record/`: spoke (write-capable). Create a record instance (`r_*`) from a record definition (`rd_*`) and drive its task flow end to end: per-task form filling (values derived from the parent asset and its referenced assets), task completion in workflow order, verification. Shares the form-filling core at `references/form-filling.md` with `upscaler-write-entry`.

Shared connection reference at `references/upscaler-access.md` defines the MCP → CLI → setup priority every skill follows. `references/form-filling.md` is the shared form-filling core used by `upscaler-write-entry` and `upscaler-run-record`. `references/personas.md` describes the target personas.

## Shared reference sync

`references/upscaler-access.md` is **duplicated** in `upscaler-adv-skills` so each repo installs standalone. It must stay byte-identical across the two. When you change it here, apply the same change there in the same PR cycle, and vice versa:

```bash
diff references/upscaler-access.md ../upscaler-adv-skills/references/upscaler-access.md
```

`references/personas.md` is duplicated too, but intentionally diverges: each copy lists the skills that actually ship in its repo. Keep the persona definitions in sync; the "skills they invoke" lines are repo-local.

`references/form-filling.md` is core-only. `references/posture-collection.md` is advanced-only. Neither is duplicated.

## For end users

See `README.md` for installation instructions across Claude Code, Cursor, Gemini CLI, OpenAI Codex CLI, and other agents that support the Agent Skills format.

## Contributing

See `CONTRIBUTING.md`. New skills should start by opening a [new-skill issue](.github/ISSUE_TEMPLATE/new_skill.yml) so maintainers can weigh in on scope before a PR.
