import json
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
            ["ai-efficiency-auditor.agent.md"],
        )
        agent = (directory / "ai-efficiency-auditor.agent.md").read_text(encoding="utf-8")
        self.assertTrue(agent.startswith("---\n"))
        header, body = agent[4:].split("\n---\n", 1)
        self.assertIn("name: AI Efficiency Auditor", header.splitlines())
        self.assertIn(
            "tools: [read, search, edit, ask_user, appmod-preview-markdown]",
            header.splitlines(),
        )
        self.assertIn("agents: []", header.splitlines())
        self.assertIn("user-invocable: true", header.splitlines())
        self.assertRegex(header, r"(?m)^description: \".+\"$")
        expected = (ROOT / "evaluations" / "expected.json").read_text(encoding="utf-8")
        version = json.loads(expected)["methodology_version"]
        self.assertIn(f"Audit methodology version: {version}.", body)

    def test_executive_summary_contract_is_declared(self) -> None:
        agent = (ROOT / ".github" / "agents" / "ai-efficiency-auditor.agent.md").read_text(
            encoding="utf-8"
        )
        agent = " ".join(agent.split())
        for requirement in (
            "at most 60 lines and 600 words",
            "Priority | Weak area | Code location | Recommended improvement | Expected benefit | Evidence",
            "do not replace the detailed six-section report",
            "without conducting a new audit",
            "do not add overlapping savings",
            'use "Executive Summary" in the title',
            "reports/<application>-audit-executive-summary.md",
            "never overwrite it",
            "must be a new `.md` file",
            "Never write in source, configuration, trace, or agent/skill discovery directories",
            "Check both length limits before saving",
            "Verify the saved file using a read tool",
            "If read-back fails",
            "Open the Executive Summary in Markdown preview?",
            "Only an explicit Yes authorizes",
            "Ask again for each newly created report",
            "file was not saved",
            "preview consent was not obtained",
            "Markdown: Open Preview",
            "Report permission, save, read-back, and preview errors explicitly",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, agent)

    def test_code_location_contract_is_declared(self) -> None:
        agent = (ROOT / ".github" / "agents" / "ai-efficiency-auditor.agent.md").read_text(
            encoding="utf-8"
        )
        agent = " ".join(agent.split())
        for requirement in (
            "smallest verified file-and-line range",
            "include each relevant location",
            "Cite repeated-call statements separately from return statements",
            "Keep verified file-and-line notation visible",
            "not only in link targets or reference definitions",
            "show each affected path and range directly alongside its symbol",
            "tie the recommended improvement to it",
            "omit secrets or sensitive values",
            "Do not copy code into the Executive Summary",
            "A trace record alone is not a verified code location",
            "Code location not verified",
            "From supplied report; not reverified",
            "Not provided in supplied report",
            "without inspecting the codebase or guessing paths, symbols, or line numbers",
            "Include both sites for redundancy spanning multiple locations",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, agent)

    def test_detailed_report_persistence_contract_is_declared(self) -> None:
        agent = (ROOT / ".github" / "agents" / "ai-efficiency-auditor.agent.md").read_text(
            encoding="utf-8"
        )
        agent = " ".join(agent.split())
        for requirement in (
            "reports/<application>-audit-detailed-report.md",
            "Save the detailed report first",
            "all six required sections and their evidence citations",
            "limits apply only to the Executive Summary, not the detailed report",
            "Provide clickable links to both verified saved reports",
            "do not generate or copy a new detailed audit",
            "identifying which report failed",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, agent)

    def test_reusable_prompts_save_both_reports(self) -> None:
        for name in ("audit-knowledge-search", "audit-agent-retries"):
            prompt = (ROOT / ".github" / "prompts" / f"{name}.prompt.md").read_text(
                encoding="utf-8"
            )
            for requirement in (
                'agent: "AI Efficiency Auditor"',
                "reports/<application>-audit-detailed-report.md",
                "reports/<application>-audit-executive-summary.md",
                "Never overwrite existing files",
                "Read both saved files back",
                "these limits do not apply to the detailed report",
                "Open the Executive Summary in Markdown preview?",
            ):
                with self.subTest(prompt=name, requirement=requirement):
                    self.assertIn(requirement, prompt)

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
