#!/usr/bin/env python3
"""Tier B fail-closed execution evidence ingestor for best-verification-eval-engineers.

ECOSYSTEM_CONTRACT v1.2.0 | suite_id: verification-eval
Constraints:
  - Python 3.9+ standard library ONLY (zero network imports).
  - Normalized 3-tier emitted severity vocabulary: BLOCKER | MAJOR | MINOR (HR-4).
  - Exit 0 = SHIP | Exit 1 = ITERATE | Exit 2 = REJECT | Exit 3 = UNVERIFIED_MISSING_TOOL (HR-7).
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

MISSING_TOOL_ID = "verification-eval:tooling:MISSING_REQUIRED_TOOL_EVIDENCE"
CANONICAL_ID_RE = re.compile(r"^verification-eval:[a-z0-9-]+:[A-Za-z0-9_-]{3,48}$")
VALID_AUDITORS = {"auditor-test-integrity", "auditor-evalops-validity"}
XML_FORBIDDEN_RE = re.compile(r"<!\s*(DOCTYPE|ENTITY)\b", re.IGNORECASE)
MAX_ARTIFACT_BYTES = 25 * 1024 * 1024  # 25 MiB cap against DoS

# HR-4 / HR-7: Legacy input aliases accepted ONLY on --semantic-findings; always emitted as BLOCKER|MAJOR|MINOR.
# CRITICAL -> BLOCKER, HIGH/MEDIUM/MODERATE -> MAJOR (NEVER auto-escalate HIGH to BLOCKER), LOW/INFO -> MINOR.
SEMANTIC_SEVERITY_MAP: Dict[str, str] = {
    "BLOCKER": "BLOCKER",
    "CRITICAL": "BLOCKER",
    "MAJOR": "MAJOR",
    "HIGH": "MAJOR",
    "MEDIUM": "MAJOR",
    "MODERATE": "MAJOR",
    "MINOR": "MINOR",
    "LOW": "MINOR",
    "INFO": "MINOR",
}

EMITTED_SEVERITY_RANK: Dict[str, int] = {
    "BLOCKER": 3,
    "MAJOR": 2,
    "MINOR": 1,
}


class MissingOrInvalidEvidenceError(Exception):
    """Fail-closed exception mapping deterministically to exit code 3."""


def _read_bounded_text(path: pathlib.Path, label: str) -> str:
    if not path.exists() or not path.is_file():
        raise MissingOrInvalidEvidenceError(f"Required {label} artifact not found: {path}")
    try:
        size = path.stat().st_size
        if size == 0:
            raise MissingOrInvalidEvidenceError(f"Required {label} artifact is empty: {path}")
        if size > MAX_ARTIFACT_BYTES:
            raise MissingOrInvalidEvidenceError(f"{label} exceeds size limit: {path}")
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise MissingOrInvalidEvidenceError(f"Cannot read {label} at {path}: {exc}") from exc


def parse_junit_xml(path: pathlib.Path) -> Dict[str, Any]:
    raw = _read_bounded_text(path, "junit.xml")
    if XML_FORBIDDEN_RE.search(raw):
        raise MissingOrInvalidEvidenceError("JUnit XML contains forbidden DOCTYPE/ENTITY declaration.")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise MissingOrInvalidEvidenceError(f"Unparseable JUnit XML: {exc}") from exc

    if root.tag not in ("testsuites", "testsuite"):
        raise MissingOrInvalidEvidenceError(f"Invalid JUnit root element: <{root.tag}>")

    total = passed = failed = errors = skipped = xfailed = 0
    failed_cases: List[str] = []

    for tc in root.iter("testcase"):
        total += 1
        name = f"{tc.attrib.get('classname', '')}::{tc.attrib.get('name', 'unnamed')}".strip(":")
        has_error = tc.find("error") is not None
        has_failure = tc.find("failure") is not None
        skip_el = tc.find("skipped")
        # Strict precedence: error > failure > skipped > passed
        if has_error:
            errors += 1
            failed_cases.append(f"ERROR:{name}")
        elif has_failure:
            failed += 1
            failed_cases.append(f"FAIL:{name}")
        elif skip_el is not None:
            if skip_el.attrib.get("type") == "pytest.xfail":
                xfailed += 1
            else:
                skipped += 1
        else:
            passed += 1

    for suite_el in ([root] if root.tag == "testsuite" else list(root.iter("testsuite"))):
        for attr in ("tests", "failures", "errors", "skipped", "skips"):
            if attr in suite_el.attrib:
                try:
                    v = int(suite_el.attrib[attr])
                except ValueError as exc:
                    raise MissingOrInvalidEvidenceError(f"Non-integer JUnit {attr} attribute") from exc
                if v < 0 or v > 2_147_483_647:
                    raise MissingOrInvalidEvidenceError(f"Out-of-range JUnit {attr}={v}")

    if total == 0:
        raise MissingOrInvalidEvidenceError("JUnit XML contains 0 executed test cases (tests_executed == 0).")

    return {
        "tests_executed": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "xfailed": xfailed,
        "failed_cases": failed_cases[:50],
    }


def parse_lcov(path: pathlib.Path) -> Dict[str, Any]:
    raw = _read_bounded_text(path, "lcov.info")
    line_hits: Dict[Tuple[str, int], int] = {}
    branch_hits: Dict[Tuple[str, int, str, str], int] = {}
    current_sf: Optional[str] = None
    records = 0

    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if line.startswith("SF:"):
            current_sf = line[3:].strip()
        elif line.startswith("DA:") and current_sf:
            parts = line[3:].split(",")
            if len(parts) >= 2:
                try:
                    lno, hits = int(parts[0]), int(parts[1])
                except ValueError as exc:
                    raise MissingOrInvalidEvidenceError(f"Malformed LCOV DA line: {line}") from exc
                key = (current_sf, lno)
                line_hits[key] = max(line_hits.get(key, 0), hits)
        elif line.startswith("BRDA:") and current_sf:
            parts = line[5:].split(",")
            if len(parts) >= 4:
                lno_s, blk, br, taken = parts[0], parts[1], parts[2], parts[3]
                if lno_s == "0":
                    continue  # Tolerate coverage.py BRDA:0 emission quirk
                try:
                    lno_i = int(lno_s)
                    hits = 0 if taken == "-" else int(taken)
                except ValueError as exc:
                    raise MissingOrInvalidEvidenceError(f"Malformed LCOV BRDA line: {line}") from exc
                key_b = (current_sf, lno_i, blk, br)
                branch_hits[key_b] = max(branch_hits.get(key_b, 0), hits)
        elif line == "end_of_record":
            records += 1
            current_sf = None

    if records == 0 or not line_hits:
        raise MissingOrInvalidEvidenceError("LCOV artifact contains zero valid coverage records.")

    lines_found = len(line_hits)
    lines_hit = sum(1 for h in line_hits.values() if h > 0)
    branches_found = len(branch_hits)
    branches_hit = sum(1 for h in branch_hits.values() if h > 0)
    return {
        "format": "lcov",
        "lines_found": lines_found,
        "lines_hit": lines_hit,
        "line_pct": round((lines_hit / lines_found) * 100.0, 2),
        "branches_found": branches_found,
        "branches_hit": branches_hit,
        "branch_pct": round((branches_hit / branches_found) * 100.0, 2) if branches_found else None,
        "excluded_ratio": 0.0,
    }


def parse_coverage_json(path: pathlib.Path) -> Dict[str, Any]:
    raw = _read_bounded_text(path, "coverage.json")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MissingOrInvalidEvidenceError(f"Unparseable coverage JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise MissingOrInvalidEvidenceError("Coverage JSON root must be an object.")

    # Dialect 1: coverage.py JSON
    if "totals" in data and isinstance(data["totals"], dict) and "num_statements" in data["totals"]:
        t = data["totals"]
        stmts = int(t.get("num_statements", 0))
        cov_l = int(t.get("covered_lines", 0))
        excl = int(t.get("excluded_lines", 0))
        num_b = int(t.get("num_branches", 0))
        cov_b = int(t.get("covered_branches", 0))
        if stmts == 0:
            raise MissingOrInvalidEvidenceError("coverage.py JSON reports 0 statements.")
        return {
            "format": "coverage_py_json",
            "lines_found": stmts,
            "lines_hit": cov_l,
            "line_pct": round((cov_l / stmts) * 100.0, 2),
            "branches_found": num_b,
            "branches_hit": cov_b,
            "branch_pct": round((cov_b / num_b) * 100.0, 2) if num_b > 0 else None,
            "excluded_ratio": round(excl / (stmts + excl), 4) if (stmts + excl) > 0 else 0.0,
        }

    # Dialect 2: Istanbul / c8 / Vitest coverage-summary.json
    if "total" in data and isinstance(data["total"], dict) and "lines" in data["total"]:
        t = data["total"]
        lf, lh = int(t["lines"]["total"]), int(t["lines"]["covered"])
        bf, bh = int(t["branches"]["total"]), int(t["branches"]["covered"])
        if lf == 0:
            raise MissingOrInvalidEvidenceError("Istanbul coverage-summary.json reports 0 lines.")
        return {
            "format": "istanbul_summary_json",
            "lines_found": lf,
            "lines_hit": lh,
            "line_pct": round((lh / lf) * 100.0, 2),
            "branches_found": bf,
            "branches_hit": bh,
            "branch_pct": round((bh / bf) * 100.0, 2) if bf > 0 else None,
            "excluded_ratio": 0.0,
        }

    # Dialect 3: Istanbul coverage-final.json (recomputed from per-file s and b maps)
    if data and all(isinstance(v, dict) and "s" in v and "b" in v for v in data.values()):
        sf = sh = bf = bh = 0
        for fobj in data.values():
            for hits in fobj["s"].values():
                sf += 1
                if int(hits) > 0:
                    sh += 1
            for arms in fobj["b"].values():
                for arm_hits in arms:
                    bf += 1
                    if int(arm_hits) > 0:
                        bh += 1
        if sf == 0:
            raise MissingOrInvalidEvidenceError("Istanbul coverage-final.json reports 0 statements.")
        return {
            "format": "istanbul_final_json",
            "lines_found": sf,
            "lines_hit": sh,
            "line_pct": round((sh / sf) * 100.0, 2),
            "branches_found": bf,
            "branches_hit": bh,
            "branch_pct": round((bh / bf) * 100.0, 2) if bf > 0 else None,
            "excluded_ratio": 0.0,
        }

    raise MissingOrInvalidEvidenceError("Unrecognized coverage JSON dialect.")


def parse_mutation_json(path: pathlib.Path) -> Dict[str, Any]:
    raw = _read_bounded_text(path, "mutation.json")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MissingOrInvalidEvidenceError(f"Unparseable mutation JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise MissingOrInvalidEvidenceError("Mutation JSON root must be an object.")

    # Dialect 1: Stryker mutation-testing-report-schema
    if "schemaVersion" in data and isinstance(data.get("files"), dict):
        counts = {
            "Killed": 0, "Timeout": 0, "Survived": 0, "NoCoverage": 0,
            "CompileError": 0, "RuntimeError": 0, "Ignored": 0, "Pending": 0,
        }
        for fobj in data["files"].values():
            for mut in fobj.get("mutants", []):
                st = mut.get("status")
                if st not in counts:
                    raise MissingOrInvalidEvidenceError(f"Unknown Stryker mutant status: {st!r}")
                counts[st] += 1
        if counts["Pending"] > 0:
            raise MissingOrInvalidEvidenceError(f"Stryker run incomplete: {counts['Pending']} Pending mutants.")
        denom = counts["Killed"] + counts["Timeout"] + counts["Survived"] + counts["NoCoverage"]
        if denom == 0:
            raise MissingOrInvalidEvidenceError("Stryker report contains 0 evaluable mutants.")
        score = ((counts["Killed"] + counts["Timeout"]) / denom) * 100.0
        return {"format": "stryker", "mutation_score": round(score, 2), "evaluable_mutants": denom, "counts": counts}

    # Dialect 2: mutmut v3 mutmut-cicd-stats.json
    if "killed" in data and "survived" in data:
        killed = int(data.get("killed", 0))
        survived = int(data.get("survived", 0))
        timeout = int(data.get("timeout", 0))
        no_tests = int(data.get("no_tests", 0))
        denom = killed + timeout + survived + no_tests
        if denom == 0:
            raise MissingOrInvalidEvidenceError("mutmut report contains 0 evaluable mutants.")
        score = ((killed + timeout) / denom) * 100.0
        return {"format": "mutmut", "mutation_score": round(score, 2), "evaluable_mutants": denom, "counts": data}

    # Dialect 3: Gremlins Go mutation JSON
    if "mutants_killed" in data and "mutants_lived" in data:
        killed = int(data["mutants_killed"])
        lived = int(data["mutants_lived"])
        not_cov = int(data.get("mutants_not_covered", 0))
        denom = killed + lived + not_cov
        if denom == 0:
            raise MissingOrInvalidEvidenceError("Gremlins report contains 0 evaluable mutants.")
        return {
            "format": "gremlins",
            "mutation_score": round((killed / denom) * 100.0, 2),
            "test_efficacy": float(data.get("test_efficacy", 0.0)),
            "evaluable_mutants": denom,
        }

    raise MissingOrInvalidEvidenceError("Unrecognized mutation testing JSON format.")


def parse_tier_a_sarif(path: pathlib.Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    raw = _read_bounded_text(path, "verify_cpu_scanner.sarif")
    try:
        sarif = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MissingOrInvalidEvidenceError(f"Unparseable Tier A SARIF: {exc}") from exc
    if sarif.get("version") != "2.1.0" or not isinstance(sarif.get("runs"), list) or not sarif["runs"]:
        raise MissingOrInvalidEvidenceError("Invalid SARIF 2.1.0 structure.")
    run = sarif["runs"][0]
    cov = run.get("properties", {}).get("scan_coverage")
    if not isinstance(cov, dict) or "files_scanned" not in cov or "files_skipped" not in cov:
        raise MissingOrInvalidEvidenceError("Tier A SARIF missing mandatory runs[0].properties.scan_coverage.")

    findings: List[Dict[str, Any]] = []
    for res in run.get("results", []):
        props = res.get("properties", {})
        cid = props.get("canonical_id", "")
        sev = props.get("severity", "")
        if not CANONICAL_ID_RE.match(cid) or sev not in EMITTED_SEVERITY_RANK:
            raise MissingOrInvalidEvidenceError(f"Malformed Tier A SARIF result metadata: {cid!r}/{sev!r}")
        loc = res.get("locations", [{}])[0].get("physicalLocation", {})
        findings.append(
            {
                "source": "tier_a",
                "canonical_id": cid,
                "severity": sev,
                "file_path": loc.get("artifactLocation", {}).get("uri", ""),
                "line": int(loc.get("region", {}).get("startLine", 0)),
                "message": res.get("message", {}).get("text", ""),
            }
        )
    return findings, cov


def parse_semantic_findings(path: pathlib.Path) -> List[Dict[str, Any]]:
    raw = _read_bounded_text(path, "--semantic-findings")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MissingOrInvalidEvidenceError(f"Unparseable --semantic-findings JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("findings"), list):
        raise MissingOrInvalidEvidenceError("--semantic-findings must be a JSON object with a 'findings' list.")
    auditor = payload.get("auditor")
    if auditor not in VALID_AUDITORS:
        raise MissingOrInvalidEvidenceError(f"Invalid Clean-Room auditor identity: {auditor!r}")
    if payload.get("read_only_attested") is not True:
        raise MissingOrInvalidEvidenceError("Clean-Room findings missing read_only_attested=true.")

    normalized: List[Dict[str, Any]] = []
    for idx, item in enumerate(payload["findings"]):
        if not isinstance(item, dict):
            raise MissingOrInvalidEvidenceError(f"Semantic finding #{idx} is not an object.")
        cid = item.get("canonical_id", "")
        if not isinstance(cid, str) or not CANONICAL_ID_RE.match(cid):
            raise MissingOrInvalidEvidenceError(f"Malformed semantic canonical_id: {cid!r}")
        raw_sev = item.get("severity")
        if not isinstance(raw_sev, str) or raw_sev.upper() not in SEMANTIC_SEVERITY_MAP:
            raise MissingOrInvalidEvidenceError(
                f"Unknown semantic severity {raw_sev!r}; silent coercion prohibited."
            )
        mapped_sev = SEMANTIC_SEVERITY_MAP[raw_sev.upper()]
        normalized.append(
            {
                "source": f"clean_room:{auditor}",
                "canonical_id": cid,
                "severity": mapped_sev,
                "file_path": str(item.get("file_path", "")),
                "line": int(item.get("line", 0)),
                "message": str(item.get("message", "")),
            }
        )
    return normalized


def verify_human_signoff_dict(
    data: Dict[str, Any],
    pr_author: str,
    stewards: List[str],
    source_path: str,
) -> Optional[Dict[str, Any]]:
    approver = str(data.get("approver", "")).strip()
    author = pr_author.strip() or str(data.get("pr_author", "")).strip()
    ticket = str(data.get("ticket_id", "")).strip()
    expires = str(data.get("expires_at", "")).strip()
    if not approver or not author or not ticket:
        return {
            "source": "tier_b_governance",
            "canonical_id": "verification-eval:anti-tampering-eval-governance:INVALID_HUMAN_SIGNOFF",
            "severity": "MAJOR",
            "file_path": source_path,
            "line": 1,
            "message": "Human signoff missing approver, pr_author, or ticket_id.",
        }
    if approver.lower() == author.lower():
        return {
            "source": "tier_b_governance",
            "canonical_id": "verification-eval:anti-tampering-eval-governance:SELF_APPROVAL_PROHIBITED",
            "severity": "BLOCKER",
            "file_path": source_path,
            "line": 1,
            "message": f"Separation of Duties violation: approver '{approver}' equals pr_author '{author}'.",
        }
    if stewards and approver not in stewards:
        return {
            "source": "tier_b_governance",
            "canonical_id": "verification-eval:anti-tampering-eval-governance:UNAUTHORIZED_SIGNOFF",
            "severity": "MAJOR",
            "file_path": source_path,
            "line": 1,
            "message": f"Approver '{approver}' is not in authorized verification stewards list.",
        }
    try:
        exp_dt = datetime.date.fromisoformat(expires[:10])
    except ValueError:
        return {
            "source": "tier_b_governance",
            "canonical_id": "verification-eval:anti-tampering-eval-governance:EXPIRED_OR_INVALID_SIGNOFF",
            "severity": "MAJOR",
            "file_path": source_path,
            "line": 1,
            "message": f"Invalid ISO-8601 expires_at date: {expires!r}.",
        }
    today = datetime.date.today()
    if exp_dt < today or (exp_dt - today).days > 90:
        return {
            "source": "tier_b_governance",
            "canonical_id": "verification-eval:anti-tampering-eval-governance:EXPIRED_OR_INVALID_SIGNOFF",
            "severity": "MAJOR",
            "file_path": source_path,
            "line": 1,
            "message": f"Human signoff expires_at {exp_dt.isoformat()} is expired or exceeds 90-day ceiling.",
        }
    return None


def verify_human_signoff(path: pathlib.Path, pr_author: str, stewards: List[str]) -> Optional[Dict[str, Any]]:
    raw = _read_bounded_text(path, "--human-signoff")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise MissingOrInvalidEvidenceError("--human-signoff must be a JSON object.")
    return verify_human_signoff_dict(data, pr_author, stewards, str(path))


def verify_envelope_file(path: pathlib.Path, pr_author: str, stewards: List[str]) -> int:
    """Verify a serialized Verdict Envelope JSON file, enforcing approver != pr_author on human_signoff."""
    try:
        raw = _read_bounded_text(path, "--verify-envelope")
        doc = json.loads(raw)
    except (MissingOrInvalidEvidenceError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 3

    env = doc.get("verdict_envelope", doc) if isinstance(doc, dict) else None
    if not isinstance(env, dict):
        print(json.dumps({"ok": False, "error": "Envelope must be a JSON object."}, indent=2))
        return 3

    signoff = env.get("domain_extensions", {}).get("human_signoff") or env.get("human_signoff")
    if isinstance(signoff, dict):
        err = verify_human_signoff_dict(signoff, pr_author, stewards, str(path))
        if err is not None:
            print(json.dumps({"ok": False, "finding": err}, indent=2))
            return 2 if err["severity"] == "BLOCKER" else 1

    print(json.dumps({"ok": True, "suite_id": env.get("suite_id"), "verdict": env.get("verdict")}, indent=2))
    return 0


def deduplicate_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    dedup: Dict[Tuple[str, str, int], Dict[str, Any]] = {}
    for f in findings:
        norm_path = str(f.get("file_path", "")).replace("\\", "/")
        key = (f["canonical_id"], norm_path, int(f.get("line", 0)))
        if key not in dedup:
            dedup[key] = dict(f, file_path=norm_path, corroborated_by=[f["source"]])
        else:
            existing = dedup[key]
            if f["source"] not in existing["corroborated_by"]:
                existing["corroborated_by"].append(f["source"])
            if EMITTED_SEVERITY_RANK[f["severity"]] > EMITTED_SEVERITY_RANK[existing["severity"]]:
                existing["severity"] = f["severity"]
    return list(dedup.values())


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Tier B fail-closed verification evidence ingestor (ECOSYSTEM_CONTRACT v1.2.0)")
    ap.add_argument("--verify-envelope", type=pathlib.Path, default=None, help="Verify a Verdict Envelope JSON file (including approver != pr_author)")
    ap.add_argument("--junit", type=pathlib.Path, default=None)
    ap.add_argument("--tier-a-sarif", type=pathlib.Path, default=None)
    ap.add_argument("--lcov", type=pathlib.Path, default=None)
    ap.add_argument("--coverage-json", type=pathlib.Path, default=None)
    ap.add_argument("--mutation-json", type=pathlib.Path, default=None)
    ap.add_argument("--semantic-findings", type=pathlib.Path, default=None)
    ap.add_argument("--gate-policy", choices=[
        "AUTO_PASS_ON_CLEAN_ORACLE",
        "MANDATORY_CLEAN_ROOM_TEST_AUDIT",
        "MANDATORY_NAMED_HUMAN_SIGNOFF",
    ], default="AUTO_PASS_ON_CLEAN_ORACLE")
    ap.add_argument("--human-signoff", type=pathlib.Path, default=None)
    ap.add_argument("--pr-author", type=str, default="")
    ap.add_argument("--authorized-steward", action="append", default=[])
    ap.add_argument("--min-line-coverage", type=float, default=80.0)
    ap.add_argument("--min-branch-coverage", type=float, default=75.0)
    ap.add_argument("--min-mutation-score", type=float, default=65.0)
    ap.add_argument("--out", type=pathlib.Path, default=None)
    args = ap.parse_args(argv)

    if args.verify_envelope is not None:
        return verify_envelope_file(args.verify_envelope, args.pr_author, args.authorized_steward)

    findings: List[Dict[str, Any]] = []
    evidence: Dict[str, Any] = {}
    missing_tool_errors: List[str] = []

    if args.tier_a_sarif is None:
        missing_tool_errors.append("Required --tier-a-sarif artifact not supplied.")
    else:
        try:
            tier_a_findings, scan_cov = parse_tier_a_sarif(args.tier_a_sarif)
            findings.extend(tier_a_findings)
            evidence["tier_a_scan_coverage"] = scan_cov
            sk = scan_cov["files_skipped"]
            if sk.get("python_syntax_error_count", 0) > 0 or sk.get("os_error_count", 0) > 0:
                findings.append(
                    {
                        "source": "tier_b",
                        "canonical_id": "verification-eval:anti-tampering-eval-governance:TIER_A_INCOMPLETE_COVERAGE",
                        "severity": "MAJOR",
                        "file_path": str(args.tier_a_sarif),
                        "line": 1,
                        "message": f"Tier A skipped files due to syntax/OS errors: {sk}",
                    }
                )
        except MissingOrInvalidEvidenceError as exc:
            missing_tool_errors.append(str(exc))

    if args.junit is None:
        missing_tool_errors.append("Required --junit test runner artifact not supplied.")
    else:
        try:
            junit = parse_junit_xml(args.junit)
            evidence["junit"] = junit
            if junit["errors"] > 0:
                findings.append(
                    {
                        "source": "tier_b",
                        "canonical_id": "verification-eval:test-execution-oracles:TEST_EXECUTION_ERROR",
                        "severity": "BLOCKER",
                        "file_path": str(args.junit),
                        "line": 1,
                        "message": f"{junit['errors']} test execution/setup error(s): {junit['failed_cases'][:5]}",
                    }
                )
            if junit["failed"] > 0:
                findings.append(
                    {
                        "source": "tier_b",
                        "canonical_id": "verification-eval:test-execution-oracles:TEST_SUITE_FAILURE",
                        "severity": "BLOCKER",
                        "file_path": str(args.junit),
                        "line": 1,
                        "message": f"{junit['failed']} failing test assertion(s): {junit['failed_cases'][:5]}",
                    }
                )
        except MissingOrInvalidEvidenceError as exc:
            missing_tool_errors.append(str(exc))

    for cov_arg, parser_fn in ((args.lcov, parse_lcov), (args.coverage_json, parse_coverage_json)):
        if cov_arg is not None:
            try:
                cov = parser_fn(cov_arg)
                evidence[cov["format"]] = cov
                if cov["line_pct"] < args.min_line_coverage:
                    findings.append(
                        {
                            "source": "tier_b",
                            "canonical_id": "verification-eval:test-execution-oracles:LINE_COVERAGE_BELOW_FLOOR",
                            "severity": "MAJOR",
                            "file_path": str(cov_arg),
                            "line": 1,
                            "message": f"Line coverage {cov['line_pct']}% < floor {args.min_line_coverage}%.",
                        }
                    )
                if cov["branch_pct"] is not None and cov["branch_pct"] < args.min_branch_coverage:
                    findings.append(
                        {
                            "source": "tier_b",
                            "canonical_id": "verification-eval:test-execution-oracles:BRANCH_COVERAGE_BELOW_FLOOR",
                            "severity": "MAJOR",
                            "file_path": str(cov_arg),
                            "line": 1,
                            "message": f"Branch coverage {cov['branch_pct']}% < floor {args.min_branch_coverage}%.",
                        }
                    )
                if cov.get("excluded_ratio", 0.0) > 0.05:
                    findings.append(
                        {
                            "source": "tier_b",
                            "canonical_id": "verification-eval:anti-tampering-eval-governance:EXCESSIVE_COVERAGE_EXCLUSION",
                            "severity": "MAJOR",
                            "file_path": str(cov_arg),
                            "line": 1,
                            "message": f"Excluded line ratio {cov['excluded_ratio']*100:.2f}% exceeds 5% tamper ceiling.",
                        }
                    )
            except MissingOrInvalidEvidenceError as exc:
                missing_tool_errors.append(str(exc))

    if args.mutation_json is not None:
        try:
            mut = parse_mutation_json(args.mutation_json)
            evidence["mutation"] = mut
            if mut["mutation_score"] < args.min_mutation_score:
                findings.append(
                    {
                        "source": "tier_b",
                        "canonical_id": "verification-eval:assertion-mutation-strength:MUTATION_SCORE_BELOW_FLOOR",
                        "severity": "MAJOR",
                        "file_path": str(args.mutation_json),
                        "line": 1,
                        "message": f"Mutation score {mut['mutation_score']}% < floor {args.min_mutation_score}%.",
                    }
                )
        except MissingOrInvalidEvidenceError as exc:
            missing_tool_errors.append(str(exc))

    if args.semantic_findings is not None:
        try:
            findings.extend(parse_semantic_findings(args.semantic_findings))
        except MissingOrInvalidEvidenceError as exc:
            missing_tool_errors.append(str(exc))
    elif args.gate_policy == "MANDATORY_CLEAN_ROOM_TEST_AUDIT":
        findings.append(
            {
                "source": "tier_b_governance",
                "canonical_id": "verification-eval:anti-tampering-eval-governance:PENDING_CLEAN_ROOM_AUDIT",
                "severity": "MAJOR",
                "file_path": "",
                "line": 0,
                "message": "Gate policy MANDATORY_CLEAN_ROOM_TEST_AUDIT requires --semantic-findings.",
            }
        )

    if args.gate_policy == "MANDATORY_NAMED_HUMAN_SIGNOFF":
        if args.human_signoff is None:
            findings.append(
                {
                    "source": "tier_b_governance",
                    "canonical_id": "verification-eval:anti-tampering-eval-governance:PENDING_HUMAN_SIGNOFF",
                    "severity": "MAJOR",
                    "file_path": "",
                    "line": 0,
                    "message": "Gate policy MANDATORY_NAMED_HUMAN_SIGNOFF requires --human-signoff.",
                }
            )
        else:
            try:
                err_f = verify_human_signoff(args.human_signoff, args.pr_author, args.authorized_steward)
                if err_f:
                    findings.append(err_f)
            except (MissingOrInvalidEvidenceError, json.JSONDecodeError) as exc:
                missing_tool_errors.append(str(exc))

    deduped = deduplicate_findings(findings)
    blockers = [f for f in deduped if f["severity"] == "BLOCKER"]
    majors = [f for f in deduped if f["severity"] == "MAJOR"]
    minors = [f for f in deduped if f["severity"] == "MINOR"]

    # Conjunctive gate precedence: REJECT (2) > UNVERIFIED_MISSING_TOOL (3) > ITERATE (1) > SHIP (0)
    if blockers:
        verdict, exit_code = "REJECT", 2
        evidence_tier = "TOOL_VERIFIED"
        blocking_ids = sorted({f["canonical_id"] for f in blockers})
    elif missing_tool_errors:
        verdict, exit_code = "ITERATE", 3
        evidence_tier = "UNVERIFIED_MISSING_TOOL"
        blocking_ids = [MISSING_TOOL_ID]
    elif majors:
        verdict, exit_code = "ITERATE", 1
        evidence_tier = "TOOL_VERIFIED"
        blocking_ids = sorted({f["canonical_id"] for f in majors})
    else:
        verdict, exit_code = "SHIP", 0
        evidence_tier = "TOOL_VERIFIED"
        blocking_ids = []

    result = {
        "suite_id": "verification-eval",
        "gate_policy": args.gate_policy,
        "evidence_tier": evidence_tier,
        "verdict": verdict,
        "exit_code": exit_code,
        "unverified_missing_tool": bool(missing_tool_errors),
        "missing_tool_errors": missing_tool_errors,
        "blocking_ids": blocking_ids,
        "counts": {
            "blocker": len(blockers),
            "major": len(majors),
            "minor": len(minors),
        },
        "evidence": evidence,
        "findings": deduped,
    }
    output_text = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.write_text(output_text, encoding="utf-8")
    else:
        print(output_text)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
