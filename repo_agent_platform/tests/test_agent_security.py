import unittest

from repo_agent_platform.tools.generate_agents import build_agent
from repo_agent_platform.tools.validate_agents import validate_item


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


if __name__ == "__main__":
    unittest.main()
