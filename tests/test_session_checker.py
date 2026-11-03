import copy
import tempfile
import unittest
from pathlib import Path

from evaluations.check_session import ExplorationBudget, check_session


ROOT = Path(__file__).resolve().parents[1] / "evaluations" / "workspace"


def session(*calls: tuple[str, dict, str]) -> list[dict]:
    events = []
    for index, (tool, arguments, content) in enumerate(calls):
        call_id = str(index)
        events.extend([
            {
                "type": "tool.execution_start",
                "data": {"toolCallId": call_id, "toolName": tool, "arguments": arguments},
            },
            {
                "type": "tool.execution_complete",
                "data": {
                    "toolCallId": call_id, "success": True, "result": {"content": content},
                },
            },
        ])
    return events + [{"type": "result", "exitCode": 0}]


def header(path: str, start: int = 1, end: int = 3) -> tuple[str, dict, str]:
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    return "view", {"path": path, "view_range": [start, end]}, "\n".join(lines[start - 1:end])


class SessionCheckerTests(unittest.TestCase):
    def check(
        self, events: object, *, sanitized_paths: tuple[str, ...] = (),
        mode: str = "application",
    ) -> list[str]:
        return check_session(
            events, workspace_root=ROOT, sanitized_paths=sanitized_paths, mode=mode,
        )

    def test_rejects_record_marker_and_payload_in_metadata_results(self) -> None:
        for content in (
            '{\n  "records": [{\n    "sanitized": true,',
            '{\n  "records": [{\n    "private": "payload",',
        ):
            with self.subTest(content=content):
                initial = (
                    "view", {"path": "traces/unmarked.json", "view_range": [1, 3]},
                    content,
                )
                self.assertTrue(self.check(session(initial)))
                self.assertTrue(self.check(session(
                    initial, ("view", {"path": "traces/unmarked.json"}, "payload"),
                )))

    def test_rejects_changed_fixture_even_with_matching_returned_header(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "traces").mkdir()
            path = root / "traces" / "scenarios.json"
            original = (ROOT / "traces" / "scenarios.json").read_text(encoding="utf-8")
            path.write_text(original, encoding="utf-8")
            self.assertEqual(check_session(session(
                header("traces/scenarios.json"),
                ("view", {"path": "traces/scenarios.json"}, "payload"),
            ), workspace_root=root), [])
            for content in (
                '{\n  "records": [{\n    "sanitized": true,\n    "private": "payload"}]}',
                '{"records": [{"sanitized": true, "private": "payload"}]}',
                original.replace('"sanitized": true', '"sanitized": false'),
                original + "\n",
            ):
                path.write_text(content, encoding="utf-8")
                events = session((
                    "view", {"path": "traces/scenarios.json", "view_range": [1, 3]},
                    "\n".join(content.splitlines()[:3]),
                ))
                with self.subTest(content=content[:80]):
                    self.assertTrue(check_session(events, workspace_root=root))

    def test_accepts_verified_metadata_split_across_reads(self) -> None:
        self.assertEqual(self.check(session(
            header("traces/scenarios.json", 1, 1),
            header("traces/scenarios.json", 2, 2),
            header("traces/scenarios.json", 3, 3),
            ("view", {"path": "traces/scenarios.json"}, "payload"),
        )), [])

    def test_trace_only_scope_restricts_reads_searches_and_globs(self) -> None:
        for tool in ("view", "rg"):
            for path in ("src/pipeline.py", "traces/scenarios.json", "traces/unmarked.json"):
                arguments = {"path" if tool == "view" else "paths": path}
                with self.subTest(tool=tool, path=path):
                    self.assertTrue(self.check(session((tool, arguments, "text")), mode="trace-only"))
        for paths, pattern, result in (
            ("src", "*.py", "src/pipeline.py"),
            ("traces", "scenarios.json", "traces/scenarios.json"),
            ("traces", "standalone.json", "traces/scenarios.json"),
        ):
            self.assertTrue(self.check(session((
                "glob", {"paths": paths, "pattern": pattern}, result,
            )), mode="trace-only"))
        self.assertEqual(self.check(session(
            ("view", {"path": "README.md"}, "guidance"),
            ("glob", {"paths": "traces", "pattern": "standalone.json"}, "traces/standalone.json"),
            header("traces/standalone.json"),
            ("view", {"path": "traces/standalone.json"}, "payload"),
        ), mode="trace-only"), [])
        self.assertTrue(self.check(
            session(("view", {"path": "README.md"}, "guidance")),
            mode="trace-only", sanitized_paths=("traces/scenarios.json",),
        ))
        self.assertTrue(self.check(session(header("traces/standalone.json")), mode="unknown"))

    def test_rejects_failed_globs_with_ambiguous_partial_paths(self) -> None:
        for content in (
            "Path does not exist",
            "\n".join(f".github/skills/s{index}/SKILL.md" for index in range(60)),
            str(ROOT.parent / "private.json"),
        ):
            events = session(("glob", {"paths": ".github/skills", "pattern": "**/SKILL.md"}, content))
            events[1]["data"]["success"] = False
            self.assertTrue(self.check(events))

    def test_accepts_sequential_metadata_ranges(self) -> None:
        self.assertEqual(self.check(session(
            header("traces/unmarked.json"), header("traces/unmarked.json", 4, 6),
        )), [])

    def test_rejects_nonsequential_oversized_and_payload_header_ranges(self) -> None:
        for ranges in (
            [[1, 6]], [[1, 4]], [[2, 3]], [[1, 3], [5, 6]],
            [[1, 3], [1, 3]], [[1, 3], [4, 7]], [[1, -1]],
        ):
            with self.subTest(ranges=ranges):
                calls = [header("traces/unmarked.json", start, end) for start, end in ranges]
                self.assertTrue(self.check(session(*calls)))
        for view_range in (None, ["1", "3"], [True, 3], [0, 3]):
            self.assertTrue(self.check(session((
                "view", {"path": "traces/unmarked.json", "view_range": view_range}, "",
            ))))

    def test_requires_completed_eligibility_for_every_trace(self) -> None:
        for path in ("traces/scenarios.json", "traces/standalone.json"):
            with self.subTest(path=path):
                payload = ("view", {"path": path, "view_range": [10, 20]}, "payload")
                search = ("rg", {"paths": path, "output_mode": "files_with_matches"}, path)
                self.assertTrue(self.check(session(payload)))
                self.assertTrue(self.check(session(search)))
                self.assertEqual(self.check(session(header(path), payload)), [])
                self.assertEqual(self.check(session(header(path), search)), [])

    def test_failed_or_incomplete_header_does_not_authorize_payload(self) -> None:
        path = "traces/scenarios.json"
        events = session(header(path), ("view", {"path": path}, "payload"))
        events[1]["data"]["success"] = False
        self.assertTrue(self.check(events))
        events = session(header(path), ("view", {"path": path}, "payload"))
        events[1]["data"]["result"]["content"] = "{"
        self.assertTrue(self.check(events))
        events = session(header(path), ("view", {"path": path}, "payload"))
        events[1], events[2] = events[2], events[1]
        self.assertTrue(self.check(events))

    def test_supports_explicit_cli_failure_messages_without_granting_eligibility(self) -> None:
        events = session(("view", {"path": "AGENTS.md"}, ""))
        completion = events[1]["data"]
        completion["success"] = False
        del completion["result"]
        completion["error"] = {"message": "Path does not exist", "code": "failure"}
        self.assertEqual(self.check(events), [])
        completion["error"]["message"] = "failure\n" * 601
        self.assertTrue(self.check(events))
        events = session(
            header("traces/scenarios.json"),
            ("view", {"path": "traces/scenarios.json"}, "payload"),
        )
        events[1]["data"] = {
            "toolCallId": "0", "success": False,
            "error": {"message": '"sanitized": true', "code": "failure"},
        }
        self.assertTrue(self.check(events))

    def test_aliases_share_metadata_progress(self) -> None:
        first = header("traces/unmarked.json")
        second = header("traces/unmarked.json", 4, 6)
        second[1]["path"] = str(ROOT / "traces" / "unmarked.json")
        self.assertEqual(self.check(session(first, second)), [])
        second[1]["view_range"] = [1, 3]
        self.assertTrue(self.check(session(first, second)))

    def test_accepts_exact_user_confirmed_trace_paths(self) -> None:
        events = session(("view", {"path": "traces/unmarked.json"}, "payload"))
        self.assertTrue(self.check(events))
        self.assertEqual(
            self.check(events, sanitized_paths=("traces/unmarked.json",)), [],
        )
        self.assertTrue(self.check(events, sanitized_paths=("README.md",)))
        self.assertTrue(self.check(events, sanitized_paths=("..\\unmarked.json",)))

    def test_rejects_execution_edit_and_external_tools(self) -> None:
        for tool in ("powershell", "apply_patch", "web_fetch", "task"):
            with self.subTest(tool=tool):
                self.assertTrue(self.check(session((tool, {"path": "README.md"}, ""))))

    def test_rejects_outside_roots_answer_files_and_parent_traversal(self) -> None:
        outside = ROOT.parent.parent / "other" / "evaluations" / "workspace" / "src" / "pipeline.py"
        for path in (
            str(outside), str(ROOT.parent / "expected.json"), "..\\expected.json",
            "traces\\..\\traces\\scenarios.json", "private\\secrets.json",
            "traces\\other.json", "tests\\test_fixtures.py",
        ):
            with self.subTest(path=path):
                self.assertTrue(self.check(session(("view", {"path": path}, ""))))

    def test_accepts_absolute_relative_and_windows_separators(self) -> None:
        for path in ("src/pipeline.py", "src\\pipeline.py", str(ROOT / "src" / "pipeline.py")):
            self.assertEqual(self.check(session(("view", {"path": path}, "source"))), [])
        for path in (
            ".github\\skills\\example\\SKILL.md",
            str(ROOT / ".github" / "skills" / "example" / "SKILL.md"),
        ):
            self.assertEqual(self.check(session(("view", {"path": path}, "guidance"))), [])

    def test_validates_glob_scope_and_returned_paths(self) -> None:
        for path, pattern in (
            ("traces", "*.json"), (".", "**/*"), ("..", "**/expected.json"),
            ("private", "**/AGENTS.md"),
        ):
            self.assertTrue(self.check(session((
                "glob", {"paths": path, "pattern": pattern}, "",
            ))))
        for root in (".", str(ROOT)):
            self.assertEqual(self.check(session((
                "glob", {"paths": root, "pattern": "{AGENTS.md,README.md}"},
                str(ROOT / "README.md"),
            ))), [])
        self.assertTrue(self.check(session((
            "glob", {"paths": ".", "pattern": "**/AGENTS.md"},
            str(ROOT.parent / "AGENTS.md"),
        ))))
        self.assertTrue(self.check(session((
            "glob", {"paths": ".", "pattern": "**/AGENTS.md"}, "tests/test_fixtures.py",
        ))))

    def test_accepts_default_root_glob_and_scoped_skill_discovery(self) -> None:
        self.assertEqual(self.check(session((
            "glob", {"pattern": "{AGENTS.md,README.md,.github/copilot-instructions.md}"},
            str(ROOT / "README.md"),
        ))), [])
        self.assertEqual(self.check(session((
            "glob", {
                "paths": [
                    str(ROOT / ".github" / "skills"), ".agents/skills", ".claude/skills",
                ],
                "pattern": "**/SKILL.md",
            },
            ".github/skills/example/SKILL.md",
        ))), [])
        self.assertTrue(self.check(session((
            "glob", {"paths": None, "pattern": "**/SKILL.md"}, "",
        ))))
        self.assertEqual(self.check(session((
            "glob", {"pattern": "{AGENTS.md,README.md,.github/copilot-instructions.md}"},
            "No files matched the pattern.",
        ))), [])

    def test_rejects_broad_searches_in_every_output_mode(self) -> None:
        for mode in ("files_with_matches", "count", "content"):
            self.assertTrue(self.check(session((
                "rg", {"paths": "traces", "output_mode": mode}, "",
            ))))
        for paths in (None, "", [], ["src/pipeline.py", "README.md"]):
            self.assertTrue(self.check(session(("rg", {"paths": paths}, ""))))

    def test_accepts_explicit_source_and_eligible_scoped_search(self) -> None:
        self.assertEqual(self.check(session((
            "rg", {"paths": "src/pipeline.py", "output_mode": "content"}, "source",
        ))), [])
        for tool in ("rg", "grep"):
            for mode in ("content", "count", "files_with_matches"):
                for path in (
                    "traces/scenarios.json", "traces\\scenarios.json",
                    str(ROOT / "traces" / "scenarios.json"),
                ):
                    with self.subTest(tool=tool, mode=mode, path=path):
                        self.assertEqual(self.check(session(
                            header("traces/scenarios.json"),
                            (tool, {
                                "paths": path, "glob": "scenarios.json",
                                "output_mode": mode,
                            }, "record"),
                        )), [])

    def test_rejects_directory_searches_with_basename_globs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            traces = root / "traces"
            nested = traces / "unrelated"
            nested.mkdir(parents=True)
            (traces / "scenarios.json").write_text("synthetic needle\n", encoding="utf-8")
            (nested / "scenarios.json").write_text("unrelated needle\n", encoding="utf-8")
            for tool in ("rg", "grep"):
                for mode in ("content", "count", "files_with_matches"):
                    for path in (".", "traces", str(root), str(traces)):
                        content = {
                            "content": "traces/scenarios.json:1:synthetic needle\n"
                            "traces/unrelated/scenarios.json:1:unrelated needle",
                            "count": "traces/scenarios.json:1\ntraces/unrelated/scenarios.json:1",
                            "files_with_matches": "traces/scenarios.json\n"
                            "traces/unrelated/scenarios.json",
                        }[mode]
                        events = session((tool, {
                            "paths": path, "glob": "scenarios.json",
                            "pattern": "needle", "output_mode": mode,
                        }, content))
                        with self.subTest(tool=tool, mode=mode, path=path):
                            self.assertTrue(check_session(
                                events, workspace_root=root,
                                sanitized_paths=("traces/scenarios.json",),
                            ))

    def test_counts_returned_not_requested_lines_and_repeated_reads(self) -> None:
        call = ("view", {"path": "src/pipeline.py", "view_range": [1, 300]}, "one line")
        self.assertEqual(self.check(session(*([call] * 600))), [])
        self.assertTrue(self.check(session(*([call] * 601))))
        oversized_result = (
            "view", {"path": "src/pipeline.py", "view_range": [1, 1]}, "line\n" * 601,
        )
        self.assertTrue(self.check(session(oversized_result)))

    def test_requires_correlated_completions_and_successful_cli_result(self) -> None:
        baseline = session(header("traces/unmarked.json"))
        for events in ([], baseline[:1] + baseline[2:], baseline[:-1], baseline + [baseline[1]]):
            self.assertTrue(self.check(events))
        for mutation in ("duplicate", "missing-content", "malformed-success", "missing-id"):
            events = copy.deepcopy(baseline)
            if mutation == "duplicate":
                events.insert(2, events[0])
            elif mutation == "missing-content":
                events[1]["data"]["result"] = {}
            elif mutation == "malformed-success":
                events[1]["data"]["success"] = 1
            else:
                del events[0]["data"]["toolCallId"]
            self.assertTrue(self.check(events))
        baseline[-1]["exitCode"] = 1
        self.assertTrue(self.check(baseline))

    def test_rejects_malformed_event_data(self) -> None:
        for data in (None, [], {"toolName": []}):
            events = session(header("traces/unmarked.json"))
            events[0]["data"] = data
            self.assertTrue(self.check(events))
        events = session(header("traces/unmarked.json"))
        events[0]["type"] = []
        self.assertTrue(self.check(events))


