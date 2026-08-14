# Contributing

Thanks for your interest in extending the Upscaler Skills library. This guide covers the full path from idea to merged skill.

## Before you start

- Open a [new-skill issue](.github/ISSUE_TEMPLATE/new_skill.yml) describing the skill. This lets maintainers weigh in on scope and avoid duplication.
- Small fixes (typos, clearer triggers, corrected examples) can skip the issue step and go straight to a PR.
- **Check the skill is in scope.** This repo holds Q&A, asset authoring, register entries, and record completion. Evidence assembly, design-doc gap review, framework setup, management review, and status reporting are deliberately out of scope.

## Skill structure

Every skill is a directory under `skills/` containing at least a `SKILL.md`:

```
skills/my-skill/
├── SKILL.md              # required — frontmatter + instructions
├── README.md             # optional — user-facing overview
├── scripts/              # optional — executables the skill invokes
│   └── do_thing.py
└── references/           # optional — long-form docs loaded on demand
    └── api.md
```

### `SKILL.md` format

```markdown
---
name: my-skill
description: One-sentence purpose + the trigger phrases / domains where Claude should load this skill.
---

# My Skill

## When to use

Concrete trigger examples.

## Instructions

Steps Claude should follow. Keep it tight — reference `references/` for deep detail.

## Examples

Input/output pairs that show the skill in action.
```

Rules the validator enforces (aligned with the [Agent Skills spec](https://agentskills.io/specification)):

- Frontmatter must include non-empty `name` and `description`.
- `name` must match the directory name, be kebab-case (`[a-z0-9][a-z0-9-]*`), be at most 64 characters, contain no consecutive hyphens, and not end with a hyphen.
- `description` must be at most 1024 characters.

## Local workflow

```bash
# 1. Copy the template
cp -r docs/skill-template skills/my-skill

# 2. Edit SKILL.md (frontmatter + body)

# 3. Validate before committing
python3 scripts/validate_skills.py

# 4. Optional, install locally and try it
ln -s "$(pwd)/skills/my-skill" ~/.claude/skills/my-skill
```

## Writing effective skills

- **Description is the router.** Claude decides whether to load your skill based solely on the description — write it as the list of situations where you want to be picked.
- **Prefer doing over narrating.** Give Claude the command or API call to run, not paragraphs of background.
- **Scope tightly.** One skill = one coherent capability. If it tries to do everything, triggers become noisy.
- **Test the trigger.** Try 3–5 real user phrasings in Claude Code and confirm the skill is picked.
- **Never assume a skill outside this library is installed.** If your skill's prose points at one, phrase it as optional and give the degraded behaviour.

## Pull request checklist

- [ ] `python3 scripts/validate_skills.py` passes.
- [ ] All packagers still build: `python3 scripts/build_bundle.py`, `python3 scripts/build_chatgpt_skills.py`, `python3 scripts/build_editor_bundles.py`.
- [ ] Skill added to the table in `README.md`, the list in `AGENTS.md`, and the index in `llms.txt`.
- [ ] Any schema or format change reflected in `docs/skill-template/`, the validator, and `CLAUDE.md`.
- [ ] `CHANGELOG.md` updated under **Unreleased**.

## Releasing & distribution

The repo ships as a Claude Code plugin (`upscaler-skills` in the `upscaler` marketplace) and as a Vercel `npx skills` source. The Claude and marketplace manifests omit `version`, so the **git commit SHA is the version** — every merge to `main` is a release. `.codex-plugin/plugin.json` carries semver for Codex, which requires it; bump that on a release.

### Cutting a release

`.github/workflows/package.yml` builds every distributable package on each push and pull request, and publishes them to a GitHub Release when a `v*` tag arrives. To release:

1. Bump `"version"` in `.codex-plugin/plugin.json` and land it on `main`.
2. Tag the commit and push the tag:

   ```bash
   git tag v1.1.0 && git push --tags
   ```

3. The workflow verifies the tag matches the manifest version, builds the offline bundle, the ChatGPT per-skill zips, the Cursor rules, and the Gemini context file, then attaches them all to the release.

A tag that disagrees with the manifest fails the build instead of publishing a mislabelled release, so bump first and tag second. Release asset names stay stable across versions, which is what keeps `releases/latest/download/<asset>` working for users, so do not add a version suffix to them.

Pinned plugin install: `/plugin marketplace add upscaler-io/upscaler-skills@v1.1.0`.

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).
