"""Check the structured companion for the trace-only synthetic evaluation."""

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def check_trace_only(report: object) -> list[str]:
    if not isinstance(report, dict):
        return ["report must be a JSON object"]
    errors = []
    if report.get("mode") != "trace-only":
        errors.append("mode must be trace-only")
    version = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))[
        "methodology_version"
    ]
    if report.get("methodology_version") != version:
        errors.append("methodology_version must match the candidate version")
    expected_metrics = {
        "logical_calls": 2,
        "execution_attempts": 2,
        "downstream_requests": 2,
        "confirmed_avoidable_calls": None,
    }
    metrics = report.get("metrics")
    if not isinstance(metrics, dict) or set(metrics) != set(expected_metrics):
        errors.append("metric keys do not match trace-only contract")
    else:
        for key, expected in expected_metrics.items():
            value = metrics[key]
            if value != expected or (expected is not None and type(value) is not int):
                errors.append(f"{key} expected {expected!r}, got {value!r}")
    if report.get("finding_categories") != []:
        errors.append("avoidability is unproven; ranked findings must be empty")
    evidence = report.get("evidence")
    required = {"standalone-1", "standalone-2"}
    if not isinstance(evidence, list):
        errors.append("evidence must be an array")
    else:
        cited = set()
        for entry in evidence:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("path"), str)
                or entry["path"].replace("\\", "/") != "traces/standalone.json"
                or not isinstance(entry.get("record_id"), str)
                or entry.get("record_id") not in required
            ):
                errors.append("invalid trace citation")
            else:
                cited.add(entry["record_id"])
        if cited != required:
            errors.append("both execution records must be cited")
    categories = report.get("limitation_categories")
    if (
        not isinstance(categories, list)
        or any(not isinstance(item, str) for item in categories)
        or set(categories) != {"missing-source", "unverified-optimization"}
        or len(categories) != 2
    ):
        errors.append("trace-only limitation categories must match exactly")
    limitations = report.get("limitations")
    if not isinstance(limitations, list) or not limitations or any(
        not isinstance(item, str) or not item.strip() for item in limitations
    ):
        errors.append("limitations must contain nonempty explanations")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="trace-only JSON companion")
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        parser.exit(2, f"Cannot read report: {error}\n")
    errors = check_trace_only(report)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors))
        return 1
    print("PASS: trace-only metrics, unknowns, categories and citations match.")
    print("Manual review is still required for reasoning, privacy and host behavior.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
