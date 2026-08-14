#!/usr/bin/env python3
"""Tool-call cost harness for upscaler-ask.

For each should_trigger query in trigger_eval.json, run `claude -p <query>`
with stream-json output, then capture per-run metrics:
  - total tool calls made
  - whether upscaler-ask was invoked (via the Skill tool)
  - whether any upscaler_* MCP tool was called
  - whether any upscaler CLI Bash call was made
  - duration_ms and cost

Aggregate into mean/median per category and write a markdown report.

Usage:
  python tool_call_cost.py [--limit N] [--out DIR]

Defaults:
  --limit  0 (run all should_trigger queries)
  --out    ../../upscaler-ask-workspace/tool-call-cost/<timestamp>/
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

EVAL_SET = Path(__file__).resolve().parent / "trigger_eval.json"
DEFAULT_OUT_BASE = (
    Path(__file__).resolve().parent.parent.parent
    / "upscaler-ask-workspace"
    / "tool-call-cost"
)


def run_query(query: str, timeout_seconds: int = 600) -> dict:
    """Invoke `claude -p` with stream-json output and parse tool usage."""
    env = {**os.environ, "CLAUDECODE": ""}  # allow nesting claude -p inside Claude Code
    started = time.time()
    proc = subprocess.run(
        [
            "claude",
            "-p",
            query,
            "--output-format",
            "stream-json",
            "--verbose",
        ],
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        env=env,
    )
    wall_seconds = time.time() - started

    tool_calls: list[str] = []
    invoked_upscaler_ask = False
    upscaler_mcp_calls: list[str] = []
    upscaler_bash_calls: list[str] = []
    result_summary: dict = {}

    for line in proc.stdout.splitlines():
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        if msg.get("type") == "assistant":
            for block in msg.get("message", {}).get("content", []) or []:
                if block.get("type") != "tool_use":
                    continue
                name = block.get("name") or ""
                tool_calls.append(name)
                inp = block.get("input") or {}
                if name == "Skill" and inp.get("skill") == "upscaler-ask":
                    invoked_upscaler_ask = True
                if name.startswith("upscaler_") or "__upscaler_" in name:
                    upscaler_mcp_calls.append(name)
                if name == "Bash":
                    cmd = inp.get("command", "")
                    if "upscaler " in cmd or cmd.startswith("upscaler"):
                        upscaler_bash_calls.append(cmd[:120])
        elif msg.get("type") == "result":
            result_summary = msg

    return {
        "query": query,
        "tool_calls_total": len(tool_calls),
        "tool_calls": tool_calls,
        "invoked_upscaler_ask": invoked_upscaler_ask,
        "upscaler_mcp_calls": upscaler_mcp_calls,
        "upscaler_bash_calls_count": len(upscaler_bash_calls),
        "duration_ms": result_summary.get("duration_ms", int(wall_seconds * 1000)),
        "total_cost_usd": result_summary.get("total_cost_usd"),
        "is_error": result_summary.get("is_error", False),
        "num_turns": result_summary.get("num_turns"),
    }


def aggregate(rows: list[dict]) -> dict:
    by_category: dict[str, list[dict]] = {}
    for r in rows:
        by_category.setdefault(r["category"], []).append(r)

    def stats(values: list[float | int]) -> dict:
        if not values:
            return {"n": 0}
        result = {
            "n": len(values),
            "mean": round(statistics.mean(values), 1),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
        }
        if len(values) > 1:
            result["stdev"] = round(statistics.stdev(values), 1)
        return result

    return {
        "overall": {
            "n": len(rows),
            "trigger_rate": round(
                sum(1 for r in rows if r["invoked_upscaler_ask"]) / len(rows), 3
            )
            if rows
            else 0,
            "tool_calls": stats([r["tool_calls_total"] for r in rows]),
            "duration_seconds": stats(
                [round(r["duration_ms"] / 1000, 1) for r in rows]
            ),
            "cost_usd": stats(
                [r["total_cost_usd"] for r in rows if r.get("total_cost_usd") is not None]
            ),
        },
        "by_category": {
            cat: {
                "n": len(items),
                "trigger_rate": round(
                    sum(1 for r in items if r["invoked_upscaler_ask"]) / len(items), 3
                ),
                "tool_calls": stats([r["tool_calls_total"] for r in items]),
                "duration_seconds": stats(
                    [round(r["duration_ms"] / 1000, 1) for r in items]
                ),
            }
            for cat, items in by_category.items()
        },
    }


def write_markdown_report(rows: list[dict], agg: dict, out_path: Path) -> None:
    overall = agg["overall"]
    lines: list[str] = []
    lines.append("# upscaler-ask tool-call cost benchmark\n")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}\n")
    lines.append("## Overall\n")
    lines.append(f"- Queries run: **{overall['n']}**")
    lines.append(f"- Trigger rate (upscaler-ask invoked): **{overall['trigger_rate'] * 100:.1f}%**")
    lines.append(
        f"- Tool calls per query: mean **{overall['tool_calls'].get('mean')}**, "
        f"median {overall['tool_calls'].get('median')}, "
        f"range {overall['tool_calls'].get('min')}-{overall['tool_calls'].get('max')}"
    )
    lines.append(
        f"- Duration per query: mean **{overall['duration_seconds'].get('mean')}s**, "
        f"median {overall['duration_seconds'].get('median')}s"
    )
    if overall["cost_usd"].get("n"):
        lines.append(
            f"- Cost per query: mean **${overall['cost_usd'].get('mean')}**, "
            f"total ~${round(overall['cost_usd'].get('mean') * overall['n'], 2)}"
        )
    lines.append("")
    lines.append("## Per-query results\n")
    lines.append("| # | Category | Triggered? | Tool calls | Duration | Query |")
    lines.append("|---|---|---|---:|---:|---|")
    for i, r in enumerate(rows, 1):
        triggered = "yes" if r["invoked_upscaler_ask"] else "no"
        dur = f"{r['duration_ms'] / 1000:.1f}s"
        q = r["query"][:80].replace("|", "\\|")
        lines.append(
            f"| {i} | {r['category']} | {triggered} | {r['tool_calls_total']} | {dur} | {q} |"
        )
    lines.append("")
    lines.append("## By category\n")
    lines.append("| Category | N | Trigger rate | Tool calls (mean) | Duration (mean) |")
    lines.append("|---|---:|---:|---:|---:|")
    for cat, c in agg["by_category"].items():
        lines.append(
            f"| {cat} | {c['n']} | {c['trigger_rate'] * 100:.0f}% | "
            f"{c['tool_calls'].get('mean')} | {c['duration_seconds'].get('mean')}s |"
        )
    out_path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Run only the first N should-trigger queries (0 = all)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: ../upscaler-ask-workspace/tool-call-cost/<timestamp>/)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Per-query timeout in seconds (default 600)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of runs per query (for variance estimation)",
    )
    parser.add_argument(
        "--filter-categories",
        type=str,
        default=None,
        help="Comma-separated category names to include (default: all should_trigger)",
    )
    args = parser.parse_args()

    eval_set = json.loads(EVAL_SET.read_text())
    queries = [e for e in eval_set if e.get("should_trigger")]
    if args.filter_categories:
        wanted = {c.strip() for c in args.filter_categories.split(",")}
        queries = [q for q in queries if q.get("category") in wanted]
    if args.limit:
        queries = queries[: args.limit]
    # Expand by --runs so each query appears N times (with a run_index suffix).
    expanded = []
    for q in queries:
        for r in range(args.runs):
            expanded.append({**q, "_run_index": r + 1})
    queries = expanded

    out_dir = args.out or (
        DEFAULT_OUT_BASE / datetime.now().strftime("%Y%m%d-%H%M%S")
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Running {len(queries)} should-trigger queries...", file=sys.stderr)
    print(f"Output dir: {out_dir}", file=sys.stderr)

    rows: list[dict] = []
    for i, eval_item in enumerate(queries, 1):
        category = eval_item.get("category", "uncategorized")
        query = eval_item["query"]
        print(f"[{i}/{len(queries)}] {category}: {query[:60]}...", file=sys.stderr)
        try:
            result = run_query(query, timeout_seconds=args.timeout)
        except subprocess.TimeoutExpired:
            result = {
                "query": query,
                "tool_calls_total": 0,
                "tool_calls": [],
                "invoked_upscaler_ask": False,
                "upscaler_mcp_calls": [],
                "upscaler_bash_calls_count": 0,
                "duration_ms": args.timeout * 1000,
                "total_cost_usd": None,
                "is_error": True,
                "num_turns": None,
            }
            print(f"  TIMEOUT after {args.timeout}s", file=sys.stderr)
        result["category"] = category
        result["run_index"] = eval_item.get("_run_index", 1)
        rows.append(result)
        print(
            f"  -> tool_calls={result['tool_calls_total']}, "
            f"triggered={result['invoked_upscaler_ask']}, "
            f"dur={result['duration_ms'] / 1000:.1f}s",
            file=sys.stderr,
        )
        # Write incremental row so a crash mid-run doesn't lose everything.
        suffix = f"-r{result['run_index']}" if args.runs > 1 else ""
        (out_dir / f"run-{i:02d}-{category}{suffix}.json").write_text(
            json.dumps(result, indent=2)
        )

    agg = aggregate(rows)
    (out_dir / "runs.json").write_text(json.dumps(rows, indent=2))
    (out_dir / "aggregate.json").write_text(json.dumps(agg, indent=2))
    write_markdown_report(rows, agg, out_dir / "report.md")

    print(f"\nDone. Report: {out_dir}/report.md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
