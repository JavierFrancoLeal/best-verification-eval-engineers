---
name: verification-director
description: >-
  CPU-first pre-merge verification and EvalOps governance director. Runs deterministic
  AST/config pre-scanning, fail-closed JUnit/coverage/mutation ingestion, and Clean-Room
  cross-model semantic test and eval validity auditing under ECOSYSTEM_CONTRACT v1.2.0.
license: MIT
compatibility: >-
  Requires Python 3.9+ stdlib for bundled CPU tools; integrates with pytest, vitest,
  jest, go test, coverage.py, c8/lcov, mutmut, stryker, and gremlins.
allowed-tools: Read Grep Glob Bash
metadata:
  schema_version: "1.2.0"
  suite_id: "verification-eval"
  author: "Trasunto / best-verification-eval-engineers"
  routing_matrix: "./references/control-matrix.yaml"
  pre_scanner: "./tools/verify_cpu_scanner.py"
---

# Verification & EvalOps Director (`verification-director`)

## When To Use
- Auditing pull requests, test suites, CI quality gates, mutation/coverage configs, property/metamorphic tests, or LLM/RAG evaluation harnesses before merge.
- Verifying that AI-generated or human-authored tests actually detect faults rather than performing assertion-free or mock-verifies-mock theater.
- Enforcing fail-closed test runner execution (`tests_executed > 0`), statistical holdout calibration, and anti-tampering separation of powers.

## Do Not Use When
- Auditing SAST/SCA vulnerabilities, secret scanning, AuthN/AuthZ boundaries, or compliance trails (route to `security-governance`, Priority 1).
- Auditing static dependency boundaries, build/lint harnesses, or destructive SQL schema migrations (route to `systems-harness`).
- Auditing pre-implementation requirements or ambiguous acceptance criteria before code exists (route to `spec-context`).
- Auditing UI/UX visual ergonomics, WCAG AA contrast, or motion physics (route to `ui-ux`).
- Operating production SRE observability, live canary rollbacks, or cloud FinOps (explicitly out of scope).

## Required Inputs
- Target repository or PR diff (`git diff` + touched test, CI, and eval files).
- Deterministic Tier A SARIF (`./tools/verify_cpu_scanner.py`) and Tier B runner artifacts (`junit.xml`, optional LCOV/coverage JSON and mutation JSON).
- Gate policy context (`AUTO_PASS_ON_CLEAN_ORACLE`, `MANDATORY_CLEAN_ROOM_TEST_AUDIT`, or `MANDATORY_NAMED_HUMAN_SIGNOFF`) plus `--pr-author` when waivers/signoffs are present.

## Orchestration Protocol
1. **Tier A CPU Pre-Scan:** Run `python3 ./tools/verify_cpu_scanner.py --target . --sarif-out verify_cpu_scanner.sarif` to detect the 7 deterministic rules (`VER-TAU-*`, `VER-FLK-*`, `VER-GOV-*`, `VER-EVAL-*`) and emit `scan_coverage`.
2. **Tier B Fail-Closed Evidence Ingest:** Run `python3 ./tools/eval_ingest.py --tier-a-sarif verify_cpu_scanner.sarif --junit junit.xml` (plus `--lcov`/`--coverage-json`/`--mutation-json` when present). Missing or zero-test runner evidence exits `3` (`UNVERIFIED_MISSING_TOOL`, verdict `ITERATE`, blocking ID `verification-eval:tooling:MISSING_REQUIRED_TOOL_EVIDENCE`).
3. **Functional Control Routing:** Match touched surfaces against `./references/control-matrix.yaml` and load ONLY matching `./references/modules/<module_id>/BRIEF.md` (and `VERIFY.md` on demand).
4. **Clean-Room Cross-Model Audit:** When triggered by test additions (`> 25` net lines), new mocks, eval harness edits, or sibling escalation, invoke read-only `./references/auditors/auditor-test-integrity/AUDITOR.md` and/or `./references/auditors/auditor-evalops-validity/AUDITOR.md` in a fresh cross-model session and re-ingest via `--semantic-findings`.
5. **Conjunctive Synthesis:** Deduplicate single-root-cause findings (`BLOCKER >= 1 -> REJECT`, `UNVERIFIED_MISSING_TOOL -> ITERATE`, `MAJOR >= 1 -> ITERATE`, else `SHIP`). Never average severities (`score_heuristic: null`).

## Mandatory Closing Output
Terminate every audit with this exact parseable `Verdict Envelope v1.2.0` YAML block:

```yaml
verdict_envelope:
  envelope_version: "1.2.0"
  envelope_id: "<deterministic-run-id>"
  trace_id: "<shared-correlation-id>"
  suite_id: "verification-eval"
  director_slug: "verification-director"
  artifact_ref: "<PR ref or file paths>"
  sdlc_stage: "verify"
  regime: "conjunctive_gate"
  synthesis_mode: "conjunctive_gate"
  evidence_tier: "<TOOL_VERIFIED | STATIC_LLM_INFERRED | UNVERIFIED_MISSING_TOOL>"
  evidence:
    - tool: "verify_cpu_scanner"
      command_or_ref: "python3 ./tools/verify_cpu_scanner.py --target . --sarif-out verify_cpu_scanner.sarif"
      exit_code: 0
      format: "sarif"
      summary: "blocker=0 major=0 minor=0"
    - tool: "eval_ingest"
      command_or_ref: "python3 ./tools/eval_ingest.py --tier-a-sarif verify_cpu_scanner.sarif --junit junit.xml"
      exit_code: 0
      format: "json"
      summary: "tests_executed=0 verdict=SHIP"
  verdict: "<SHIP | ITERATE | REJECT>"
  counts:
    blocker: 0
    major: 0
    minor: 0
  score_heuristic: null
  blocking_ids: []
  clean_room_required: true
  hop_count: 0
  max_hops: 2
  visited_suites: ["verification-eval"]
  escalations: []
  domain_extensions:
    gate_policy: "AUTO_PASS_ON_CLEAN_ORACLE"
    cross_model_auditor_verified: false
```

## Guardrails
- **Fail-Closed Mandate:** Never emit `SHIP` when required test runner evidence is missing or `tests_executed == 0`.
- **Anti-Self-Auditing (§8.1):** Builder agents MUST NOT edit `tests/`, `evals/`, `rules.yaml`, `validators/`, or audit logs to manufacture `SHIP`. Human signoff MUST enforce `approver != pr_author`.
- **No Synthetic-to-Production Overclaims:** Layer 1 synthetic fixtures are regression floors only (`production_claim_prohibited: true`); production prevalence claims require Layer 2 Rogan-Gladen / Wilson CI calibration.
- **Cycle Prevention:** Never escalate to a `target_suite_id` already in `visited_suites` or when `hop_count >= max_hops`. Respect precedence: `security-governance > verification-eval > systems-harness > spec-context > ui-ux`.
