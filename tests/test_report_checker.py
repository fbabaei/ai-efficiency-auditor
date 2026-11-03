import copy
import json
import unittest

from evaluations.check_report import ROOT, check_report


def reference_report() -> dict:
    expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
    return {
        "methodology_version": expected["methodology_version"],
        "cases": [
            {
                "id": case["id"],
                "metrics": copy.deepcopy(case["metrics"]),
                "finding_categories": case["finding_categories"].copy(),
                "evidence": [
                    {"path": "traces/scenarios.json", "record_id": record_id}
                    for record_id in case["required_evidence"]
                ],
                "limitations": ["Fixture limitation requires manual semantic review."]
                if case["limitation_required"]
                else [],
            }
            for case in expected["cases"]
        ],
    }


class ReportCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = reference_report()

    def test_accepts_reference_shape(self) -> None:
        self.assertEqual(check_report(self.report), [])

    def test_rejects_bad_counts_and_unknowns(self) -> None:
        for index, field, wrong in [
            (0, "execution_attempts", 1),
            (3, "downstream_requests", 4),
            (3, "confirmed_avoidable_calls", 3),
            (4, "execution_attempts", 3),
            (5, "elapsed_ms", 200),
            (6, "logical_calls", 0),
            (6, "attempts_lower_bound", 0),
            (7, "execution_attempts", 1),
            (0, "confirmed_avoidable_calls", True),
        ]:
            with self.subTest(index=index, field=field):
                report = copy.deepcopy(self.report)
                report["cases"][index]["metrics"][field] = wrong
                self.assertTrue(check_report(report))

    def test_rejects_missing_and_false_positive_findings(self) -> None:
        for index, findings in [(0, []), (1, ["duplicate-read"]), (2, ["duplicate-read"])]:
            with self.subTest(index=index):
                report = copy.deepcopy(self.report)
                report["cases"][index]["finding_categories"] = findings
                self.assertTrue(check_report(report))

    def test_rejects_missing_fabricated_and_cross_scenario_citations(self) -> None:
        for evidence in [
            [],
            [{"path": "traces/scenarios.json", "record_id": "invented"}],
            [{"path": "traces/scenarios.json", "record_id": "identity-1"}],
            [{"path": "traces/unmarked.json", "record_id": "unmarked-1"}],
        ]:
            with self.subTest(evidence=evidence):
                report = copy.deepcopy(self.report)
                report["cases"][0]["evidence"] = evidence
                self.assertTrue(check_report(report))

    def test_rejects_ineligible_evidence_even_without_counts(self) -> None:
        self.report["cases"][7]["evidence"] = [
            {"path": "traces/unmarked.json", "record_id": "unmarked-1"}
        ]
        self.assertTrue(check_report(self.report))

    def test_requires_limitations_for_unknowns(self) -> None:
        self.report["cases"][6]["limitations"] = []
        self.assertTrue(check_report(self.report))

    def test_rejects_missing_duplicate_and_extra_scenarios(self) -> None:
        for change in ("missing", "duplicate", "extra"):
            with self.subTest(change=change):
                report = copy.deepcopy(self.report)
                if change == "missing":
                    report["cases"].pop()
                else:
                    case = copy.deepcopy(report["cases"][0])
                    if change == "extra":
                        case["id"] = "extra"
                    report["cases"].append(case)
                self.assertTrue(check_report(report))

    def test_rejects_malformed_reports(self) -> None:
        for report in [None, [], {}, {"cases": "wrong"}, {"cases": [None]}]:
            with self.subTest(report=report):
                self.assertTrue(check_report(report))


if __name__ == "__main__":
    unittest.main()
