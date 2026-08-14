#!/usr/bin/env python3
"""Package every skill for editors that have no Agent Skills loader.

Claude Code, Codex, and `npx skills` install this repo directly and need no
artifact. ChatGPT gets per-skill zips from build_chatgpt_skills.py. The two
remaining agents in the README's support table load a single flat context
file each, so they need the skills reshaped:

  Cursor      reads `.cursor/rules/*.mdc` - one rule file per skill, with
              Cursor's own frontmatter keys (description / globs /
              alwaysApply) instead of the Agent Skills ones.
  Gemini CLI  reads one `GEMINI.md` - every skill concatenated into a single
              document.

Both reshapes break the same thing: a skill's markdown links out to the
repo-root `references/` directory (`../../references/<file>.md`) and to its
own support files (`references/`, `examples/`, `scripts/`). Neither path
resolves once the skill is flattened, so this script copies every linked
file into the bundle under a single namespaced root and rewrites the links
to match. A skill that links a file which does not exist is a hard error,
because a bundle with dead links is worse than no bundle.

Outputs, all under dist/editors/ (gitignored):
  cursor-rules.zip    unzip at a project root -> .cursor/rules/
  gemini-context.zip  unzip at a project root -> GEMINI.md + refs
  GEMINI.md           the same file standalone, for appending by hand

Usage:
  python3 scripts/build_editor_bundles.py           # both bundles
  python3 scripts/build_editor_bundles.py cursor    # just Cursor
  python3 scripts/build_editor_bundles.py gemini    # just Gemini

Exits non-zero on failure. No third-party dependencies.
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
SHARED_REFS_DIR = REPO_ROOT / "references"
DIST_DIR = REPO_ROOT / "dist" / "editors"
CODEX_MANIFEST = REPO_ROOT / ".codex-plugin" / "plugin.json"

# Directory the bundles park every linked reference under. One namespaced root
# keeps a flattened skill's links unambiguous and collision-free.
REF_ROOT = "upscaler-skills-refs"
SHARED_SUBDIR = f"{REF_ROOT}/shared"

# Support directories inside a skill that ship with the bundles. `evals/` is
# development-only tooling and is deliberately excluded.
SUPPORT_DIRS = ("references", "examples", "scripts")

# A `../` chain reaching the repo-root references/ directory. From SKILL.md,
# which sits at the skill root, that chain is exactly two segments long.
SHARED_LINK_RE = re.compile(r"(?:\.\./){2}references/([A-Za-z0-9][A-Za-z0-9._-]*\.md)")

IGNORE_NAMES = {"__pycache__", ".DS_Store", "Thumbs.db"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def bundle_version() -> str:
    try:
        return json.loads(CODEX_MANIFEST.read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError) as exc:
        fail(f"could not read version from {CODEX_MANIFEST.name}: {exc}")


def split_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    """Return (frontmatter, body) for a SKILL.md.

    Deliberately minimal, matching validate_skills.py: flat string keys only.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        fail(f"{path}: missing opening '---' frontmatter delimiter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        fail(f"{path}: missing closing '---' frontmatter delimiter")

    frontmatter: dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        key, _, value = raw.partition(":")
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return frontmatter, "\n".join(lines[end + 1 :]).strip()


def support_files(skill_dir: Path) -> list[str]:
    """Skill-relative paths of the support files that ship with the bundles."""
    found: list[str] = []
    for sub in SUPPORT_DIRS:
        root = skill_dir / sub
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and not any(p in IGNORE_NAMES for p in path.parts):
                found.append(str(path.relative_to(skill_dir)))
    return found


def rewrite_links(body: str, skill_name: str, files: list[str]) -> tuple[str, set[str]]:
    """Point a flattened skill's links at the bundled copies.

    Returns the rewritten body and the shared reference filenames it used.
    Handles both link styles the library uses: markdown `](path)` and inline
    `` `path` `` mentions, by rewriting the path token itself either way.
    """
    used: set[str] = set()

    def replace_shared(match: re.Match[str]) -> str:
        filename = match.group(1)
        if not (SHARED_REFS_DIR / filename).is_file():
            fail(f"{skill_name} links missing shared reference: references/{filename}")
        used.add(filename)
        return f"{SHARED_SUBDIR}/{filename}"

    body = SHARED_LINK_RE.sub(replace_shared, body)

    # Longest path first, so `references/01-a.md` cannot be partially rewritten
    # by a shorter prefix. The lookbehind stops a match inside an already
    # rewritten path.
    for rel in sorted(files, key=len, reverse=True):
        body = re.sub(
            rf"(?<![\w./-]){re.escape(rel)}",
            f"{REF_ROOT}/{skill_name}/{rel}",
            body,
        )
    return body, used


def collect_skills() -> list[tuple[Path, dict[str, str], str, list[str], set[str]]]:
    """(dir, frontmatter, rewritten body, support files, shared refs used)."""
    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if not skill_dirs:
        fail("no skills found under skills/")

    collected = []
    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            fail(f"skills/{skill_dir.name} has no SKILL.md")
        frontmatter, body = split_frontmatter(skill_md)
        for field in ("name", "description"):
            if not frontmatter.get(field):
                fail(f"skills/{skill_dir.name}: SKILL.md frontmatter missing {field}")
        files = support_files(skill_dir)
        body, used = rewrite_links(body, skill_dir.name, files)
        collected.append((skill_dir, frontmatter, body, files, used))
    return collected


def add_refs(archive: zipfile.ZipFile, prefix: str, skills, written: set[str]) -> None:
    """Write every linked reference into the archive under `prefix`."""
    for skill_dir, _, _, files, used in skills:
        for filename in sorted(used):
            arc = f"{prefix}{SHARED_SUBDIR}/{filename}"
            if arc not in written:
                archive.write(SHARED_REFS_DIR / filename, arc)
                written.add(arc)
        for rel in files:
            arc = f"{prefix}{REF_ROOT}/{skill_dir.name}/{rel}"
            if arc not in written:
                archive.write(skill_dir / rel, arc)
                written.add(arc)


def verify_bundle(zip_path: Path, prefix: str) -> int:
    """Assert every rewritten reference link resolves inside the archive.

    Dead links are the exact failure the bundling exists to prevent, so this
    runs as part of the build rather than as a separate opt-in check.
    """
    link_re = re.compile(rf"{re.escape(REF_ROOT)}/[A-Za-z0-9][A-Za-z0-9._/-]*")
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        checked, dangling = 0, []
        for name in sorted(names):
            if not name.endswith((".md", ".mdc")):
                continue
            text = archive.read(name).decode("utf-8")
            for target in sorted(set(link_re.findall(text))):
                checked += 1
                if prefix + target not in names:
                    dangling.append(f"{name} -> {target}")
    if dangling:
        fail(
            f"{zip_path.name} has {len(dangling)} dangling reference link(s):\n       "
            + "\n       ".join(dangling)
        )
    return checked


def build_cursor(skills, version: str) -> Path:
    """One .mdc rule per skill, laid out so unzipping at a project root works."""
    prefix = ".cursor/rules/"
    out_path = DIST_DIR / "cursor-rules.zip"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.unlink(missing_ok=True)

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for _, frontmatter, body, _, _ in skills:
            name = frontmatter["name"]
            # Agent-requested rule: a description Cursor matches against, no
            # glob attachment, not always-on. That is the closest analogue to
            # how an Agent Skills host loads a skill by description.
            mdc = (
                "---\n"
                f"description: {frontmatter['description']}\n"
                "globs:\n"
                "alwaysApply: false\n"
                "---\n\n"
                f"{body}\n"
            )
            archive.writestr(f"{prefix}{name}.mdc", mdc)
        add_refs(archive, prefix, skills, set())
        archive.writestr(f"{prefix}{REF_ROOT}/README.md", cursor_readme(version))

    checked = verify_bundle(out_path, prefix)
    print(f"  {out_path.relative_to(REPO_ROOT)}  "
          f"({out_path.stat().st_size / 1024:.0f} KB, {len(skills)} rules, "
          f"{checked} links verified)")
    return out_path


def cursor_readme(version: str) -> str:
    return (
        f"# Upscaler skills for Cursor (v{version})\n\n"
        "Generated by `scripts/build_editor_bundles.py`. Do not edit by hand.\n\n"
        "Each `../<skill>.mdc` is an agent-requested Cursor rule: Cursor matches "
        "its `description` against your prompt and loads it on demand. The "
        "markdown files in this directory are the reference docs those rules "
        "link to.\n\n"
        "Install: unzip at your project root so the files land in "
        "`.cursor/rules/`.\n"
    )


def build_gemini(skills, version: str) -> tuple[Path, Path]:
    """One concatenated GEMINI.md, plus the references it links."""
    parts = [
        f"# Upscaler Agent Skills (v{version})",
        "",
        "Generated by `scripts/build_editor_bundles.py`. Do not edit by hand.",
        "",
        "Each section below is one skill. Apply a skill when the request matches "
        "its **Use when** line. Reference documents are linked inline and live "
        f"under `{REF_ROOT}/` next to this file; read them on demand rather than "
        "up front.",
        "",
        "## Skills",
        "",
        "| Skill | Use when |",
        "| --- | --- |",
    ]
    for _, frontmatter, _, _, _ in skills:
        summary = frontmatter["description"].split(". ")[0].rstrip(".")
        parts.append(f"| `{frontmatter['name']}` | {summary}. |")
    parts.append("")

    for _, frontmatter, body, _, _ in skills:
        parts += [
            "---",
            "",
            f"# Skill: {frontmatter['name']}",
            "",
            f"**Use when:** {frontmatter['description']}",
            "",
            body,
            "",
        ]

    document = "\n".join(parts).rstrip() + "\n"

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    md_path = DIST_DIR / "GEMINI.md"
    md_path.write_text(document, encoding="utf-8")

    zip_path = DIST_DIR / "gemini-context.zip"
    zip_path.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("GEMINI.md", document)
        add_refs(archive, "", skills, set())

    checked = verify_bundle(zip_path, "")
    print(f"  {md_path.relative_to(REPO_ROOT)}  ({len(document) / 1024:.0f} KB, "
          f"{len(skills)} skills inlined)")
    print(f"  {zip_path.relative_to(REPO_ROOT)}  "
          f"({zip_path.stat().st_size / 1024:.0f} KB, GEMINI.md + references, "
          f"{checked} links verified)")
    return md_path, zip_path


def main(argv: list[str]) -> int:
    targets = argv or ["cursor", "gemini"]
    unknown = [t for t in targets if t not in ("cursor", "gemini")]
    if unknown:
        fail(f"unknown target: {unknown[0]} (expected 'cursor' and/or 'gemini')")

    version = bundle_version()
    skills = collect_skills()
    print(f"Packaging {len(skills)} skill(s) for {', '.join(targets)} "
          f"into {DIST_DIR.relative_to(REPO_ROOT)}/")

    if "cursor" in targets:
        build_cursor(skills, version)
    if "gemini" in targets:
        build_gemini(skills, version)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
