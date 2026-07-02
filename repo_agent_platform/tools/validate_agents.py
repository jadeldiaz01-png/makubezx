#!/usr/bin/env python3
import json
import sys
from pathlib import Path

REQUIRED = {"agent_id", "role", "name", "mission", "tools_allowed", "guardrails", "quality_gate", "priority"}

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_agents.py <agents.jsonl>")
    path = Path(sys.argv[1])
    count = 0
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            item = json.loads(line)
            missing = REQUIRED - set(item)
            if missing:
                raise SystemExit(f"line {line_number}: missing {sorted(missing)}")
            count += 1
    print(f"valid_agents={count}")

if __name__ == "__main__":
    main()
