# LLM, RAG & Agent EvalOps Statistical Calibration — Operational Brief (`llm-rag-evalops-calibration`)

**Scope:** Prevents holdout leakage, same-family LLM-judge self-preference bias, unadjusted noisy-judge prevalence, and uncalibrated accuracy overclaims.

## Deterministic Rules (`TOOL_VERIFIED`)
- `VER-EVAL-UNCAL-001` (`MAJOR`, `verify_cpu_scanner`): Accuracy/precision/recall/pass_rate claims must include Layer 2 holdout calibration metadata (n_pos >= 100, n_neg >= 100, 95% CI, Youden J) or declare layer_1_synthetic_fixture_regression_floor with production_claim_prohibited: true.

## Semantic Invariants (`STATIC_LLM_INFERRED`)
- `verification-eval:auditor-evalops-validity:evalops-01` (`BLOCKER`, `auditor-evalops-validity`): Prompt-tuning, few-shot selection, or hyperparameter optimization loops must remain strictly disjoint from reported holdout evaluation splits.
- `verification-eval:auditor-evalops-validity:evalops-02` (`BLOCKER`, `auditor-evalops-validity`): Pairwise LLM-as-a-Judge harnesses must use a distinct cross-family judge model, randomize/swap slot ordering, and calibrate against human labels.
- `verification-eval:auditor-evalops-validity:evalops-03` (`BLOCKER`, `auditor-evalops-validity`): Defect or pass prevalence estimated by an imperfect judge (Se < 1 or Sp < 1) must apply Rogan-Gladen adjustment and propagate calibration uncertainty.
- `verification-eval:auditor-evalops-validity:evalops-06` (`MAJOR`, `auditor-evalops-validity`): Evaluation claims must report finite-sample confidence intervals (Wilson/Clopper-Pearson) and prohibit significance claims from underpowered samples.
- `verification-eval:auditor-evalops-validity:evalops-07` (`MAJOR`, `auditor-evalops-validity`): Pairwise arena/Bradley-Terry win-rate rankings must not be extrapolated to domain-specific production accuracy without domain-stratified calibration.

## Escalation & Gate
- Missing required runner evidence (`tests_executed == 0`) -> `exit 3` (`UNVERIFIED_MISSING_TOOL`, `ITERATE`).
- Any `BLOCKER` -> `REJECT`; any `MAJOR` -> `ITERATE`; zero `BLOCKER`/`MAJOR` -> `SHIP`.
- Load `VERIFY.md` for full Draft 2020-12 schema and primary sources.
