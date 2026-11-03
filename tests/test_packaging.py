from pathlib import Path
import re
import unittest
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_agent_directory_contains_only_the_definition(self) -> None:
        directory = ROOT / ".github" / "agents"
        self.assertEqual(
            sorted(path.name for path in directory.iterdir()),
            ["tool-call-optimization-auditor.agent.md"],
        )
        agent = (directory / "tool-call-optimization-auditor.agent.md").read_text(encoding="utf-8")
        self.assertTrue(agent.startswith("---\n"))
        header, body = agent[4:].split("\n---\n", 1)
        self.assertIn("tools: [read, search]", header.splitlines())
        self.assertIn("agents: []", header.splitlines())
        self.assertIn("user-invocable: true", header.splitlines())
        self.assertRegex(header, r"(?m)^description: \".+\"$")
        self.assertIn("Audit methodology version: 0.2.0.", body)

    def test_documentation_links_resolve(self) -> None:
        paths = [ROOT / "README.md", ROOT / "CHANGELOG.md"]
        paths.extend((ROOT / "docs").glob("*.md"))
        paths.append(ROOT / "evaluations" / "README.md")
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if "://" in target or target.startswith("#"):
                    continue
                target = unquote(target.split("#", 1)[0])
                with self.subTest(source=path.name, target=target):
                    self.assertTrue((path.parent / target).exists())

    def test_license_is_explicit(self) -> None:
        self.assertTrue((ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License"))


if __name__ == "__main__":
    unittest.main()
