import copy
import json
import unittest

from evaluations.check_report import ROOT
from evaluations.check_trace_only import check_trace_only


def reference_report() -> dict:
    expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
    return {
        "mode": "trace-only",
        "methodology_version": expected["methodology_version"],
        "metrics": {
            "logical_calls": 2,
            "execution_attempts": 2,
            "downstream_requests": 2,
            "confirmed_avoidable_calls": None,
        },
        "finding_categories": [],
        "evidence": [
            {"path": "traces/standalone.json", "record_id": "standalone-1"},
            {"path": "traces/standalone.json", "record_id": "standalone-2"},
        ],
        "limitations": ["Source and optimization evidence are unavailable."],
        "limitation_categories": ["missing-source", "unverified-optimization"],
    }


class TraceOnlyCheckerTests(unittest.TestCase):
    def test_reference_and_fixture_counts(self) -> None:
        self.assertEqual(check_trace_only(reference_report()), [])
        trace = json.loads(
            (ROOT / "workspace" / "traces" / "standalone.json").read_text(encoding="utf-8")
        )
        self.assertIs(trace["metadata"]["sanitized"], True)
        records = trace["records"]
        metrics = reference_report()["metrics"]
        self.assertEqual(len({record["logical_call_id"] for record in records}),
                         metrics["logical_calls"])
        self.assertEqual(len({record["execution_span_id"] for record in records}),
                         metrics["execution_attempts"])
        self.assertEqual(sum(record["downstream_requests"] for record in records),
                         metrics["downstream_requests"])

    def test_rejects_bad_counts_findings_and_missing_evidence(self) -> None:
        for change in ("count", "avoidable", "finding", "evidence", "limitation", "mode"):
            with self.subTest(change=change):
                report = copy.deepcopy(reference_report())
                if change == "count":
                    report["metrics"]["execution_attempts"] = 1
                elif change == "avoidable":
                    report["metrics"]["confirmed_avoidable_calls"] = 0
                elif change == "finding":
                    report["finding_categories"] = ["duplicate-read"]
                elif change == "evidence":
                    report["evidence"].pop()
                elif change == "limitation":
                    report["limitation_categories"] = ["missing-source"]
                else:
                    report["mode"] = "application"
                self.assertTrue(check_trace_only(report))

    def test_accepts_windows_relative_paths(self) -> None:
        report = reference_report()
        for citation in report["evidence"]:
            citation["path"] = "traces\\standalone.json"
        self.assertEqual(check_trace_only(report), [])

    def test_requires_exact_limitation_categories_without_duplicates(self) -> None:
        for categories in (
            ["missing-source", "unverified-optimization", "missing-pricing"],
            ["missing-source", "unverified-optimization", "missing-source"],
        ):
            report = reference_report()
            report["limitation_categories"] = categories
            self.assertTrue(check_trace_only(report))
        report = reference_report()
        report["limitation_categories"].reverse()
        self.assertEqual(check_trace_only(report), [])

    def test_rejects_malformed_reports(self) -> None:
        malformed = reference_report()
        malformed["evidence"][0]["record_id"] = []
        for report in (None, [], {}, {"metrics": []}, malformed):
            with self.subTest(report=report):
                self.assertTrue(check_trace_only(report))


if __name__ == "__main__":
    unittest.main()
