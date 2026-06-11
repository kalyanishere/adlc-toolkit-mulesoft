# mule-preflight

Pre-deploy gate for MuleSoft projects. Mirrors the role of `tools/sf-preflight/` in the SFDC fork: a single shell entry point that runs every blocking check before a deploy is allowed.

This is the **final gate** before `mvn deploy` / DX MCP `deploy_mule_application`. Phase 5 reviewers may have already run mule-lint; preflight runs everything that needs to be green to ship.

## What it runs (in order)

1. **`mule-lint`** — static rule check (`tools/mule-lint/check.sh`). Errors fail the run; warnings print.
2. **`mvn validate compile`** — POM is well-formed, sources compile.
3. **`mvn munit:test`** — full MUnit suite passes.
4. **`mule-coverage`** — parses `target/site/munit/coverage/munit-summary.json` and asserts coverage ≥ `mulesoft.coverage.munit_floor` from `.adlc/config.yml` (default 80). In brownfield mode also asserts per-changed-flow ≥ `mulesoft.coverage.flow_floor` (default 75).
5. **secret scan** — `mule-lint --rules hardcoded-credentials` re-runs across the full source tree (defense-in-depth; same rule but in case lint was bypassed).
6. **policy declarations** — when `governance.api_manager_enabled: true`, asserts that every API instance touched by the change has a corresponding declaration in `Policies.md` (template at `templates/policies-template.md`).
7. **governance scan (optional)** — runs `anypoint-cli-v4 governance:validate` against the API specs in `src/main/resources/api/` if `governance.governance_ruleset` is set in `.adlc/config.yml`.

Each stage is gated independently — you can run a single stage with `sh check.sh <stage>`.

## Usage

```sh
# Run the full pipeline:
sh tools/mule-preflight/check.sh

# Run a single stage:
sh tools/mule-preflight/check.sh lint
sh tools/mule-preflight/check.sh test
sh tools/mule-preflight/check.sh coverage
sh tools/mule-preflight/check.sh secrets
sh tools/mule-preflight/check.sh policies
sh tools/mule-preflight/check.sh governance
```

Each stage exits 0 on pass, non-zero on fail.

## Integration

- Pre-merge gate via GitHub Actions: `.github/workflows/preflight.yml` runs `sh tools/mule-preflight/check.sh` on every PR.
- `/canary` skill calls `sh tools/mule-preflight/check.sh` before promoting Sandbox → Staging or Staging → Prod.
- `/wrapup` skill calls it as the last gate before `mvn deploy`.
