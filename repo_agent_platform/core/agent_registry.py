from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class AgentRecord:
    agent_id: str
    role: str
    name: str
    mission: str
    status: str = "available"
    version: str = "1.0.0"


class AgentRegistry:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write_jsonl(self, agents: Iterable[AgentRecord]) -> int:
        count = 0
        with self.path.open("w", encoding="utf-8") as file:
            for agent in agents:
                file.write(json.dumps(asdict(agent), ensure_ascii=False) + "\n")
                count += 1
        return count

    def read_jsonl(self) -> list[AgentRecord]:
        records: list[AgentRecord] = []
        if not self.path.exists():
            return records
        with self.path.open(encoding="utf-8") as file:
            for line in file:
                records.append(AgentRecord(**json.loads(line)))
        return records

    def find_by_role(self, role: str, limit: int = 10) -> list[AgentRecord]:
        return [agent for agent in self.read_jsonl() if agent.role == role][:limit]
