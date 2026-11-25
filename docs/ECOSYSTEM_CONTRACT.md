# ECOSYSTEM CONTRACT v1.2.0 — POST-AI PRE-MERGE CHANGE GOVERNANCE SUITES

## 1. Purpose, Scope & Explicit Non-Goals

This contract defines the **domain-neutral interoperability layer** for a family of open-source **Pre-Merge Change Governance** suites designed for `agentskills.io`-compatible coding agents and CI pipelines.

Each suite combines:
1. **Deterministic CPU Tooling First** (real static scanners, linters, test/coverage/mutation runners, SAST/SCA, or DOM/CSS analyzers emitting machine-readable evidence), and
2. **Scoped Semantic LLM Auditing** (catching workflow, intent, state, and business-logic defects that static tools cannot see), packaged as portable `SKILL.md` directors with compact operational briefs and a terminable `Verdict Envelope` (`v1.1.0` / `v1.2.0`).

### Explicit v1 Scope vs. Out-of-Scope
- **In Scope (v1 — Pre-Merge Change Governance):** `Plan`, `Design`, `Build`, `Verify`, and `Secure` checks runnable on repositories, specs, diffs, and pull requests prior to merge (including pre-merge destructive database/schema migration checks).
- **Interoperable Layer-2 Sibling Suites (Optional Consumer Layer):** Non-SDLC strategic/business suites (e.g., `tech-economics`, `go-to-market`) may adopt this contract's `suite.yaml`, CPU-first fail-closed gate, `rules.yaml` schema, and `Verdict Envelope` under `layer: "business-strategy"` without entering the 5-suite SDLC code-merge precedence chain.
- **Explicitly Out of Scope (deferred to v2):** Production SRE/observability (SLOs, alerting, on-call incident response), live release/rollback orchestration (canary, blue-green, Terraform/IaC drift), and cloud FinOps/capacity planning. Suites MUST NOT claim coverage of these operational functions.

---

## 2. Canonical Five-Suite Registry & Exclusive Ownership Matrix

Every `suite_id` and `director_slug` is globally unique. Rather than overlapping generic SDLC stage labels, suites are partitioned by **exclusive primary ownership of artifact & defect classes**:

| Order | `suite_id` | Repository Name | `director_slug` | Judgment File | Exclusive Primary Ownership (Artifact & Defect Class) | Default Synthesis |
|---|---|---|---|---|---|---|
| 1 | `ui-ux` | `best-ui-ux-designers` | `design-director` | `DESIGN.md` | User-facing interfaces (`HTML`/`CSS`/`JSX`/`TSX`/`Vue`/`Svelte`): accessibility (WCAG 2.2 AA), motion physics, perceived latency, cognitive/form load, client interaction state, and embedded-AI UX anti-patterns. | `weighted_panel` (anti-dilution) |
| 2 | `verification-eval` | `best-verification-eval-engineers` | `verification-director` | `VERIFY.md` | Executable verification & quality oracles: test runner execution, branch/mutation coverage, tautological/flaky tests, property-based invariants, and holdout LLM/RAG evaluation harnesses. | `conjunctive_gate` |
| 3 | `systems-harness` | `best-systems-harness-architects` | `systems-director` | `ARCH.md` | Structural architecture & static build harnesses: dependency boundaries, structural code clones, silent error swallowing, oversized PR diffs, destructive DB/schema migrations, and deterministic lint/type gates. | `conjunctive_gate` |
| 4 | `security-governance` | `best-security-governance-architects` | `security-director` | `SEC.md` | Security & compliance controls: SAST/SCA/secret scanning, AuthN/AuthZ & IDOR boundaries, credential/PII isolation, prompt-injection/sandboxing guards, and auditable compliance trails. | `conjunctive_gate` |
| 5 | `spec-context` | `best-spec-context-architects` | `spec-director` | `SPEC.md` | Pre-implementation specifications & domain contracts: ambiguous requirements, contradictory business rules, undocumented brownfield constraints, and acceptance-criteria completeness. | `conjunctive_gate` |

