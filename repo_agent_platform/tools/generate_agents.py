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
    "deny_by_default",
    "audit_trail_required",
    "rollback_plan_required"
]

ROLE_CAPABILITIES = {
    "researcher": ["public_web.read", "report.write"],
    "reviewer": ["artifact.read", "review.write"],
    "tester": ["test.execute_scoped", "report.write"],
    "monitor": ["telemetry.read", "alert.write"],
}

DEFAULT_CAPABILITIES = ["artifact.read", "report.write"]
FORBIDDEN_TOOLS = ["shell.unrestricted", "filesystem.unrestricted", "github.write"]


def build_agent(index: int) -> dict:
    role = ROLES[(index - 1) % len(ROLES)]
    return {
        "agent_id": f"agent_{index:05d}",
        "tenant": "default",
        "owner": "UNASSIGNED",
        "role": role,
        "name": f"{role.title()} Agent {index:05d}",
        "mission": f"Execute {role} tasks with validation, traceability, and quality gates.",
        "capabilities": ROLE_CAPABILITIES.get(role, DEFAULT_CAPABILITIES),
        "tools_allowed": [],
        "tools_forbidden": FORBIDDEN_TOOLS,
        "risk_level": "MEDIUM",
        "status": "PROPOSED",
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

    if args.count < 1 or args.count > 15000:
        raise SystemExit("count must be between 1 and 15000")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for index in range(1, args.count + 1):
            file.write(json.dumps(build_agent(index), ensure_ascii=False) + "\n")
    print(f"generated_agents={args.count}")
    print(f"output={output}")


if __name__ == "__main__":
    main()
