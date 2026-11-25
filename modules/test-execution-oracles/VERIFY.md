---
schema_version: 1.2.0
module_id: test-execution-oracles
suite_id: verification-eval
owner_role: Verification Execution Oracle Lead
clean_room_auditor: auditor-test-integrity
deterministic_rules:
- rule_id: VER-EXE-NONZERO-001
  canonical_id: verification-eval:test-execution-oracles:VER-EXE-NONZERO-001
  engine: eval_ingest
  engine_rule_ref: parse_junit_xml:tests_executed_gt_0
  severity: BLOCKER
  evidence_tier: TOOL_VERIFIED
  source_id: SRC-PYTEST-EXIT
  languages:
  - python
  - typescript
  - javascript
  - go
  predicate: JUnit XML must parse cleanly without DOCTYPE/ENTITY and report tests_executed
    > 0 with failed == 0 and errors == 0.
  false_positive_exemption: Documentation-only PRs with zero executable code changes.
- rule_id: VER-EXE-COVFLOOR-001
  canonical_id: verification-eval:test-execution-oracles:VER-EXE-COVFLOOR-001
  engine: coverage_py
  engine_rule_ref: eval_ingest:min_line_branch_coverage
  severity: MAJOR
  evidence_tier: TOOL_VERIFIED
  source_id: SRC-INOZEMTSEVA-ICSE-2014
  languages:
  - python
  - typescript
  - javascript
  - go
  predicate: Line coverage >= 80%, branch coverage >= 75%, and excluded_ratio <= 5%.
  false_positive_exemption: Temporary waiver with independent human signoff (approver
    != pr_author).
semantic_invariants:
- invariant_id: INV-OFFUTT-02
  canonical_id: verification-eval:auditor-test-integrity:testint-02
  auditor: auditor-test-integrity
  severity: MAJOR
  evidence_tier: STATIC_LLM_INFERRED
  statement: Unit tests must exercise the real system under test rather than mocking
    the SUT method itself and asserting mocked outputs.
  failure_signals:
  - SUT class/method patched via unittest.mock or vi.spyOn and asserted against mock
    return value.
  why_not_tier_a: Distinguishing legitimate external dependency stubs from self-mocked
    SUT behavior requires semantic symbol resolution across diff hunks.
  source_id: SRC-OFFUTT-TOSEM-1992
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
- source_id: SRC-PYTEST-EXIT
  title: 'pytest Exit Codes Specification (Exit Code 5: No Tests Collected)'
  citation_type: OFFICIAL_DOCS
  identifier: https://docs.pytest.org/en/stable/reference/exit-codes.html
  year: 2024
- source_id: SRC-INOZEMTSEVA-ICSE-2014
  title: Coverage Is Not Strongly Correlated with Test Suite Effectiveness (ICSE 2014)
  citation_type: PEER_REVIEWED_PAPER
  identifier: doi:10.1145/2568225.2568271
  year: 2014
- source_id: SRC-OFFUTT-TOSEM-1992
  title: Investigations of the Software Testing Coupling Effect (ACM TOSEM 1992)
  citation_type: PEER_REVIEWED_PAPER
  identifier: doi:10.1145/125489.125473
  year: 1992
---

# Test Execution & Coverage Oracles (`VERIFY.md`)

## Operational Contract
This module operates under `conjunctive_gate` synthesis (`ECOSYSTEM_CONTRACT v1.2.0`). Deterministic CPU rules execute first (`TOOL_VERIFIED`), followed by read-only Clean-Room semantic auditing via `auditor-test-integrity` (`STATIC_LLM_INFERRED`).

## Failure Modes & Remediation
1. Remediate all `BLOCKER` findings before merge (`REJECT` is non-compensable).
2. Resolve `MAJOR` findings or supply a time-bounded independent human signoff (`approver != pr_author`).
3. Never weaken assertions, zero coverage/mutation thresholds, or bypass CI gates to manufacture `SHIP`.
