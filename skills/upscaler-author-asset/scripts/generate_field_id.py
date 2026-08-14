#!/usr/bin/env python3
"""Generate Upscaler form field IDs.

Produces identifiers in the format `ff_<28 chars>` where the 28-char
suffix is drawn uniformly from the base62 alphabet `A-Za-z0-9`
(no underscore, no hyphen). This matches the platform's native field
naming convention: the platform mints base62 ids, and the select_values
regex `^ff_[A-Za-z0-9_]+$` silently drops any hyphenated key, so a
non-base62 id projects to nothing.

Usage:
  python3 generate_field_id.py          # one ID
  python3 generate_field_id.py 10       # ten IDs (one per line)
  python3 generate_field_id.py --check ff_btHrCEEWqKfq5zO7Konyy2DfGTTE
                                        # validate a single ID, exit 0/1
"""
from __future__ import annotations

import re
import secrets
import sys

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
SIZE = 28
PATTERN = re.compile(r"^ff_[A-Za-z0-9]{28}$")


def generate_field_id() -> str:
    return "ff_" + "".join(secrets.choice(ALPHABET) for _ in range(SIZE))


def is_valid(field_id: str) -> bool:
    return bool(PATTERN.match(field_id))


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[1] == "--check":
        return 0 if is_valid(argv[2]) else 1

    count = 1
    if len(argv) >= 2:
        try:
            count = int(argv[1])
        except ValueError:
            print(f"Usage: {argv[0]} [count] | --check <field_id>", file=sys.stderr)
            return 2
        if count < 1:
            print("count must be >= 1", file=sys.stderr)
            return 2

    for _ in range(count):
        print(generate_field_id())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
