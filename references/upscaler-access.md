# Upscaler platform access (MCP → CLI → setup)

Shared reference loaded on demand by every Upscaler skill. Defines the connection-priority pattern, the tool/command mapping, asset ID prefixes, and the setup-fallback message.

## Connection priority

Every Upscaler skill follows the same three-tier priority. Pick the first tier that's available; do **not** mix tiers in one operation.

1. **MCP server (preferred)** — if the agent's tool list contains any tool whose name matches `upscaler_*` or ends in `__upscaler_*` (e.g. `mcp__claude_ai_Upscaler__upscaler_search_documents`), call those tools directly. Lowest friction, no shell, structured payloads. Where a tool exposes `response_format`, keep the default `json` for structured reads and use `markdown` only for short human-readable output. `upscaler_list` has no `response_format`; `upscaler_get_asset` instead uses `format: ["json"|"schema"|"markdown"]` (a list).
2. **`upscaler` CLI (fallback)** — if no MCP tools are present but the `upscaler` binary is on `$PATH` (test with `command -v upscaler`), use it. Always pass `--json` for parseable output, and check `upscaler status` to confirm the session is authenticated before running queries.
3. **Setup prompt (last resort)** — if neither is available, print the setup message in the section below and stop. Do **not** attempt the workflow with neither connection.

### Detecting which tier is active

Use the tool-name probe at the start of every workflow. Pseudocode:

```
if any tool name in the current session matches /(?:^|__)upscaler_/:
    tier = "MCP"
elif `command -v upscaler` returns a path:
    tier = "CLI"
else:
    print SETUP_MESSAGE and stop.
```

Record the chosen tier once and use it consistently for the whole task. Do not retry the other tier on error; surface the error instead.

## Operation mapping (MCP ↔ CLI)

The Upscaler MCP server and CLI expose the same surface under different shapes. Pick the row that matches the operation and call the corresponding tier.

| Operation                              | MCP tool                       | CLI command                                                        |
| -------------------------------------- | ------------------------------ | ------------------------------------------------------------------ |
| Hybrid semantic+keyword content search (documents AND register entries) | `upscaler_search_documents` | `upscaler --json search "<text>" --limit 5 [--parent-id <id>] [--published-after <ISO>] [--include-metadata]` |
| Keyword node search by title/description (excludes task/release/todo) | `upscaler_search_nodes` | *(no exact CLI equivalent — `asset find` is a different op, see below)* |
| Wildcard title/description lookup over the asset tree | *(no MCP equivalent)* | `upscaler --json asset find --title "<pattern>" [--description <pat>] [--type <raw enum>]` |
| Get one asset                          | `upscaler_get_asset`           | `upscaler --json get <asset-id>` (use `--format markdown\|schema`) |
| Get an asset's descendant hierarchy    | `upscaler_get_asset_hierarchy` | `upscaler --json hierarchy <asset-id> --depth 3`                   |
| List definitions / entries / todos     | `upscaler_list`                | `upscaler --json list definitions` / `list entries --definition-id <id>` / `list todos` |
| List entries with field values         | `upscaler_list({ type: "entries", include_values: true })` or `select_values: ["ff_…"]` | `upscaler --json list entries --definition-id <id> --include-values [--resolve-labels]` or `--select-value "<Label or ff_…>"` |
| List field options (for select fields) | `upscaler_list`                | `upscaler --json list field-options --definition-id <id> --field-key <key>` |
| List members / groups / deleted assets | `upscaler_list` with `type: "members"|"groups"|"deleted_assets"` | `upscaler --json list members` / `list groups` / `list deleted` |
| Create / update / delete an asset      | `upscaler_manage_asset`        | `upscaler asset create --type <type> --data @file.json` / `asset update --asset-id <id> --data …` / `asset delete --asset-id <id>` |
| Create / update an entry (record/item) | `upscaler_manage_entry`        | `upscaler entry create --definition-id <id> --data @file.json` / `entry update --entry-id <id> --data …` |
| Manage a todo                          | `upscaler_manage_todo`         | `upscaler todo {create,update,close,reopen,delete}`                |
| Manage an automation                   | `upscaler_manage_automation`   | `upscaler automation {list,get,runs,create,update,enable,disable,run,delete}` |
| Manage a compliance framework          | `upscaler_manage_framework`    | `upscaler framework {list-installed,get-installed,list-contributions,list-requirement-contributions,list-test-bindings,bind,update-binding,remove-binding,set-test-binding,clear-test-binding,set-test-override,reset-test-override,reset-overrides,add-test,remove-test,evaluate,sweep}` |
| Presign upload / get a download URL    | `upscaler_manage_file`         | `upscaler files presign` / `files sign-get` (`files download` streams bytes) |
| List / add / edit / delete comments    | `upscaler_manage_comment`      | `upscaler comment {list,add,edit,delete}`                           |
| Restore a deleted asset (a **write**)  | `upscaler_recover_item` (compatibility name; accepts all supported asset prefixes) | `upscaler recover <asset-id> [--dry-run]` |
| Read the user manual                   | `upscaler_get_user_manual`     | (no CLI equivalent — use MCP)                                      |
| Auth: sign in / status / refresh / out | (handled by MCP host config)   | `upscaler login` / `upscaler status` / `upscaler refresh` / `upscaler logout` |
| Profiles: list / current / delete      | (n/a — MCP host owns one bucket) | `upscaler profile list` / `upscaler profile current` / `upscaler profile delete <name> --yes` |

