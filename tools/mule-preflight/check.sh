#!/bin/sh
# mule-preflight — pre-deploy gate for MuleSoft projects.
#
# Usage:
#   sh tools/mule-preflight/check.sh           # run all stages
#   sh tools/mule-preflight/check.sh <stage>   # run a single stage
#
# Stages: lint test coverage secrets policies governance

set -u

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
TOOLKIT_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
PROJECT_ROOT=${PROJECT_ROOT:-$(pwd)}

# When invoked from a consumer project, find the project root by climbing for pom.xml.
find_project_root() {
  p=$(pwd)
  while [ "$p" != "/" ]; do
    if [ -f "$p/pom.xml" ]; then
      echo "$p"
      return 0
    fi
    p=$(dirname "$p")
  done
  echo "$PROJECT_ROOT"
}

PROJECT_ROOT=$(find_project_root)

log() { printf "[mule-preflight] %s\n" "$*"; }
err() { printf "[mule-preflight] ERROR: %s\n" "$*" >&2; }

stage_header() { printf "\n========== %s ==========\n" "$1"; }

# --- stage: lint ---
run_lint() {
  stage_header "lint"
  if [ -x "$TOOLKIT_ROOT/tools/mule-lint/check.sh" ]; then
    sh "$TOOLKIT_ROOT/tools/mule-lint/check.sh" "$PROJECT_ROOT"
  elif [ -x "$HOME/.claude/skills-mulesoft/tools/mule-lint/check.sh" ]; then
    sh "$HOME/.claude/skills-mulesoft/tools/mule-lint/check.sh" "$PROJECT_ROOT"
  else
    err "mule-lint not found at $TOOLKIT_ROOT/tools/mule-lint/check.sh"
    return 2
  fi
}

# --- stage: test ---
run_test() {
  stage_header "test (mvn validate compile munit:test)"
  if ! command -v mvn >/dev/null 2>&1; then
    err "mvn not found in PATH"
    return 2
  fi
  cd "$PROJECT_ROOT" || return 2
  mvn -q validate compile munit:test
}

# --- stage: coverage ---
run_coverage() {
  stage_header "coverage"
  if [ -x "$TOOLKIT_ROOT/tools/mule-coverage/check.sh" ]; then
    sh "$TOOLKIT_ROOT/tools/mule-coverage/check.sh" "$PROJECT_ROOT"
  elif [ -x "$HOME/.claude/skills-mulesoft/tools/mule-coverage/check.sh" ]; then
    sh "$HOME/.claude/skills-mulesoft/tools/mule-coverage/check.sh" "$PROJECT_ROOT"
  else
    err "mule-coverage not found"
    return 2
  fi
}

# --- stage: secrets ---
run_secrets() {
  stage_header "secrets (re-run lint with --rules hardcoded-credentials)"
  if [ -x "$TOOLKIT_ROOT/tools/mule-lint/check.sh" ]; then
    sh "$TOOLKIT_ROOT/tools/mule-lint/check.sh" --rules hardcoded-credentials "$PROJECT_ROOT"
  else
    err "mule-lint not found"
    return 2
  fi
}

# --- stage: policies ---
run_policies() {
  stage_header "policies"
  config="$PROJECT_ROOT/.adlc/config.yml"
  if [ ! -f "$config" ]; then
    log "no .adlc/config.yml — skipping policies stage"
    return 0
  fi
  enabled=$(grep -E '^\s*api_manager_enabled:\s*true' "$config" 2>/dev/null || true)
  if [ -z "$enabled" ]; then
    log "governance.api_manager_enabled is not true — skipping policies stage"
    return 0
  fi
  # Look for at least one Policies.md somewhere under .adlc/specs/ touched by the open change.
  if find "$PROJECT_ROOT/.adlc/specs" -type f -name 'Policies.md' 2>/dev/null | grep -q .; then
    log "found Policies.md declaration(s)"
    return 0
  fi
  err "governance.api_manager_enabled is true but no Policies.md found under .adlc/specs/"
  err "  → generate from templates/policies-template.md as part of /wrapup"
  return 1
}

# --- stage: governance ---
run_governance() {
  stage_header "governance (anypoint-cli-v4 governance:validate)"
  config="$PROJECT_ROOT/.adlc/config.yml"
  if [ ! -f "$config" ]; then
    log "no .adlc/config.yml — skipping governance stage"
    return 0
  fi
  ruleset=$(grep -E '^\s*governance_ruleset:' "$config" 2>/dev/null | head -1 | sed -E 's/.*:[[:space:]]*"?([^"#]*)"?.*/\1/' | tr -d ' ')
  if [ -z "$ruleset" ]; then
    log "no governance.governance_ruleset configured — skipping"
    return 0
  fi
  if ! command -v anypoint-cli-v4 >/dev/null 2>&1; then
    err "anypoint-cli-v4 not found in PATH (governance scan skipped — install per README prerequisites)"
    return 2
  fi
  api_root="$PROJECT_ROOT/src/main/resources/api"
  if [ ! -d "$api_root" ]; then
    log "no API specs at $api_root — skipping"
    return 0
  fi
  # Iterate spec files; one validate per spec.
  fail=0
  find "$api_root" -type f \( -name '*.raml' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml' \) | while read -r spec; do
    log "validating $spec against ruleset=$ruleset"
    if ! anypoint-cli-v4 governance:validate --rulesets "$ruleset" "$spec"; then
      err "governance validation failed for $spec"
      fail=1
    fi
  done
  return $fail
}

run_all() {
  rc=0
  for stage in lint test coverage secrets policies governance; do
    if ! run_$stage; then
      rc=1
    fi
  done
  return $rc
}

case "${1:-all}" in
  all) run_all ;;
  lint) run_lint ;;
  test) run_test ;;
  coverage) run_coverage ;;
  secrets) run_secrets ;;
  policies) run_policies ;;
  governance) run_governance ;;
  *) err "unknown stage: ${1}"; exit 2 ;;
esac
