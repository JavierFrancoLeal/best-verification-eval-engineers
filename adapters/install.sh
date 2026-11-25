#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SUITE_ID="verification-eval"
DIRECTOR_SLUG="verification-director"
REPO_NAME="best-verification-eval-engineers"

TARGET="all"
MODE="director-only"
SCOPE="workspace"
DEST=""
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: install.sh [OPTIONS]

Install best-verification-eval-engineers (suite_id: verification-eval) into
one or more coding-agent harnesses without colliding with sibling ECOSYSTEM_CONTRACT v1.2.0 suites.

Options:
  --target <name>   antigravity | deepseek | claude | codex | cursor | windsurf | all (default: all)
  --mode <mode>     director-only | full (default: director-only)
  --scope <scope>   workspace | global (default: workspace)
  --dest <path>     Destination workspace root (required for workspace scope if not PWD)
  --dry-run         Print planned operations without writing files
  -h, --help        Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --mode)   MODE="${2:-}"; shift 2 ;;
    --scope)  SCOPE="${2:-}"; shift 2 ;;
    --dest)   DEST="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "ERROR: Unknown argument: $1" >&2; usage >&2; exit 1 ;;
  esac
done

case "${TARGET}" in
  antigravity|deepseek|claude|codex|cursor|windsurf|all) ;;
  *) echo "ERROR: Invalid --target '${TARGET}'" >&2; exit 1 ;;
esac

case "${MODE}" in
  director-only|full) ;;
  *) echo "ERROR: Invalid --mode '${MODE}' (expected director-only or full)" >&2; exit 1 ;;
esac

case "${SCOPE}" in
  workspace|global) ;;
  *) echo "ERROR: Invalid --scope '${SCOPE}' (expected workspace or global)" >&2; exit 1 ;;
esac

if [[ "${SCOPE}" == "workspace" ]]; then
  [[ -n "${DEST}" ]] || DEST="$(pwd)"
else
  [[ -n "${DEST}" ]] || DEST="${HOME}"
fi

log() {
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    printf '[dry-run] %s\n' "$*"
  else
    printf '[install] %s\n' "$*"
  fi
}

run_mkdir() {
  local dir="$1"
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    log "mkdir -p ${dir}"
  else
    mkdir -p "${dir}"
  fi
}

copy_file() {
  local src="$1"
  local dst="$2"
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    log "copy file ${src} -> ${dst}"
  else
    mkdir -p "$(dirname "${dst}")"
    cp "${src}" "${dst}"
  fi
}

safe_replace_owned_dir() {
  local src="$1"
  local dst="$2"
  local expected_prefix="$3"
  local base
  base="$(basename "${dst}")"
  if [[ "${base}" != "${expected_prefix}"* && "${base}" != "${DIRECTOR_SLUG}" ]]; then
    echo "ERROR: Refusing to replace unowned directory '${dst}'" >&2
    exit 1
  fi
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    log "sync dir ${src} -> ${dst}"
  else
    mkdir -p "$(dirname "${dst}")"
    rm -rf "${dst}"
    cp -R "${src}" "${dst}"
  fi
}