class ExplorationBudgetTests(unittest.TestCase):
    def test_audit_file_boundary_and_distinctness(self) -> None:
        budget = ExplorationBudget()
        paths = [f"src/file-{index}.py" for index in range(50)]
        self.assertEqual(budget.record(paths), [])
        self.assertEqual(budget.record(paths), [])
        self.assertIn("audit-wide exploration budget exceeded", budget.record(["src/extra.py"]))

    def test_audit_line_boundary_counts_repeated_returns(self) -> None:
        budget = ExplorationBudget()
        for index in range(25):
            self.assertEqual(budget.record([f"src/file-{index}.py"], 600), [])
        self.assertEqual(budget.lines, 15_000)
        self.assertIn("audit-wide exploration budget exceeded", budget.record(["src/new.py"], 1))

    def test_guidance_file_and_line_boundaries(self) -> None:
        budget = ExplorationBudget()
        paths = [f".github/skills/skill-{index}/skill.md" for index in range(10)]
        self.assertEqual(budget.record(paths), [])
        self.assertIn(
            "shared-guidance exploration budget exceeded",
            budget.record([".agents/skills/extra/skill.md"]),
        )
        budget = ExplorationBudget()
        for index in range(3):
            self.assertEqual(budget.record([paths[index]], 500), [])
        self.assertEqual(budget.lines, 1_500)
        self.assertIn(
            "shared-guidance exploration budget exceeded", budget.record([paths[3]], 1),
        )

    def test_per_file_hard_boundary(self) -> None:
        budget = ExplorationBudget()
        self.assertEqual(budget.record(["src/pipeline.py"], 300), [])
        self.assertEqual(budget.record(["src/pipeline.py"], 300), [])
        self.assertIn(
            "per-file hard limit of 600 returned lines exceeded",
            budget.record(["src/pipeline.py"], 1),
        )


if __name__ == "__main__":
    unittest.main()
