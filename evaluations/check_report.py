"""Check a structured synthetic audit report; never execute the audited project."""

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def check_report(report: object) -> list[str]:
    expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
    trace = json.loads(
        (ROOT / "workspace" / "traces" / "scenarios.json").read_text(encoding="utf-8")
    )
    records = {
        case["id"]: {record["record_id"] for record in case["records"]}
        for case in trace["scenarios"]
    }
    if not isinstance(report, dict):
        return ["report must be a JSON object"]
    errors = []
    if report.get("methodology_version") != expected["methodology_version"]:
        errors.append("methodology_version must match the candidate version")
    cases = report.get("cases")
    if not isinstance(cases, list):
        return errors + ["cases must be an array"]
    actual = {}
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            errors.append("each case must be an object with a string id")
            continue
        if case["id"] in actual:
            errors.append(f"duplicate case: {case['id']}")
        actual[case["id"]] = case
    expected_ids = {case["id"] for case in expected["cases"]}
    required_limitations = expected["required_limitations"]
    source_lines = (ROOT / "workspace" / "src" / "pipeline.py").read_text(
        encoding="utf-8"
    ).splitlines()
    allowed_limitations = {
        category
        for categories in required_limitations.values()
        for category in categories
    }
    if set(actual) != expected_ids:
        errors.append("case IDs must match all fixture scenarios exactly")
    for target in expected["cases"]:
        case_id = target["id"]
        if case_id not in actual:
            continue
        case = actual[case_id]
        metrics = case.get("metrics")
        if not isinstance(metrics, dict) or set(metrics) != set(target["metrics"]):
            errors.append(f"{case_id}: metric keys do not match the contract")
        else:
            for name, value in target["metrics"].items():
                observed = metrics[name]
                if value is None:
                    valid_type = observed is None
                elif type(value) is int:
                    valid_type = type(observed) is int
                else:
                    valid_type = type(observed) in (int, float)
                if observed != value or not valid_type:
                    errors.append(f"{case_id}: {name} expected {value!r}, got {observed!r}")
        if "cost_currency" not in case:
            errors.append(f"{case_id}: cost_currency field is required, even when null")
        elif case["cost_currency"] != target.get("cost_currency"):
            errors.append(
                f"{case_id}: cost_currency expected "
                f"{target.get('cost_currency')!r}, got {case.get('cost_currency')!r}"
            )
        findings = case.get("finding_categories")
        if not isinstance(findings, list) or findings != target["finding_categories"]:
            errors.append(f"{case_id}: missing finding or false-positive ranked finding")
        limitations = case.get("limitations")
        if not isinstance(limitations, list) or any(
            not isinstance(item, str) or not item.strip() for item in limitations
        ):
            errors.append(f"{case_id}: limitations must be an array of nonempty strings")
        elif target["limitation_required"] and not limitations:
            errors.append(f"{case_id}: an evidence limitation is required")
        categories = case.get("limitation_categories")
        if not isinstance(categories, list) or any(
            not isinstance(category, str) or category not in allowed_limitations
            for category in categories
        ):
            errors.append(f"{case_id}: invalid limitation categories")
        elif (
            set(required_limitations.get(case_id, [])) != set(categories)
            or len(categories) != len(set(categories))
        ):
            errors.append(f"{case_id}: limitation categories must match this scenario exactly")
        source_evidence = case.get("source_evidence")
        if not isinstance(source_evidence, list):
            errors.append(f"{case_id}: source_evidence must be an array")
        else:
            cited_lines = set()
            for citation in source_evidence:
                if (
                    not isinstance(citation, dict)
                    or not isinstance(citation.get("path"), str)
                    or citation["path"].replace("\\", "/") != "src/pipeline.py"
                    or type(citation.get("line")) is not int
                    or not 1 <= citation["line"] <= len(source_lines)
                ):
                    errors.append(f"{case_id}: invalid source citation")
                else:
                    cited_lines.add(citation["line"])
            if not set(expected["required_source_lines"].get(case_id, [])).issubset(cited_lines):
                errors.append(f"{case_id}: missing source citations")
        evidence = case.get("evidence")
        if not isinstance(evidence, list):
            errors.append(f"{case_id}: evidence must be an array")
            continue
        cited_ids = set()
        for citation in evidence:
            if not isinstance(citation, dict):
                errors.append(f"{case_id}: citation must be an object")
                continue
            record_id = citation.get("record_id")
            if (
                not isinstance(citation.get("path"), str)
                or citation["path"].replace("\\", "/") != "traces/scenarios.json"
                or not isinstance(record_id, str)
                or record_id not in records.get(case_id, set())
            ):
                errors.append(f"{case_id}: invalid, ineligible, or wrong-scenario citation")
            else:
                cited_ids.add(record_id)
        if not set(target["required_evidence"]).issubset(cited_ids):
            errors.append(f"{case_id}: missing required record citations")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="JSON companion report to check")
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        parser.exit(2, f"Cannot read report: {error}\n")
    errors = check_report(report)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors))
        return 1
    print("PASS: all fixture cases match counts, unknowns, findings, and citations.")
    print("Manual review is still required for reasoning, privacy, and host tool behavior.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
