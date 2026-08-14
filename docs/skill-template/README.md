# Skill template

Copy this directory to create a new skill:

```bash
cp -r docs/skill-template skills/my-new-skill
```

Then:

1. Edit `SKILL.md`:
   - Set `name:` to match the new directory name (kebab-case, matching `[a-z0-9]([a-z0-9-]*[a-z0-9])?`, max 64 chars, no consecutive hyphens).
   - Write a specific `description:` (max 1024 chars). This is what the agent matches against user intent to decide whether to load the skill.
2. Move supporting scripts into `scripts/` and long-form reference material into `references/`.
3. Run `python3 scripts/validate_skills.py` from the repo root.
4. Add the skill to the table in the top-level `README.md`.
5. Log the addition in `CHANGELOG.md` under **Unreleased**.

This template lives under `docs/` rather than `skills/` because its name (`example-skill`) is a placeholder, not a published skill. See the [agentskills.io specification](https://agentskills.io/specification) for the full format.
