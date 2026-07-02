#!/usr/bin/env python3
import json
from pathlib import Path

path = Path("repo_agent_platform/catalog/categories.json")
data = json.loads(path.read_text(encoding="utf-8"))
assert data["target_total_repositories"] == 300
assert data["rules"]["dry_run_default"] is True
assert data["rules"]["require_manual_approval"] is True
assert len(data["categories"]) >= 10
print("catalog_valid=true")
print("target_total_repositories=300")
print(f"categories={len(data['categories'])}")
