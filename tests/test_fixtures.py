import json
import unittest

from evaluations.check_report import ROOT


class FixtureTests(unittest.TestCase):
    def test_complete_trace_counts_are_independently_consistent(self) -> None:
        trace = json.loads(
            (ROOT / "workspace" / "traces" / "scenarios.json").read_text(encoding="utf-8")
        )
        self.assertIs(trace["metadata"]["sanitized"], True)
        expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
        targets = {case["id"]: case["metrics"] for case in expected["cases"]}
        self.assertEqual(len(targets), 8)
        for case in trace["scenarios"]:
            with self.subTest(case=case["id"]):
                if case["id"] == "incomplete-correlation":
                    self.assertEqual(case["records"][0]["kind"], "start")
                    self.assertNotIn("end_ms", case["records"][0])
                    self.assertEqual(targets[case["id"]]["attempts_lower_bound"], 1)
                    continue
                executions = {}
                for record in case["records"]:
                    if record["kind"] != "execution":
                        continue
                    span_id = record["execution_span_id"]
                    if span_id in executions:
                        self.assertEqual(executions[span_id], record)
                    executions[span_id] = record
                records = list(executions.values())
                metrics = {
                    "logical_calls": len({record["logical_call_id"] for record in records}),
                    "execution_attempts": len(records),
                    "downstream_requests": sum(record["downstream_requests"] for record in records),
                    "elapsed_ms": max(record["end_ms"] for record in records)
                    - min(record["start_ms"] for record in records),
                    "summed_tool_ms": sum(
                        record["end_ms"] - record["start_ms"] for record in records
                    ),
                }
                for key, value in metrics.items():
                    self.assertEqual(targets[case["id"]][key], value)

    def test_unmarked_negative_fixture_remains_ineligible(self) -> None:
        data = json.loads(
            (ROOT / "workspace" / "traces" / "unmarked.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("sanitized", data["metadata"])

    def test_expected_evidence_exists_in_its_scenario(self) -> None:
        trace = json.loads(
            (ROOT / "workspace" / "traces" / "scenarios.json").read_text(encoding="utf-8")
        )
        expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
        records = {
            case["id"]: {record["record_id"] for record in case["records"]}
            for case in trace["scenarios"]
        }
        for case in expected["cases"]:
            with self.subTest(case=case["id"]):
                self.assertTrue(set(case["required_evidence"]).issubset(records.get(case["id"], set())))


if __name__ == "__main__":
    unittest.main()