### Boundary Disambiguation & Conflict Precedence
1. **`spec-context` vs. `verification-eval`:** `spec-context` owns *human/contractual intent and acceptance criteria before code is written*; `verification-eval` owns *executable tests, assertions, and runtime/eval verification of implemented code*.
2. **`systems-harness` vs. `verification-eval`:** `systems-harness` owns *static structural health, module boundaries, migrations, and build/lint/type harnesses*; `verification-eval` owns *behavioral test execution, mutation/coverage scores, and eval accuracy*.
3. **`ui-ux` vs. `security-governance`:** `ui-ux` owns *perceived responsiveness, affordances, and interaction ergonomics*; `security-governance` owns *authorization, credential boundaries, and compliance gates*.
4. **Cross-Suite Conflict Precedence:** When two suites emit conflicting recommendations on the same PR (e.g., `ui-ux` requesting optimistic writes vs. `security-governance` requiring server-side authorization before state mutation), higher precedence wins strictly in this order:
   `security-governance` > `verification-eval` > `systems-harness` > `spec-context` > `ui-ux`.

---

## 3. Mandatory `suite.yaml` v1.2.0 Root Manifest

Every repository MUST include a machine-readable `suite.yaml` at its root (and copy it inside `<director_slug>/references/suite.yaml` on installation):

```yaml
ecosystem_contract_version: "1.2.0"
suite_id: "<ui-ux | verification-eval | systems-harness | security-governance | spec-context>"
repo_name: "<best-...>"
director_slug: "<globally-unique-director-slug>"
judgment_file: "<DESIGN.md | VERIFY.md | ARCH.md | SEC.md | SPEC.md>"
schema_version: "1.2.0"
synthesis_mode: "<conjunctive_gate | weighted_panel>"
sdlc_scope:
  primary_artifacts: ["<artifact globs or classes>"]
  sdlc_stages: ["<plan | design | build | verify | secure>"]
  explicit_out_of_scope: ["sre_observability", "production_release_rollback", "cloud_finops"]
execution_modes:
  fast_pr_gate: "Run deterministic CPU pre-scanner + unconditional Via Negativa checks; escalate to director on BLOCKER or scope shift."
  architecture_review: "Run deterministic CPU pre-scanner + active domain modules + semantic audit + Verdict Envelope."
tooling:
  pre_scanner: "<relative path to bundled CPU pre-scanner, e.g. tools/uiux_cpu_scanner.py>"
  required_tools: []      # e.g. ["semgrep", "gitleaks", "osv-scanner", "trivy"]
  optional_tools: []      # e.g. ["node", "eslint", "axe", "conftest"]
  accepted_formats: ["json", "sarif", "junit", "lcov", "exit_code"]
  fail_closed_on_missing_required_tool: false  # MUST be true for verification-eval & security-governance
roster_summary:
  module_type: "<functional_controls | expert_panel | hybrid>"
  total_modules: 0        # Flexible by domain (no mandatory count)
  auditors: 0             # Flexible by domain
  regimes: 0              # Flexible by domain (0 if threat/control matrix instead of regimes)
domain_extensions: []     # Optional suite-specific verdict_envelope.domain_extensions keys
handoff_targets:
  - suite_id: "<sibling_suite_id>"
    trigger_condition: "<Falsifiable boundary condition requiring cross-suite escalation>"
```

*(Backward compatibility: `ecosystem_core_validator.py` v1.2.0 accepts both `"1.1.0"` and `"1.2.0"` for `ecosystem_contract_version` and `envelope_version` during additive MINOR rollouts; newly compiled suites MUST target `"1.2.0"`.)*

---

## 4. Tool Execution & Evidence Contract (CPU-First)

Text-only LLM inspection of mechanical predicates exhibits unacceptable run-to-run variance and misses real runtime/syntax bugs. Every suite MUST enforce a strict split between **deterministic CPU execution** and **semantic LLM judgment**:

1. **Deterministic CPU Before LLM:**
   - Mechanical checks (syntax/undefined symbols, AST/clone detection, CSS/HTML accessibility attributes, `prefers-reduced-motion`, test execution, coverage/mutation, SAST/SCA, secret scanning) MUST execute via real CPU tools emitting structured JSON, SARIF 2.1.0, JUnit XML, LCOV, or exit codes.
   - Semantic LLM judgment MUST consume the CPU tool report first and focus exclusively on higher-order defects that static tools miss (e.g., broken user flows, copy-vs-behavior contradictions, tautological assertions, business-logic authorization bypasses, missing rollback/undo).
