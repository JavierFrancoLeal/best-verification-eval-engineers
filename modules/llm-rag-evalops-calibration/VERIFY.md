---
schema_version: 1.2.0
module_id: llm-rag-evalops-calibration
suite_id: verification-eval
owner_role: EvalOps Statistical Calibration Lead
clean_room_auditor: auditor-evalops-validity
deterministic_rules:
- rule_id: VER-EVAL-UNCAL-001
  canonical_id: verification-eval:llm-rag-evalops-calibration:VER-EVAL-UNCAL-001
  engine: verify_cpu_scanner
  engine_rule_ref: VER-EVAL-UNCAL-001
  severity: MAJOR
  evidence_tier: TOOL_VERIFIED
  source_id: SRC-ROGAN-GLADEN-1978
  languages:
  - python
  - json
  - yaml
  predicate: 'Accuracy/precision/recall/pass_rate claims must include Layer 2 holdout
    calibration metadata (n_pos >= 100, n_neg >= 100, 95% CI, Youden J) or declare
    layer_1_synthetic_fixture_regression_floor with production_claim_prohibited: true.'
  false_positive_exemption: 'Layer 1 synthetic regression benchmarks explicitly marked
    production_claim_prohibited: true.'
semantic_invariants:
- invariant_id: INV-CHIANG-02
  canonical_id: verification-eval:auditor-evalops-validity:evalops-01
  auditor: auditor-evalops-validity
  severity: BLOCKER
  evidence_tier: STATIC_LLM_INFERRED
  statement: Prompt-tuning, few-shot selection, or hyperparameter optimization loops
    must remain strictly disjoint from reported holdout evaluation splits.
  failure_signals:
  - Prompt selection loop iterates over the same eval_cases list later reported as
    final release accuracy.
  why_not_tier_a: Dataflow contamination across prompt-tuning scripts and dataset
    loaders requires semantic trace analysis.
  source_id: SRC-YANG-CHIANG-2023
- invariant_id: INV-CHIANG-01
  canonical_id: verification-eval:auditor-evalops-validity:evalops-02
  auditor: auditor-evalops-validity
  severity: BLOCKER
  evidence_tier: STATIC_LLM_INFERRED
  statement: Pairwise LLM-as-a-Judge harnesses must use a distinct cross-family judge
    model, randomize/swap slot ordering, and calibrate against human labels.
  failure_signals:
  - Candidate model family judges its own outputs in fixed Slot-A order without position
    swapping.
  why_not_tier_a: Recognizing model family identity and asymmetric prompt slot ordering
    requires semantic inspection.
  source_id: SRC-ZHENG-CHIANG-NEURIPS-2023
- invariant_id: INV-KOHAVI-02
  canonical_id: verification-eval:auditor-evalops-validity:evalops-03
  auditor: auditor-evalops-validity
  severity: BLOCKER
  evidence_tier: STATIC_LLM_INFERRED
  statement: Defect or pass prevalence estimated by an imperfect judge (Se < 1 or
    Sp < 1) must apply Rogan-Gladen adjustment and propagate calibration uncertainty.
  failure_signals:
  - Raw judge positive rate reported directly as true production defect rate without
    Se/Sp correction.
  why_not_tier_a: Verifying whether reported statistics correctly propagate judge
    sensitivity/specificity requires mathematical semantic review.
  source_id: SRC-KOHAVI-TANG-XU-2020
- invariant_id: INV-KOHAVI-01
  canonical_id: verification-eval:auditor-evalops-validity:evalops-06
  auditor: auditor-evalops-validity
  severity: MAJOR
  evidence_tier: STATIC_LLM_INFERRED
  statement: Evaluation claims must report finite-sample confidence intervals (Wilson/Clopper-Pearson)
    and prohibit significance claims from underpowered samples.
  failure_signals:
  - Point-estimate comparison between two models on n < 30 prompts with no confidence
    interval or paired test.
  why_not_tier_a: Evaluating statistical power and multiple-comparison validity requires
    semantic methodology inspection.
  source_id: SRC-KOHAVI-IJCAI-1995
