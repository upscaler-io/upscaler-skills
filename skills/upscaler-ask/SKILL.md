---
name: upscaler-ask
description: Answer compliance-manager questions about an Upscaler workspace and route to the right specialist skill when a workflow is implied. Use when the user asks a question about controls, evidence, audit readiness, risks, policies, procedures, training, processes, suppliers, or any register entries — including "what is the status of…", "show me…", "do we have…", "how many…", "group/count/tally/breakdown/distribution by…", "is X covered?", "which control…", "find our…" phrasing scoped to Upscaler. ALSO use for a bare Upscaler ID (to_, d_, rg_, rd_, r_, i_, cd_, cl_, t_, g_) with a look/review/check/show verb, e.g. "review todo to_…". Framework-agnostic (ISO 27001 / ISMS, ISO 9001 / QMS, SOC 2, NIST CSF, NIS2, DORA) — pulls live data from the user's Upscaler MCP or CLI. Routes workflow intents to the spokes upscaler-author-asset, upscaler-write-entry, and upscaler-run-record.
license: MIT
compatibility: Requires Upscaler MCP server (preferred) OR the `upscaler` CLI.
---

# Upscaler Q&A (compliance-manager entry point)

The entry point into the Upscaler agent-skills library. Acts like a compliance manager / ISMS owner: answers questions about controls, evidence, risks, and policies in **concise prose with citations**, and routes to a specialist skill when the user's request implies a workflow rather than a question.

This skill is **read-only on its own**. When the user asks for an artifact (evidence pack, gap review, new policy) or wants to mutate state (set a Test Binding, add a custom Test), it hands off to the corresponding specialist skill rather than fabricating output or writing inline.

Write-capable spokes: `upscaler-author-asset` (drafts and revises asset definitions), `upscaler-write-entry` (creates/updates register entries `i_*`), and `upscaler-run-record` (creates record instances `r_*` and completes their tasks, including Supplier Agreement / Monitoring Activity review records). Write-capable spokes always use propose-then-confirm UX, never silent mutation.

Some workflow requests fall outside this library's scope. See [Workflows outside this library](#workflows-outside-this-library).

## Platform connection (MCP → CLI → setup)

Always run the connection-priority probe **first**, before any retrieval. The full reference is at [`../../references/upscaler-access.md`](../../references/upscaler-access.md).

1. **MCP first:** scan the active tool list for any name matching `upscaler_*` (e.g. `upscaler_search_documents`, `upscaler_search_nodes`, `upscaler_get_asset`, `upscaler_get_asset_hierarchy`, `upscaler_list`). If present, use them.
2. **CLI fallback:** otherwise run `command -v upscaler`. If it resolves, use `upscaler --json …` commands. Global flags work in any position; examples put them first for consistency. Confirm the session is authenticated via `upscaler status` and follow the shared auth recovery rules.
3. **Setup prompt:** if neither, print the setup message from the shared reference and stop. Do not guess answers.

Record the chosen tier once per session and stay on it. Do not mix tiers in one answer.

## Common shape: bare ID lookup

Match this before anything else. If the prompt contains a bare Upscaler ID (`to_`, `d_`, `rg_`, `rd_`, `r_`, `i_`, `cd_`, `cl_`, `t_`, `g_` prefix) with a look/review/check/show/open verb, it is a workspace lookup regardless of surrounding vocabulary:

1. `upscaler --json get <id>` — the prefix routes automatically; no `--type` needed except for members (unprefixed ids).
2. Follow what the object references. A todo (`to_*`) commonly links documents, records, or a change request in its `description` — fetch those too, since "review todo X" almost always means "assess the state of what the todo asks for". Todo discussion lives at `upscaler comment list --asset-id <to_> --asset-type todo` (there is no `todo get` subcommand; reads go through the top-level `get`).
3. Answer with status, due date vs today, assignees, and an assessment of whether the referenced work is done — with citations.
4. If the follow-up implies mutation ("draft the updates", "apply the changes", "complete the record"), route to the matching write-capable spoke (`upscaler-author-asset` for document/definition edits, `upscaler-run-record` for `r_*` tasks, `upscaler-write-entry` for `i_*` rows). Re-evaluate routing on EVERY turn — a session that starts as a lookup often turns into a write workflow two prompts later, and the spoke owns the write-safety rules that this skill does not carry.

## Common shape: list-and-count

Match this **before** the domain categories below. Any question of the form "How many X?", "Group/count X by Y", "Breakdown of X by Y", "Tally/distribution of X" is a list-and-count, regardless of domain (processes, risks, suppliers, controls, audits, training, etc.).

