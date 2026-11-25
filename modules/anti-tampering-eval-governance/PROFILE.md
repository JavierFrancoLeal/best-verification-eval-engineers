---
name: anti-tampering-eval-governance
description: >-
  Blocks CI continue-on-error bypasses, untracked test skips, zeroed coverage/mutation thresholds, write-enabled auditors, and self-approval tampering.
license: MIT
compatibility: Python 3.9+ stdlib CPU tools; integrates with pytest, vitest, jest, go test.
metadata:
  schema_version: "1.2.0"
  judgment_schema: "VERIFY.md"
  suite_id: "verification-eval"
  author: "Trasunto / best-verification-eval-engineers"
  clean_room_auditor: "auditor-test-integrity"
---

# Anti-Tampering, Separation of Powers & CI Gate Governance (`anti-tampering-eval-governance`)

## When To Use
- PRs touching .github/workflows/*, pytest/vitest/jest/stryker configs, Clean-Room AUDITOR.md files, or skipped tests.
- Validating human signoff waivers (approver != pr_author) and Separation of Powers.

## Do Not Use When
- General CI/CD secret exposure or workflow injection vulnerabilities (route to security-governance).

## Required Inputs
- Tier A verify_cpu_scanner.sarif (VER-GOV-SKIP-001, VER-GOV-TAMPER-001).
- Tier B --human-signoff / --verify-envelope JSON and --pr-author handle.

## Execution & Audit Workflow
1. Run tools/verify_cpu_scanner.py to detect untracked skips, continue-on-error bypasses, zeroed thresholds, mass pragmas, and write-enabled auditors.
2. Run tools/eval_ingest.py --verify-envelope --pr-author to enforce approver != pr_author on human signoffs.
3. Invoke auditor-test-integrity (testint-07) and auditor-evalops-validity (evalops-04) whenever a builder touches verification/eval governance artifacts.

## Verdict & Severity Criteria
- **BLOCKER (`REJECT`):** Any deterministic or Clean-Room `BLOCKER` finding forces `REJECT` (non-compensable).
- **MAJOR (`ITERATE`):** Any unresolved `MAJOR` finding or `UNVERIFIED_MISSING_TOOL` condition prohibits `SHIP`.
- **MINOR (`SHIP` with advisory):** Advisory findings logged without blocking merge.

## Guardrails
- Enforce single-root-cause deduplication per `file:line`.
- Never dilute `MAJOR` findings via score averaging (`score_heuristic: null`).
- Respect Separation of Powers: builder agents must not modify verification oracles or `rules.yaml`.
