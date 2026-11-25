#!/usr/bin/env python3
"""Targeted unit tests for tools/verify_cpu_scanner.py and tools/eval_ingest.py (Gate 3)."""
from __future__ import annotations

import datetime
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCANNER = REPO_ROOT / "tools" / "verify_cpu_scanner.py"
INGEST = REPO_ROOT / "tools" / "eval_ingest.py"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import verify_cpu_scanner as cpu_scanner  # noqa: E402


class TestVerifyCpuScanner(unittest.TestCase):
    def test_files_skipped_telemetry_oversized_binary_and_syntax_error(self) -> None:
        with tempfile.TemporaryDirectory(prefix="verify-skip-") as tmp:
            root = pathlib.Path(tmp)
            # 1. Valid clean Python test
            (root / "test_clean.py").write_text(
                "def test_addition():\n    assert 2 + 2 == 4\n",
                encoding="utf-8",
            )
            # 2. Oversized test file (> 128 bytes limit used in test)
            (root / "test_oversized.py").write_text(
                "def test_big():\n    assert '" + ("a" * 500) + "' != ''\n",
                encoding="utf-8",
            )
            # 3. Binary / NUL-byte test file
            (root / "test_binary.py").write_bytes(b"def test_bin():\n\x00\xff\xfe\n")
            # 4. SyntaxError Python test file
            (root / "test_broken_syntax.py").write_text(
                "def test_bad(:\n    assert True\n",
                encoding="utf-8",
            )

            report = cpu_scanner.scan_repository(root, max_file_bytes=128)
            cov = report["scan_coverage"]
            sk = cov["files_skipped"]

            self.assertEqual(cov["files_scanned"], 1)
            self.assertEqual(sk["total"], 3)
            self.assertEqual(cov["total_candidate_files"], 4)
            self.assertEqual(sk["oversized_count"], 1)
            self.assertEqual(sk["oversized_sample"], ["test_oversized.py"])
            self.assertEqual(sk["binary_or_decode_count"], 1)
            self.assertEqual(sk["binary_or_decode_sample"], ["test_binary.py"])
            self.assertEqual(sk["python_syntax_error_count"], 1)
            self.assertEqual(sk["python_syntax_error_sample"], ["test_broken_syntax.py"])

            # Verify SARIF 2.1.0 mirrors scan_coverage identically
            sarif = cpu_scanner.to_sarif(report)
            self.assertEqual(sarif["version"], "2.1.0")
            self.assertEqual(sarif["runs"][0]["properties"]["scan_coverage"], cov)

    def test_zero_fp_real_world_behavioral_tests(self) -> None:
        with tempfile.TemporaryDirectory(prefix="verify-clean-") as tmp:
            root = pathlib.Path(tmp)
            (root / "test_payments.py").write_text(
                "import pytest\n"
                "def assert_non_negative(val):\n"
                "    assert val >= 0\n"
                "def test_fee_helper():\n"
                "    assert_non_negative(150)\n"
                "def test_invalid_raises():\n"
                "    with pytest.raises(ValueError):\n"
                "        int('bad')\n",
                encoding="utf-8",
            )
            (root / "checkout.test.ts").write_text(
                "import { describe, expect, test, vi } from 'vitest';\n"
                "describe('checkout', () => {\n"
                "  vi.useFakeTimers();\n"
                "  test('applies discount', () => {\n"
                "    setTimeout(() => {}, 100);\n"
                "    expect(100 - 20).toBe(80);\n"
                "  });\n"
                "});\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [sys.executable, str(SCANNER), "--target", str(root), "--format", "json"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            data = json.loads(proc.stdout)
            self.assertEqual(data["findings"], [])
            self.assertEqual(data["scan_coverage"]["files_scanned"], 2)

    def test_ci_shell_exit_masking_scopes_to_test_gates_only(self) -> None:
        with tempfile.TemporaryDirectory(prefix="verify-ci-mask-") as tmp:
            root = pathlib.Path(tmp)
            wf = root / ".github" / "workflows"
            wf.mkdir(parents=True)
            # Best-effort cleanup / npm deprecate || true must NOT trigger VER-GOV-TAMPER-001
            (wf / "publish.yml").write_text(
                "name: Publish\non: workflow_dispatch\njobs:\n  pub:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: npm deprecate pkg@0.0.0-stage 'placeholder' || true\n",
                encoding="utf-8",
            )
            rep_clean = cpu_scanner.scan_repository(root)
            self.assertEqual(rep_clean["findings"], [])

            # Masking a real test/quality gate MUST trigger VER-GOV-TAMPER-001
            (wf / "ci.yml").write_text(
                "name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: sh tools/check.sh || true\n",
                encoding="utf-8",
            )
            rep_tamper = cpu_scanner.scan_repository(root)
            cids = [f["canonical_id"] for f in rep_tamper["findings"]]
            self.assertEqual(cids, ["verification-eval:anti-tampering-eval-governance:VER-GOV-TAMPER-001"])

    def test_node_test_dash_prefix_convention(self) -> None:
        with tempfile.TemporaryDirectory(prefix="verify-node-dash-") as tmp:
            root = pathlib.Path(tmp)
            tools = root / "tools"
            tools.mkdir()
            (tools / "test-clean-module.mjs").write_text(
                "import assert from 'node:assert/strict';\n"
                "assert.strictEqual(2 + 2, 4);\n",
                encoding="utf-8",
            )
            (tools / "test-tautology.mjs").write_text(
                "test('fake', () => { expect(true).toBe(true); });\n",
                encoding="utf-8",
            )
            rep = cpu_scanner.scan_repository(root)
            self.assertEqual(rep["scan_coverage"]["files_scanned"], 2)
            cids = [f["canonical_id"] for f in rep["findings"]]
            self.assertEqual(cids, ["verification-eval:assertion-mutation-strength:VER-TAU-CONST-001"])


class TestEvalIngestFailClosed(unittest.TestCase):
    def _write_clean_sarif(self, path: pathlib.Path) -> None:
        sarif = {
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {"driver": {"name": "verify_cpu_scanner", "version": "1.2.0", "rules": []}},
                    "results": [],
                    "properties": {
                        "scan_coverage": {
                            "total_candidate_files": 1,
                            "files_scanned": 1,
                            "files_skipped": {
                                "total": 0,
                                "oversized_count": 0,
                                "binary_or_decode_count": 0,
                                "os_error_count": 0,
                                "python_syntax_error_count": 0,
                            },
                        }
                    },
                }
            ],
        }
        path.write_text(json.dumps(sarif), encoding="utf-8")

    def _write_clean_junit(self, path: pathlib.Path) -> None:
        path.write_text(
            '<testsuite name="unit" tests="1" failures="0" errors="0">'
            '<testcase classname="test_mod" name="test_ok"/>'
            '</testsuite>',
            encoding="utf-8",
        )

    def test_exit_3_on_missing_tools_and_zero_tests(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ingest-missing-") as tmp:
            root = pathlib.Path(tmp)
            sarif_p = root / "tier_a.sarif"
            self._write_clean_sarif(sarif_p)
            zero_junit = root / "zero.xml"
            zero_junit.write_text('<testsuite name="empty" tests="0"></testsuite>', encoding="utf-8")

            # Missing --junit entirely -> exit 3
            p1 = subprocess.run(
                [sys.executable, str(INGEST), "--tier-a-sarif", str(sarif_p)],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(p1.returncode, 3)
            d1 = json.loads(p1.stdout)
            self.assertEqual(d1["evidence_tier"], "UNVERIFIED_MISSING_TOOL")
            self.assertEqual(d1["verdict"], "ITERATE")
            self.assertEqual(d1["blocking_ids"], ["verification-eval:tooling:MISSING_REQUIRED_TOOL_EVIDENCE"])

            # tests_executed == 0 -> exit 3
            p2 = subprocess.run(
                [sys.executable, str(INGEST), "--tier-a-sarif", str(sarif_p), "--junit", str(zero_junit)],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(p2.returncode, 3)
            d2 = json.loads(p2.stdout)
            self.assertEqual(d2["evidence_tier"], "UNVERIFIED_MISSING_TOOL")

    def test_semantic_findings_nonexistent_unknown_severity_malformed_cid_and_high_to_major(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ingest-sem-") as tmp:
            root = pathlib.Path(tmp)
            sarif_p = root / "tier_a.sarif"
            junit_p = root / "junit.xml"
            self._write_clean_sarif(sarif_p)
            self._write_clean_junit(junit_p)

            # 1. Nonexistent --semantic-findings -> exit 3
            p_missing = subprocess.run(
                [
                    sys.executable, str(INGEST),
                    "--tier-a-sarif", str(sarif_p),
                    "--junit", str(junit_p),
                    "--semantic-findings", str(root / "does_not_exist.json"),
                ],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(p_missing.returncode, 3)

            # 2. Unknown severity -> exit 3
            bad_sev = root / "bad_sev.json"
            bad_sev.write_text(json.dumps({
                "auditor": "auditor-test-integrity",
                "read_only_attested": True,
                "findings": [{
                    "canonical_id": "verification-eval:auditor-test-integrity:testint-02",
                    "severity": "CATASTROPHIC",
                    "file_path": "tests/a.py",
                    "line": 10,
                    "message": "Unknown severity string",
                }],
            }), encoding="utf-8")
            p_bad_sev = subprocess.run(
                [
                    sys.executable, str(INGEST),
                    "--tier-a-sarif", str(sarif_p),
                    "--junit", str(junit_p),
                    "--semantic-findings", str(bad_sev),
                ],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(p_bad_sev.returncode, 3)

            # 3. Malformed canonical_id -> exit 3
            bad_cid = root / "bad_cid.json"
            bad_cid.write_text(json.dumps({
                "auditor": "auditor-test-integrity",
                "read_only_attested": True,
                "findings": [{
                    "canonical_id": "testint-02",
                    "severity": "MAJOR",
                    "file_path": "tests/a.py",
                    "line": 10,
                    "message": "Bare 1-part ID",
                }],
            }), encoding="utf-8")
            p_bad_cid = subprocess.run(
                [
                    sys.executable, str(INGEST),
                    "--tier-a-sarif", str(sarif_p),
                    "--junit", str(junit_p),
                    "--semantic-findings", str(bad_cid),
                ],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(p_bad_cid.returncode, 3)

            # 4. Legacy HIGH -> MAJOR (NEVER auto-escalated to BLOCKER -> exit 1 ITERATE, not 2 REJECT)
            high_sem = root / "high_sem.json"
            high_sem.write_text(json.dumps({
                "auditor": "auditor-test-integrity",
                "read_only_attested": True,
                "findings": [{
                    "canonical_id": "verification-eval:auditor-test-integrity:testint-02",
                    "severity": "HIGH",
                    "file_path": "tests/a.py",
                    "line": 10,
                    "message": "Mirrored oracle formula",
                }],
            }), encoding="utf-8")
            p_high = subprocess.run(
                [
                    sys.executable, str(INGEST),
                    "--tier-a-sarif", str(sarif_p),
                    "--junit", str(junit_p),
                    "--semantic-findings", str(high_sem),
                ],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(p_high.returncode, 1)
            d_high = json.loads(p_high.stdout)
            self.assertEqual(d_high["verdict"], "ITERATE")
            self.assertEqual(d_high["counts"], {"blocker": 0, "major": 1, "minor": 0})
            self.assertEqual(d_high["findings"][0]["severity"], "MAJOR")

    def test_verify_envelope_enforces_approver_neq_pr_author(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ingest-env-") as tmp:
            root = pathlib.Path(tmp)
            future = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
            env_p = root / "envelope.json"
            env_p.write_text(json.dumps({
                "verdict_envelope": {
                    "suite_id": "verification-eval",
                    "verdict": "SHIP",
                    "domain_extensions": {
                        "human_signoff": {
                            "approver": "alice",
                            "ticket_id": "SEC-42",
                            "expires_at": future,
                        }
                    },
                }
            }), encoding="utf-8")

            # Self-approval (approver == pr_author) -> exit 2 BLOCKER
            p_self = subprocess.run(
                [sys.executable, str(INGEST), "--verify-envelope", str(env_p), "--pr-author", "alice"],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(p_self.returncode, 2)

            # Independent steward (approver != pr_author) -> exit 0
            p_ok = subprocess.run(
                [sys.executable, str(INGEST), "--verify-envelope", str(env_p), "--pr-author", "bob"],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(p_ok.returncode, 0)

    def test_js_empty_catch_and_cli_aliases(self) -> None:
        with tempfile.TemporaryDirectory(prefix="verify-catch-") as tmp:
            root = pathlib.Path(tmp)
            # Swallowing an assertion inside catch {} MUST still fire BLOCKER VER-TAU-SWALLOW-001
            (root / "bad_swallow.test.ts").write_text(
                "test('swallows', () => { try { expect(1).toBe(2); } catch {} });\n"
                "test('after_finally', () => { try { doWork(); } finally { done(); } try { doMoreWork(); } catch {} });\n"
                "test('after_loop', () => { for (let i=0;i<3;i++){ f(i); } try { risky(); } catch {} await sleep(10); });\n",
                encoding="utf-8",
            )
            json_out = root / "out.json"
            sarif_out = root / "out.sarif"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCANNER),
                    "--root",
                    str(root),
                    "--json-output",
                    str(json_out),
                    "--sarif-output",
                    str(sarif_out),
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(proc.returncode, 2)
            data = json.loads(json_out.read_text(encoding="utf-8"))
            swallows = [
                f for f in data["findings"]
                if f["canonical_id"] == "verification-eval:assertion-mutation-strength:VER-TAU-SWALLOW-001"
            ]
            self.assertEqual(len(swallows), 3, f"Expected all 3 swallows to fire, got {swallows}")
            self.assertEqual(json.loads(sarif_out.read_text(encoding="utf-8"))["version"], "2.1.0")

    def test_eval_ingest_malformed_line_and_oversized_skip(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ingest-edge-") as tmp:
            root = pathlib.Path(tmp)
            sarif_p = root / "tier_a.sarif"
            junit_p = root / "junit.xml"
            junit_p.write_text(
                '<testsuite tests="1" failures="0" errors="0"><testcase name="ok"/></testsuite>\n',
                encoding="utf-8",
            )
            # 1. Oversized skipped file -> emits MAJOR TIER_A_INCOMPLETE_COVERAGE
            sarif_p.write_text(
                json.dumps(
                    {
                        "version": "2.1.0",
                        "runs": [
                            {
                                "tool": {"driver": {"name": "verify_cpu_scanner", "version": "1.2.0", "rules": []}},
                                "results": [],
                                "properties": {
                                    "scan_coverage": {
                                        "total_candidate_files": 2,
                                        "files_scanned": 1,
                                        "files_skipped": {
                                            "total": 1,
                                            "oversized_count": 1,
                                            "binary_or_decode_count": 0,
                                            "os_error_count": 0,
                                            "python_syntax_error_count": 0,
                                        },
                                    }
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            p_over = subprocess.run(
                [sys.executable, str(INGEST), "--tier-a-sarif", str(sarif_p), "--junit", str(junit_p)],
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(p_over.returncode, 1)
            out_over = json.loads(p_over.stdout)
            self.assertIn(
                "verification-eval:anti-tampering-eval-governance:TIER_A_INCOMPLETE_COVERAGE",
                out_over["blocking_ids"],
            )

            # 2. Malformed non-integer line in --semantic-findings -> clean exit 3 (never traceback)
            self._write_clean_sarif(sarif_p)
            sem_p = root / "bad_line.json"
            sem_p.write_text(
                json.dumps(
                    {
                        "auditor": "auditor-test-integrity",
                        "read_only_attested": True,
                        "findings": [
                            {
                                "canonical_id": "verification-eval:auditor-test-integrity:testint-01",
                                "severity": "MAJOR",
                                "file_path": "a.py",
                                "line": "not-an-int",
                                "message": "bad line",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            p_bad = subprocess.run(
                [
                    sys.executable,
                    str(INGEST),
                    "--tier-a-sarif",
                    str(sarif_p),
                    "--junit",
                    str(junit_p),
                    "--semantic-findings",
                    str(sem_p),
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(p_bad.returncode, 3)


if __name__ == "__main__":
    unittest.main()
