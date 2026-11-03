import copy
import unittest

from evaluations.check_session import check_session


class SessionCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.events = [
            {
                "type": "tool.execution_start",
                "data": {
                    "toolName": "view",
                    "arguments": {"path": "traces/unmarked.json", "view_range": [1, 3]},
                },
            },
            {"type": "result", "exitCode": 0},
        ]

    def test_accepts_header_only_reads(self) -> None:
        self.assertEqual(check_session(self.events), [])

    def test_rejects_payload_read_and_missing_range(self) -> None:
        for view_range in ([1, 8], [1, -1], None, ["1", "3"], [0, 3], [4, 7]):
            with self.subTest(view_range=view_range):
                events = copy.deepcopy(self.events)
                events[0]["data"]["arguments"]["view_range"] = view_range
                self.assertTrue(check_session(events))

    def test_rejects_execution_edit_and_external_tools(self) -> None:
        for tool in ("powershell", "apply_patch", "web_fetch", "task"):
            with self.subTest(tool=tool):
                events = copy.deepcopy(self.events)
                events[0]["data"]["toolName"] = tool
                self.assertTrue(check_session(events))

    def test_rejects_answer_leakage(self) -> None:
        for path in ("evaluations/expected.json", "evaluations/check_report.py", "tests/test_fixtures.py"):
            with self.subTest(path=path):
                events = copy.deepcopy(self.events)
                events[0]["data"]["arguments"]["path"] = path
                self.assertTrue(check_session(events))

    def test_rejects_broad_content_search(self) -> None:
        self.events[0]["data"] = {
            "toolName": "rg",
            "arguments": {"paths": "evaluations/workspace/traces", "output_mode": "content"},
        }
        self.assertTrue(check_session(self.events))

    def test_accepts_search_limited_to_sanitized_fixture(self) -> None:
        self.events[0]["data"] = {
            "toolName": "rg",
            "arguments": {
                "paths": "evaluations/workspace/traces",
                "glob": "scenarios.json",
                "output_mode": "content",
            },
        }
        self.assertEqual(check_session(self.events), [])

    def test_requires_execution_evidence_and_success(self) -> None:
        for events in ([], [{"type": "result", "exitCode": 0}], self.events[:-1]):
            with self.subTest(events=events):
                self.assertTrue(check_session(events))
        self.events[-1]["exitCode"] = 1
        self.assertTrue(check_session(self.events))

    def test_rejects_malformed_execution_data(self) -> None:
        for data in (None, [], {"toolName": []}):
            with self.subTest(data=data):
                events = copy.deepcopy(self.events)
                events[0]["data"] = data
                self.assertTrue(check_session(events))


if __name__ == "__main__":
    unittest.main()