2. **Mandatory Evidence Tiers:** Every audit finding and every `verdict_envelope` MUST declare its provenance:
   - `TOOL_VERIFIED`: Directly backed by an executed CPU tool output (command, exit code, and finding ID/line).
   - `STATIC_LLM_INFERRED`: Derived from LLM inspection of source code with exact `file:line` citation.
   - `UNVERIFIED_MISSING_TOOL`: Check could not execute because a required runtime, browser, telemetry source, or CLI scanner was absent.
3. **Fail-Closed Gate for Deterministic Suites:** When `suite.yaml -> tooling.fail_closed_on_missing_required_tool` is `true` (mandatory for `verification-eval` and `security-governance`), missing required tool execution MUST prohibit `SHIP` (maximum verdict `ITERATE` with blocking ID `<suite_id>:tooling:MISSING_REQUIRED_TOOL_EVIDENCE`).
4. **Tool Permissions (`allowed-tools`):** `SKILL.md` frontmatter explicitly permits the `agentskills.io` `allowed-tools` key so directors and modules can declare required CLI runners cleanly.

---

## 5. Domain-Polymorphic Internal Topology, Auditor Schema & Severity Model

### 5.1 Ecosystem-Wide Invariants (Fixed)
1. **Normalized 3-Tier Finding Severity:**
   - **`BLOCKER`** *(equivalent to `hard_veto`)*: Non-compensable defect (data loss, crash, WCAG AA hard failure, exploitable vulnerability, broken invariant). Any `BLOCKER >= 1` forces `REJECT`.
   - **`MAJOR`** *(equivalent to `conditional_block`)*: Significant defect requiring remediation or explicit waiver. Any unresolved `MAJOR >= 1` prohibits `SHIP` (forces at least `ITERATE`) and **MUST NEVER be diluted away by panel averaging**.
   - **`MINOR`**: Advisory improvement; does not block `SHIP`.
2. **Single-Root-Cause Deduplication (Anti-Saturation):** A single underlying defect at `file:line` MUST be counted **at most once** per module (at its highest applicable severity). Suites MUST NOT stack identical defects simultaneously as veto + filter + signal penalties.
3. **Brand & Project Token Exemption:** Stylistic/visual rules (such as gradient or color-system checks) MUST accept declared project brand tokens (`brand_tokens`, CSS custom properties, or project `DESIGN.md`) so intentional brand identity is never flagged as generic slop.
4. **Operational Context Budget (`<= 25 KB` default load):** A single director invocation MUST load `<= 25 KB` (`25,600 bytes`, `~6,250 tokens`) of normative briefs by default. Deep reference specifications (extended essays, engineer/architect dossiers under `docs/`, primary-source bibliographies) MUST stay on disk and be loaded only on targeted demand.
5. **Honest Calibration Labeling:** Numeric thresholds or weights MUST be labeled **heuristic** (`score_heuristic`) unless backed by a published empirical calibration dataset and benchmark script in the repository.

### 5.2 Domain-Flexible Internals & Canonical Auditor `rules.yaml` Schema (NEW in v1.2.0)
The ecosystem contract deliberately does **NOT** mandate a fixed number of modules, human personas, Barbell splits, regimes, or weighted formulas across domains:
- **`conjunctive_gate` (required default for `verification-eval`, `security-governance`, `systems-harness`, `spec-context`):** Organizes checks as functional control modules or threat/invariant domains. Verdict is computed conjunctively from deduplicated severities (`BLOCKER >= 1 -> REJECT`, `MAJOR >= 1 -> ITERATE`, else `SHIP`). No persona roleplay and no `Q_total` averaging.
- **`weighted_panel` (permitted for multi-criteria trade-off domains such as `ui-ux`):** A suite may define its own specialist panel, regime routing, and heuristic panel score (`score_heuristic`) inside its repository documentation and suite-specific validator, provided it honors `BLOCKER` non-compensation, `MAJOR` non-dilution, single-root-cause deduplication, and the `<= 25 KB` operational context budget.

#### 5.2.1 Canonical Clean-Room Auditor `rules.yaml` Schema & `UNVERIFIED_SOURCE` Discipline
Whenever a suite ships declarative Clean-Room auditor rulesets under `committee/auditors/<auditor_slug>/rules.yaml`, every rule entry MUST provide these portable, machine-parseable fields (domain-specific enrichments such as `applies_to`, `negative_control`, `required_evidence`, and `deduplication_key` are encouraged alongside them):

