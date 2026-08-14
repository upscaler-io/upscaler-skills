#!/usr/bin/env python3
"""Package every skill under skills/ as a self-contained zip for ChatGPT.

ChatGPT installs skills one at a time via Settings -> Skills -> "Upload from
your computer", using the same Agent Skills format as this repo (a folder
anchored by SKILL.md). The one thing that breaks on upload is the repo-level
sharing: skills link to the four shared reference docs at the repository root
via relative paths (`../../references/<file>.md`), which resolve to nothing
once a skill folder leaves the repo.

This script builds an uploadable package per skill:
  1. Stage a copy of the skill directory.
  2. Find links that climb out of the skill to the repo-root `references/`
     directory (a `../` chain whose length equals the linking file's depth
     inside the skill plus two). Skill-internal `references/` links are left
     untouched.
  3. Copy each shared reference the skill actually links into the staged
     skill at `references/shared/` and rewrite the links to point there.
  4. Zip the staged folder to `dist/chatgpt/<skill-name>.zip` with the skill
     directory as the zip's single top-level entry.

Usage:
  python3 scripts/build_chatgpt_skills.py                    # package all skills
  python3 scripts/build_chatgpt_skills.py skills/upscaler-ask  # package one skill

Exits non-zero on failure. No third-party dependencies.
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
SHARED_REFS_DIR = REPO_ROOT / "references"
DIST_DIR = REPO_ROOT / "dist" / "chatgpt"

SHARED_SUBDIR = "references/shared"

# A chain of one or more `../` segments followed by `references/<file>.md`.
SHARED_LINK_RE = re.compile(r"((?:\.\./)+)references/([A-Za-z0-9][A-Za-z0-9._-]*\.md)")

IGNORE_NAMES = {"__pycache__", ".DS_Store"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def rewrite_links(staged_skill: Path) -> set[str]:
    """Rewrite repo-root reference links in every markdown file of the staged
    skill to point at the bundled copy. Returns the shared filenames used."""
    used: set[str] = set()
    for md_file in sorted(staged_skill.rglob("*.md")):
        depth = len(md_file.relative_to(staged_skill).parts) - 1
        text = md_file.read_text(encoding="utf-8")

        def replace(match: re.Match[str]) -> str:
            ups = match.group(1).count("../")
            filename = match.group(2)
            # From a file at depth d inside the skill, exactly d+2 `../`
            # segments reach the repository root; anything else is a
            # skill-internal or unrelated path and stays as written.
            if ups != depth + 2:
                return match.group(0)
            used.add(filename)
            return "../" * depth + f"{SHARED_SUBDIR}/{filename}"

        rewritten = SHARED_LINK_RE.sub(replace, text)
        if rewritten != text:
            md_file.write_text(rewritten, encoding="utf-8")
    return used


def bundle_shared_refs(staged_skill: Path, filenames: set[str]) -> None:
    if not filenames:
        return
    shared_dir = staged_skill / SHARED_SUBDIR
    shared_dir.mkdir(parents=True, exist_ok=True)
    for filename in sorted(filenames):
        source = SHARED_REFS_DIR / filename
        if not source.is_file():
            fail(f"{staged_skill.name} links missing shared reference: references/{filename}")
        shutil.copy2(source, shared_dir / filename)


def zip_skill(staged_skill: Path, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(staged_skill.rglob("*")):
            if path.is_dir() or path.name in IGNORE_NAMES:
                continue
            archive.write(path, f"{staged_skill.name}/{path.relative_to(staged_skill)}")


def build_skill(skill_dir: Path) -> None:
    if not (skill_dir / "SKILL.md").is_file():
        fail(f"{skill_dir} has no SKILL.md")
    with tempfile.TemporaryDirectory() as tmp:
        staged = Path(tmp) / skill_dir.name
        shutil.copytree(skill_dir, staged, ignore=shutil.ignore_patterns(*IGNORE_NAMES))
        used = rewrite_links(staged)
        bundle_shared_refs(staged, used)
        out_path = DIST_DIR / f"{skill_dir.name}.zip"
        zip_skill(staged, out_path)
    size_kb = out_path.stat().st_size / 1024
    shared = ", ".join(sorted(used)) if used else "none"
    print(f"  {out_path.relative_to(REPO_ROOT)}  ({size_kb:.0f} KB, shared refs: {shared})")


def main(argv: list[str]) -> None:
    if argv:
        targets = [Path(arg).resolve() for arg in argv]
        for target in targets:
            if not target.is_dir():
                fail(f"not a directory: {target}")
    else:
        targets = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    print(f"Packaging {len(targets)} skill(s) for ChatGPT into {DIST_DIR.relative_to(REPO_ROOT)}/")
    for skill_dir in targets:
        build_skill(skill_dir)
    print("Done. Upload each zip in ChatGPT via Settings -> Skills -> Upload from your computer.")


if __name__ == "__main__":
    main(sys.argv[1:])
