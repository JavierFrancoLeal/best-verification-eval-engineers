---
name: test-execution-oracles
description: >-
  Enforces fail-closed test runner execution (tests_executed > 0), JUnit XML leaf recomputation, and line/branch coverage floors.
license: MIT
compatibility: Python 3.9+ stdlib CPU tools; integrates with pytest, vitest, jest, go test.
metadata:
  schema_version: "1.2.0"
  judgment_schema: "VERIFY.md"
  suite_id: "verification-eval"
  author: "Trasunto / best-verification-eval-engineers"
  clean_room_auditor: "auditor-test-integrity"
---

# Test Execution & Coverage Oracles (`test-execution-oracles`)

## When To Use
- Any PR modifying executable application code, build/test scripts, or JUnit/LCOV/coverage.py reports.
- Verifying that test suites actually executed non-zero test cases without exit-code masking.

## Do Not Use When
- Pure documentation edits with zero executable source or config changes.
- Static SAST/secret scanning (route to security-governance) or architecture boundary checks (route to systems-harness).

## Required Inputs
- Tier A SARIF from tools/verify_cpu_scanner.py.
- Tier B JUnit XML (pytest, vitest, jest, go test) and LCOV or coverage.json.

## Execution & Audit Workflow
1. Run tools/verify_cpu_scanner.py to verify zero runner tamper flags.
2. Ingest JUnit XML and coverage reports via tools/eval_ingest.py; fail closed (exit 3) if tests_executed == 0 or artifacts are missing.
3. Check line (>= 80%) and branch (>= 75%) coverage floors and excluded-line ratio (<= 5%).
4. Escalate diffs adding > 25 net test lines to auditor-test-integrity.

## Verdict & Severity Criteria
- **BLOCKER (`REJECT`):** Any deterministic or Clean-Room `BLOCKER` finding forces `REJECT` (non-compensable).
- **MAJOR (`ITERATE`):** Any unresolved `MAJOR` finding or `UNVERIFIED_MISSING_TOOL` condition prohibits `SHIP`.
- **MINOR (`SHIP` with advisory):** Advisory findings logged without blocking merge.

## Guardrails
- Enforce single-root-cause deduplication per `file:line`.
- Never dilute `MAJOR` findings via score averaging (`score_heuristic: null`).
- Respect Separation of Powers: builder agents must not modify verification oracles or `rules.yaml`.
