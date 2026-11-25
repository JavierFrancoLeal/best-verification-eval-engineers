---
name: contract-boundary-regressions
description: >-
  Enforces Design-by-Contract preconditions/postconditions, API/schema contract tests, and mandatory negative auth/boundary regression tests.
license: MIT
compatibility: Python 3.9+ stdlib CPU tools; integrates with pytest, vitest, jest, go test.
metadata:
  schema_version: "1.2.0"
  judgment_schema: "VERIFY.md"
  suite_id: "verification-eval"
  author: "Trasunto / best-verification-eval-engineers"
  clean_room_auditor: "auditor-test-integrity"
---

# Contract, Design-by-Contract & Negative Boundary Regressions (`contract-boundary-regressions`)

## When To Use
- PRs modifying API handlers, tenant-scoped endpoints, parsers, schema contracts, or bug fixes.
- Verifying that security/authorization fixes include executable negative (401/403/rejection) regression tests.

## Do Not Use When
- Designing the authorization policy itself (route to security-governance).
- Writing pre-implementation requirements specs (route to spec-context).

## Required Inputs
- Changed API/contract code and corresponding integration/regression test files.
- Tier B JUnit XML confirming negative regression tests executed and passed.

## Execution & Audit Workflow
1. Verify every changed contract or bug fix has a corresponding executable regression test in Tier B JUnit.
2. Invoke auditor-test-integrity (testint-03, testint-04) to verify negative security/boundary test coverage and intact DbC preconditions/postconditions.
3. Escalate missing server-side tenant/authz enforcement to security-governance (Priority 1).

## Verdict & Severity Criteria
- **BLOCKER (`REJECT`):** Any deterministic or Clean-Room `BLOCKER` finding forces `REJECT` (non-compensable).
- **MAJOR (`ITERATE`):** Any unresolved `MAJOR` finding or `UNVERIFIED_MISSING_TOOL` condition prohibits `SHIP`.
- **MINOR (`SHIP` with advisory):** Advisory findings logged without blocking merge.

## Guardrails
- Enforce single-root-cause deduplication per `file:line`.
- Never dilute `MAJOR` findings via score averaging (`score_heuristic: null`).
- Respect Separation of Powers: builder agents must not modify verification oracles or `rules.yaml`.
