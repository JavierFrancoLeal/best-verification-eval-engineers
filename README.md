# best-verification-eval-engineers

Open-source **Pre-Merge Verification & EvalOps Governance Suite** (`suite_id: verification-eval`, `director_slug: verification-director`, `judgment_file: VERIFY.md`, **`ECOSYSTEM_CONTRACT v1.2.0`**).

Combines **deterministic CPU static + execution verification first** with **strictly read-only Clean-Room cross-model semantic auditing** to catch AI test theater, flaky/unseeded tests, CI gate tampering, holdout contamination, and uncalibrated LLM-as-a-Judge claims before merge.

## Architecture

1. **Tier A Deterministic CPU Pre-Scanner (`tools/verify_cpu_scanner.py`)**
   - Python 3.9+ stdlib only, zero network imports, disjoint `files_scanned` / `files_skipped` telemetry in JSON and SARIF 2.1.0.
   - Enforces 7 canonical rules (`VER-TAU-NOASSERT-001`, `VER-TAU-CONST-001`, `VER-TAU-SWALLOW-001`, `VER-FLK-NONDET-001`, `VER-GOV-SKIP-001`, `VER-GOV-TAMPER-001`, `VER-EVAL-UNCAL-001`).
2. **Tier B Fail-Closed Evidence Ingestor (`tools/eval_ingest.py`)**
   - Normalizes JUnit XML, LCOV, coverage JSON (`coverage.py`/Istanbul), mutation JSON (Stryker/mutmut/Gremlins), Tier A SARIF, and `--semantic-findings`.
   - Exits `3` (`UNVERIFIED_MISSING_TOOL`, verdict `ITERATE`) on missing/empty runner evidence (`tests_executed == 0`), unreadable `--semantic-findings`, unknown severity strings, or malformed 3-part `canonical_id`s.
   - Enforces `approver != pr_author` Separation of Duties via `--human-signoff` and `--verify-envelope --pr-author`.
3. **7 Canonical Functional Control Modules (`modules/<slug>/`)**
   - `test-execution-oracles`
   - `assertion-mutation-strength`
   - `determinism-flakiness-isolation`
   - `property-metamorphic-invariants`
   - `contract-boundary-regressions`
   - `llm-rag-evalops-calibration`
   - `anti-tampering-eval-governance`
4. **2 Strictly Read-Only Clean-Room Auditors (`committee/auditors/`)**
   - `auditor-test-integrity` (`testint-01..07`)
   - `auditor-evalops-validity` (`evalops-01..07`)

## Quick Start

```bash
# Install into any agentskills.io-compatible harness (non-destructive director-only default)
bash adapters/install.sh --target all --mode director-only --scope workspace --dest /path/to/repo

# Run Tier A CPU pre-scanner
python3 tools/verify_cpu_scanner.py --target . --sarif-out verify_cpu_scanner.sarif

# Run Two-Layer Adversarial Benchmark (10 TP + 6 TN + 8 Semantic AST-orthogonality fixtures)
python3 tools/run_verify_benchmark.py

# Run full ECOSYSTEM_CONTRACT v1.2.0 + suite conformance validation
python3 validators/validate_repo.py
```

## License
MIT — see [LICENSE](LICENSE).
