# Verification & EvalOps Pre-Merge Bootstrap (`verification-eval`)

Use this rule when auditing test suites, CI quality gates, coverage/mutation thresholds, property/metamorphic tests, or LLM/RAG evaluation harnesses under `ECOSYSTEM_CONTRACT v1.2.0`.

1. **CPU-First Fail-Closed:** Run `.agents/skills/verification-director/tools/verify_cpu_scanner.py --target . --sarif-out verify_cpu_scanner.sarif` and ingest JUnit/coverage/mutation artifacts via `.agents/skills/verification-director/tools/eval_ingest.py`. Missing or zero-test runner evidence (`tests_executed == 0`) exits `3` (`UNVERIFIED_MISSING_TOOL`) and prohibits `SHIP`.
2. **Route Lazily:** Consult `.agents/skills/verification-director/references/control-matrix.yaml` and load only matching module `BRIEF.md` files (`<= 25.6 KB` active context ceiling).
3. **Clean-Room Cross-Model Separation:** Escalate test additions (`> 25` net lines), new mocks, or eval harness edits to strictly read-only `auditor-test-integrity` and/or `auditor-evalops-validity`.
4. **Anti-Self-Auditing (§8.1):** Never modify `tests/`, `evals/`, `rules.yaml`, `validators/`, or audit logs to manufacture `SHIP`. Human signoffs require `approver != pr_author`.
5. **Precedence:** `security-governance > verification-eval > systems-harness > spec-context > ui-ux`. Terminate with `Verdict Envelope v1.2.0`.
