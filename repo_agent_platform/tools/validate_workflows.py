#!/usr/bin/env python3
"""Validate that external GitHub Actions are pinned to immutable commit SHAs."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

FULL_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
USES_LINE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)")


def iter_workflow_files(root: Path) -> Iterable[Path]:
    """Yield workflow YAML files in deterministic order."""
    if not root.exists():
        return
    yield from sorted((*root.glob("*.yml"), *root.glob("*.yaml")))


def validate_uses_reference(reference: str) -> str | None:
    """Return an error message when a uses reference is unsafe."""
    if reference.startswith("./"):
        return None
    if reference.startswith("docker://"):
        image = reference.removeprefix("docker://")
        if "@sha256:" not in image:
            return "container action must be pinned by sha256 digest"
        return None
    if "@" not in reference:
        return "external action is missing an immutable ref"
    action, ref = reference.rsplit("@", 1)
    if not action or not FULL_SHA.fullmatch(ref):
        return "external action must use a full 40-character commit SHA"
    return None


def validate_workflow(path: Path) -> list[str]:
    """Validate every uses entry in one workflow file."""
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = USES_LINE.match(line)
        if not match:
            continue
        reference = match.group(1).strip('"\'')
        error = validate_uses_reference(reference)
        if error:
            errors.append(f"{path}:{line_number}: {reference}: {error}")
    return errors


def validate_workflows(root: Path) -> list[str]:
    """Validate all workflows under root."""
    errors: list[str] = []
    for path in iter_workflow_files(root):
        errors.extend(validate_workflow(path))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(".github/workflows"))
    args = parser.parse_args()

    errors = validate_workflows(args.root)
    if errors:
        raise SystemExit("\n".join(errors))
    print("workflow_action_pinning_valid=true")


if __name__ == "__main__":
    main()
