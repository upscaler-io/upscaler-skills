# upscaler-ask eval harness

Two complementary benchmarks for the `upscaler-ask` skill.

| Harness | What it measures | When to use |
|---|---|---|
| `trigger_eval.json` + skill-creator's `run_eval.py` | Whether Claude picks the *description* (as a fresh skill alias) for each query | Iterating on the `description:` frontmatter in isolation, before the skill is widely installed |
| `tool_call_cost.py` | Whether the *real, installed* `upscaler-ask` triggers, plus tool calls / duration / cost per query | Steady-state benchmarking once the skill is in production and competing skills are already installed |

Both consume the same `trigger_eval.json` so the eval set is shared.

## Eval set

`trigger_eval.json` contains 23 queries: 15 `should_trigger: true` covering all five categories the skill answers plus the list-and-count shape, and 8 `should_trigger: false` that are tricky near-misses (upscaler-flavored but route to a specialist skill, or compliance-flavored but not Upscaler at all).

Each entry has `query`, `should_trigger`, and `category` (used for per-category aggregation in the cost harness).

To add or edit queries, hand-edit the JSON. Keep negatives genuinely tricky — obvious irrelevancies do not test anything.

## Harness 1: trigger accuracy (skill-creator)

```bash
REPO=$(git rev-parse --show-toplevel)   # run from inside your upscaler-skills clone
SC=$(ls -d "$HOME"/.claude/plugins/cache/*/skill-creator/*/skills/skill-creator | head -1)
OUT="$HOME/upscaler-ask-evals"           # keep outputs outside the repo, see "Output location" below
mkdir -p "$OUT/baseline"

cd "$SC" && python3 -m scripts.run_eval \
  --eval-set "$REPO/skills/upscaler-ask/evals/trigger_eval.json" \
  --skill-path "$REPO/skills/upscaler-ask" \
  --runs-per-query 1 \
  --num-workers 4 \
  --model claude-opus-4-7 \
  --verbose \
  > "$OUT/baseline/results.json"
```

**What this is measuring.** `run_eval.py` writes the skill's current `description:` text into a fresh slash-command alias `upscaler-ask-skill-<uuid>` in `.claude/commands/`, then runs each query and checks whether Claude invokes the *alias* via the `Skill` tool. It is the right tool for iterating on the description in isolation — it removes confounds from skill body content, examples, and so on.

**The catch in our setup.** The real `upscaler-ask` skill is already installed alongside many specialist Upscaler skills (`upscaler-author-asset`, `compliance-assistant`, etc.). For any well-shaped Upscaler question, Claude will usually pick the *real* installed skill rather than the test alias — which `run_eval.py` records as a FAIL even though the routing behavior is correct.

Concretely, the first baseline run on this eval set scored 8/23 (all 15 positives failed, all 8 negatives passed). Re-running `claude -p` interactively on the same prompts shows the real `upscaler-ask` triggers cleanly — confirming the FAILs are a measurement artifact, not a routing problem.

**Use `run_eval.py` for:**

- Pre-install iteration: testing whether a candidate description would attract triggering in an empty skill list (the original skill-creator workflow).
- Description-only A/B: hold the skill body constant, vary just the `description:`, see which scores higher.

**Do not use it for:**

- Measuring the live triggering rate of an already-installed skill. The skill-creator's `run_loop.py` description-optimization loop has the same limitation since it uses `run_eval.py` under the hood.

## Harness 2: tool-call cost (`tool_call_cost.py`)

```bash
cd "$(git rev-parse --show-toplevel)/skills/upscaler-ask/evals"
OUT="$HOME/upscaler-ask-evals/tool-call-cost"

python3 tool_call_cost.py --out "$OUT"              # all 15 should_trigger queries
python3 tool_call_cost.py --limit 3 --out "$OUT"    # smoke-test on first 3
```

### Output location

Always pass `--out`. The default is `../../upscaler-ask-workspace/tool-call-cost/<timestamp>/`, which resolves to `skills/upscaler-ask-workspace/` inside the repo. `scripts/validate_skills.py` iterates every directory under `skills/` and requires a `SKILL.md` in each, so leaving that workspace in place breaks validation (and therefore CI and `scripts/build_bundle.py`) with `upscaler-ask-workspace: missing SKILL.md`. It is not gitignored either. Point `--out` outside the repo, or delete the workspace before validating.

For each `should_trigger` query, the script spawns `claude -p <query> --output-format stream-json --verbose`, parses the streamed tool-use events, and records:

- `tool_calls_total` — every `tool_use` block across all assistant messages in the run
- `invoked_upscaler_ask` — whether any `Skill` tool call had `input.skill == "upscaler-ask"`
- `upscaler_mcp_calls` — tool calls to `upscaler_*` (or `*__upscaler_*`) MCP tools
- `upscaler_bash_calls_count` — Bash calls that ran the `upscaler` CLI
- `duration_ms`, `total_cost_usd`, `num_turns`

Outputs land in `<--out>/<timestamp>/`:

- `run-NN-<category>.json` — per-query raw result (written incrementally, survives mid-run crashes)
- `runs.json` — all results in one file
- `aggregate.json` — overall + per-category stats (mean, median, min, max for tool_calls / duration / cost; trigger rate)
- `report.md` — human-readable summary

Cost: each `claude -p` call uses Opus 4.7 with a ~46k-token cached context (the full skill / tool list). First call creates the cache (~$0.30); subsequent calls hit cache and amortize down. Expect $0.50–$1.50 per query depending on how exploratory the question is. For 15 queries, budget ~$15–$25 and 45–75 minutes wall time.

## Interpreting results

**Trigger rate (`tool_call_cost.py`)** is the headline. The real `upscaler-ask` should fire on ≥90% of should_trigger queries. If it does not, look at which categories miss — that points at a gap in the `description:` triggers or in the skill body's category recipes.

**Tool calls per query** is the efficiency signal. A simple list-and-count question should land near ~6–10 tool calls (1 schema fetch + 1 list call + the rest is reasoning / formatting). Categories that consistently spike past ~15 mean the skill's recipe is not specific enough — the agent is exploring instead of executing.

**By-category breakdown** is where regressions surface. Adding a new recipe should leave other categories stable. If `tool_calls.mean` jumps in an unrelated category after an edit, the new text is probably attracting the agent into the wrong recipe.

## Re-running after a skill change

1. Edit `SKILL.md` (or its frontmatter).
2. `python3 tool_call_cost.py --out "$OUT"` to re-measure cost on all 15.
3. Compare the new `aggregate.json` against the previous timestamped dir.
4. If trigger rate dropped or tool_calls spiked, read the affected per-query JSONs to see which tools the agent reached for.

## Files

```
evals/
├── README.md                # this file
├── trigger_eval.json        # the 23-query shared eval set
└── tool_call_cost.py        # harness 2 implementation

$OUT/                        # outside the repo, e.g. ~/upscaler-ask-evals/
├── baseline/                # harness 1 outputs (run_eval.py)
│   ├── results.json
│   └── progress.log
└── tool-call-cost/<ts>/     # harness 2 outputs (one dir per run)
    ├── run-NN-<cat>.json
    ├── runs.json
    ├── aggregate.json
    └── report.md
```
