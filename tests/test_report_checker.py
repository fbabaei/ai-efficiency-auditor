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
                "cost_currency": case.get("cost_currency"),
                "finding_categories": case["finding_categories"].copy(),
                "evidence": [
                    {"path": "traces/scenarios.json", "record_id": record_id}
                    for record_id in case["required_evidence"]
                ],
                "limitations": ["Fixture limitation requires manual semantic review."]
                if case["limitation_required"]
                else [],
                "limitation_categories": expected["required_limitations"].get(case["id"], []),
                "source_evidence": [
                    {"path": "src/pipeline.py", "line": line}
                    for line in expected["required_source_lines"].get(case["id"], [])
                ],
            }
            for case in expected["cases"]
        ],
    }


class ReportCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = reference_report()

    def test_accepts_reference_shape(self) -> None:
        self.assertEqual(check_report(self.report), [])

    def test_requires_currency_field_even_when_unknown(self) -> None:
        for case in self.report["cases"]:
            report = copy.deepcopy(self.report)
            target = next(item for item in report["cases"] if item["id"] == case["id"])
            del target["cost_currency"]
            with self.subTest(case=case["id"]):
                self.assertTrue(check_report(report))

    def test_accepts_windows_relative_evidence_paths(self) -> None:
        for case in self.report["cases"]:
            for citation in case["evidence"] + case["source_evidence"]:
                citation["path"] = citation["path"].replace("/", "\\")
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

    def test_rejects_float_lookalikes_for_integer_metrics(self) -> None:
        for case_id, field in [
            ("duplicate-read", "logical_calls"),
            ("model-retries", "model_attempts"),
            ("model-incomplete-correlation", "model_attempts_lower_bound"),
        ]:
            with self.subTest(case=case_id, field=field):
                report = copy.deepcopy(self.report)
                case = next(case for case in report["cases"] if case["id"] == case_id)
                case["metrics"][field] = float(case["metrics"][field])
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

    def test_requires_specific_limitation_categories(self) -> None:
        for case_id, categories in [
            ("model-retries", ["missing-pricing"]),
            ("model-incomplete-correlation", ["missing-pricing", "incomplete-usage"]),
            ("unmarked-artifact", ["missing-correlation"]),
            ("model-efficiency-hypotheses", ["missing-pricing"]),
            ("duplicate-model", ["unrelated"]),
            ("duplicate-model", None),
            ("priced-model-retries", ["uncertain-retry", "missing-pricing"]),
            ("priced-model-retries", ["uncertain-retry", "incomplete-usage"]),
            ("duplicate-read", ["missing-correlation"]),
            ("duplicate-model", ["missing-pricing", "missing-pricing"]),
        ]:
            with self.subTest(case=case_id, categories=categories):
                report = copy.deepcopy(self.report)
                case = next(case for case in report["cases"] if case["id"] == case_id)
                case["limitation_categories"] = categories
                self.assertTrue(check_report(report))

    def test_accepts_limitation_categories_in_any_order(self) -> None:
        for case in self.report["cases"]:
            case["limitation_categories"] = list(reversed(case["limitation_categories"]))
        self.assertEqual(check_report(self.report), [])

    def test_rejects_bad_model_counts_usage_and_invented_cost(self) -> None:
        for case_id, field, wrong in [
            ("duplicate-model", "model_attempts", 1),
            ("duplicate-model", "input_tokens", 300),
            ("duplicate-model", "confirmed_avoidable_model_calls", 0),
            ("model-required-sampling", "elapsed_ms", 60),
            ("model-retries", "model_logical_calls", 2),
            ("model-retries", "input_tokens", 100),
            ("model-retries", "confirmed_avoidable_model_calls", 1),
            ("model-exported-duplicates", "model_attempts", 2),
            ("model-exported-duplicates", "output_tokens", 25),
            ("model-exported-duplicates", "input_tokens", 140),
            ("model-unused-routing", "confirmed_avoidable_model_calls", True),
            ("model-efficiency-hypotheses", "confirmed_avoidable_model_calls", 0),
            ("model-efficiency-hypotheses", "model_cost", 0.01),
            ("model-incomplete-correlation", "model_attempts", 1),
            ("model-incomplete-correlation", "model_attempts_lower_bound", 0),
            ("source-case-a", "confirmed_avoidable_model_calls", 0),
            ("source-case-b", "confirmed_avoidable_model_calls", 1),
        ]:
            with self.subTest(case=case_id, field=field):
                report = copy.deepcopy(self.report)
                case = next(case for case in report["cases"] if case["id"] == case_id)
                case["metrics"][field] = wrong
                self.assertTrue(check_report(report))

    def test_requires_priced_case_currency_and_correct_cost(self) -> None:
        case = next(
            case for case in self.report["cases"] if case["id"] == "priced-model-retries"
        )
        self.assertEqual(case["cost_currency"], "USD")
        for currency, cost in [(None, 0.00305), ("EUR", 0.00305), ("USD", 0.00306)]:
            with self.subTest(currency=currency, cost=cost):
                report = copy.deepcopy(self.report)
                case = next(
                    case for case in report["cases"] if case["id"] == "priced-model-retries"
                )
                case["cost_currency"] = currency
                case["metrics"]["model_cost"] = cost
                self.assertTrue(check_report(report))
        for case_id in ("duplicate-read", "duplicate-model"):
            with self.subTest(case=case_id):
                report = copy.deepcopy(self.report)
                case = next(case for case in report["cases"] if case["id"] == case_id)
                case["cost_currency"] = "USD"
                self.assertTrue(check_report(report))

    def test_rejects_model_false_positives_and_missing_findings(self) -> None:
        for case_id, findings in [
            ("duplicate-model", []),
            ("model-unused-routing", []),
            ("model-different-identities", ["duplicate-model"]),
            ("model-changed-context", ["duplicate-model"]),
            ("model-required-sampling", ["duplicate-model"]),
            ("model-retries", ["unnecessary-model-retry"]),
            ("model-efficiency-hypotheses", ["smaller-model", "token-waste"]),
            ("source-case-a", []),
            ("source-case-b", ["duplicate-model"]),
        ]:
            with self.subTest(case=case_id):
                report = copy.deepcopy(self.report)
                case = next(case for case in report["cases"] if case["id"] == case_id)
                case["finding_categories"] = findings
                self.assertTrue(check_report(report))

    def test_model_evidence_and_unknown_cost_requirements(self) -> None:
        for change in ("missing", "tool-citation", "cross-model-citation", "no-limitation"):
            with self.subTest(change=change):
                report = copy.deepcopy(self.report)
                case = next(
                    case for case in report["cases"] if case["id"] == "duplicate-model"
                )
                if change == "missing":
                    case["evidence"] = []
                elif change == "no-limitation":
                    case["limitations"] = []
                else:
                    record_id = "dup-1" if change == "tool-citation" else "model-identity-1"
                    case["evidence"] = [
                        {"path": "traces/scenarios.json", "record_id": record_id}
                    ]
                self.assertTrue(check_report(report))

    def test_requires_source_anchors_for_source_cases(self) -> None:
        for citations in (
            [],
            [{"path": "src/pipeline.py", "line": 44}],
            [{"path": "other.py", "line": 37}, {"path": "src/pipeline.py", "line": 44}],
            [{"path": "src/pipeline.py", "line": True}],
        ):
            with self.subTest(citations=citations):
                report = copy.deepcopy(self.report)
                case = next(case for case in report["cases"] if case["id"] == "source-case-a")
                case["source_evidence"] = citations
                self.assertTrue(check_report(report))

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
