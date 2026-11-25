---
name: determinism-flakiness-isolation
description: >-
  Prevents wall-clock sleeps, unseeded randomness, shared global state, and non-deterministic async races in tests.
license: MIT
compatibility: Python 3.9+ stdlib CPU tools; integrates with pytest, vitest, jest, go test.
metadata:
  schema_version: "1.2.0"
  judgment_schema: "VERIFY.md"
  suite_id: "verification-eval"
  author: "Trasunto / best-verification-eval-engineers"
  clean_room_auditor: "auditor-test-integrity"
---

# Determinism, Hermeticity & Flakiness Isolation (`determinism-flakiness-isolation`)

## When To Use
- Tests introducing timers, sleeps, PRNG calls, concurrency, or clock-dependent logic.
- Investigating flaky CI failures or order-dependent test suites.

## Do Not Use When
- Production observability/alerting on live latency SLOs (out of scope).
- LLM judge statistical noise (route to llm-rag-evalops-calibration).

## Required Inputs
- Tier A verify_cpu_scanner.sarif (VER-FLK-NONDET-001).
- Test source files and async/concurrency test harness configs.

## Execution & Audit Workflow
1. Run tools/verify_cpu_scanner.py to detect wall-clock sleeps (time.sleep, setTimeout without fake timers) and unseeded PRNG calls.
2. Verify deterministic seeds (Hypothesis @seed/derandomize, seeded PRNG) and virtual clocks (vi.useFakeTimers).
3. Invoke auditor-test-integrity (testint-05) on concurrent/distributed tests to check deterministic simulation boundaries.

## Verdict & Severity Criteria
- **BLOCKER (`REJECT`):** Any deterministic or Clean-Room `BLOCKER` finding forces `REJECT` (non-compensable).
- **MAJOR (`ITERATE`):** Any unresolved `MAJOR` finding or `UNVERIFIED_MISSING_TOOL` condition prohibits `SHIP`.
- **MINOR (`SHIP` with advisory):** Advisory findings logged without blocking merge.

## Guardrails
- Enforce single-root-cause deduplication per `file:line`.
- Never dilute `MAJOR` findings via score averaging (`score_heuristic: null`).
- Respect Separation of Powers: builder agents must not modify verification oracles or `rules.yaml`.