Recipe (always **2 round-trips** total — one schema, one list — never loop `get` per entry):

1. Resolve the register definition by title: `upscaler --json asset find --title "<register name>" --type register_definition`. If the user named a domain (e.g. "QMS processes"), try common register names: "Process Register", "Risk Register", "Supplier Register", "Audit Register", "Improvement Register".
2. Fetch the schema once to find the exact label of the grouping field — labels are case-sensitive when passed to `--select-value`:
   `upscaler --json get <rg_id> --format schema | jq '.data.schema.fields[] | {key, label}'`
3. Pull entries projecting only the grouping field, with labels resolved client-side:
   `upscaler --json list entries --definition-id <rg_id> --select-value "<exact label>" --resolve-labels --limit 200`
   (MCP equivalent: `upscaler_list({ type: "entries", definition_id: "<rg_id>", select_values: ["<ff_…>"] })`. Resolve the `ff_*` key from the schema first.)
4. Tally client-side (`group_by` in jq, or `Counter` in Python). Present as a markdown table with the total row. Value-shape rules for tallying: (a) multi-select and checkbox values are **arrays** — flatten before `group_by` or rows collapse into array-valued buckets; (b) select/radio store the option's visible **text**, so tallies and `--filter "<Label>=<value>"` predicates must match the option text exactly (never an index or id); (c) a missing/null key means the field was never answered — count it as its own "unanswered" bucket instead of silently dropping the row.

Worked example — "Group the processes by Priority":

```bash
upscaler --json asset find --title "Process Register" --type register_definition
upscaler --json get rg_T3o…  --format schema | jq '.data.schema.fields[] | select(.label|test("Priority"))'
upscaler --json list entries --definition-id rg_T3o… \
  --select-value "Process Priority/Value" --resolve-labels --limit 200 \
  | jq '[.data.items[].values["Process Priority/Value"]] | group_by(.) | map({(.[0]): length}) | add'
# {"Critical": 1, "High": 11, "Medium": 4}
```

**Do not** loop `upscaler get <i_…>` per row. **Do not** call `--include-values` (which returns every field) when one or two fields suffice — `--select-value` keeps the payload tight. If `--select-value` rejects your label, re-read the schema and copy the exact string (matching is case-insensitive but the label must exist).

When the question is a **predicate count** rather than a full breakdown ("how many risks are High?", "how many open audits?"), push the predicate server-side instead of pulling 200 rows: `upscaler --json list entries --definition-id <rg_id> --filter "<Label>=<value>" --limit 0` returns the count at `data.total` with an empty `data.items` list (MCP: `upscaler_list({ type:"entries", definition_id, filters:{ "values.<ff_>": "<value>" }, limit: 0 })`). Reserve the pull-and-tally pattern above for true group-by/distribution where no single predicate fits.

## What this skill answers

Four question categories. The skill recognizes the category from the user's phrasing and follows the matching retrieval recipe.

### 1. Control & framework status

Examples: "Is ISO 27001 A.5.1 covered?" · "What's our SOC 2 readiness?" · "Which controls have no implementing policy?"

Use this recipe **only for coverage / readiness / status questions** about a framework Requirement. If the user is asking **who owns** a policy, **where to find** it, **what version** it is, or any other metadata about a known document, route to Recipe #4 (Document, policy & training lookup) — those questions need a `search` + `get`, not framework introspection. The phrase "policy" or "control" alone is not a signal — the verb is ("is X covered" vs "who owns X").

Recipe (prefer framework introspection — it answers "is X covered" in 2–3 calls; only fall back to document search if the framework is not installed):

