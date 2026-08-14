#!/usr/bin/env python3
"""Validate every skill under skills/ against the Agent Skills specification.

Rules enforced (https://agentskills.io/specification):
  1. Each skill is a directory containing a SKILL.md file.
  2. SKILL.md begins with a YAML frontmatter block delimited by `---`.
  3. Frontmatter defines non-empty `name` and `description`.
  4. `name` equals the directory name, matches [a-z0-9][a-z0-9-]*, is at most
     64 chars, has no consecutive hyphens, and does not end with a hyphen.
  5. `description` is at most 1024 characters.
  6. The SKILL.md body is non-empty.

Also lints `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
when present (Claude Code plugin distribution; format documented at
https://code.claude.com/docs/en/plugins and /plugin-marketplaces), and
`.codex-plugin/plugin.json` when present (OpenAI Codex CLI plugin manifest;
format documented at https://developers.openai.com/codex/plugins/build).

Usage:
  python3 scripts/validate_skills.py                      # validate all skills
  python3 scripts/validate_skills.py skills/upscaler-asset-definition  # validate one skill

Exits non-zero on failure. No third-party dependencies.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
PLUGIN_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_MANIFEST = REPO_ROOT / ".claude-plugin" / "marketplace.json"
CODEX_PLUGIN_MANIFEST = REPO_ROOT / ".codex-plugin" / "plugin.json"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
MAX_NAME_LEN = 64
MAX_DESCRIPTION_LEN = 1024
REQUIRED_FIELDS = ("name", "description")

# Marketplace names reserved for Anthropic; third-party marketplaces using these
# are rejected by the Claude.ai marketplace sync.
RESERVED_MARKETPLACE_NAMES = frozenset(
    {
        "claude-code-marketplace",
        "claude-code-plugins",
        "claude-plugins-official",
        "anthropic-marketplace",
        "anthropic-plugins",
        "agent-skills",
        "knowledge-work-plugins",
        "life-sciences",
    }
)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse a minimal YAML frontmatter block (flat string keys only)."""
    if not text.startswith("---"):
        raise ValueError("SKILL.md must start with a '---' frontmatter block")

    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        raise ValueError("Missing opening '---' delimiter")

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError("Missing closing '---' delimiter")

    frontmatter: dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            raise ValueError(f"Malformed frontmatter line: {raw!r}")
        key, value = raw.split(":", 1)
        key, value = key.strip(), value.strip()
        # A ": " inside an unquoted plain scalar is a nested mapping to a real
        # YAML parser, which rejects it. Splitting on the first colon alone
        # hides that, so the error only surfaces in the upstream agentskills
        # check in CI. Catch it here instead.
        quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'"
        if not quoted and ": " in value:
            raise ValueError(
                f"Frontmatter value for {key!r} contains ': ' outside quotes; "
                "strict YAML parsers read that as a nested mapping and fail. "
                "Rephrase to drop the colon, or quote the whole value."
            )
        frontmatter[key] = value.strip('"').strip("'")

    body = "\n".join(lines[end + 1 :]).strip()
    return frontmatter, body


def _check_kebab_name(label: str, name: str) -> list[str]:
    errors: list[str] = []
    if not NAME_RE.match(name):
        errors.append(f"{label}: name {name!r} must match [a-z0-9][a-z0-9-]*")
    if len(name) > MAX_NAME_LEN:
        errors.append(f"{label}: name {name!r} exceeds {MAX_NAME_LEN} chars")
    if "--" in name:
        errors.append(f"{label}: name {name!r} must not contain consecutive hyphens")
    if name.endswith("-"):
        errors.append(f"{label}: name {name!r} must not end with a hyphen")
    return errors


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.is_file():
        return [f"{skill_dir.name}: missing SKILL.md"]

    try:
        frontmatter, body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except ValueError as e:
        return [f"{skill_dir.name}/SKILL.md: {e}"]

    for field in REQUIRED_FIELDS:
        if not frontmatter.get(field):
            errors.append(f"{skill_dir.name}/SKILL.md: frontmatter missing '{field}'")

    name = frontmatter.get("name", "")
    if name:
        errors.extend(_check_kebab_name(f"{skill_dir.name}/SKILL.md", name))
        if name != skill_dir.name:
            errors.append(
                f"{skill_dir.name}/SKILL.md: name {name!r} does not match directory name "
                f"{skill_dir.name!r}"
            )

    description = frontmatter.get("description", "")
    if description and len(description) > MAX_DESCRIPTION_LEN:
        errors.append(
            f"{skill_dir.name}/SKILL.md: description exceeds {MAX_DESCRIPTION_LEN} chars "
            f"({len(description)} chars)"
        )

    if not body:
        errors.append(f"{skill_dir.name}/SKILL.md: body is empty")

    return errors


def validate_plugin_manifest(path: Path) -> list[str]:
    label = path.relative_to(REPO_ROOT).as_posix()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{label}: invalid JSON ({e.msg} at line {e.lineno} col {e.colno})"]

    if not isinstance(data, dict):
        return [f"{label}: top-level must be a JSON object"]

    errors: list[str] = []
    name = data.get("name")
    if not name or not isinstance(name, str):
        errors.append(f"{label}: missing required string field 'name'")
    else:
        errors.extend(_check_kebab_name(label, name))

    description = data.get("description")
    if not description or not isinstance(description, str):
        errors.append(f"{label}: missing required string field 'description'")

    return errors


