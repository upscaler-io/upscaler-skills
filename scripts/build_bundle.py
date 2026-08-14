#!/usr/bin/env python3
"""Package the whole library as one installable bundle zip.

Unlike the per-skill ChatGPT packages (see build_chatgpt_skills.py), the bundle
keeps the repository shape intact: `skills/` sits next to the repo-root
`references/` directory, so every skill's `../../references/<file>.md` link
still resolves inside the zip. No link rewriting, no per-skill staging.

The bundle carries both plugin manifests (`.claude-plugin/`, `.codex-plugin/`),
so an unzipped copy is directly installable as a local Claude Code or Codex
plugin, and is also usable by hand (copy `skills/<name>/` into
`~/.claude/skills/`).

Development-only files are left out: `scripts/` (the packagers themselves),
`.github/`, `.git/`, `dist/`, and editor/OS noise.

Every build runs the same validation CI runs (validate_skills.main), because a
distribution artifact that violates the Agent Skills spec is worse than no
artifact. A failing tree refuses to package unless `--force` is passed, which
still validates and still reports, but writes the zip anyway: for packaging a
work-in-progress tree to test locally, never for anything handed to a user.

The bundle name and version both come from `.codex-plugin/plugin.json`, the
only manifest carrying semver, so a repo rename cannot desync them.

Usage:
  python3 scripts/build_bundle.py            # -> dist/<plugin-name>.zip
  python3 scripts/build_bundle.py --force    # package a failing tree anyway

Exits non-zero on failure. No third-party dependencies.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import validate_skills

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
DIST_DIR = REPO_ROOT / "dist"
CODEX_MANIFEST = REPO_ROOT / ".codex-plugin" / "plugin.json"

# Top-level repo entries that ship in the bundle. Everything else is treated as
# development-only. Directories are included recursively.
BUNDLE_ENTRIES = (
    ".claude-plugin",
    ".codex-plugin",
    "skills",
    "references",
    "docs",
    "README.md",
    "AGENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "llms.txt",
)

# Never packaged, at any depth.
IGNORE_NAMES = {"__pycache__", ".DS_Store", "Thumbs.db", ".remember"}
IGNORE_SUFFIXES = {".pyc", ".pyo"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def is_ignored(path: Path) -> bool:
    """True if any path segment is ignored, or the file has an ignored suffix."""
    if path.suffix in IGNORE_SUFFIXES:
        return True
    return any(part in IGNORE_NAMES for part in path.parts)


def collect_files() -> list[Path]:
    """Repo-relative paths to package, in stable order."""
    collected: list[Path] = []
    for entry_name in BUNDLE_ENTRIES:
        entry = REPO_ROOT / entry_name
        if not entry.exists():
            fail(f"bundle entry missing from repo: {entry_name}")
        if entry.is_file():
            collected.append(entry.relative_to(REPO_ROOT))
            continue
        for path in sorted(entry.rglob("*")):
            if path.is_file() and not is_ignored(path.relative_to(REPO_ROOT)):
                collected.append(path.relative_to(REPO_ROOT))
    return collected


def bundled_skills() -> list[str]:
    """Skill directory names, asserting each is anchored by a SKILL.md."""
    if not SKILLS_DIR.is_dir():
        fail("skills/ directory not found")
    names = []
    for skill_dir in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        if skill_dir.name in IGNORE_NAMES:
            continue
        if not (skill_dir / "SKILL.md").is_file():
            fail(f"skills/{skill_dir.name} has no SKILL.md")
        names.append(skill_dir.name)
    if not names:
        fail("no skills found under skills/")
    return names


def bundle_identity() -> tuple[str, str]:
    """(name, version) from the Codex manifest, the only manifest with semver.

    Derived rather than hard-coded so the zip name tracks the plugin name
    across repos instead of drifting from it.
    """
    try:
        manifest = json.loads(CODEX_MANIFEST.read_text(encoding="utf-8"))
        return manifest["name"], manifest["version"]
    except (OSError, ValueError, KeyError) as exc:
        fail(f"could not read name/version from {CODEX_MANIFEST.name}: {exc}")


def validate(force: bool) -> None:
    """Run the CI validation over the tree about to be packaged.

    Delegates to validate_skills.main with no targets so the gate stays
    identical to the CI check instead of drifting into a second rule set.
    """
    if validate_skills.main(["build_bundle"]) == 0:
        return
    print()
    if not force:
        fail(
            "validation failed, refusing to package a spec-invalid bundle.\n"
            "       Fix the errors above, or re-run with --force to package anyway."
        )
    print("WARNING: packaging a spec-invalid bundle because --force was passed.")
    print("         Do not distribute this zip.")
    print()


def build(force: bool = False) -> Path:
    validate(force)
    skills = bundled_skills()
    bundle_name, version = bundle_identity()
    files = collect_files()

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DIST_DIR / f"{bundle_name}.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for rel_path in files:
            archive.write(REPO_ROOT / rel_path, Path(bundle_name) / rel_path)

    print(f"{bundle_name} {version} -> {zip_path.relative_to(REPO_ROOT)}")
    print(f"  {len(files)} files, {zip_path.stat().st_size / 1024:.0f} KB")
    print(f"  {len(skills)} skills: {', '.join(skills)}")
    return zip_path


if __name__ == "__main__":
    args = sys.argv[1:]
    unknown = [a for a in args if a != "--force"]
    if unknown:
        fail(f"unexpected argument: {unknown[0]} (only --force is accepted)")
    build(force="--force" in args)