For flag-level CLI detail, run `upscaler <command> --help`. The CLI is the canonical surface.

## Asset ID prefixes

Both MCP and CLI auto-detect asset kind from the ID prefix. Use this table when reasoning about a hit returned by search. Note the definition-vs-instance split: a *definition* is the template/schema; an *instance* is one filled-in row or record created from it. Tests, schema reads, and authoring target definitions; status updates and "complete this" actions target instances.

| Prefix         | Kind        |
| -------------- | ----------- |
| `doc_`, `d_`   | Documents   |
| `rg_`          | Register definitions |
| `i_`           | Items: entries (instances) inside a register |
| `rd_`          | Record definitions |
| `r_`, `rec_`   | Records: instances of a record definition |
| `t_`           | Tasks (`td_` = task *definition* on a record definition) |
| `to_`          | Todos       |
| `g_`           | Groups      |
| `cd_`, `cr_`   | Course definitions / course records (LMS) |
| `tg_`          | Tags        |
| `auto_`        | Automations |

A record instance carries its parent definition in `userRecordDefinitionId` (an `rd_*`). To act on a record *type* (e.g. bind a Test, read its schema), resolve `r_*` → `rd_*` first. Do **not** read `r_` as a register: `r_` is a record instance, `rg_` is a register definition.

## CLI conventions

- **Global flags work in any position.** The CLI hoists `--json`, `--no-json`, `--quiet`, `--verbose`, `--server`, and `--profile` before parsing, so both `upscaler --json list todos` and `upscaler list todos --json` work. Prefer putting them first for consistent examples.
- **`--data` accepts inline JSON, a file (`@payload.json`), or stdin (`-`).** Prefer files for anything non-trivial.
- **Preview writes with `--dry-run` *where supported*.** The basic `asset`/`entry`/`todo`/`automation` create/update/delete commands, the asset task/lesson content commands, and `framework {bind,update-binding,remove-binding}` support it; check `--help` for the exact subcommand. The framework **Test** commands (`set-test-binding`, `clear-test-binding`, `set-test-override`, `reset-*`, `add-test`, `remove-test`, `evaluate`, `sweep`) do **not** support `--dry-run` — treat them as immediate writes.
- **Exit codes and auth:** `0` success and `1` runtime error. Exit `2` can mean auth required **or** a Click usage error, so inspect stderr instead of classifying by code alone. If `status` returns `{"authenticated": false}` or stderr says `Run: upscaler login`, stop and ask for `upscaler [--profile <p>] login`. If `status` shows `expired: true` with `refresh_token_present: true`, run `upscaler [--profile <p>] refresh` and re-check once; normal API calls also auto-refresh on a 401. If refresh fails or no refresh token exists, ask for login. Never switch tiers to hide an auth or usage error.

