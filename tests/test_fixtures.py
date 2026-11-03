import json
import unittest

from evaluations.check_report import ROOT
from evaluations.workspace.src.pipeline import (
    deterministic_route_fixture,
    duplicate_model_fixture,
    source_case_a,
    source_case_b,
)


class FixtureTests(unittest.TestCase):
    def test_complete_trace_counts_are_independently_consistent(self) -> None:
        trace = json.loads(
            (ROOT / "workspace" / "traces" / "scenarios.json").read_text(encoding="utf-8")
        )
        self.assertIs(trace["metadata"]["sanitized"], True)
        expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
        targets = {case["id"]: case["metrics"] for case in expected["cases"]}
        self.assertEqual(len(targets), 20)
        for case in trace["scenarios"]:
            with self.subTest(case=case["id"]):
                if "model_attempts" in targets[case["id"]]:
                    continue
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

    def test_model_counts_and_usage_are_independently_consistent(self) -> None:
        trace = json.loads(
            (ROOT / "workspace" / "traces" / "scenarios.json").read_text(encoding="utf-8")
        )
        expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
        targets = {case["id"]: case["metrics"] for case in expected["cases"]}
        expected_cases = {case["id"]: case for case in expected["cases"]}
        model_cases = [
            case for case in trace["scenarios"]
            if "model_attempts" in targets[case["id"]]
        ]
        self.assertEqual(len(model_cases), 12)
        for case in model_cases:
            with self.subTest(case=case["id"]):
                target = targets[case["id"]]
                if case["id"] == "model-incomplete-correlation":
                    self.assertEqual(case["records"][0]["kind"], "model_start")
                    self.assertNotIn("end_ms", case["records"][0])
                    self.assertEqual(target["model_attempts_lower_bound"], 1)
                    for field in ("model_logical_calls", "model_attempts", "input_tokens"):
                        self.assertIsNone(target[field])
                    continue
                executions = {}
                for record in case["records"]:
                    if record["kind"] != "model_execution":
                        continue
                    span_id = record["execution_span_id"]
                    if span_id in executions:
                        self.assertEqual(executions[span_id], record)
                    executions[span_id] = record
                records = list(executions.values())
                metrics = {
                    "model_logical_calls": len({
                        record["logical_model_call_id"] for record in records
                    }),
                    "model_attempts": len(records),
                    "elapsed_ms": max(record["end_ms"] for record in records)
                    - min(record["start_ms"] for record in records),
                    "summed_model_ms": sum(
                        record["end_ms"] - record["start_ms"] for record in records
                    ),
                    "model_cost": None,
                }
                for field in (
                    "input_tokens", "output_tokens", "cached_input_tokens", "reasoning_tokens"
                ):
                    values = [record[field] for record in records]
                    metrics[field] = (
                        None if any(value is None for value in values) else sum(values)
                    )
                for record in records:
                    if record["input_tokens"] is not None:
                        self.assertLessEqual(
                            record["cached_input_tokens"], record["input_tokens"]
                        )
                    if record["output_tokens"] is not None:
                        self.assertLessEqual(record["reasoning_tokens"], record["output_tokens"])
                pricing = case.get("pricing")
                if pricing:
                    self.assertTrue(all(record["model"] == pricing["model"] for record in records))
                    self.assertTrue(
                        all(record["model_version"] == pricing["version"] for record in records)
                    )
                    uncached_input_tokens = (
                        metrics["input_tokens"] - metrics["cached_input_tokens"]
                    )
                    metrics["model_cost"] = (
                        uncached_input_tokens * pricing["input_per_million_tokens"]
                        + metrics["cached_input_tokens"]
                        * pricing["cached_input_per_million_tokens"]
                        + metrics["output_tokens"] * pricing["output_per_million_tokens"]
                    ) / 1_000_000
                    self.assertEqual(
                        expected_cases[case["id"]]["cost_currency"],
                        pricing["currency"],
                    )
                for key, value in metrics.items():
                    self.assertEqual(target[key], value)

    def test_model_fixture_source_matches_its_contract(self) -> None:
        class RecordingModel:
            def __init__(self) -> None:
                self.calls: list[tuple[str, str]] = []

            def generate(self, context_id: str, *, identity: str) -> str:
                self.calls.append((context_id, identity))
                return "ignored-by-router"

        model = RecordingModel()
        self.assertEqual(
            duplicate_model_fixture(model, "context-v1", "tenant-a"),
            ("ignored-by-router", "ignored-by-router"),
        )
        self.assertEqual(model.calls, [("context-v1", "tenant-a")] * 2)
        for route in ("search", "answer"):
            self.assertEqual(deterministic_route_fixture(model, route, "tenant-a"), route)
        self.assertEqual(model.calls[-2:], [("search", "tenant-a"), ("answer", "tenant-a")])
        before = len(model.calls)
        with self.assertRaises(ValueError):
            deterministic_route_fixture(model, "unsupported", "tenant-a")
        self.assertEqual(len(model.calls), before)

    def test_source_cases_expose_output_consumption(self) -> None:
        class ChangingModel:
            def __init__(self) -> None:
                self.calls = 0

            def generate(self, context_id: str, *, identity: str) -> str:
                self.calls += 1
                return str(self.calls)

        model = ChangingModel()
        self.assertEqual(source_case_a(model, "context", "tenant"), "1")
        self.assertEqual(model.calls, 2)
        self.assertEqual(source_case_b(model, "context", "tenant"), ("3", "4"))
        self.assertEqual(model.calls, 4)

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