1. Identify the framework and control(s). If the user names only a framework ("SOC 2"), ask which control or topic to focus on rather than enumerating everything.
2. **Check if the framework is installed**: `framework list-installed` / `upscaler_manage_framework { action: "list_installed" }`. If installed, use the structured introspection path (steps 3–4). If not installed, jump to step 5.
3. **Coverage at the Requirement level**: `framework get-installed <framework-id>` (the id is the catalog id, e.g. `iso27001:2022`, passed **positionally** — not `--framework-id`) returns each Requirement under `.data.framework.requirements[]`, each with a `coverageState` (`excluded` / `untested` / `compliant` / `nonCompliant`). Filter to the Requirement(s) asked about and read the state directly. For "which controls have no implementing policy", filter to `coverageState` in `["untested","nonCompliant"]`.
4. **Identify the implementing assets** for a covered Requirement: `framework list-requirement-contributions --framework-id <framework-id> --requirement-id <req-id>` returns `{documents, records}` — cite those contributing assets by `assetId`. (The Test behind a contribution lives in `requirements[].tests[].binding` from get-installed.)
5. **Fallback (framework not installed)**: `upscaler --json search "<topic>" --no-include-metadata` for implementing policies. To keep hits in scope, resolve the management-system root once and pass `--parent-id <root>` (MCP `parent_id`) rather than walking each hit (`hierarchy <id>` returns *descendants*, not ancestors). The root is framework-relative (ISMS for ISO 27001; a QMS / EMS / DORA program differs) — discover it, don't hard-code it.
6. Answer in 2–4 sentences with conclusion + citations. If `coverageState` is `untested`/`nonCompliant`, name the uncovered Requirement and say what is missing. If the gap is a policy document, suggest `upscaler-author-asset`; if it is a Test binding, say so and stop — fixing bindings is a framework-setup workflow ([Workflows outside this library](#workflows-outside-this-library)).

Worked example — "Is ISO 27001 A.5.15 covered?":

```bash
upscaler --json framework list-installed
# -> iso27001:2022 is the installed framework id (catalog id, NOT if_*)
upscaler --json framework get-installed iso27001:2022 \
  | jq '.data.framework.requirements[] | select(.id == "A.5.15") | {id, coverageState}'
# -> {"id": "A.5.15", "coverageState": "compliant"}
upscaler --json framework list-requirement-contributions \
  --framework-id iso27001:2022 --requirement-id A.5.15 \
  | jq '[.data.documents[]?, .data.records[]?] | .[] | {assetId, title}'
# -> contributing assets to cite (assetId + title)
```

Three calls to answer "is X covered?" with citations — instead of searching documents and walking the hierarchy.

### 2. Evidence & audit readiness

Examples: "Which evidence is missing or expiring?" · "Show me last quarter's audit findings." · "Am I ready for the surveillance audit?"

Recipe (always pull values in one call — do not loop `get` per row; do not use semantic `search` for date-scoped enumeration):

1. Resolve the scope (control, topic, period). If the request is to **assemble** an evidence pack ("build me a pack", "give me the full narrative"), that is an evidence-pack workflow — see [Workflows outside this library](#workflows-outside-this-library) and stop.
2. Resolve the relevant register by title: `upscaler --json asset find --title "<Audit Register|Incident Register|Improvement Register>" --type register_definition`.
3. Pull entries with their full values in one call: `upscaler --json list entries --definition-id <rg_id> --include-values --resolve-labels --limit 200` (MCP equivalent: `upscaler_list({ type: "entries", definition_id: "<rg_id>", include_values: true })`). For tight payloads, narrow with `--select-value "<Date field label>" --select-value "<Status>"` / `select_values: ["ff_…"]`.
4. Filter client-side in jq/python. Common patterns:
   - **Quarter window** (e.g. "Q3 2025"): `jq '.data.items[] | select(((.values["Audit date"] // .updatedAt)[0:7]) | IN("2025-07","2025-08","2025-09"))'`. Fall back to `updatedAt` if the register has no dedicated date field. Caveat: the `[0:7]` slice assumes `YYYY-MM-DD` storage, but the API returns stored values verbatim, and two other shapes occur: legacy `DD/MM/YYYY` strings from old data, and non-`date` pickers, which store their own formats (quarter `2025-Q3`, week `2025-33th`, year `2025`). Legacy and quarter/week/year values silently drop out of the window — and a week value like `2025-07th` even slices to `2025-07` and falsely matches July. Guard first (e.g. `select(.values["Audit date"] | test("^\\d{4}-\\d{2}-\\d{2}$"))`) and report non-conforming values rather than silently excluding them.
   - **Stale check**: compare a "Next review date" field against today; flag items where the field is missing or in the past.
   - **Topic filter**: substring match on `title` or the narrative text field.
5. Return prose + bulleted citations. Flag stale or missing evidence explicitly.

Anti-patterns: do **not** run `upscaler search "Q3 2025 audit findings"` — semantic search is wrong for date-scoped enumeration. Do **not** enumerate via `upscaler get <i_…>` per entry — `--include-values` returns everything in one call.

### 3. Risk register insight

Examples: "Top 5 open risks without an owner." · "Risks linked to control A.8.3." · "Trend of risk score over the last quarter."

Recipe:

1. Pull risk-register entries with their values in one call: `upscaler_list({ type: "entries", definition_id: "<rg_id>", include_values: true })` or `upscaler --json list entries --definition-id <rg_id> --include-values --resolve-labels` (find the definition ID first with `upscaler --json asset find --title "Risk Register" --type register_definition`). If the question only needs a couple of fields (e.g. owner and score), pass `select_values: ["ff_…", "ff_…"]` / `--select-value "Risk owner" --select-value "Risk rating"` to keep the payload tight.
2. Filter client-side on owner, status, linked control, score, or date as the question requires. Interpreting values: unwrap `{value, label}` owner/lookup values via `.value` before comparing; "risks without an owner" means a missing key **or** an empty value; when the register maps controls via a Linked Requirements field, match `requirementId` inside the `{frameworkId, requirementId}` objects rather than substring-matching text; calculated risk scores are persisted in the values map, so read and tally them directly.
3. Return a short narrative answer plus a compact list of cited entries. For "trend" or aggregate questions, summarize the count / movement and cite the underlying entries.

### 4. Document, policy & training lookup

Examples: "Find our incident response procedure." · "Who owns the access control policy?" · "Which training is overdue for engineering?"

Recipe:

1. For document lookup: `upscaler_search_documents` / `upscaler --json search "<phrase>"`.
2. For owner/metadata: hit `upscaler_get_asset` / `upscaler --json get <id>` on the top hit and read the metadata.
3. For training overdue: list course-completion entries and filter client-side on due date and group.
4. Answer in 1–2 sentences with the asset title, owner (if asked), and citation.

### 5. Framework / Test binding lookup

Examples: "Which bindings are ambiguous on ISO 27001?" · "How many Requirements are `untested`?" · "Show me the Tests on A.5.15." · "Is A.8.3 compliant?"

Recipe (pick the **one** call that fits the question — do not enumerate the whole framework when a requirement-scoped call exists):

1. List installed frameworks if the user hasn't named one: `framework list-installed` / `upscaler_manage_framework { action: "list_installed" }`. The framework id is the catalog id (e.g. `iso27001:2022`); there is no `if_*` id.
2. **"Show me the Tests on <requirement-id>"**: read them from `framework get-installed <framework-id>` at `.data.framework.requirements[] | select(.id=="<req>") | .tests[]` (each Test has `pattern`, `binding`, `result`). `list-requirement-contributions` returns the *contributing documents/records*, not the Tests.
3. **"What was the latest evaluation result for <requirement-id>"** (pass/fail per Test, with reasons): read it from the same `get-installed` projection — `.tests[] | {pattern, result}`. Do **NOT** call `framework evaluate` or `framework sweep` — both are **mutations** that re-run and persist evaluation. Triggering a re-eval is a framework-setup workflow ([Workflows outside this library](#workflows-outside-this-library)).
4. **Binding-state questions across the whole framework** ("which are ambiguous?", "how many untested?"): `framework list-test-bindings --framework-id <framework-id>` (framework-wide flat rows), optionally `--source ambiguous` / `--unbound-only` / `--coverage-state untested` to filter server-side. (MCP: `upscaler_manage_framework { action: "list_framework_test_bindings", framework_id, data: { source: "ambiguous" } }`.)
5. **Coverage at the Requirement level** ("is A.8.3 compliant?", "which are nonCompliant?"): `framework get-installed <framework-id>` → `.data.framework.requirements[].coverageState` (`excluded` / `untested` / `compliant` / `nonCompliant`).
6. Answer in 1–2 sentences with counts and citations. If the user wants to **fix** any of this (set a binding, add a Test, disable a Test, re-evaluate), that is a framework-setup workflow — see [Workflows outside this library](#workflows-outside-this-library).

## Routing to specialist skills

When the user's intent is a **workflow** (produce an artifact), hand off rather than answering. Do this **before** doing retrieval — the specialist skill owns its own retrieval recipe.

| User intent (paraphrased)                                  | Hand off to              |
| ---------------------------------------------------------- | ------------------------ |
| "Draft / author / create / scaffold a policy / procedure / register / record / course" | `upscaler-author-asset`  |
| "Update / revise / amend an existing policy / procedure / document (`d_*`)" | `upscaler-author-asset` (its read-modify-write flow is mandatory — document writes publish immediately) |
| "Create / add / update an entry or row in a register (`rg_*` / `i_*`)" | `upscaler-write-entry` |
| "Add a row to the risk register / populate a sample item"  | `upscaler-write-entry` |
| "Review a supplier / SDD / complete a Supplier Agreement or Monitoring Activity Review" | `upscaler-run-record` |
| "Create / fill / complete / advance a record (`rd_*` / `r_*`), complete its tasks" | `upscaler-run-record` |
| "Run an incident / audit / meeting-minutes record"          | `upscaler-run-record` |

Handoff phrasing (use verbatim, replacing `<skill>`):

> This is a `<skill>` workflow. Invoking it now.

Then load the specialist skill's instructions and follow them. Do not paraphrase the specialist's logic from memory — load its `SKILL.md`.

### Workflows outside this library

These five workflow shapes are out of scope for this library. A separate skill covering one of them may or may not be loaded in the session, so treat each as optional.

| User intent (paraphrased)                                                | Out-of-scope workflow  |
| ------------------------------------------------------------------------ | ---------------------- |
| "Build / assemble an evidence pack / full narrative / audit pack"         | Evidence assembly      |
| "Review / gap-check this PRD / ADR / spec / design doc"                   | Design-doc gap review  |
| "Set up / configure a framework, bind / add / disable Tests, re-evaluate" | Framework setup        |
| "Prepare the management review / clause 9.3 input pack"                   | Management review      |
| "Status report / board summary / posture update for <audience>"           | Status reporting       |

Two cases:

1. **A skill covering it is loaded in this session.** Route to it exactly as to any spoke above, using the same handoff phrasing.
2. **No such skill is loaded.** Do not improvise the workflow and do not half-build the artifact. Answer whichever part of the request is a plain read-only question using the recipes above, then say in one sentence that producing the full artifact is outside this skill's scope, and stop.

Never fabricate the output of a skill that is not present, and never claim a skill is unavailable without checking the loaded skills first.

## Output format

Default: **concise prose + bulleted citations**, compliance-manager style.

- Answer in 2–4 sentences. State the conclusion, then the evidence.
- Follow with a `Citations:` block listing each Upscaler item: `- [<title>](upscaler:<asset_id>)`.
- Skip filler ("Great question…", "Based on my analysis…"). The user is a busy compliance manager.
- For tabular questions ("list the top 5 risks"), use a markdown table — but still cite each row.
- Do not produce a multi-section report. If the user wants one, see [Workflows outside this library](#workflows-outside-this-library).

Example:

```
Yes, A.5.15 (Access control) is covered. The implementing policy sets quarterly access
reviews and tier-based authorization, and we have three review records inside the period.

Citations:
- [Access Control Policy](upscaler:asset_abc123) — §3.2 quarterly review
- [Q1 2026 access review](upscaler:entry_def456) — completed 2026-03-31
- [Q4 2025 access review](upscaler:entry_ghi789) — completed 2025-12-22
```

## Rules & constraints

1. **Never invent citations.** If a query returns nothing, say so. The skill loses credibility the first time it hallucinates an asset ID.
2. **Stay read-only.** Do not call mutating `upscaler_manage_*` actions, `upscaler entry create`, `upscaler todo create`, etc. Mixed-scope tools may be used only for documented read actions. Write workflows route to the relevant write-capable skill.
3. **Framework-agnostic.** Do not assume ISO 27001 unless the user names it. Discover the framework from the workspace.
4. **Stay inside the compliance-system scope** when the question is compliance-scoped. Scope hits to the relevant management-system root (ISMS for ISO 27001; a QMS / EMS / DORA program has a different root — discover it, don't hard-code "ISMS"). Prefer scoping the search with `--parent-id <root>` / `parent_id`; `hierarchy <id>` returns descendants, not ancestors, so don't use it to check a hit's lineage.
5. **Route before answering** when the intent is workflow-shaped. Don't half-build an evidence pack — hand off to the specialist.
6. **One tier per session.** Pick MCP or CLI at the start and stay on it; mixing produces inconsistent schemas.
7. **Cite by `upscaler:<asset_id>`** so the user can resolve via the platform UI or `upscaler get <id>`.

## Anti-patterns

- Producing a multi-section "compliance report" when the user asked a simple question. → Answer concisely; if they want the full pack, see [Workflows outside this library](#workflows-outside-this-library).
- Returning the raw JSON from MCP/CLI. → Always synthesize into prose + citations.
- Asking the user to specify the framework before checking the workspace. → Check `upscaler_search_nodes` / `upscaler --json asset find --title …` first; only ask if the workspace has multiple frameworks.
- Inventing control catalogs. → The user's workspace is the catalog.
- Falling back to "general best practice" answers when retrieval is empty. → Say "no matching assets found in your Upscaler workspace" and stop.
