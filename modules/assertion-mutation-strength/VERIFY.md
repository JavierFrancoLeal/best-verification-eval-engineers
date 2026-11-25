---
schema_version: 1.2.0
module_id: assertion-mutation-strength
suite_id: verification-eval
owner_role: Mutation & Oracle Strength Lead
clean_room_auditor: auditor-test-integrity
deterministic_rules:
- rule_id: VER-TAU-NOASSERT-001
  canonical_id: verification-eval:assertion-mutation-strength:VER-TAU-NOASSERT-001
  engine: verify_cpu_scanner
  engine_rule_ref: VER-TAU-NOASSERT-001
  severity: BLOCKER
  evidence_tier: TOOL_VERIFIED
  source_id: SRC-AMMANN-OFFUTT-2017
  languages:
  - python
  - typescript
  - javascript
  - go
  predicate: Every test function/block must contain at least one executable assertion,
    expected-exception context, or assertion-bearing helper call.
  false_positive_exemption: Non-test helper functions or fixtures not prefixed with
    test_/Test.
- rule_id: VER-TAU-CONST-001
  canonical_id: verification-eval:assertion-mutation-strength:VER-TAU-CONST-001
  engine: verify_cpu_scanner
  engine_rule_ref: VER-TAU-CONST-001
  severity: BLOCKER
  evidence_tier: TOOL_VERIFIED
  source_id: SRC-JUST-FSE-2014
  languages:
  - python
  - typescript
  - javascript
  predicate: Forbid constant-true assertions (assert True, expect(true).toBe(true)),
    reflexive x == x checks, and len(x) >= 0 tautologies.
  false_positive_exemption: None; tautological assertions must be replaced with behavioral
    checks.
- rule_id: VER-TAU-SWALLOW-001
  canonical_id: verification-eval:assertion-mutation-strength:VER-TAU-SWALLOW-001
  engine: verify_cpu_scanner
  engine_rule_ref: VER-TAU-SWALLOW-001
  severity: BLOCKER
  evidence_tier: TOOL_VERIFIED
  source_id: SRC-AMMANN-OFFUTT-2017
  languages:
  - python
  - typescript
  - javascript
  predicate: 'Forbid broad except Exception: pass, bare except: ..., and empty catch
    {} blocks inside test functions.'
  false_positive_exemption: Explicit pytest.raises / expect().toThrow() expected-exception
    assertions.
- rule_id: VER-MUT-SCORE-001
  canonical_id: verification-eval:assertion-mutation-strength:VER-MUT-SCORE-001
  engine: mutmut
  engine_rule_ref: eval_ingest:min_mutation_score_65
  severity: MAJOR
  evidence_tier: TOOL_VERIFIED
  source_id: SRC-PETROVIC-TSE-2022
  languages:
  - python
  - typescript
  - javascript
  - go
  predicate: Diff-scoped mutation kill score >= 65% with zero Pending mutants in Stryker/mutmut/Gremlins
    reports.
  false_positive_exemption: Documented equivalent mutants verified by human steward.
semantic_invariants:
- invariant_id: INV-OFFUTT-01
  canonical_id: verification-eval:auditor-test-integrity:testint-01
  auditor: auditor-test-integrity
  severity: BLOCKER
  evidence_tier: STATIC_LLM_INFERRED
  statement: Test oracles must derive expected outcomes from independent specifications
    rather than duplicating the SUT's implementation formula.
  failure_signals:
  - Test recomputes expected value by copying the exact arithmetic or branching logic
    from the changed production function.
  why_not_tier_a: AST checks see valid assert actual == expected syntax and cannot
    prove whether expected mirrors a buggy SUT formula.
  source_id: SRC-AMMANN-OFFUTT-2017
- invariant_id: INV-OFFUTT-03
  canonical_id: verification-eval:auditor-test-integrity:testint-06
  auditor: auditor-test-integrity
  severity: MAJOR
  evidence_tier: STATIC_LLM_INFERRED
  statement: Assertions on critical state transitions must verify output state and
    side effects strongly enough to kill boundary/relational mutants.
  failure_signals:
  - Assertions only check truthiness or non-null status on financial, parser, or authorization
    outputs.
  why_not_tier_a: Assessing whether an assertion's precision matches domain fault
    sensitivity requires semantic understanding of the SUT contract.
  source_id: SRC-OFFUTT-TOSEM-1996
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
- source_id: SRC-AMMANN-OFFUTT-2017
  title: Introduction to Software Testing (2nd ed., Cambridge University Press)
  citation_type: BOOK
  identifier: ISBN 978-1-107-17201-2
  year: 2017
- source_id: SRC-JUST-FSE-2014
  title: Are Mutants a Valid Substitute for Real Faults in Software Testing? (FSE
    2014)
  citation_type: PEER_REVIEWED_PAPER
  identifier: doi:10.1145/2635868.2635929
  year: 2014
- source_id: SRC-PETROVIC-TSE-2022
  title: 'Practical Mutation Testing at Scale: A View from Google (IEEE TSE 2022)'
  citation_type: PEER_REVIEWED_PAPER
  identifier: doi:10.1109/TSE.2021.3107634
  year: 2022
- source_id: SRC-OFFUTT-TOSEM-1992
  title: Investigations of the Software Testing Coupling Effect (ACM TOSEM 1992)
  citation_type: PEER_REVIEWED_PAPER
  identifier: doi:10.1145/125489.125473
  year: 1992
- source_id: SRC-OFFUTT-TOSEM-1996
  title: An Experimental Determination of Sufficient Mutant Operators (ACM TOSEM 1996)
  citation_type: PEER_REVIEWED_PAPER
  identifier: doi:10.1145/227607.227610
  year: 1996
---

# Assertion & Mutation Fault-Detection Strength (`VERIFY.md`)

## Operational Contract
This module operates under `conjunctive_gate` synthesis (`ECOSYSTEM_CONTRACT v1.2.0`). Deterministic CPU rules execute first (`TOOL_VERIFIED`), followed by read-only Clean-Room semantic auditing via `auditor-test-integrity` (`STATIC_LLM_INFERRED`).

## Failure Modes & Remediation
1. Remediate all `BLOCKER` findings before merge (`REJECT` is non-compensable).
2. Resolve `MAJOR` findings or supply a time-bounded independent human signoff (`approver != pr_author`).
3. Never weaken assertions, zero coverage/mutation thresholds, or bypass CI gates to manufacture `SHIP`.
