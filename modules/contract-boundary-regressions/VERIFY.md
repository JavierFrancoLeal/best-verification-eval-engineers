---
schema_version: 1.2.0
module_id: contract-boundary-regressions
suite_id: verification-eval
owner_role: Boundary & Contract Regression Lead
clean_room_auditor: auditor-test-integrity
deterministic_rules:
- rule_id: VER-CON-REGRESS-001
  canonical_id: verification-eval:contract-boundary-regressions:VER-CON-REGRESS-001
  engine: pytest
  engine_rule_ref: eval_ingest:junit_contract_regression_pass
  severity: BLOCKER
  evidence_tier: TOOL_VERIFIED
  source_id: SRC-MEYER-OOSC2-1997
  languages:
  - python
  - typescript
  - javascript
  - go
  predicate: All contract and boundary regression test suites must execute with zero
    failures and zero errors.
  false_positive_exemption: None; failing contract regressions block merge.
semantic_invariants:
- invariant_id: INV-HUGHES-01
  canonical_id: verification-eval:auditor-test-integrity:testint-03
  auditor: auditor-test-integrity
  severity: BLOCKER
  evidence_tier: STATIC_LLM_INFERRED
  statement: Changes to authentication, tenant isolation, input validation, or state-machine
    transitions must include negative/adversarial regression tests exercising rejection
    paths (401/403/400).
  failure_signals:
  - Tenant-scoped endpoint tests only cover 200 OK happy paths and omit cross-tenant
    403/401 rejection tests.
  why_not_tier_a: AST scanners cannot know which endpoints enforce tenant ownership
    or require negative authorization regression tests.
  source_id: SRC-HUGHES-LNCS-2016
- invariant_id: INV-MEYER-01
  canonical_id: verification-eval:auditor-test-integrity:testint-04
  auditor: auditor-test-integrity
  severity: BLOCKER
  evidence_tier: STATIC_LLM_INFERRED
  statement: PR diffs must not silently weaken existing Design-by-Contract assertions,
    postconditions, or expected-error invariants to make failing tests pass.
  failure_signals:
  - Existing assertion narrowed from exact equality to loose truthiness or expected
    exception assertion deleted alongside SUT change.
  why_not_tier_a: Distinguishing an intentional breaking contract update from silent
    assertion weakening requires semantic diff analysis.
  source_id: SRC-MEYER-OOSC2-1997
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
- source_id: SRC-MEYER-OOSC2-1997
  title: Object-Oriented Software Construction (2nd ed., Prentice Hall)
  citation_type: BOOK
  identifier: ISBN 978-0-13-629155-8
  year: 1997
- source_id: SRC-HUGHES-LNCS-2016
  title: 'Experiences with QuickCheck: Testing the Hard Stuff and Staying Sane (LNCS
    9600, 2016)'
  citation_type: PEER_REVIEWED_PAPER
  identifier: doi:10.1007/978-3-319-30936-1_9
  year: 2016
---

# Contract, Design-by-Contract & Negative Boundary Regressions (`VERIFY.md`)

## Operational Contract
This module operates under `conjunctive_gate` synthesis (`ECOSYSTEM_CONTRACT v1.2.0`). Deterministic CPU rules execute first (`TOOL_VERIFIED`), followed by read-only Clean-Room semantic auditing via `auditor-test-integrity` (`STATIC_LLM_INFERRED`).

## Failure Modes & Remediation
1. Remediate all `BLOCKER` findings before merge (`REJECT` is non-compensable).
2. Resolve `MAJOR` findings or supply a time-bounded independent human signoff (`approver != pr_author`).
3. Never weaken assertions, zero coverage/mutation thresholds, or bypass CI gates to manufacture `SHIP`.
