#!/usr/bin/env python3
"""Suite-specific deterministic repository validator for best-verification-eval-engineers (v1.2.0).

Enforces ECOSYSTEM_CONTRACT v1.2.0 + HR-1..HR-12:
  1. Immutable SHA-256-pinned ecosystem_core_validator.py (all 7 core checks + coexistence smoke test).
  2. Bijective Anti-Phantom-Rule invariant (VERIFY.md verify_cpu_scanner rules == RULE_META).
  3. Single-Source Severity Parity across RULE_META, VERIFY.md, rules.yaml, manifest.json, and evals.json.
  4. Active context budget <= 25,600 B, BRIEF.md <= 2,600 B, verification-mindset.md <= 6,000 B, 8 dossiers.
  5. Zero-network AST import guard on bundled Python tools & UNVERIFIED_SOURCE citation hygiene.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import jsonschema
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "validators"))
sys.path.insert(0, str(REPO_ROOT / "tools"))
import ecosystem_core_validator as core  # noqa: E402
import verify_cpu_scanner as cpu_scanner  # noqa: E402

EXPECTED_MODULES = [
    "anti-tampering-eval-governance",
    "assertion-mutation-strength",
    "contract-boundary-regressions",
    "determinism-flakiness-isolation",
    "llm-rag-evalops-calibration",
    "property-metamorphic-invariants",
    "test-execution-oracles",
]

EXPECTED_ENGINEERS = [
    "bertrand-meyer",
    "bowen-baker",
    "jeff-offutt",
    "john-hughes",
    "ron-kohavi",
    "tsong-yueh-chen",
    "wei-lin-chiang",
    "will-wilson",
]

REQUIRED_MODULE_H2 = [
    "When To Use",
    "Do Not Use When",
    "Required Inputs",
    "Execution & Audit Workflow",
    "Verdict & Severity Criteria",
    "Guardrails",
]

ALLOWED_SEVS = {"BLOCKER", "MAJOR", "MINOR"}
SEV_RANK = {"BLOCKER": 3, "MAJOR": 2, "MINOR": 1}
CANONICAL_3PART_RE = re.compile(r"^verification-eval:[a-z0-9-]+:[A-Za-z0-9_-]{3,48}$")
FORBIDDEN_NET_MODULES = {
    "socket", "ssl", "http", "urllib", "ftplib", "smtplib",
    "xmlrpc", "asyncio", "requests", "httpx", "aiohttp", "urllib3",
}
UNVERIFIED_YEAR_RE = re.compile(
    r"(?:\b(?:ICLR|EMNLP|MSR|ICML|NeurIPS|ACL)\s+202[56]\b|\barXiv[:\s]*2[56]\d{2}\.\d+|\(202[56]\)|_202[56]\b)"
)


def scanner_smoke_fn(installed_scanner: Path, dest: Path) -> list[str]:
    """Domain smoke check executed inside live coexistence workspace."""
    errors: list[str] = []
    sample = dest / "test_smoke_noassert.py"
    sample.write_text("def test_empty_oracle():\n    x = 1 + 1\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(installed_scanner), "--target", str(sample), "--format", "json"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if proc.returncode != 2:
        errors.append(f"Installed verify_cpu_scanner expected exit 2 on assertion-free test, got {proc.returncode}")
    else:
        data = json.loads(proc.stdout)
        if data.get("counts", {}).get("blocker", 0) < 1:
            errors.append("Installed verify_cpu_scanner returned 0 blockers on assertion-free test")
        cov = data.get("scan_coverage", {})
        if cov.get("files_scanned") != 1 or cov.get("files_skipped", {}).get("total") != 0:
            errors.append(f"Installed verify_cpu_scanner unexpected scan_coverage: {cov}")
    return errors


def check_suite_invariants(suite_data: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if suite_data.get("suite_id") != "verification-eval":
        errors.append(f"suite_id must be 'verification-eval', got {suite_data.get('suite_id')!r}")
    if suite_data.get("director_slug") != "verification-director":
        errors.append(f"director_slug mismatch: {suite_data.get('director_slug')!r}")
    if suite_data.get("judgment_file") != "VERIFY.md":
        errors.append(f"judgment_file must be 'VERIFY.md', got {suite_data.get('judgment_file')!r}")
    if suite_data.get("synthesis_mode") != "conjunctive_gate":
        errors.append("synthesis_mode must be 'conjunctive_gate'")
    if suite_data.get("score_heuristic") is not None:
        errors.append("score_heuristic must be null for conjunctive_gate")
    if suite_data.get("clean_room_required") is not True:
        errors.append("clean_room_required must be true")
    tooling = suite_data.get("tooling", {})
    if tooling.get("fail_closed_on_missing_required_tool") is not True:
        errors.append("tooling.fail_closed_on_missing_required_tool must be true")
    roster = suite_data.get("roster_summary", {})
    if roster.get("total_modules") != 7 or roster.get("auditors") != 2 or roster.get("regimes") != 0:
        errors.append(f"roster_summary mismatch: {roster}")
    return len(errors) == 0, errors


def load_auditor_severity_map() -> tuple[dict[str, str], list[str]]:
    sev_map: dict[str, str] = {}
    errors: list[str] = []
    for rfile in sorted((REPO_ROOT / "committee" / "auditors").glob("*/rules.yaml")):
        doc = yaml.safe_load(rfile.read_text(encoding="utf-8"))
        for r in doc.get("rules", []):
            cid = r.get("canonical_id", "")
            sev = r.get("severity", "")
            if not CANONICAL_3PART_RE.match(cid):
                errors.append(f"{rfile.relative_to(REPO_ROOT)}: invalid canonical_id '{cid}'")
            if sev not in ALLOWED_SEVS:
                errors.append(f"{rfile.relative_to(REPO_ROOT)}: invalid severity '{sev}'")
            sev_map[cid] = sev
    return sev_map, errors


def check_modules_verify_and_phantom_rules(auditor_sev: dict[str, str]) -> tuple[bool, list[str], dict[str, str]]:
    errors: list[str] = []
    all_rule_sev: dict[str, str] = dict(auditor_sev)
    for rid, meta in cpu_scanner.RULE_META.items():
        all_rule_sev[meta["canonical_id"]] = meta["severity"]

    schema = json.loads((REPO_ROOT / "schemas" / "schema_verify.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    actual_modules = sorted(p.name for p in (REPO_ROOT / "modules").iterdir() if p.is_dir())
    if actual_modules != EXPECTED_MODULES:
        errors.append(f"modules/ mismatch expected={EXPECTED_MODULES}, actual={actual_modules}")

    nested_skills = list((REPO_ROOT / "modules").rglob("SKILL.md"))
    if nested_skills:
        errors.append(f"Forbidden nested SKILL.md under modules/: {[str(p.relative_to(REPO_ROOT)) for p in nested_skills]}")

    declared_cpu_refs: set[str] = set()

    for slug in EXPECTED_MODULES:
        mdir = REPO_ROOT / "modules" / slug

        prof = mdir / "PROFILE.md"
        if not prof.is_file():
            errors.append(f"Missing modules/{slug}/PROFILE.md")
        else:
            fm, body = core._parse_frontmatter(prof.read_text(encoding="utf-8"))
            if not fm or fm.get("name") != slug:
                errors.append(f"modules/{slug}/PROFILE.md invalid frontmatter or name != '{slug}'")
            h2s = core._extract_h2(body)
            if h2s != REQUIRED_MODULE_H2:
                errors.append(f"modules/{slug}/PROFILE.md H2 mismatch: {h2s}")

        brief = mdir / "BRIEF.md"
        if not brief.is_file():
            errors.append(f"Missing modules/{slug}/BRIEF.md")
        elif brief.stat().st_size > 2600:
            errors.append(f"modules/{slug}/BRIEF.md exceeds 2,600 B ({brief.stat().st_size} B)")

        vpath = mdir / "VERIFY.md"
        if not vpath.is_file():
            errors.append(f"Missing modules/{slug}/VERIFY.md")
            continue

        fm, _ = core._parse_frontmatter(vpath.read_text(encoding="utf-8"))
        if not fm:
            errors.append(f"modules/{slug}/VERIFY.md missing YAML frontmatter")
            continue

        for err in validator.iter_errors(fm):
            errors.append(f"modules/{slug}/VERIFY.md schema error: {err.message}")
        if fm.get("module_id") != slug:
            errors.append(f"modules/{slug}/VERIFY.md module_id '{fm.get('module_id')}' != '{slug}'")

        src_ids = {s["source_id"] for s in fm.get("authoritative_sources", []) if isinstance(s, dict) and "source_id" in s}

        for idx, rule in enumerate(fm.get("deterministic_rules", [])):
            if rule.get("source_id") not in src_ids:
                errors.append(f"modules/{slug}/VERIFY.md deterministic_rules[{idx}]: unresolved source_id '{rule.get('source_id')}'")
            cid = rule.get("canonical_id", "")
            sev = rule.get("severity", "")
            if not cid.startswith(f"verification-eval:{slug}:"):
                errors.append(f"modules/{slug}/VERIFY.md deterministic_rules[{idx}]: canonical_id prefix mismatch '{cid}'")
            all_rule_sev[cid] = sev

            if rule.get("engine") == "verify_cpu_scanner":
                ref = rule.get("engine_rule_ref", "")
                if ref not in cpu_scanner.RULE_META:
                    errors.append(f"modules/{slug}/VERIFY.md PHANTOM RULE '{ref}' not in verify_cpu_scanner.RULE_META")
                else:
                    declared_cpu_refs.add(ref)
                    meta = cpu_scanner.RULE_META[ref]
                    if rule.get("rule_id") != ref:
                        errors.append(f"modules/{slug}/VERIFY.md rule_id '{rule.get('rule_id')}' != engine_rule_ref '{ref}'")
                    if cid != meta["canonical_id"]:
                        errors.append(f"modules/{slug}/VERIFY.md canonical_id '{cid}' != RULE_META '{meta['canonical_id']}'")
                    if sev != meta["severity"]:
                        errors.append(f"modules/{slug}/VERIFY.md severity '{sev}' != RULE_META '{meta['severity']}'")

        for idx, inv in enumerate(fm.get("semantic_invariants", [])):
            if inv.get("source_id") not in src_ids:
                errors.append(f"modules/{slug}/VERIFY.md semantic_invariants[{idx}]: unresolved source_id '{inv.get('source_id')}'")
            cid = inv.get("canonical_id", "")
            sev = inv.get("severity", "")
            if cid not in auditor_sev:
                errors.append(f"modules/{slug}/VERIFY.md semantic_invariants[{idx}]: unknown auditor rule '{cid}'")
            elif sev != auditor_sev[cid]:
                errors.append(
                    f"modules/{slug}/VERIFY.md semantic_invariants[{idx}]: severity parity mismatch '{sev}' != rules.yaml '{auditor_sev[cid]}' for '{cid}'"
                )

    orphans = sorted(set(cpu_scanner.RULE_META.keys()) - declared_cpu_refs)
    if orphans:
        errors.append(f"Orphaned verify_cpu_scanner.RULE_META rules not declared in any VERIFY.md: {orphans}")

    return len(errors) == 0, errors, all_rule_sev


def check_severity_parity_manifest_and_evals(all_rule_sev: dict[str, str]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    # System-level canonical IDs allowed in evals
    known_sev = dict(all_rule_sev)
    known_sev["verification-eval:tooling:MISSING_REQUIRED_TOOL_EVIDENCE"] = "MAJOR"

    # 1. tests/fixtures/manifest.json
    mpath = REPO_ROOT / "tests" / "fixtures" / "manifest.json"
    if not mpath.is_file():
        errors.append("Missing tests/fixtures/manifest.json")
    else:
        manifest = json.loads(mpath.read_text(encoding="utf-8"))
        for fx in manifest.get("fixtures", []):
            fid = fx.get("fixture_id", "?")
            mod = fx.get("module_id", "")
            if mod not in EXPECTED_MODULES:
                errors.append(f"manifest.json:{fid}: non-canonical module_id '{mod}'")
            cids = fx.get("expected_canonical_ids", [])
            exp_sev = fx.get("expected_severity")
            if fx.get("should_trigger"):
                if not cids:
                    errors.append(f"manifest.json:{fid}: should_trigger=true requires expected_canonical_ids")
                if exp_sev not in ALLOWED_SEVS:
                    errors.append(f"manifest.json:{fid}: invalid expected_severity '{exp_sev}'")
                sevs = []
                for cid in cids:
                    if not CANONICAL_3PART_RE.match(cid):
                        errors.append(f"manifest.json:{fid}: non-3-part canonical_id '{cid}'")
                    elif cid not in known_sev:
                        errors.append(f"manifest.json:{fid}: unknown canonical_id '{cid}'")
                    else:
                        sevs.append(known_sev[cid])
                if sevs:
                    max_sev = max(sevs, key=lambda s: SEV_RANK[s])
                    if exp_sev != max_sev:
                        errors.append(f"manifest.json:{fid}: expected_severity '{exp_sev}' != single-source '{max_sev}'")
            else:
                if cids:
                    errors.append(f"manifest.json:{fid}: negative control must have empty expected_canonical_ids")
                if exp_sev is not None:
                    errors.append(f"manifest.json:{fid}: negative control expected_severity must be null, got {exp_sev!r}")

    # 2. Root evals/evals.json, director evals/evals.json, and all 7 module evals.json
    eval_paths = [
        REPO_ROOT / "evals" / "evals.json",
        REPO_ROOT / "committee" / "verification-director" / "evals" / "evals.json",
    ] + [REPO_ROOT / "modules" / slug / "evals" / "evals.json" for slug in EXPECTED_MODULES]

    for ep in eval_paths:
        rel = str(ep.relative_to(REPO_ROOT))
        if not ep.is_file():
            errors.append(f"Missing {rel}")
            continue
        doc = json.loads(ep.read_text(encoding="utf-8"))
        evals = doc.get("evals", [])
        if rel in ("evals/evals.json", "committee/verification-director/evals/evals.json"):
            if doc.get("skill_name") != "verification-director" or doc.get("schema_version") != "1.2.0":
                errors.append(f"{rel}: skill_name/schema_version mismatch")
            pos = sum(1 for e in evals if e.get("expected_output", {}).get("should_trigger") is True)
            neg = sum(1 for e in evals if e.get("expected_output", {}).get("should_trigger") is False)
            if pos < 3 or neg < 3:
                errors.append(f"{rel}: requires >=3 positive and >=3 negative cases, got pos={pos}, neg={neg}")

        for item in evals:
            eid = item.get("id", "?")
            eo = item.get("expected_output", {})
            for rmod in eo.get("routed_modules", []):
                if rmod not in EXPECTED_MODULES:
                    errors.append(f"{rel}:{eid}: non-canonical routed_module '{rmod}'")
            cids = eo.get("expected_canonical_ids", [])
            exp_sev = eo.get("expected_severity")
            if eo.get("should_trigger"):
                if exp_sev not in ALLOWED_SEVS:
                    errors.append(f"{rel}:{eid}: invalid expected_severity '{exp_sev}'")
                sevs = []
                for cid in cids:
                    if not CANONICAL_3PART_RE.match(cid):
                        errors.append(f"{rel}:{eid}: non-3-part canonical_id '{cid}'")
                    elif cid not in known_sev:
                        errors.append(f"{rel}:{eid}: unknown canonical_id '{cid}'")
                    else:
                        sevs.append(known_sev[cid])
                if sevs:
                    max_sev = max(sevs, key=lambda s: SEV_RANK[s])
                    if exp_sev != max_sev:
                        errors.append(f"{rel}:{eid}: expected_severity '{exp_sev}' != single-source '{max_sev}'")
            elif exp_sev is not None:
                errors.append(f"{rel}:{eid}: negative eval expected_severity must be null, got {exp_sev!r}")

    return len(errors) == 0, errors


def check_context_budget_dossiers_and_hygiene() -> tuple[bool, list[str]]:
    errors: list[str] = []
    active_files = [
        REPO_ROOT / "committee" / "verification-director" / "SKILL.md",
        REPO_ROOT / "committee" / "verification-director" / "control-matrix.yaml",
        REPO_ROOT / "committee" / "auditors" / "auditor-test-integrity" / "AUDITOR.md",
        REPO_ROOT / "committee" / "auditors" / "auditor-evalops-validity" / "AUDITOR.md",
    ] + [REPO_ROOT / "modules" / slug / "BRIEF.md" for slug in EXPECTED_MODULES]

    total_bytes = sum(p.stat().st_size for p in active_files if p.is_file())
    if total_bytes > 25600:
        errors.append(f"Total active operational context {total_bytes} B exceeds 25,600 B ceiling")

    mindset = REPO_ROOT / "docs" / "verification-mindset.md"
    if not mindset.is_file():
        errors.append("Missing docs/verification-mindset.md")
    elif mindset.stat().st_size > 6000:
        errors.append(f"docs/verification-mindset.md exceeds 6,000 B ({mindset.stat().st_size} B)")

    actual_eng = sorted(p.stem for p in (REPO_ROOT / "docs" / "engineers").glob("*.md"))
    if actual_eng != EXPECTED_ENGINEERS:
        errors.append(f"docs/engineers/ mismatch expected={EXPECTED_ENGINEERS}, actual={actual_eng}")

    # Zero-network AST import guard on bundled Python tools
    for tool_name in ("verify_cpu_scanner.py", "eval_ingest.py", "run_verify_benchmark.py"):
        tpath = REPO_ROOT / "tools" / tool_name
        tree = ast.parse(tpath.read_text(encoding="utf-8"), filename=tool_name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    if root_mod in FORBIDDEN_NET_MODULES:
                        errors.append(f"tools/{tool_name}: forbidden network import '{alias.name}'")
            elif isinstance(node, ast.ImportFrom) and node.module:
                root_mod = node.module.split(".")[0]
                if root_mod in FORBIDDEN_NET_MODULES:
                    errors.append(f"tools/{tool_name}: forbidden network import from '{node.module}'")

    # UNVERIFIED_SOURCE citation hygiene across rules.yaml, VERIFY.md, docs/
    hygiene_paths = (
        list((REPO_ROOT / "committee" / "auditors").glob("*/rules.yaml"))
        + list((REPO_ROOT / "docs").rglob("*.md"))
    )
    for hp in hygiene_paths:
        if hp.name == "ECOSYSTEM_CONTRACT.md":
            continue
        rel = str(hp.relative_to(REPO_ROOT))
        for lineno, line in enumerate(hp.read_text(encoding="utf-8").splitlines(), start=1):
            if UNVERIFIED_YEAR_RE.search(line) and "UNVERIFIED_SOURCE" not in line:
                errors.append(f"{rel}:{lineno}: 2025/2026 citation missing explicit UNVERIFIED_SOURCE tag")

    return len(errors) == 0, errors


def main() -> int:
    core_ok, core_results, suite_data = core.run_all_core_checks(REPO_ROOT, scanner_smoke_fn=scanner_smoke_fn)
    suite_results: list[tuple[str, bool, list[str]]] = []

    ok, errs = check_suite_invariants(suite_data)
    suite_results.append(("[Suite] verification-eval v1.2.0 manifest invariants", ok, errs))

    aud_sev, aud_errs = load_auditor_severity_map()
    ok_m, errs_m, all_rule_sev = check_modules_verify_and_phantom_rules(aud_sev)
    suite_results.append(("[Suite] 7 modules, VERIFY.md Draft 2020-12 & anti-phantom-rule bijection", ok_m and not aud_errs, aud_errs + errs_m))

    ok_p, errs_p = check_severity_parity_manifest_and_evals(all_rule_sev)
    suite_results.append(("[Suite] Single-source severity parity (RULE_META/VERIFY/rules/manifest/evals)", ok_p, errs_p))

    ok_c, errs_c = check_context_budget_dossiers_and_hygiene()
    suite_results.append(("[Suite] Active context <=25.6KB, 8 dossiers, zero-net AST & UNVERIFIED_SOURCE", ok_c, errs_c))

    all_results = core_results + suite_results
    all_ok = core_ok and all(p for _, p, _ in suite_results)

    print("=" * 80)
    print("  VERIFICATION-EVAL REPOSITORY VALIDATOR (ECOSYSTEM_CONTRACT v1.2.0)")
    print("=" * 80)
    for label, passed, errs in all_results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {label}")
        for e in errs:
            print(f"         -> {e}")
    print("-" * 80)
    if all_ok:
        print("  ALL CORE + SUITE CHECKS PASSED.")
        return 0
    print("  VALIDATION FAILED.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
