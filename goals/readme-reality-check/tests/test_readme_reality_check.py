from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from readme_reality_check_lib import audit_repository
from readme_reality_check_lib.renderers import render_report


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "readme_reality_check.py"
FIXTURE = ROOT / "fixtures" / "demo-repo"
TEST_OUTPUT = ROOT / "out" / "test-artifacts"


class ReadmeRealityCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        shutil.rmtree(TEST_OUTPUT, ignore_errors=True)
        TEST_OUTPUT.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(TEST_OUTPUT, ignore_errors=True)

    def test_audit_repository_reports_stale_docs(self) -> None:
        report = audit_repository(FIXTURE)

        self.assertGreater(len(report.findings), 0)
        kinds = {finding.kind for finding in report.findings}
        references = {finding.reference for finding in report.findings}

        self.assertIn("missing_script", kinds)
        self.assertIn("dev", references)
        self.assertIn("scripts/bootstrap.py", references)

    def test_help_command_succeeds(self) -> None:
        result = self._run_cli("--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Audit README and setup docs", result.stdout)
        self.assertIn("--help", result.stdout)

    def test_json_output_is_valid(self) -> None:
        result = self._run_cli("audit", str(FIXTURE), "--format", "json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertGreater(payload["finding_count"], 0)
        self.assertEqual(payload["facts"]["doc_files"], ["README.md"])

    def test_html_renderer_and_output_file(self) -> None:
        html_output_path = TEST_OUTPUT / "demo-report.html"
        result = self._run_cli("audit", str(FIXTURE), "--format", "html", "--output", str(html_output_path))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(html_output_path.is_file())
        rendered = html_output_path.read_text(encoding="utf-8")
        self.assertIn("<!DOCTYPE html>", rendered)
        self.assertIn("README Reality Check Report", rendered)
        self.assertIn("scripts/bootstrap.py", rendered)

        report = audit_repository(FIXTURE)
        inline_html = render_report(report, "html")
        self.assertIn("<table>", inline_html)
        self.assertIn("missing_script", inline_html)

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
