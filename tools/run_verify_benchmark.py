#!/usr/bin/env python3
"""Two-Layer Adversarial Verification Benchmark Harness for best-verification-eval-engineers.

ECOSYSTEM_CONTRACT v1.2.0 | suite_id: verification-eval | Python 3.9+ stdlib only.
- Layer 1 (CPU): Runs tools/verify_cpu_scanner.py on all tests/fixtures/cpu/* from manifest.json.
  Asserts Recall == 1.00, FPR == 0.00, Wilson 95% CIs, labeled
  `synthetic_fixture_regression_floor_not_universal_production_precision`.
- Layer 2 (Semantic): Runs tools/verify_cpu_scanner.py on all tests/fixtures/semantic/* and asserts
  `semantic_ast_zero_verified == true` (0 Tier A findings on semantic fixtures).
  Sets `layer2.status = "skipped_no_runner"` unless `--live-runner` is explicitly provided.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
import verify_cpu_scanner as scanner  # noqa: E402

CALIBRATION_LABEL = "synthetic_fixture_regression_floor_not_universal_production_precision"
Z_95 = 1.959963984540054


def wilson_95_ci(k: int, n: int) -> Tuple[float, float]:
    if n <= 0:
        return (0.0, 1.0)
    p = k / n
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    half = (Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * n)) / n)) / denom
    return (round(max(0.0, center - half), 4), round(min(1.0, center + half), 4))


def run_benchmark(manifest_path: pathlib.Path, live_runner: Optional[str] = None) -> Dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fixtures = manifest.get("fixtures", [])

    layer1_items = [f for f in fixtures if f.get("layer") == "layer1_cpu"]
    layer2_items = [f for f in fixtures if f.get("layer") == "layer2_semantic"]

    tp = fn = tn = fp = 0
    layer1_details: List[Dict[str, Any]] = []

    for item in layer1_items:
        fpath = (REPO_ROOT / item["path"]).resolve()
        rep = scanner.scan_repository(fpath)
        cov = rep["scan_coverage"]
        scan_ok = cov["files_scanned"] == 1 and cov["files_skipped"]["total"] == 0
        actual_ids = sorted({f["canonical_id"] for f in rep["findings"]})
        expected_ids = sorted(item.get("expected_canonical_ids", []))
        should_trigger = bool(item.get("should_trigger", False))

        if should_trigger:
            matched = scan_ok and (actual_ids == expected_ids) and len(expected_ids) > 0
            if matched:
                tp += 1
            else:
                fn += 1
        else:
            matched = scan_ok and len(actual_ids) == 0
            if matched:
                tn += 1
            else:
                fp += 1

        layer1_details.append(
            {
                "fixture_id": item["fixture_id"],
                "should_trigger": should_trigger,
                "scan_ok": scan_ok,
                "expected_canonical_ids": expected_ids,
                "actual_canonical_ids": actual_ids,
                "pass": matched,
            }
        )

    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0
    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0

    # Layer 2: Verify strict AST-orthogonality (0 Tier A findings on semantic fixtures)
    sem_ast_findings_total = 0
    sem_scan_all_ok = True
    layer2_details: List[Dict[str, Any]] = []
    for item in layer2_items:
        fpath = (REPO_ROOT / item["path"]).resolve()
        rep = scanner.scan_repository(fpath)
        cov = rep["scan_coverage"]
        scan_ok = cov["files_scanned"] == 1 and cov["files_skipped"]["total"] == 0
        if not scan_ok:
            sem_scan_all_ok = False
        cnt = len(rep["findings"])
        sem_ast_findings_total += cnt
        layer2_details.append(
            {
                "fixture_id": item["fixture_id"],
                "scan_ok": scan_ok,
                "ast_findings_count": cnt,
                "ast_canonical_ids": sorted({f["canonical_id"] for f in rep["findings"]}),
                "ast_orthogonal": scan_ok and cnt == 0,
            }
        )

    semantic_ast_zero_verified = sem_scan_all_ok and (sem_ast_findings_total == 0)
    layer1_pass = (recall == 1.0 and fpr == 0.0 and (tp + fn) > 0 and (tn + fp) > 0)

    if live_runner:
        raise SystemExit("ERROR: --live-runner is not wired in offline stdlib mode; invoke Clean-Room auditors externally.")

    return {
        "schema_version": "1.2.0",
        "suite_id": "verification-eval",
        "calibration_scope_label": CALIBRATION_LABEL,
        "production_claim_prohibited": True,
        "layer1": {
            "status": "PASS" if layer1_pass else "FAIL",
            "tp": tp,
            "fn": fn,
            "tn": tn,
            "fp": fp,
            "recall": recall,
            "recall_ci95_wilson": list(wilson_95_ci(tp, tp + fn)),
            "fpr": fpr,
            "fpr_ci95_wilson": list(wilson_95_ci(fp, fp + tn)),
            "precision": precision,
            "details": layer1_details,
        },
        "layer2": {
            "status": "skipped_no_runner" if not live_runner else "executed",
            "semantic_fixture_count": len(layer2_items),
            "semantic_ast_findings_total": sem_ast_findings_total,
            "semantic_ast_zero_verified": semantic_ast_zero_verified,
            "details": layer2_details,
        },
        "overall_pass": layer1_pass and semantic_ast_zero_verified,
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Two-layer verification benchmark harness")
    ap.add_argument("--manifest", type=pathlib.Path, default=REPO_ROOT / "tests/fixtures/manifest.json")
    ap.add_argument("--live-runner", type=str, default=None, help="Optional live Clean-Room runner command")
    ap.add_argument("--out", type=pathlib.Path, default=None)
    args = ap.parse_args(argv)

    result = run_benchmark(args.manifest.resolve(), live_runner=args.live_runner)
    txt = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.write_text(txt, encoding="utf-8")
    else:
        print(txt)
    return 0 if result["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