| Field | Required Requirement |
|---|---|
| `id` | Unique short rule slug within the auditor (e.g., `authz-01`). |
| `canonical_id` | Exact 3-part canonical ID: `<suite_id>:<auditor_slug>:<id>`. |
| `name` | Concise defect name (zero decorative clichés). |
| `severity` | Normalized tier: `BLOCKER` \| `MAJOR` \| `MINOR`. |
| `engineer_slug` *(or `architect_slug` / `authority_slug`)* | Primary-source authority slug (zero persona cosplay; provenance only). |
| `invariant_id` | Traceable invariant ID defined in `docs/` dossiers or control matrix. |
| `source_id` | Non-empty primary-source ID resolving to a verified DOI, ISBN, RFC, statutory code, or official specification URL. |
| `non_sast_rationale` *(or `non_cpu_rationale`)* | Explicit proof of why deterministic CPU tools miss this defect. |
| `diff_inspection_protocol` *(or `artifact_inspection_protocol`)* | Step-by-step falsifiable inspection procedure on the diff/artifact. |
| `false_positive_exemption` | Explicit conditions under which the rule MUST suppress findings. |
| `mandatory_remediation` | Concrete structural fix required to clear the finding. |
| `cross_model_recommended` | Boolean (`true` required whenever `clean_room_required: true`). |

**Universal `UNVERIFIED_SOURCE` Discipline:**
- Suites MUST NEVER silently cite unverified secondary statistics, future-dated/unresolvable preprints, or placeholder identifiers (`TBD`, `TODO`, `example.invalid`) as primary evidence.
- Any citation whose primary identifier (DOI, ISBN, RFC, official spec) cannot be live-verified MUST be explicitly tagged **`UNVERIFIED_SOURCE`**.
- *Domain-Flexible Severity:* Labeling is mandatory across all suites; the gating consequence of an `UNVERIFIED_SOURCE` tag (e.g., blocking `conjunctive_gate` citation checks vs. advisory warning in `weighted_panel` suites) remains domain-scoped in each suite's `validate_repo.py`.

### 5.3 Mandatory `SKILL.md` Contract (`agentskills.io`)
- Max `500` lines per `SKILL.md`.
- Allowed root frontmatter keys: `name` (must match folder slug), `description` (third-person, `<= 320` chars), `license: MIT`, `compatibility`, `metadata`, and optional `allowed-tools`.
- **Director `SKILL.md`:**
  - `metadata` required keys: `schema_version`, `suite_id`, `author` (optional: `routing_matrix`, `pre_scanner`).
  - Required literal `##` headings: `When To Use`, `Do Not Use When`, `Required Inputs`, `Orchestration Protocol`, `Mandatory Closing Output`, `Guardrails`.
- **Module / Expert `SKILL.md`:**
  - `metadata` required keys: `schema_version`, `judgment_schema`, `suite_id`, `author` (suite-specific extra metadata keys permitted).
  - Required literal `##` headings: `When To Use`, `Do Not Use When`, `Required Inputs`, `Execution & Audit Workflow`, `Verdict & Severity Criteria`, `Guardrails`.
- **Unified `evals/evals.json`:** Root keys `skill_name`, `schema_version` (`"1.1.0"` or `"1.2.0"`), `evals` (`>= 5` cases: `>= 3` `should_trigger`, `>= 2` `near_miss`/`out_of_universe` with structured `expected_output` objects).

---

## 6. Multi-Suite Anti-Collision & Installation Specification

Installing multiple suites into a single workspace MUST NEVER overflow skill-catalog discovery caps, clobber sibling files, or break relative paths. Every repository's `adapters/install.sh` MUST enforce:

1. **Safe Default Mode (`--mode director-only`):**
   - `--mode director-only` is the **default** installation mode. It registers **only** `<director_slug>/SKILL.md` in the harness skill directory.
   - **Anti-Recursive-Discovery Rule:** All lazy-loaded module/auditor files copied under `<director_slug>/references/` MUST be renamed away from `SKILL.md` (use `PROFILE.md` for modules/experts, `AUDITOR.md` for auditors, `BRIEF.md` for compact operational briefs) so harnesses performing recursive `**/SKILL.md` discovery index **strictly 1 skill per suite** (`5 entries, <= 1,600 chars total`).
   - Any bundled CPU pre-scanner (`tools/*`) and `suite.yaml` MUST be copied inside `<director_slug>/` (`./tools/` and `./references/suite.yaml`), and `director/SKILL.md` MUST resolve paths relative to its own installed directory (never `../../suite.yaml` outside the skill root).
   - `--mode full` (standalone single-suite install) MUST namespace module/auditor folder slugs with `<suite_id>-` (or refuse to overwrite foreign folders) and NEVER run blind `rm -rf` on shared parent paths.