- invariant_id: INV-CHIANG-03
  canonical_id: verification-eval:auditor-evalops-validity:evalops-07
  auditor: auditor-evalops-validity
  severity: MAJOR
  evidence_tier: STATIC_LLM_INFERRED
  statement: Pairwise arena/Bradley-Terry win-rate rankings must not be extrapolated
    to domain-specific production accuracy without domain-stratified calibration.
  failure_signals:
  - General-purpose leaderboard Elo/win-rate cited as sufficient release gate for
    specialized production task.
  why_not_tier_a: Detecting invalid benchmark-to-domain transfer claims requires semantic
    review of evaluation rationale.
  source_id: SRC-LI-CHIANG-ICML-2025
calibration_contract:
  layer_1_synthetic_fixture_regression_floor:
    enabled: true
    min_positive_fixtures: 1
    min_negative_fixtures: 1
    min_deterministic_recall: 1.0
    max_deterministic_fpr: 0.0
    production_claim_prohibited: true
  layer_2_calibrated_holdout_eval:
    required: true
    estimator: rogan_gladen_lang_reiczigel
    confidence_level: 0.95
    min_holdout_per_class: 100
    min_youden_j: 0.6
    max_ci_half_width: 0.1
    holdout_leakage_prohibited: true
    requires_human_signoff_on_holdout_change: true
authoritative_sources:
- source_id: SRC-ROGAN-GLADEN-1978
  title: Estimating Prevalence from the Results of a Screening Test (Am J Epidemiol
    1978)
  citation_type: PEER_REVIEWED_PAPER
  identifier: doi:10.1093/oxfordjournals.aje.a112510
  year: 1978
- source_id: SRC-YANG-CHIANG-2023
  title: Rethinking Benchmark and Contamination for Language Models like Rewritten
    Samples (arXiv 2023)
  citation_type: PEER_REVIEWED_PAPER
  identifier: https://arxiv.org/abs/2311.01964
  year: 2023
- source_id: SRC-ZHENG-CHIANG-NEURIPS-2023
  title: Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena (NeurIPS 2023)
  citation_type: PEER_REVIEWED_PAPER
  identifier: https://arxiv.org/abs/2306.05685
  year: 2023
- source_id: SRC-KOHAVI-TANG-XU-2020
  title: Trustworthy Online Controlled Experiments (Cambridge University Press)
  citation_type: BOOK
  identifier: ISBN 978-1-108-72426-5
  year: 2020
- source_id: SRC-KOHAVI-IJCAI-1995
  title: A Study of Cross-Validation and Bootstrap for Accuracy Estimation and Model
    Selection (IJCAI 1995)
  citation_type: PEER_REVIEWED_PAPER
  identifier: https://www.ijcai.org/Proceedings/95-2/Papers/016.pdf
  year: 1995
- source_id: SRC-LI-CHIANG-ICML-2025
  title: Arena-Hard / Crowdsourced LLM Evaluation Calibration (UNVERIFIED_SOURCE)
  citation_type: UNVERIFIED_SOURCE
  identifier: UNVERIFIED_SOURCE:LI_CHIANG_ICML_2025
  year: 2025
---

# LLM, RAG & Agent EvalOps Statistical Calibration (`VERIFY.md`)

## Operational Contract
This module operates under `conjunctive_gate` synthesis (`ECOSYSTEM_CONTRACT v1.2.0`). Deterministic CPU rules execute first (`TOOL_VERIFIED`), followed by read-only Clean-Room semantic auditing via `auditor-evalops-validity` (`STATIC_LLM_INFERRED`).

## Failure Modes & Remediation
1. Remediate all `BLOCKER` findings before merge (`REJECT` is non-compensable).
2. Resolve `MAJOR` findings or supply a time-bounded independent human signoff (`approver != pr_author`).
3. Never weaken assertions, zero coverage/mutation thresholds, or bypass CI gates to manufacture `SHIP`.