def validate_codex_plugin_manifest(path: Path) -> list[str]:
    label = path.relative_to(REPO_ROOT).as_posix()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{label}: invalid JSON ({e.msg} at line {e.lineno} col {e.colno})"]

    if not isinstance(data, dict):
        return [f"{label}: top-level must be a JSON object"]

    errors: list[str] = []

    name = data.get("name")
    if not name or not isinstance(name, str):
        errors.append(f"{label}: missing required string field 'name'")
    else:
        errors.extend(_check_kebab_name(label, name))

    version = data.get("version")
    if not version or not isinstance(version, str):
        errors.append(f"{label}: missing required string field 'version'")
    elif not SEMVER_RE.match(version):
        errors.append(f"{label}: version {version!r} must be semver (e.g. '1.0.0')")

    description = data.get("description")
    if not description or not isinstance(description, str):
        errors.append(f"{label}: missing required string field 'description'")

    skills = data.get("skills")
    if skills is not None:
        if not isinstance(skills, str):
            errors.append(f"{label}: 'skills' must be a string path")
        else:
            target = (path.parent.parent / skills).resolve()
            if not target.is_dir():
                errors.append(f"{label}: skills path {skills!r} does not resolve to a directory")

    return errors


def validate_marketplace_manifest(path: Path) -> list[str]:
    label = path.relative_to(REPO_ROOT).as_posix()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{label}: invalid JSON ({e.msg} at line {e.lineno} col {e.colno})"]

    if not isinstance(data, dict):
        return [f"{label}: top-level must be a JSON object"]

    errors: list[str] = []

    name = data.get("name")
    if not name or not isinstance(name, str):
        errors.append(f"{label}: missing required string field 'name'")
    else:
        errors.extend(_check_kebab_name(label, name))
        if name in RESERVED_MARKETPLACE_NAMES:
            errors.append(
                f"{label}: marketplace name {name!r} is reserved by Anthropic; "
                f"choose a different name (reserved: {sorted(RESERVED_MARKETPLACE_NAMES)})"
            )

    owner = data.get("owner")
    if not isinstance(owner, dict) or not owner.get("name"):
        errors.append(f"{label}: 'owner.name' is required")

    plugins = data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        errors.append(f"{label}: 'plugins' must be a non-empty array")
    else:
        seen: set[str] = set()
        for i, entry in enumerate(plugins):
            entry_label = f"{label} plugins[{i}]"
            if not isinstance(entry, dict):
                errors.append(f"{entry_label}: must be an object")
                continue
            entry_name = entry.get("name")
            if not entry_name or not isinstance(entry_name, str):
                errors.append(f"{entry_label}: missing required string field 'name'")
            else:
                errors.extend(_check_kebab_name(entry_label, entry_name))
                if entry_name in seen:
                    errors.append(f"{entry_label}: duplicate plugin name {entry_name!r}")
                seen.add(entry_name)
            source = entry.get("source")
            if source is None:
                errors.append(f"{entry_label}: missing required field 'source'")
                continue
            if isinstance(source, str):
                if not source.startswith("./"):
                    errors.append(
                        f"{entry_label}: relative source {source!r} must start with './'"
                    )
                if ".." in Path(source).parts:
                    errors.append(f"{entry_label}: source {source!r} must not contain '..'")
                target = (REPO_ROOT / source).resolve()
                if not target.is_dir():
                    errors.append(f"{entry_label}: source {source!r} does not resolve to a directory")
                elif target != REPO_ROOT:
                    nested_manifest = target / ".claude-plugin" / "plugin.json"
                    if not nested_manifest.is_file():
                        errors.append(
                            f"{entry_label}: nested plugin source {source!r} is missing "
                            f".claude-plugin/plugin.json"
                        )
            elif isinstance(source, dict):
                source_kind = source.get("source")
                if source_kind not in {"github", "url", "git-subdir", "npm"}:
                    errors.append(
                        f"{entry_label}: source.source must be one of "
                        f"github/url/git-subdir/npm (got {source_kind!r})"
                    )
            else:
                errors.append(f"{entry_label}: source must be a string or object")

    return errors


def iter_skill_dirs(targets: list[str]) -> list[Path]:
    if targets:
        return [Path(t).resolve() for t in targets]
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())


def main(argv: list[str]) -> int:
    skill_dirs = iter_skill_dirs(argv[1:])

    all_errors: list[str] = []

    if not skill_dirs:
        print("No skills found under skills/")
    else:
        for skill_dir in skill_dirs:
            errors = validate_skill(skill_dir)
            if errors:
                print(f"FAIL  {skill_dir.name}")
                all_errors.extend(errors)
            else:
                print(f"ok    {skill_dir.name}")

    # Skip plugin/marketplace checks when running against a single skill target.
    if not argv[1:]:
        if PLUGIN_MANIFEST.is_file():
            errors = validate_plugin_manifest(PLUGIN_MANIFEST)
            label = PLUGIN_MANIFEST.relative_to(REPO_ROOT).as_posix()
            if errors:
                print(f"FAIL  {label}")
                all_errors.extend(errors)
            else:
                print(f"ok    {label}")

        if MARKETPLACE_MANIFEST.is_file():
            errors = validate_marketplace_manifest(MARKETPLACE_MANIFEST)
            label = MARKETPLACE_MANIFEST.relative_to(REPO_ROOT).as_posix()
            if errors:
                print(f"FAIL  {label}")
                all_errors.extend(errors)
            else:
                print(f"ok    {label}")

        if CODEX_PLUGIN_MANIFEST.is_file():
            errors = validate_codex_plugin_manifest(CODEX_PLUGIN_MANIFEST)
            label = CODEX_PLUGIN_MANIFEST.relative_to(REPO_ROOT).as_posix()
            if errors:
                print(f"FAIL  {label}")
                all_errors.extend(errors)
            else:
                print(f"ok    {label}")

    if all_errors:
        print()
        print(f"{len(all_errors)} error(s):")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