2. **Exact Nested `adapters/` Layout & `<suite_id>-` Rule Namespacing (Zero Drift):**
   - Every suite MUST store harness adapters in **nested** subdirectories under `adapters/{antigravity,claude-code,codex-chatgpt,cursor,deepseek-harness,windsurf-devin}/` plus executable `adapters/install.sh` (never a flat `adapters/` dump).
   - Every harness rule file MUST start with the exact literal `<suite_id>-` prefix (e.g., `ui-ux-`, `verification-eval-`, `security-governance-` — never drop hyphens):
     - Antigravity: `adapters/antigravity/<suite_id>-bootstrap.md` -> `.agents/rules/<suite_id>-bootstrap.md` (`< 24,000` bytes)
     - Cursor: `adapters/cursor/<suite_id>-director.mdc` -> `.cursor/rules/<suite_id>-director.mdc` (`alwaysApply: false` + domain `globs`)
     - Windsurf / Devin: `adapters/windsurf-devin/<suite_id>-director.md` -> `.devin/rules/<suite_id>-director.md` and `.windsurf/rules/<suite_id>-director.md` (`< 12,000` chars hard cap)
     - DeepSeek Harness: `adapters/deepseek-harness/dsh-plugin.json` MUST install with valid destination-relative paths when selected.
   - `--target all` MUST deduplicate shared skill directories (e.g., `.agents/skills`) rather than wiping and recopying the same folder multiple times.
3. **Non-Destructive `AGENTS.md` & `CLAUDE.md` Injection:**
   - `install.sh` MUST NEVER overwrite existing `AGENTS.md` or `CLAUDE.md` content.
   - Upsert an idempotent fenced block `<!-- BEGIN <repo_name> -->` ... `<!-- END <repo_name> -->` into `AGENTS.md` (referencing exact installed paths for the CPU pre-scanner and Fast PR Gate auditors).
   - If `CLAUDE.md` does not exist, create relative symlink `CLAUDE.md -> AGENTS.md`. If `CLAUDE.md` already exists as a regular file, upsert the same fenced block into `CLAUDE.md` rather than silently skipping it.
4. **Mandatory Multi-Suite Coexistence CI Test:** Every suite's CI workflow (`.github/workflows/validate.yml`) MUST run an integration test installing the suite alongside at least one mock sibling suite into a shared `--dest` directory and asserting: zero file clobber, exact recursive `SKILL.md` count `== 2`, valid installed `suite.yaml` and pre-scanner paths, and successful CPU pre-scanner execution.

---

## 7. Terminable Inter-Suite Handoff Contract (`Verdict Envelope`)

Every Director MUST terminate its audit output with this exact parseable YAML block (`envelope_version: "1.2.0"`, backward-compatible with `"1.1.0"`). *(Note: automated multi-suite chaining is `experimental` until a reference runner/orchestrator is published; single-suite and CI consumers parse this envelope directly.)*

```yaml
verdict_envelope:
  envelope_version: "1.2.0"
  envelope_id: "<uuid-or-deterministic-run-id>"
  trace_id: "<shared-correlation-id-across-handoffs>"
  suite_id: "<suite_id>"
  director_slug: "<director_slug>"
  artifact_ref: "<file paths, PR ref, or module scope>"
  sdlc_stage: "<plan | design | build | verify | secure>"
  regime: "<domain_regime_or_control_profile>"
  synthesis_mode: "<conjunctive_gate | weighted_panel>"
  evidence_tier: "<TOOL_VERIFIED | STATIC_LLM_INFERRED | UNVERIFIED_MISSING_TOOL>"
  evidence:
    - tool: "<tool_name>"
      command_or_ref: "<exact command or report path>"
      exit_code: 0
      format: "<json | sarif | junit | lcov | exit_code>"
      summary: "<concise machine-verified counts>"
  verdict: "<SHIP | ITERATE | REJECT>"
  counts:
    blocker: 0
    major: 0
    minor: 0
  score_heuristic: null   # Optional numeric heuristic for weighted_panel suites; null for conjunctive_gate
  blocking_ids: []        # Canonical format: "<suite_id>:<module_id>:<rule_id>"
  clean_room_required: false
  hop_count: 0
  max_hops: 2
  visited_suites: ["<suite_id>"]
  escalations: []         # List of { target_suite_id, reason, blocking_ids, artifact_slice }
  domain_extensions: {}   # Optional suite-specific metadata (e.g. ui-ux: { solow_stage: ... })
```