## Profiles

A **profile** is an isolated bucket of CLI state (auth tokens + config). Use profiles to keep separate sessions for different Upscaler hosts (e.g. prod vs a local dev server) without re-authenticating each time.

- **Selection:** `--profile <name>` overrides the `UPSCALER_PROFILE` env var, which overrides the built-in default (`prod`). It is a global option but is accepted in any position.
- **Storage:** each profile lives at `~/.upscaler/profiles/{name}/` with its own `config.json`, `tokens.enc`, `.salt`, and `pending_device.json`. Deleting a profile dir removes all of its state.
- **Defaults:** the `prod` profile uses the CLI's build-time server URL (the prod wheel ships pointing at the prod host); the `dev` profile's built-in default is staging (`https://ai.stg.upscaler.app`); any other profile name falls back to the build-time default. These are only defaults — a developer's `dev` profile is often pointed at a **local** host (e.g. `https://ai.localhost`). Don't infer the host from the profile name; read it from `upscaler profile list` / `upscaler status`. Override per-profile with `upscaler --profile <name> config set server_url <url>`.
- **Resolution priority for any setting:** `--server` flag > `UPSCALER_SERVER` env > profile config > profile default. The env var is a global override; it wins over the active profile's saved config.
- **Legacy migration:** existing users with `~/.upscaler/{config.json,tokens.enc,.salt}` are auto-migrated into `profiles/prod/` on first run, once, transparently.

Typical workflow:

```bash
upscaler login                                  # logs into the default (prod) profile
upscaler --profile dev login                    # separate session for the dev profile
upscaler --profile dev config set server_url https://your-dev-host
upscaler --profile dev config set verify_ssl false   # if self-signed
upscaler profile list                           # see all profiles + which is active
upscaler --profile dev list todos               # any command can be scoped per profile
```

When MCP is the active tier, profiles are not relevant — MCP host configuration owns the single connection. Profiles apply only to the CLI tier.

## Schema-first writes

Before any create/update on an entry or asset, **inspect the schema** so the payload satisfies validation:

- MCP: `upscaler_get_asset({ asset_id: "<definition-id>", format: ["schema"] })`, then `upscaler_list({ type: "field_options", definition_id: "<id>", field_key: "<key>" })` for a select/radio whose options are not already inlined. Checkbox options are in the schema; `field_options` returns none for checkbox.
- CLI: `upscaler --json get <definition-id> --format schema`, then `upscaler --json list field-options --definition-id <id> --field-key <key>`.

This applies even when the user supplies the payload — silent rejections are worse than a noisy preflight.

## Batched MCP formats

`upscaler_get_asset` accepts multiple formats in one call: `format: ["json", "schema", "markdown"]`. Prefer one batched call over three round-trips when you need overview, schema, and rendered content together.

## Listing entries with values (avoid N+1)

`upscaler_list({ type: "entries" })` and `upscaler list entries` return `{_id, title}` per row by default. To read values, **do not** loop `get_asset` per row, opt the values into the same call:

- **MCP:** `upscaler_list({ type: "entries", definition_id: "<id>", include_values: true })` for all values keyed by `ff_*`, or `select_values: ["ff_…", "ff_…"]` to project only specific fields. `select_values` implies `include_values`. Each key is an `ff_` field id — `ff_` + 28 base62 chars (`^ff_[A-Za-z0-9]{28}$`; the platform never mints `_` or `-`); keys with characters outside `[A-Za-z0-9_]` (e.g. hyphens) are dropped by the backend. Resolve `ff_*` keys to labels via a separate `upscaler_get_asset(format: ["schema"])` call when needed.
- **CLI:** `upscaler --json list entries --definition-id <id> --include-values` for raw `ff_*` keys. Add `--resolve-labels` to rewrite keys to their human labels in one extra schema fetch — this now recurses into nested **table** fields too, the only composite field type (column sub-ids resolve to their column labels), so you rarely need a follow-up schema read. Use `--select-value "<Label or ff_…>"` (repeatable) to project just the named field; accepts either the schema label (case-insensitive) or the `ff_*` key; unknown labels fail fast with an exit-2 `BadParameter` listing the valid labels.

