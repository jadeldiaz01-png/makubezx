#!/usr/bin/env python3
import json
import sys
from pathlib import Path

REQUIRED = {
    "agent_id", "tenant", "owner", "role", "name", "mission",
    "capabilities", "tools_allowed", "tools_forbidden", "risk_level",
    "status", "guardrails", "quality_gate", "priority"
}
ALLOWED_STATUSES = {"PROPOSED", "ADR_APPROVED", "IMPLEMENTING", "EXPERIMENTAL"}
DANGEROUS_ALLOWED_TOOLS = {"shell", "filesystem", "github", "shell.unrestricted", "filesystem.unrestricted", "github.write"}


def validate_item(item: dict, line_number: int) -> None:
    missing = REQUIRED - set(item)
    if missing:
        raise SystemExit(f"line {line_number}: missing {sorted(missing)}")
    if item["status"] not in ALLOWED_STATUSES:
        raise SystemExit(f"line {line_number}: unsupported status {item['status']!r}")
    if not isinstance(item["tools_allowed"], list):
        raise SystemExit(f"line {line_number}: tools_allowed must be a list")
    dangerous = DANGEROUS_ALLOWED_TOOLS.intersection(item["tools_allowed"])
    if dangerous:
        raise SystemExit(f"line {line_number}: dangerous global tools allowed {sorted(dangerous)}")
    if not item["quality_gate"].get("manual_approval_required", False):
        raise SystemExit(f"line {line_number}: manual approval must be required")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_agents.py <agents.jsonl>")
    path = Path(sys.argv[1])
    count = 0
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            item = json.loads(line)
            validate_item(item, line_number)
            count += 1
    print(f"valid_agents={count}")


if __name__ == "__main__":
    main()
