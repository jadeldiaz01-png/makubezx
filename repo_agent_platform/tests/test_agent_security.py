import json
import tempfile
import unittest
from pathlib import Path

from repo_agent_platform.tools.generate_agents import build_agent
from repo_agent_platform.tools.validate_agents import validate_file, validate_item


class AgentSecurityTests(unittest.TestCase):
    def test_generated_agent_has_no_global_tools(self) -> None:
        agent = build_agent(1)
        self.assertEqual(agent["tools_allowed"], [])
        self.assertIn("shell.unrestricted", agent["tools_forbidden"])
        self.assertEqual(agent["status"], "PROPOSED")

    def test_validator_rejects_global_shell(self) -> None:
        agent = build_agent(1)
        agent["tools_allowed"] = ["shell"]
        with self.assertRaises(SystemExit):
            validate_item(agent, 1)

    def test_validator_requires_human_approval(self) -> None:
        agent = build_agent(1)
        agent["quality_gate"]["manual_approval_required"] = False
        with self.assertRaises(SystemExit):
            validate_item(agent, 1)

    def test_generation_is_bounded(self) -> None:
        self.assertEqual(build_agent(15000)["agent_id"], "agent_15000")

    def test_validator_rejects_empty_tenant(self) -> None:
        agent = build_agent(1)
        agent["tenant"] = "  "
        with self.assertRaises(SystemExit):
            validate_item(agent, 1)

    def test_validator_rejects_empty_owner(self) -> None:
        agent = build_agent(1)
        agent["owner"] = ""
        with self.assertRaises(SystemExit):
            validate_item(agent, 1)

    def test_validator_rejects_invalid_priority_type(self) -> None:
        agent = build_agent(1)
        agent["priority"] = True
        with self.assertRaises(SystemExit):
            validate_item(agent, 1)

    def test_file_validator_rejects_duplicate_agent_id(self) -> None:
        agent = build_agent(1)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "agents.jsonl"
            path.write_text(
                json.dumps(agent) + "\n" + json.dumps(agent) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(SystemExit):
                validate_file(path)

    def test_file_validator_rejects_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "agents.jsonl"
            path.write_text('{"agent_id": invalid}\n', encoding="utf-8")
            with self.assertRaises(SystemExit):
                validate_file(path)

    def test_file_validator_rejects_empty_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "agents.jsonl"
            path.write_text("", encoding="utf-8")
            with self.assertRaises(SystemExit):
                validate_file(path)


if __name__ == "__main__":
    unittest.main()