install_lazy_references() {
  local director_dst="$1"
  run_mkdir "${director_dst}/references/modules"
  run_mkdir "${director_dst}/references/auditors"
  run_mkdir "${director_dst}/tools"

  copy_file "${REPO_ROOT}/suite.yaml" "${director_dst}/references/suite.yaml"
  copy_file "${REPO_ROOT}/committee/${DIRECTOR_SLUG}/control-matrix.yaml" "${director_dst}/references/control-matrix.yaml"
  [[ -f "${REPO_ROOT}/tools/verify_cpu_scanner.py" ]] && copy_file "${REPO_ROOT}/tools/verify_cpu_scanner.py" "${director_dst}/tools/verify_cpu_scanner.py"
  [[ -f "${REPO_ROOT}/tools/eval_ingest.py" ]] && copy_file "${REPO_ROOT}/tools/eval_ingest.py" "${director_dst}/tools/eval_ingest.py"

  # Anti-recursive-discovery: keep PROFILE.md / AUDITOR.md / BRIEF.md / VERIFY.md
  # with ZERO nested SKILL.md under references/ so **/SKILL.md indexes strictly 1 skill per suite.
  for d in "${REPO_ROOT}"/modules/*; do
    [[ -d "${d}" ]] || continue
    local slug
    slug="$(basename "${d}")"
    local dst_m="${director_dst}/references/modules/${slug}"
    run_mkdir "${dst_m}"
    [[ -f "${d}/BRIEF.md" ]] && copy_file "${d}/BRIEF.md" "${dst_m}/BRIEF.md"
    [[ -f "${d}/VERIFY.md" ]] && copy_file "${d}/VERIFY.md" "${dst_m}/VERIFY.md"
    [[ -f "${d}/PROFILE.md" ]] && copy_file "${d}/PROFILE.md" "${dst_m}/PROFILE.md"
  done

  for a in "${REPO_ROOT}"/committee/auditors/*; do
    [[ -d "${a}" ]] || continue
    local aslug
    aslug="$(basename "${a}")"
    local dst_a="${director_dst}/references/auditors/${aslug}"
    run_mkdir "${dst_a}"
    [[ -f "${a}/rules.yaml" ]] && copy_file "${a}/rules.yaml" "${dst_a}/rules.yaml"
    [[ -f "${a}/AUDITOR.md" ]] && copy_file "${a}/AUDITOR.md" "${dst_a}/AUDITOR.md"
  done
}

INSTALLED_SKILL_DIRS="|"
install_skills_into() {
  local skills_dir="$1"
  if [[ "${INSTALLED_SKILL_DIRS}" == *"|${skills_dir}|"* ]]; then
    return 0
  fi
  INSTALLED_SKILL_DIRS="${INSTALLED_SKILL_DIRS}${skills_dir}|"

  run_mkdir "${skills_dir}"
  local director_dst="${skills_dir}/${DIRECTOR_SLUG}"

  if [[ "${MODE}" == "director-only" ]]; then
    log "Installing director-only (1 active SKILL.md + non-recursive references/ + CPU tools) into ${skills_dir}"
    run_mkdir "${director_dst}"
    copy_file "${REPO_ROOT}/committee/${DIRECTOR_SLUG}/SKILL.md" "${director_dst}/SKILL.md"
    install_lazy_references "${director_dst}"
  else
    log "Installing full mode (namespaced ${SUITE_ID}-* modules + director + CPU tools) into ${skills_dir}"
    run_mkdir "${director_dst}"
    copy_file "${REPO_ROOT}/committee/${DIRECTOR_SLUG}/SKILL.md" "${director_dst}/SKILL.md"
    install_lazy_references "${director_dst}"
    for d in "${REPO_ROOT}"/modules/*; do
      [[ -d "${d}" ]] || continue
      local slug
      slug="$(basename "${d}")"
      local dst_m="${skills_dir}/${SUITE_ID}-${slug}"
      safe_replace_owned_dir "${d}" "${dst_m}" "${SUITE_ID}-"
      if [[ "${DRY_RUN}" -eq 0 && -f "${dst_m}/PROFILE.md" ]]; then
        mv "${dst_m}/PROFILE.md" "${dst_m}/SKILL.md"
      fi
    done
    for a in "${REPO_ROOT}"/committee/auditors/*; do
      [[ -d "${a}" ]] || continue
      local aslug
      aslug="$(basename "${a}")"
      local dst_a="${skills_dir}/${SUITE_ID}-${aslug}"
      safe_replace_owned_dir "${a}" "${dst_a}" "${SUITE_ID}-"
      if [[ "${DRY_RUN}" -eq 0 && -f "${dst_a}/AUDITOR.md" ]]; then
        mv "${dst_a}/AUDITOR.md" "${dst_a}/SKILL.md"
      fi
    done
  fi
}

upsert_fenced_block() {
  local target_file="$1"
  local begin_marker="<!-- BEGIN ${REPO_NAME} -->"
  local end_marker="<!-- END ${REPO_NAME} -->"
  local block="$2"

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    log "upsert fenced block (${begin_marker} .. ${end_marker}) into ${target_file}"
    return 0
  fi

  mkdir -p "$(dirname "${target_file}")"
  if [[ ! -f "${target_file}" ]]; then
    printf '# %s\n\n%s\n' "$(basename "${target_file}")" "${block}" > "${target_file}"
  elif grep -qF "${begin_marker}" "${target_file}"; then
    local tmp_file block_file
    tmp_file="$(mktemp)"
    block_file="$(mktemp)"
    printf '%s\n' "${block}" > "${block_file}"
    awk -v begin="${begin_marker}" -v end="${end_marker}" -v bfile="${block_file}" '
      $0 == begin {
        while ((getline line < bfile) > 0) print line
        close(bfile)
        skip=1
        next
      }
      $0 == end { skip=0; next }
      !skip { print }
    ' "${target_file}" > "${tmp_file}"
    mv "${tmp_file}" "${target_file}"
    rm -f "${block_file}"
  else
    printf '\n%s\n' "${block}" >> "${target_file}"
  fi
}

AGENTS_UPSERTED=0
upsert_agents_md() {
  local workspace_root="$1"
  local skills_rel="${2:-.agents/skills}"
  if [[ "${AGENTS_UPSERTED}" -eq 1 ]]; then
    return 0
  fi
  AGENTS_UPSERTED=1

  local agents_file="${workspace_root}/AGENTS.md"
  local claude_link="${workspace_root}/CLAUDE.md"

  local block
  block="$(cat <<EOF
<!-- BEGIN best-verification-eval-engineers -->
## Verification & EvalOps Pre-Merge Gate (\`best-verification-eval-engineers\`, \`suite_id: verification-eval\`, v1.2.0)
- **Step 0 (CPU-First Fail-Closed):** Run \`python3 ${skills_rel}/verification-director/tools/verify_cpu_scanner.py --target . --sarif-out verify_cpu_scanner.sarif\` and ingest JUnit/coverage/mutation evidence via \`python3 ${skills_rel}/verification-director/tools/eval_ingest.py\`.
- **Fast PR Gate (\`build\`/\`verify\`):** Route via \`${skills_rel}/verification-director/references/control-matrix.yaml\`; escalate test theater, mocking, or eval harness edits to Clean-Room cross-model auditors (\`auditor-test-integrity\`, \`auditor-evalops-validity\`).
- **Anti-Self-Auditing:** Builder agents MUST NOT edit \`tests/\`, \`evals/\`, \`rules.yaml\`, \`validators/\`, or audit logs to manufacture \`SHIP\`. Emit \`Verdict Envelope v1.2.0\`.
<!-- END best-verification-eval-engineers -->
EOF
)"

  upsert_fenced_block "${agents_file}" "${block}"

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    log "ensure ${claude_link} symlinks to AGENTS.md (or upsert fenced block if regular file exists)"
    return 0
  fi

  if [[ ! -e "${claude_link}" && ! -L "${claude_link}" ]]; then
    (cd "${workspace_root}" && ln -s "AGENTS.md" "CLAUDE.md")
  elif [[ -f "${claude_link}" && ! -L "${claude_link}" ]]; then
    upsert_fenced_block "${claude_link}" "${block}"
  fi
}

install_antigravity() {
  if [[ "${SCOPE}" == "workspace" ]]; then
    install_skills_into "${DEST}/.agents/skills"
    copy_file "${REPO_ROOT}/adapters/antigravity/${SUITE_ID}-bootstrap.md" "${DEST}/.agents/rules/${SUITE_ID}-bootstrap.md"
    upsert_agents_md "${DEST}"
  else
    install_skills_into "${DEST}/.gemini/config/skills"
    copy_file "${REPO_ROOT}/adapters/antigravity/${SUITE_ID}-bootstrap.md" "${DEST}/.gemini/config/rules/${SUITE_ID}-bootstrap.md"
  fi
}

install_deepseek() {
  local skills_dir="${DEST}/.agents/skills"
  install_skills_into "${skills_dir}"
  copy_file "${REPO_ROOT}/adapters/deepseek-harness/dsh-plugin.json" "${skills_dir}/${DIRECTOR_SLUG}/dsh-plugin.json"
  if [[ "${SCOPE}" == "workspace" ]]; then
    upsert_agents_md "${DEST}"
  fi
}

install_claude() {
  install_skills_into "${DEST}/.claude/skills"
  if [[ "${SCOPE}" == "workspace" ]]; then
    upsert_agents_md "${DEST}" ".claude/skills"
  fi
}

install_codex() {
  install_skills_into "${DEST}/.agents/skills"
  if [[ "${SCOPE}" == "workspace" ]]; then
    upsert_agents_md "${DEST}" ".agents/skills"
  fi
}

install_cursor() {
  install_skills_into "${DEST}/.cursor/skills"
  if [[ "${SCOPE}" == "workspace" ]]; then
    copy_file "${REPO_ROOT}/adapters/cursor/${SUITE_ID}-director.mdc" "${DEST}/.cursor/rules/${SUITE_ID}-director.mdc"
    upsert_agents_md "${DEST}" ".cursor/skills"
  fi
}

install_windsurf() {
  install_skills_into "${DEST}/.windsurf/skills"
  if [[ "${SCOPE}" == "workspace" ]]; then
    copy_file "${REPO_ROOT}/adapters/windsurf-devin/${SUITE_ID}-director.md" "${DEST}/.devin/rules/${SUITE_ID}-director.md"
    copy_file "${REPO_ROOT}/adapters/windsurf-devin/${SUITE_ID}-director.md" "${DEST}/.windsurf/rules/${SUITE_ID}-director.md"
    upsert_agents_md "${DEST}" ".windsurf/skills"
  fi
}

log "Starting ${REPO_NAME} installer (target=${TARGET}, mode=${MODE}, scope=${SCOPE}, dest=${DEST})"

case "${TARGET}" in
  antigravity) install_antigravity ;;
  deepseek)    install_deepseek ;;
  claude)      install_claude ;;
  codex)       install_codex ;;
  cursor)      install_cursor ;;
  windsurf)    install_windsurf ;;
  all)
    install_antigravity
    install_deepseek
    install_claude
    install_codex
    install_cursor
    install_windsurf
    ;;
esac

log "Completed installation successfully."