### Termination & Cycle Prevention Rules
- A suite MUST NEVER append a `target_suite_id` to `escalations` if it is already present in `visited_suites`.
- If `hop_count >= max_hops`, automated escalation MUST terminate and emit unresolved cross-domain items for human review.
- `blocking_ids` MUST follow the canonical 3-part format `<suite_id>:<module_id>:<rule_id>` (e.g., `ui-ux:cpu-scanner:CPU-JS-01` or `security-governance:auditor-authz-intent:authz-01`).

---

## 8. Cross-Suite Engineering Guardrails, Anti-Tampering & Modular Validation

### 8.1 Universal Anti-Self-Auditing & Tamper Protection Invariant (NEW in v1.2.0)
Every suite owns four governance-critical artifact classes: **`tests/`**, **`evals/`**, **`rules.yaml`**, and **audit/verdict logs**. No suite is exempt from Separation of Powers:
1. **Read-Only Audit Posture:** Clean-Room auditors (`committee/auditors/*/AUDITOR.md`) MUST NOT declare unrestricted file-write or file-edit tools (`Write`, `Edit`, `write_file`, `edit_file`) in their frontmatter `allowed-tools`.
2. **Builder Isolation from Verification Oracles:** An acting builder agent MUST NOT silently modify `validators/`, `evals/`, `rules.yaml`, or its own audit logs to manufacture a `PASS` verdict. Suites with `clean_room_required: true` MUST verify integrity or escalate any builder modification of verification/policy artifacts for explicit human/clean-room review.
3. **Clean-Room Cross-Model Separation:** Whenever `verification-eval` or `security-governance` audits code produced by a builder agent, the auditor MUST execute in a fresh session (`clean_room_required: true`) receiving only the repository diff, CPU tool artifacts, and serialized `verdict_envelope` YAML — never the builder's chain-of-thought.

### 8.2 Immutable Version-Pinned Core Validator (`ecosystem_core_validator.py`) (NEW in v1.2.0)
- **Single Source of Truth:** `ECOSYSTEM_CONTRACT.md` is the normative specification; `ecosystem-core/validators/ecosystem_core_validator.py` is its **immutable, version-pinned executable conformance check** (`CORE_VALIDATOR_VERSION = "1.2.0"`).
- **Thin Core, Domain-Specific Leaves:** `ecosystem_core_validator.py` enforces ONLY domain-neutral contract invariants (`suite.yaml`, Director `SKILL.md` + `Verdict Envelope`, nested `adapters/` + exact `<suite_id>-` prefix, portability/privacy leak gate, live multi-suite coexistence, Clean-Room `rules.yaml` schema + citation hygiene, and anti-self-auditing/pin immutability). All domain-specific checks (HTML fixtures, SARIF/CWE schemas, eval math) live exclusively in each suite's own `validators/validate_repo.py`.
- **No Local Forking:** Suites MUST NOT manually edit their local copy of `validators/ecosystem_core_validator.py`. Each suite pins `validators/CORE_VALIDATOR.sha256` synced via `ecosystem-core/sync_core.sh`, and CI asserts byte-exact conformance.

### 8.3 Additional Standing Guardrails
- **Domain-Scoped Anti-Cliché:** Operational rule fields MUST reject vague decorative filler phrases (e.g., `"clean UI"`, `"intuitive UX"`, `"modern look"`, `"user-friendly"`, `"seamless experience"`) without banning overloaded technical terms (such as standalone `clean` in `clean room` or `clean build`).
- **Verifiable Citations:** Every `source_id` in operational schemas MUST resolve to a verifiable primary source (DOI, ISBN, RFC, official standard URL, or reproducible empirical benchmark), or be explicitly labeled `UNVERIFIED_SOURCE`.
- **Authoring Process Independence:** Private research workflows, batching strategies, and domain essays belong in suite-specific authoring notes — never inside this interoperability contract.
