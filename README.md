# Upscaler Skills

A public collection of portable AI-agent skills for interacting with the [Upscaler](https://app.upscaler.app) platform. Use them to let your coding agent search Upscaler documents, author asset definitions, write register entries, complete records, and answer compliance questions directly from the terminal or IDE.

## Supported agents

Each skill is written as platform-neutral markdown (instructions + optional scripts), so it works with any agent that can consume markdown context. Tested install paths:

| Agent | Where skills are loaded from |
| --- | --- |
| [Claude Code](https://claude.ai/code) / [Claude.ai](https://claude.ai) | `~/.claude/skills/` or `.claude/skills/` |
| [Cursor](https://cursor.com) | `.cursor/rules/*.mdc`, from the packaged `cursor-rules.zip` |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | `GEMINI.md` at the project or user level, from the packaged `gemini-context.zip` |
| [OpenAI Codex CLI](https://github.com/openai/codex) | `AGENTS.md` at the project or user level, or `.agents/skills/` |
| [ChatGPT](https://chatgpt.com) (Business, Enterprise, Edu) | Settings → Skills → "Upload from your computer", using the packaged zips from `scripts/build_chatgpt_skills.py` |
| Any other agent | Paste `SKILL.md` content into whatever system-prompt / rules file the tool supports |

> The canonical source for every skill is its `SKILL.md`. Platform-specific installs below all boil down to "make this skill's content discoverable by your agent."

## What's in a skill

```
skills/my-skill/
├── SKILL.md              # YAML frontmatter (name, description) + instructions
├── scripts/              # optional — helpers the skill invokes
└── references/           # optional — long-form docs the agent reads on demand
```

The instructions target Upscaler's public surface (CLI, REST API, MCP server), not any particular agent host, which is why the same skill works across Claude, Cursor, Gemini, and Codex.

## Available skills

The library is organized as a **hub-and-spoke**: `upscaler-ask` is the entry point that answers compliance-manager questions and routes to a specialist skill when the user wants an artifact. Every skill prefers the Upscaler **MCP** server and falls back to the `upscaler` **CLI**; if neither is set up, it prints install instructions and stops. The shared connection pattern lives at [`references/upscaler-access.md`](references/upscaler-access.md).

| Skill | Role | Description |
| --- | --- | --- |
| [`upscaler-ask`](skills/upscaler-ask/) | Hub | Compliance-manager Q&A entry point. Answers questions about controls, evidence, risks, policies, and training in concise prose with citations. Routes to the specialist skills below when a workflow is implied. |
| [`upscaler-author-asset`](skills/upscaler-author-asset/) | Spoke | Author valid Upscaler asset definitions (policies, procedures, registers, records, training courses) with correct content types, block types, and form-field grammar. Also handles read-modify-write updates to existing documents. |
| [`upscaler-write-entry`](skills/upscaler-write-entry/) | Spoke | Create or update an entry (row, `i_*`) inside an existing register (`rg_*`): resolve fields, generate sample values, upload top-level and nested form-table files, propose-then-confirm before every write. |
| [`upscaler-run-record`](skills/upscaler-run-record/) | Spoke | Create a record instance (`r_*`) from a record definition (`rd_*`) and drive its whole task flow: per-task form filling with values derived from the parent asset and its referenced assets, task completion in workflow order, and verification. Shares its form-filling core with `upscaler-write-entry`. |

`upscaler-ask` is scoped to questions and to the three spokes above. When a request needs a workflow this library does not cover (assembling an evidence pack, gap-reviewing a design doc, configuring an installed framework, preparing a management review, producing a status report), it answers whatever part of the request is a plain lookup and says the rest is out of scope, rather than half-building the artifact.

> More skills coming. See [CONTRIBUTING.md](CONTRIBUTING.md) to propose one.

## Installation

Pick the route that matches your agent. The first three install every skill with one command and keep them updated automatically.

### Claude Code plugin (recommended)

The whole library ships as a single Claude Code plugin (`upscaler-skills`) inside the `upscaler` marketplace. From inside Claude Code:

```
/plugin marketplace add upscaler-io/upscaler-skills
/plugin install upscaler-skills@upscaler
```

Skills are then invokable under the namespaced form (`/upscaler-skills:upscaler-author-asset`) and trigger automatically when their description matches your prompt. Updates ship with each commit on `main`. To pin to a tag, append `@v1.0.0` (or any git ref) to the marketplace add command.

### OpenAI Codex CLI plugin (recommended)

The repo also ships a [Codex plugin manifest](.codex-plugin/plugin.json) — Codex picks up `.codex-plugin/plugin.json` at the repo root and bundles every skill under `skills/`. From inside Codex CLI:

```bash
codex plugin marketplace add upscaler-io/upscaler-skills
codex plugin install upscaler-skills
```

Pin to a tag or commit with `--ref <git-ref>` on the marketplace add command. After install, restart Codex so it picks up new skills.

### Any agent via `npx skills` (Vercel skills.sh)

Vercel's [`skills` CLI](https://github.com/vercel-labs/skills) installs the same skills into 18+ agent hosts (Claude Code, Cursor, Codex, Gemini CLI, Cline, OpenCode, and more):

```bash
# Install the whole bundle
npx skills add upscaler-io/upscaler-skills

# Or just one skill
npx skills add upscaler-io/upscaler-skills --skill upscaler-author-asset
```

`npx skills` discovers the plugin manifest under `.claude-plugin/` and pulls each skill from `skills/`.

### Cursor and Gemini CLI (download a package)

Neither agent has an Agent Skills loader, so each release ships a package with the skills reshaped into that agent's own format, with every reference link rewritten to resolve inside the package.

```bash
# Cursor: unzip at your project root, files land in .cursor/rules/
curl -sSL -o cursor-rules.zip https://github.com/upscaler-io/upscaler-skills/releases/latest/download/cursor-rules.zip
unzip -o cursor-rules.zip -d /path/to/your/project

# Gemini CLI: unzip at your project root (GEMINI.md + the docs it links)
curl -sSL -o gemini-context.zip https://github.com/upscaler-io/upscaler-skills/releases/latest/download/gemini-context.zip
unzip -o gemini-context.zip -d /path/to/your/project
```

Each Cursor rule is *agent-requested*: Cursor matches its `description` against your prompt and loads it on demand, mirroring how an Agent Skills host picks a skill. For Gemini, `GEMINI.md` is also published as a standalone asset if you would rather append it to one you already have (`curl -sSL https://github.com/upscaler-io/upscaler-skills/releases/latest/download/GEMINI.md >> GEMINI.md`), though the reference docs it links then need to come from the zip or a clone.

Asset names are stable across releases, so the URLs above always fetch the newest build.

### ChatGPT (upload packaged zips)

ChatGPT (Business, Enterprise, Healthcare, and Edu plans) consumes the same Agent Skills format, but installs each skill as a self-contained folder, so the repo-root shared references have to be bundled into each package first. Build the packages, then upload them:

```bash
git clone https://github.com/upscaler-io/upscaler-skills.git
cd upscaler-skills
python3 scripts/build_chatgpt_skills.py
```

This writes one zip per skill to `dist/chatgpt/`, with every shared reference the skill links (connection priority, form-filling core) inlined under `references/shared/` and the links rewritten. In ChatGPT, go to **Settings → Skills → Upload from your computer** and upload each zip you want (start with `upscaler-ask.zip`, the hub). Re-run the script and re-upload after pulling updates: uploaded skills do not auto-update.

Two caveats on this route: skills prefer the Upscaler MCP server, so connect the Upscaler connector in ChatGPT for live workspace data (the `upscaler` CLI fallback is not available inside ChatGPT), and hub-to-spoke routing only works for spokes you have also uploaded.

### Manual install (clone + copy)

If you'd rather not use a plugin manager, clone once and copy a skill into your agent's rules directory:

```bash
git clone https://github.com/upscaler-io/upscaler-skills.git
cd upscaler-skills
```

<details>
<summary><strong>Claude Code / Claude.ai</strong> — copy the directory</summary>

```bash
# User-level (all projects)
cp -r skills/upscaler-author-asset ~/.claude/skills/

# Project-level (scoped to one repo)
cp -r skills/upscaler-author-asset /path/to/your/project/.claude/skills/
```

Restart Claude Code (or run `/reload`) and the skill will trigger automatically when its description matches your prompt.
</details>

<details>
<summary><strong>Cursor</strong> — build the rules yourself</summary>

Prefer the released `cursor-rules.zip` above. To build it from a clone instead:

```bash
python3 scripts/build_editor_bundles.py cursor
unzip -o dist/editors/cursor-rules.zip -d /path/to/your/project
```

The packager converts each skill's frontmatter to Cursor's keys (`description`, `globs`, `alwaysApply`) and rewrites every reference link so it resolves inside `.cursor/rules/`. See [Cursor rules docs](https://docs.cursor.com/context/rules).
</details>

<details>
<summary><strong>Gemini CLI</strong> — build the context file yourself</summary>

Prefer the released `gemini-context.zip` above. To build it from a clone instead:

```bash
python3 scripts/build_editor_bundles.py gemini
unzip -o dist/editors/gemini-context.zip -d /path/to/your/project
```

For a user-level install, append `dist/editors/GEMINI.md` to `~/.gemini/GEMINI.md`. See [Gemini CLI docs](https://github.com/google-gemini/gemini-cli).
</details>

<details>
<summary><strong>OpenAI Codex CLI</strong> — install as a Codex plugin</summary>

This repo ships a [Codex plugin manifest](.codex-plugin/plugin.json) at the root, so it can be loaded directly by Codex CLI. From inside Codex:

```bash
codex plugin marketplace add upscaler-io/upscaler-skills
codex plugin install upscaler-skills
```

`codex plugin marketplace add` accepts a `--ref <git-ref>` flag to pin to a tag or commit.

If you'd rather drop the skills in directly without a marketplace, copy them into Codex's skill paths:

```bash
# User-level (all sessions)
cp -r skills/upscaler-author-asset ~/.codex/skills/

# Repo-scoped — Codex auto-discovers .agents/skills/ from cwd up to repo root
mkdir -p /path/to/your/project/.agents/skills
cp -r skills/upscaler-author-asset /path/to/your/project/.agents/skills/
```

Or, for a quick one-off, append the SKILL.md content to `AGENTS.md`:

```bash
cat skills/upscaler-author-asset/SKILL.md >> /path/to/your/project/AGENTS.md
```

See [Codex Plugin docs](https://developers.openai.com/codex/plugins/build), [Agent Skills in Codex](https://developers.openai.com/codex/skills), and the [AGENTS.md convention](https://agents.md).
</details>

<details>
<summary><strong>Any other agent</strong></summary>

If your tool accepts a system prompt, project-level rules file, or markdown context, paste the contents of `SKILL.md` in — the instructions are platform-agnostic.
</details>

## Usage

Once installed, ask naturally — the agent decides when to apply the skill based on the description:

- *"Search Upscaler for all open risk register entries"*
- *"Add a row to the risk register for the new vendor"*
- *"Draft a privileged-access procedure"*
- *"Complete the Findings task on record r_…"*

Each skill's `SKILL.md` documents the exact triggers and examples.

## Related projects

- [upscaler-cli](https://github.com/upscaler-io/upscaler-cli): the open-source
  `upscaler` command these skills fall back to when the MCP server is not
  configured. MIT licensed, installable with `pip install upscaler-cli`.

## Contributing

We welcome new skills and improvements. Start with [CONTRIBUTING.md](CONTRIBUTING.md) and use the [new-skill issue template](.github/ISSUE_TEMPLATE/new_skill.yml) to propose ideas.

## License

[MIT](LICENSE)