**Filter / count server-side first.** When the question names a concrete predicate, push it to the server instead of pulling every row: `list entries --filter "<Label or ff_>=<value>"` (repeat for AND; comma-separate values for OR) and `--sort <field>:asc|desc`. For a pure count use `--limit 0` (MCP `limit: 0`) — read the count from `data.total`; `data.items` is empty. Reserve client-side `jq` grouping for a true group-by where no server predicate fits.

Example group-by (no server aggregation for distributions yet — 16 entries, **2 round-trips** instead of 17; guard against missing values):

```bash
upscaler --json list entries --definition-id rg_T3ogQAKBntuonqKpNOC2JI44aMzY \
  --include-values --resolve-labels \
  | jq '[.data.items[].values["Process Priority/Value"] // "—"] | group_by(.) | map({(.[0]): length}) | add'
# {"Critical": 1, "High": 11, "Medium": 4}
```

## Scoping to the compliance root (e.g. the ISMS)

When a workflow is compliance-scoped (review, evidence, control Q&A), restrict results to the assets under the relevant management-system root before trusting them. The root is **framework-relative** — "Information Security Management System" for ISO 27001, but a QMS / EMS / DORA program has a different root; discover it (e.g. by title, or from the framework's bindings) rather than hard-coding "ISMS".

`upscaler_get_asset_hierarchy` / `upscaler hierarchy <asset-id>` returns the asset's **descendants** (its children subtree), **not** its ancestors — so you cannot "verify a hit's ancestry" by calling `hierarchy <hit-id>`. Do it the other way around:

1. Resolve the root once (`asset find --title "<root>" --type document_definition` → `d_*`).
2. Fetch its descendants once (`hierarchy <root> --depth 5`) and flatten `children` into a set of asset ids.
3. Keep a hit only if its `asset_id` is in that set.

On the MCP tier, prefer `upscaler_search_documents({ parent_id: "<root>", … })` (CLI: `upscaler search … --parent-id <root>`) so hits are pre-scoped server-side and no per-hit filtering is needed.

## Citation contract

Every fact the skill emits about an Upscaler item must cite it. Two acceptable forms:

- Markdown link: `[<title>](upscaler:<asset_id>)`, agent-readable, click-through opens the platform.
- Inline ID: `<title> (upscaler:<asset_id>)`, for prose where a link would be awkward.

Never fabricate an asset ID. If MCP/CLI returned nothing, say so; never invent.

**Search results are embedding chunks, not assets.** A hit's top-level `id` is the *chunk* id (it will not resolve via `upscaler get`); cite the **`asset_id`**. Use the promoted top-level `asset_title`; it is populated from raw metadata even when `include_metadata` is false. Request raw metadata only for fields not already promoted. One query returns several chunks of the same asset, so **de-duplicate by `asset_id`** before citing. Hybrid-search `score` is a reciprocal-rank-fusion value (often ~0.01–0.03), not a cosine similarity — treat it as ordinal ranking, never a cutoff threshold.

## Setup message (use verbatim when neither tier is available)

When the tool-name probe finds no `upscaler_*` tools and `command -v upscaler` fails, print this message and stop. Do not attempt the workflow.

```
Upscaler is not connected in this session. I can't run this workflow until one of the following is set up:

Option A, Upscaler MCP server (preferred)
  • Claude Code:  /mcp add upscaler   (or add it via your agent's MCP configuration UI)
  • Codex CLI:    add the upscaler MCP server to your Codex MCP config
  • Other agents: see https://upscaler.io/docs/mcp

Option B, Upscaler CLI  (open source: https://github.com/upscaler-io/upscaler-cli)
  pip install upscaler-cli
  upscaler login
  # Self-hosted or non-Upscaler host? Point it there first:
  #   upscaler config set server_url https://your-upscaler-host
  # Optional: keep a separate auth bucket for a non-prod host
  #   upscaler --profile dev config set server_url https://your-dev-host
  #   upscaler --profile dev login

Once either is available, re-run the request and I'll pick it up automatically.
```

Tailor the agent-specific install hint to the host if known (Claude Code, Codex, Cursor, Gemini, etc.); keep the two-option structure intact.

## Pitfalls

- **Don't mix tiers.** If MCP is available, do not also shell out to the CLI, payload shapes differ and you'll fight schema mismatches.
- **Always pass `--json` to the CLI** when downstream parsing matters. Plain output is for humans, not for prompts.
- **There is no MCP `authenticate` tool.** MCP auth is handled by the host's OAuth configuration. Match Upscaler tools by the `upscaler_*` suffix (the host prefix varies, e.g. `mcp__claude_ai_Upscaler_2__upscaler_list`); don't hard-code the prefix and don't expect an auth tool.
- **`upscaler_search_documents` has no `kind` argument** (its input schema is `extra="forbid"`, so passing `kind` raises a validation error). It is hybrid semantic + keyword search over **document AND register-entry** content already. To restrict to entries, pass `asset_type: "item"` (the exact backend enum), or resolve the register definition (`upscaler_search_nodes` with `asset_types: ["register"]`) then `upscaler_list({ type: "entries", definition_id: "<rg_id>", include_values: true })`, or use `upscaler_manage_framework({ action: "list_requirement_contributions", … })` for bound evidence.
- **`upscaler_search_nodes` (MCP) and `upscaler asset find` (CLI) are NOT the same operation.** `search_nodes` regex-matches title/description, excludes task/release/todo, and resolves type aliases (`document`/`register`/`record`). `asset find` is a wildcard (`*`,`?`) lookup over the asset tree with **no** alias resolution: `--type document` returns 0; you must pass the **raw** enum `--type document_definition`. Don't carry a `search_nodes` alias over to `asset find`.
- **Never loop `get_asset` to read each entry's field values.** `upscaler_list` / `list entries` returns `{_id, title}` only by default; ask for values explicitly via `include_values: true` / `--include-values` (or `select_values` / `--select-value` for a subset). See the "Listing entries with values" section above.
- **There is no `upscaler search documents` subcommand.** It is just `upscaler search "<text>"`. Likewise no `upscaler get asset <id>` (just `upscaler get <id>`) and no `upscaler get asset-hierarchy <id>` (use `upscaler hierarchy <id>`).
- **There is no `upscaler auth login`.** Auth lives at the top level: `upscaler login`, `upscaler status`, `upscaler refresh`, `upscaler logout`.
- **`--profile` is a global option accepted anywhere.** Both `upscaler --profile dev login` and `upscaler login --profile dev` select the same profile; prefer the first style in examples.
- **`$UPSCALER_SERVER` overrides the active profile's saved server URL.** If a user runs `--profile dev login` and the request goes to the wrong host, check whether `UPSCALER_SERVER` is exported in their shell.
- **Read-only skills must avoid write actions, not every `upscaler_manage_*` tool.** `upscaler_recover_item` is always a write. `upscaler_manage_framework`, `upscaler_manage_automation`, `upscaler_manage_file`, and `upscaler_manage_comment` have mixed scopes: their list/get actions are reads, while create/update/set/evaluate/sweep/presign/add/edit/delete actions are writes. `framework evaluate` and `framework sweep` re-run and persist evaluation; read the latest result from `get_installed` instead.
- **`list` flag gotchas:** `list definitions` and `list entries` both support `--limit`/`--offset`. `list todos` has no `--status`. `todo update` has `--title`/`--assignee`/`--due` but **no** `--description` (the MCP tool can update description through its data payload).
- **Publishing is not available via MCP.** For publish/release operations, direct the user to the Upscaler web app.
