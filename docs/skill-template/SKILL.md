---
name: example-skill
description: Replace this with a sentence that lists the concrete situations where the agent should load this skill (user intents, keywords, workflows). Keep it specific, this is the trigger.
license: MIT
---

# Skill name

One-paragraph summary of what this skill does.

## When to use

- User asks to do X with Upscaler
- User mentions Y
- User wants to Z

## When NOT to use

- Situations where a different skill (or no skill) is the better fit.

## Instructions

Step-by-step guidance Claude should follow when this skill is active.

1. …
2. …
3. …

## Examples

**User:** "…"
**Claude should:** …

## References

Point to files under `references/` or external docs for deep detail. Do not inline long reference material in this file, it bloats every invocation.

Tell the agent _when_ to load each reference. For example: "Load `references/api.md` only when the user asks about an endpoint not covered above."
