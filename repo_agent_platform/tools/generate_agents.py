#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ROLES = [
    "researcher", "coder", "reviewer", "tester", "security",
    "trading", "ml", "data", "devops", "content",
    "meta", "risk", "monitor", "optimizer", "scheduler"
]

GUARDRAILS = [
    "no_secrets_in_logs",
    "human_approval_for_publish",
    "dry_run_default",
    "audit_trail_required",
    "rollback_plan_required"
]

def build_agent(index: int) -> dict:
    role = ROLES[index % len(ROLES)]
    return {
        "agent_id": f"agent_{index:05d}",
        "role": role,
        "name": f"{role.title()} Agent {index:05d}",
        "mission": f"Execute {role} tasks with validation, traceability, and quality gates.",
        "tools_allowed": ["github", "filesystem", "python", "shell", "web_validation"],
        "guardrails": GUARDRAILS,
        "quality_gate": {
            "tests_required": True,
            "security_scan_required": True,
            "manual_approval_required": True
        },
        "priority": (index % 10) + 1
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=15000)
    parser.add_argument("--output", default="repo_agent_platform/generated/agents_15000.jsonl")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for index in range(1, args.count + 1):
            file.write(json.dumps(build_agent(index), ensure_ascii=False) + "\n")
    print(f"generated_agents={args.count}")
    print(f"output={output}")

if __name__ == "__main__":
    main()
