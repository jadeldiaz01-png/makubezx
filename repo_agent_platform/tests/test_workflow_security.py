import tempfile
import unittest
from pathlib import Path

from repo_agent_platform.tools.validate_workflows import (
    validate_uses_reference,
    validate_workflow,
)


class WorkflowSecurityTests(unittest.TestCase):
    def test_accepts_full_commit_sha(self) -> None:
        reference = "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd"
        self.assertIsNone(validate_uses_reference(reference))

    def test_accepts_local_action(self) -> None:
        self.assertIsNone(validate_uses_reference("./.github/actions/local-check"))

    def test_accepts_container_digest(self) -> None:
        digest = "a" * 64
        self.assertIsNone(validate_uses_reference(f"docker://alpine@sha256:{digest}"))

    def test_rejects_major_version_tag(self) -> None:
        self.assertIsNotNone(validate_uses_reference("actions/checkout@v4"))

    def test_rejects_branch_reference(self) -> None:
        self.assertIsNotNone(validate_uses_reference("owner/action@main"))

    def test_rejects_short_sha(self) -> None:
        self.assertIsNotNone(validate_uses_reference("owner/action@de0fac2"))

    def test_rejects_unpinned_container(self) -> None:
        self.assertIsNotNone(validate_uses_reference("docker://alpine:3.20"))

    def test_reports_unsafe_workflow_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow = Path(temp_dir) / "unsafe.yml"
            workflow.write_text(
                "jobs:\n  test:\n    steps:\n      - uses: actions/checkout@v4\n",
                encoding="utf-8",
            )
            errors = validate_workflow(workflow)
        self.assertEqual(len(errors), 1)
        self.assertIn("actions/checkout@v4", errors[0])


if __name__ == "__main__":
    unittest.main()
