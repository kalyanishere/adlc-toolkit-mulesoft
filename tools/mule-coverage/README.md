# mule-coverage

Parses MUnit coverage reports and asserts they meet the project's coverage floor declared in `.adlc/config.yml`.

## What it reads

- `target/site/munit/coverage/munit-summary.json` (preferred — emitted by `mvn munit:coverage-report`)
- `target/site/munit/coverage/coverage-summary.json` (fallback name used by some MUnit versions)

If neither exists, mule-coverage instructs the user to run `mvn munit:coverage-report` first.

## What it asserts

Read from `.adlc/config.yml` `mulesoft.coverage`:

- **`munit_floor`** (default 80) — overall app coverage percent must be ≥ this.
- **`flow_floor`** (default 75) — when `mode: brownfield`, every flow whose name appears in the diff (changed or new in the open PR) must be ≥ this.
- **`diff_only`** (default false) — when true, gate ONLY changed flows (skip the overall app floor).

Brownfield projects gate both app and per-flow. Greenfield projects gate app-level only. Skills MUST read these from config — never hardcode 75/80.

## Usage

```sh
sh tools/mule-coverage/check.sh           # cwd-discovered project root
sh tools/mule-coverage/check.sh /path/to/project
```

Exits 0 on pass, 1 on coverage shortfall, 2 on missing report or config error.

## Integration

- Called by `tools/mule-preflight/check.sh coverage` as a stage of the pre-deploy gate.
- `/wrapup` calls it before `mvn deploy`.
- Phase 5 test-auditor reviewer reads its JSON output to attach coverage findings to the review report.
