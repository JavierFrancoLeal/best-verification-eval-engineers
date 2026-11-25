---
schema_version: 1.2.0
module_id: property-metamorphic-invariants
suite_id: verification-eval
owner_role: Property & Metamorphic Testing Lead
clean_room_auditor: auditor-evalops-validity
deterministic_rules:
- rule_id: VER-PBT-SEED-001
  canonical_id: verification-eval:property-metamorphic-invariants:VER-PBT-SEED-001
  engine: hypothesis
  engine_rule_ref: hypothesis:derandomize_or_seed
  severity: MAJOR
  evidence_tier: TOOL_VERIFIED
  source_id: SRC-CLAESSEN-HUGHES-ICFP-2000
  languages:
  - python
  - typescript
  - javascript
  - go
  predicate: Property-based tests running in CI must execute non-zero examples with
    reproducible seed configuration.
  false_positive_exemption: Dedicated nightly fuzzing jobs explicitly separated from
    PR merge gates.
semantic_invariants:
- invariant_id: INV-CHEN-01
  canonical_id: verification-eval:auditor-evalops-validity:evalops-05
  auditor: auditor-evalops-validity
  severity: MAJOR
  evidence_tier: STATIC_LLM_INFERRED
  statement: Non-oracle ML, RAG, and numerical pipelines must test paired metamorphic
    relations (e.g., irrelevant-context invariance, monotonicity) rather than brittle
    exact-string snapshots.
  failure_signals:
  - RAG/LLM test suite only checks substring presence on 3 hardcoded prompts with
    zero follow-up metamorphic perturbations.
  why_not_tier_a: Determining whether a metamorphic relation is semantically valid
    and non-trivial for the target domain requires human/LLM domain reasoning.
  source_id: SRC-XIE-CHEN-JSS-2011
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
- source_id: SRC-CLAESSEN-HUGHES-ICFP-2000
  title: 'QuickCheck: A Lightweight Tool for Random Testing of Haskell Programs (ICFP
    2000)'
  citation_type: PEER_REVIEWED_PAPER
  identifier: doi:10.1145/351240.351266
  year: 2000
- source_id: SRC-XIE-CHEN-JSS-2011
  title: Testing and Validating Machine Learning Classifiers by Metamorphic Testing
    (JSS 2011)
  citation_type: PEER_REVIEWED_PAPER
  identifier: doi:10.1016/j.jss.2010.11.920
  year: 2011
---

# Property-Based & Metamorphic Invariants (`VERIFY.md`)

## Operational Contract
This module operates under `conjunctive_gate` synthesis (`ECOSYSTEM_CONTRACT v1.2.0`). Deterministic CPU rules execute first (`TOOL_VERIFIED`), followed by read-only Clean-Room semantic auditing via `auditor-evalops-validity` (`STATIC_LLM_INFERRED`).

## Failure Modes & Remediation
1. Remediate all `BLOCKER` findings before merge (`REJECT` is non-compensable).
2. Resolve `MAJOR` findings or supply a time-bounded independent human signoff (`approver != pr_author`).
3. Never weaken assertions, zero coverage/mutation thresholds, or bypass CI gates to manufacture `SHIP`.
