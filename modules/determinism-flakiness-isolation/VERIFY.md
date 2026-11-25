---
schema_version: 1.2.0
module_id: determinism-flakiness-isolation
suite_id: verification-eval
owner_role: Determinism & Simulation Lead
clean_room_auditor: auditor-test-integrity
deterministic_rules:
- rule_id: VER-FLK-NONDET-001
  canonical_id: verification-eval:determinism-flakiness-isolation:VER-FLK-NONDET-001
  engine: verify_cpu_scanner
  engine_rule_ref: VER-FLK-NONDET-001
  severity: MAJOR
  evidence_tier: TOOL_VERIFIED
  source_id: SRC-LUO-FSE-2014
  languages:
  - python
  - typescript
  - javascript
  - go
  predicate: Forbid non-zero time.sleep/asyncio.sleep/time.Sleep, setTimeout without
    fake timers, and unseeded random.*/Math.random() in tests.
  false_positive_exemption: Tests using vi.useFakeTimers()/jest.useFakeTimers(), seeded
    local PRNG instances, or asyncio.sleep(0) event-loop yields.
semantic_invariants:
- invariant_id: INV-WILSON-01
  canonical_id: verification-eval:auditor-test-integrity:testint-05
  auditor: auditor-test-integrity
  severity: MAJOR
  evidence_tier: STATIC_LLM_INFERRED
  statement: Concurrency, retry, and distributed state tests must control virtual
    time, fault injection, and execution ordering deterministically.
  failure_signals:
  - Race-condition tests relying on live OS thread scheduling, shared mutable module
    globals, or unbounded network/port bindings.
  why_not_tier_a: Hidden shared state and non-deterministic scheduling assumptions
    across helper modules cannot be reliably proved via single-file AST scans.
  source_id: SRC-ZHOU-WILSON-SIGMOD-2021
calibration_contract:
  layer_1_synthetic_fixture_regression_floor:
    enabled: true
    min_positive_fixtures: 1
    min_negative_fixtures: 1
    min_deterministic_recall: 1.0
    max_deterministic_fpr: 0.0
    production_claim_prohibited: true
  layer_2_calibrated_holdout_eval:
    required: false
    estimator: wilson_score_only
    confidence_level: 0.95
authoritative_sources:
- source_id: SRC-LUO-FSE-2014
  title: An Empirical Analysis of Flaky Tests (FSE 2014)
  citation_type: PEER_REVIEWED_PAPER
  identifier: doi:10.1145/2635868.2635920
  year: 2014
- source_id: SRC-ZHOU-WILSON-SIGMOD-2021
  title: 'FoundationDB: A Distributed Unbundled Transactional Key Value Store (SIGMOD
    2021)'
  citation_type: PEER_REVIEWED_PAPER
  identifier: doi:10.1145/3448016.3457559
  year: 2021
---

# Determinism, Hermeticity & Flakiness Isolation (`VERIFY.md`)

## Operational Contract
This module operates under `conjunctive_gate` synthesis (`ECOSYSTEM_CONTRACT v1.2.0`). Deterministic CPU rules execute first (`TOOL_VERIFIED`), followed by read-only Clean-Room semantic auditing via `auditor-test-integrity` (`STATIC_LLM_INFERRED`).

## Failure Modes & Remediation
1. Remediate all `BLOCKER` findings before merge (`REJECT` is non-compensable).
2. Resolve `MAJOR` findings or supply a time-bounded independent human signoff (`approver != pr_author`).
3. Never weaken assertions, zero coverage/mutation thresholds, or bypass CI gates to manufacture `SHIP`.
