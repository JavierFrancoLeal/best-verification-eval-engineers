---
name: assertion-mutation-strength
description: >-
  Eliminates assertion-free tests, tautological constant assertions, exception-swallowing handlers, and low mutation kill rates.
license: MIT
compatibility: Python 3.9+ stdlib CPU tools; integrates with pytest, vitest, jest, go test.
metadata:
  schema_version: "1.2.0"
  judgment_schema: "VERIFY.md"
  suite_id: "verification-eval"
  author: "Trasunto / best-verification-eval-engineers"
  clean_room_auditor: "auditor-test-integrity"
---

# Assertion & Mutation Fault-Detection Strength (`assertion-mutation-strength`)

## When To Use
- Any PR adding or modifying unit/integration test files in Python, TypeScript/JavaScript, or Go.
- Auditing mutation testing reports (mutmut, Stryker, Gremlins) or checking for test theater.

## Do Not Use When
- Flakiness/timer isolation without assertion changes (route to determinism-flakiness-isolation).
- LLM judge statistical calibration (route to llm-rag-evalops-calibration).

## Required Inputs
- Tier A verify_cpu_scanner.sarif (VER-TAU-NOASSERT-001, VER-TAU-CONST-001, VER-TAU-SWALLOW-001).
- Tier B mutation JSON (Stryker, mutmut, or Gremlins) when available.

## Execution & Audit Workflow
1. Run tools/verify_cpu_scanner.py to block assertion-free tests, tautologies, and swallowed exceptions.
2. Ingest Stryker/mutmut/Gremlins JSON via tools/eval_ingest.py against the 65% diff mutation floor.
3. Run auditor-test-integrity (testint-01, testint-02, testint-06) to catch tautological oracles mirroring buggy code.

## Verdict & Severity Criteria
- **BLOCKER (`REJECT`):** Any deterministic or Clean-Room `BLOCKER` finding forces `REJECT` (non-compensable).
- **MAJOR (`ITERATE`):** Any unresolved `MAJOR` finding or `UNVERIFIED_MISSING_TOOL` condition prohibits `SHIP`.
- **MINOR (`SHIP` with advisory):** Advisory findings logged without blocking merge.

## Guardrails
- Enforce single-root-cause deduplication per `file:line`.
- Never dilute `MAJOR` findings via score averaging (`score_heuristic: null`).
- Respect Separation of Powers: builder agents must not modify verification oracles or `rules.yaml`.
