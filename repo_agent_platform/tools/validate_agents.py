#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED = {
    "agent_id", "tenant", "owner", "role", "name", "mission",
    "capabilities", "tools_allowed", "tools_forbidden", "risk_level",
    "status", "guardrails", "quality_gate", "priority"
}
ALLOWED_STATUSES = {"PROPOSED", "ADR_APPROVED", "IMPLEMENTING", "EXPERIMENTAL"}
DANGEROUS_ALLOWED_TOOLS = {
    "shell", "filesystem", "github", "shell.unrestricted",
    "filesystem.unrestricted", "github.write"
}
MAX_AGENT_DEFINITIONS = 15000


def _require_non_empty_string(item: dict[str, Any], field: str, line_number: int) -> None:
    value = item[field]
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"line {line_number}: {field} must be a non-empty string")


def _require_string_list(item: dict[str, Any], field: str, line_number: int) -> None:
    value = item[field]
    if not isinstance(value, list) or any(not isinstance(entry, str) or not entry.strip() for entry in value):
        raise SystemExit(f"line {line_number}: {field} must be a list of non-empty strings")


def validate_item(item: dict[str, Any], line_number: int) -> None:
    if not isinstance(item, dict):
        raise SystemExit(f"line {line_number}: agent definition must be an object")

    missing = REQUIRED - set(item)
    if missing:
        raise SystemExit(f"line {line_number}: missing {sorted(missing)}")

    for field in ("agent_id", "tenant", "owner", "role", "name", "mission", "risk_level", "status"):
        _require_non_empty_string(item, field, line_number)

    if item["status"] not in ALLOWED_STATUSES:
        raise SystemExit(f"line {line_number}: unsupported status {item['status']!r}")

    for field in ("capabilities", "tools_allowed", "tools_forbidden", "guardrails"):
        _require_string_list(item, field, line_number)

    dangerous = DANGEROUS_ALLOWED_TOOLS.intersection(item["tools_allowed"])
    if dangerous:
        raise SystemExit(f"line {line_number}: dangerous global tools allowed {sorted(dangerous)}")

    quality_gate = item["quality_gate"]
    if not isinstance(quality_gate, dict):
        raise SystemExit(f"line {line_number}: quality_gate must be an object")
    if not quality_gate.get("manual_approval_required", False):
        raise SystemExit(f"line {line_number}: manual approval must be required")

    priority = item["priority"]
    if not isinstance(priority, int) or isinstance(priority, bool) or not 1 <= priority <= 10:
        raise SystemExit(f"line {line_number}: priority must be an integer between 1 and 10")


def validate_file(path: Path) -> int:
    seen_agent_ids: set[str] = set()
    count = 0

    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                raise SystemExit(f"line {line_number}: empty lines are not allowed")
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"line {line_number}: invalid JSON: {exc.msg}") from exc

            validate_item(item, line_number)
            agent_id = item["agent_id"]
            if agent_id in seen_agent_ids:
                raise SystemExit(f"line {line_number}: duplicate agent_id {agent_id!r}")
            seen_agent_ids.add(agent_id)

            count += 1
            if count > MAX_AGENT_DEFINITIONS:
                raise SystemExit(f"agent definition count exceeds {MAX_AGENT_DEFINITIONS}")

    if count == 0:
        raise SystemExit("agent definition file must contain at least one record")
    return count


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_agents.py <agents.jsonl>")
    path = Path(sys.argv[1])
    count = validate_file(path)
    print(f"valid_agents={count}")


if __name__ == "__main__":
    main()
