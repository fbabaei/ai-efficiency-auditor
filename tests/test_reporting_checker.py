import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from evaluations.check_reporting import check_reporting


HEADER = (
    "| Priority | Weak area | Code location | Recommended improvement | Expected benefit | Evidence |\n"
    "|---|---|---|---|---|---|\n"
)


def reference_report(case: str) -> dict:
    locations = {
        "multi-site": "`src/pipeline.py:10-11`, `audit_fixture`",
        "supplied-locations": (
            "`src/worker.py:42-44`, `fetch_context`; From supplied report; not reverified"
        ),
        "supplied-missing": "Not provided in supplied report",
    }
    if case == "trace-unmapped":
        detailed = (
            "Code location not verified. traces/standalone.json records "
            "standalone-1 and standalone-2 show two calls; avoidability is unknown."
        )
        body = HEADER + "\n" + detailed
    else:
        location = locations[case]
        detailed = (
            f"High confidence: duplicate read at {location}, under unchanged state "
            "and identity. Reuse the first result; one call is statically avoidable, "
            "not a measured saving."
        )
        body = (
            HEADER
            + f"| P1 | Duplicate read | {location} | Reuse the first result under "
            "unchanged state and identity | One statically avoidable call, not measured "
            "| High confidence; detailed report |\n"
        )
    return {
        "case": case,
        "detailed_report": detailed,
        "executive_summary": "# Executive Summary\n\n" + body,
    }


class ReportingCheckerTests(unittest.TestCase):
    def test_accepts_all_reference_shapes(self) -> None:
        for case in ("multi-site", "trace-unmapped", "supplied-locations", "supplied-missing"):
            with self.subTest(case=case):
                self.assertEqual(check_reporting(reference_report(case)), [])

    def test_accepts_separate_sites_and_windows_paths(self) -> None:
        report = reference_report("multi-site")
        for field in ("detailed_report", "executive_summary"):
            report[field] = report[field].replace(
                "src/pipeline.py:10-11", r"src\pipeline.py:10; src\pipeline.py:11"
            )
        self.assertEqual(check_reporting(report), [])

    def test_rejects_missing_wrong_broad_or_reversed_sites(self) -> None:
        for field in ("detailed_report", "executive_summary"):
            for location in (
                "src/pipeline.py:10", "src/pipeline.py:11", "src/other.py:10-11",
                "src/pipeline.py:1-51", "src/pipeline.py:11-10",
                "src/pipeline.py:10-110", "src/pipeline.py:0-11",
                "other/src/pipeline.py:10-11", "src/pipeline.py:10-11wrong",
            ):
                with self.subTest(field=field, location=location):
                    report = reference_report("multi-site")
                    report[field] = report[field].replace("src/pipeline.py:10-11", location)
                    self.assertTrue(check_reporting(report))

    def test_requires_symbol_and_locations_in_the_location_column(self) -> None:
        report = reference_report("multi-site")
        report["executive_summary"] = report["executive_summary"].replace("audit_fixture", "other")
        self.assertTrue(check_reporting(report))
        report = reference_report("multi-site")
        report["executive_summary"] = report["executive_summary"].replace(
            "`src/pipeline.py:10-11`, `audit_fixture`", "Unknown"
        ) + "\nsrc/pipeline.py:10-11 audit_fixture"
        self.assertTrue(check_reporting(report))

    def test_rejects_unverified_trace_source_and_ranked_findings(self) -> None:
        for addition in (
            "\nsrc/pipeline.py:10", "\nworker.ts:42",
            "\n| P1 | Duplicate | Unknown | Cache | One call | Trace |\n",
        ):
            report = reference_report("trace-unmapped")
            report["executive_summary"] += addition
            self.assertTrue(check_reporting(report))

    def test_requires_trace_provenance_and_both_records(self) -> None:
        for field in ("detailed_report", "executive_summary"):
            for text in ("Code location not verified", "standalone-1", "standalone-2"):
                with self.subTest(field=field, text=text):
                    report = reference_report("trace-unmapped")
                    report[field] = report[field].replace(text, "")
                    self.assertTrue(check_reporting(report))

    def test_rejects_changed_or_unlabeled_supplied_locations(self) -> None:
        for old, new in (
            ("42-44", "42-45"),
            ("42-44", "42-440"),
            ("42-44", "42-44wrong"),
            ("src/worker.py", "other/src/worker.py"),
            ("fetch_context", "fetch"),
            ("From supplied report; not reverified", "Verified"),
        ):
            report = reference_report("supplied-locations")
            report["executive_summary"] = report["executive_summary"].replace(old, new)
            self.assertTrue(check_reporting(report))

    def test_rejects_guessed_missing_supplied_locations(self) -> None:
        report = reference_report("supplied-missing")
        report["executive_summary"] = report["executive_summary"].replace(
            "Not provided in supplied report", "src/worker.py:42-44"
        )
        self.assertTrue(check_reporting(report))

    def test_enforces_both_summary_limits(self) -> None:
        report = reference_report("multi-site")
        summary = report["executive_summary"]
        report["executive_summary"] += "\n" * (59 - len(summary.splitlines())) + "end"
        self.assertEqual(len(report["executive_summary"].splitlines()), 60)
        self.assertEqual(check_reporting(report), [])
        report["executive_summary"] += "\nend"
        self.assertTrue(check_reporting(report))
        report = reference_report("multi-site")
        report["executive_summary"] += " word" * (600 - len(summary.split()))
        self.assertEqual(len(report["executive_summary"].split()), 600)
        self.assertEqual(check_reporting(report), [])
        report["executive_summary"] += " word"
        self.assertTrue(check_reporting(report))

    def test_rejects_missing_duplicate_and_malformed_tables(self) -> None:
        report = reference_report("multi-site")
        original = report["executive_summary"]
        for summary in (
            original.replace(HEADER, ""),
            original + "\n" + HEADER,
            original.replace("|---|---|---|---|---|---|", "|---|"),
            original.replace("| P1 |", "| P1 | Extra |"),
            original.replace("| Duplicate read |", "| |"),
            original + "\n```\nreader.read(key)\n```",
            original + "\n~~~python\nreader.read(key)\n~~~",
            original.replace("# Executive Summary", "# Report"),
        ):
            with self.subTest(summary=summary):
                changed = copy.deepcopy(report)
                changed["executive_summary"] = summary
                self.assertTrue(check_reporting(changed))

    def test_rejects_excess_rows(self) -> None:
        report = reference_report("multi-site")
        row = report["executive_summary"].splitlines()[-1]
        report["executive_summary"] += (row + "\n") * 5
        self.assertTrue(check_reporting(report))

    def test_rejects_malformed_envelopes(self) -> None:
        for report in (
            None, [], {}, {"case": []}, {"case": "unknown"},
            {"case": "multi-site", "detailed_report": None},
            {"case": "multi-site", "detailed_report": "text", "executive_summary": ""},
        ):
            with self.subTest(report=report):
                self.assertTrue(check_reporting(report))

    def test_cli_exit_codes(self) -> None:
        checker = Path(__file__).resolve().parents[1] / "evaluations" / "check_reporting.py"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            for content, expected in (
                (json.dumps(reference_report("multi-site")), 0),
                (json.dumps({}), 1),
                ("{invalid", 2),
            ):
                with self.subTest(expected=expected):
                    path.write_text(content, encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, str(checker), str(path)],
                        capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            path.unlink()
            result = subprocess.run(
                [sys.executable, str(checker), str(path)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
