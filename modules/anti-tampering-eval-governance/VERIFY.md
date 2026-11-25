---
schema_version: 1.2.0
module_id: anti-tampering-eval-governance
suite_id: verification-eval
owner_role: Verification Governance & Anti-Tampering Lead
clean_room_auditor: auditor-test-integrity
deterministic_rules:
- rule_id: VER-GOV-SKIP-001
  canonical_id: verification-eval:anti-tampering-eval-governance:VER-GOV-SKIP-001
  engine: verify_cpu_scanner
  engine_rule_ref: VER-GOV-SKIP-001
  severity: MAJOR
  evidence_tier: TOOL_VERIFIED
  source_id: SRC-NIST-800-53-AC5
  languages:
  - python
  - typescript
  - javascript
  - go
  - yaml
  predicate: 'Skipped tests (@pytest.mark.skip, it.skip, t.Skip) require both an issue
    ticket (#123/KEY-1) and YYYY-MM-DD expiry; CI continue-on-error: true requires
    a downstream steps.<id>.outcome gate.'
  false_positive_exemption: Tracked skips carrying both issue ticket and ISO YYYY-MM-DD
    expiry, or pytest.mark.xfail(strict=True).
- rule_id: VER-GOV-TAMPER-001
  canonical_id: verification-eval:anti-tampering-eval-governance:VER-GOV-TAMPER-001
  engine: verify_cpu_scanner
  engine_rule_ref: VER-GOV-TAMPER-001
  severity: BLOCKER
  evidence_tier: TOOL_VERIFIED
  source_id: SRC-NIST-800-53-AC5
  languages:
  - python
  - typescript
  - javascript
  - yaml
  - json
  - toml
  - markdown
  predicate: Forbid --passWithNoTests, --no-cov, || true exit masking, fail_under=0,
    zeroed coverage/Stryker thresholds, >3 suppression pragmas, sys.exit(0) in tests,
    and write/edit tools in Clean-Room AUDITOR.md.
  false_positive_exemption: Explicit --passWithNoTests=false or non-auditor markdown
    documentation.
semantic_invariants:
- invariant_id: INV-BAKER-01
  canonical_id: verification-eval:auditor-test-integrity:testint-07
  auditor: auditor-test-integrity
  severity: BLOCKER
  evidence_tier: STATIC_LLM_INFERRED
  statement: Builder agents must not modify test oracles, fixtures, validators, or
    CI gates in the same diff to manufacture a passing verdict without independent
    review.
  failure_signals:
  - Builder weakens test assertions or edits fixture expected outputs to match broken
    implementation output.
  why_not_tier_a: Recognizing semantic reward-hacking intent across paired production
    and test hunks requires Clean-Room reasoning.
  source_id: SRC-BAKER-OPENAI-2025
- invariant_id: INV-BAKER-02
  canonical_id: verification-eval:auditor-evalops-validity:evalops-04
  auditor: auditor-evalops-validity
  severity: BLOCKER
  evidence_tier: STATIC_LLM_INFERRED
  statement: Builder or prompt-tuning agents must not edit holdout manifests, grader
    rubrics, or evaluation thresholds to inflate benchmark scores.
  failure_signals:
  - Eval harness prompt or rubric edited to award partial credit to previously failing
    outputs.
  why_not_tier_a: Detecting subtle rubric relaxation or reward hacking in natural-language
    judge prompts cannot be done by static regexes.
  source_id: SRC-BAKER-OPENAI-2025
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
- source_id: SRC-NIST-800-53-AC5
  title: NIST SP 800-53 Rev. 5 — AC-5 Separation of Duties
  citation_type: STANDARD
  identifier: NIST SP 800-53 Rev. 5
  year: 2020
- source_id: SRC-BAKER-OPENAI-2025
  title: Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation
    (UNVERIFIED_SOURCE)
  citation_type: UNVERIFIED_SOURCE
  identifier: UNVERIFIED_SOURCE:BAKER_OPENAI_2025
  year: 2025
---

# Anti-Tampering, Separation of Powers & CI Gate Governance (`VERIFY.md`)

## Operational Contract
This module operates under `conjunctive_gate` synthesis (`ECOSYSTEM_CONTRACT v1.2.0`). Deterministic CPU rules execute first (`TOOL_VERIFIED`), followed by read-only Clean-Room semantic auditing via `auditor-test-integrity` (`STATIC_LLM_INFERRED`).

## Failure Modes & Remediation
1. Remediate all `BLOCKER` findings before merge (`REJECT` is non-compensable).
2. Resolve `MAJOR` findings or supply a time-bounded independent human signoff (`approver != pr_author`).
3. Never weaken assertions, zero coverage/mutation thresholds, or bypass CI gates to manufacture `SHIP`.
