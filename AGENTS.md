# AGENTS.md — `best-verification-eval-engineers`

This repository implements the **`verification-eval`** pre-merge verification and EvalOps governance suite (`director_slug: verification-director`, `judgment_file: VERIFY.md`, **`ECOSYSTEM_CONTRACT v1.2.0`**).

## Mandatory Pre-Merge Verification Order
1. **Tier A Deterministic CPU Pre-Scanner:** Run `python3 tools/verify_cpu_scanner.py --target . --sarif-out verify_cpu_scanner.sarif` (7 canonical Tier A rules in `RULE_META`, Python 3.9+ stdlib only, zero network imports).
2. **Tier B Fail-Closed Evidence Ingestor:** Run `python3 tools/eval_ingest.py --tier-a-sarif verify_cpu_scanner.sarif --junit junit.xml` (optional `--lcov`, `--coverage-json`, `--mutation-json`, `--semantic-findings`). Missing/zero-test runner evidence exits `3` (`UNVERIFIED_MISSING_TOOL`) and prohibits `SHIP`.
3. **Clean-Room Cross-Model Auditors:** Invoke strictly read-only (`allowed-tools: Read Grep Glob`) `committee/auditors/auditor-test-integrity/` (`testint-01..07`) and `committee/auditors/auditor-evalops-validity/` (`evalops-01..07`) in a fresh cross-model session whenever semantic triggers fire.
4. **Repository Conformance:** Run `python3 validators/validate_repo.py` and `python3 tools/run_verify_benchmark.py`.

## Guardrails
- **Immutable Core Validator:** Never edit `validators/ecosystem_core_validator.py` or `validators/CORE_VALIDATOR.sha256` directly; sync from `ecosystem-core/sync_core.sh`.
- **Anti-Self-Auditing (§8.1):** Builder agents MUST NOT weaken `tests/`, `evals/`, `rules.yaml`, `validators/`, or audit logs to manufacture `SHIP`. Human signoff enforces `approver != pr_author`.
- **Normalized Severities:** Use ONLY `BLOCKER`, `MAJOR`, `MINOR` (`score_heuristic: null`, `conjunctive_gate`).
