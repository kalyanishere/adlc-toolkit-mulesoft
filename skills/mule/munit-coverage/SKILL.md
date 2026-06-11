---
name: munit-coverage
description: 120-point test-coverage rubric for MUnit suites. Loaded by Phase 5 test-auditor when the change set touches src/test/munit/** OR adds/modifies a flow/dwl that lacks paired tests.
glob: src/test/munit/**/*.xml
dimension: test-coverage
---

# munit-coverage (120-pt rubric)

Score MUnit suites against this rubric. Coverage threshold from `.adlc/config.yml` `mulesoft.coverage`.

## Categories (120 points total)

| Category | Points | Focus |
|---|---:|---|
| Coverage thresholds | 20 | app-level ≥ `munit_floor`; per-flow ≥ `flow_floor` (brownfield) |
| Mock completeness | 25 | every external connector mocked; happy + error paths |
| Assertion quality | 20 | meaningful assertions; not just "no exception thrown" |
| Suite structure | 15 | `<munit:before-suite>` / `<munit:before-test>` for setup; one suite per flow |
| Verify-call discipline | 10 | `<munit-tools:verify-call>` for connector invocation count |
| Determinism | 10 | no `Thread.sleep`; no real-clock dependencies |
| Fixture data | 10 | realistic payload shapes (not `{}`); fixtures under `src/test/resources/` |
| Naming | 10 | `<flow-name>-test-suite.xml`; test methods describe scenario |

## Non-negotiables (any violation = Critical)

- **Every flow has at least one MUnit test**
- **All external connectors mocked** via `<munit-tools:mock-when>` — no real HTTP/DB/SFDC/Kafka/JMS callouts
- **App-level coverage ≥ `mulesoft.coverage.munit_floor`** (default 80) with meaningful assertions
- **Per-changed-flow coverage ≥ `mulesoft.coverage.flow_floor`** (default 75) in brownfield mode
- **No `Thread.sleep`** — use `<munit-tools:sleep>` or assertion-based waits

## Major findings

- **Mock returns wrong shape**: mocked response payload doesn't match the upstream's actual contract — passes the test, fails in prod
- **Vacuous assertion**: `<munit:assertion-equal expected="#[true]" actual="#[true]"/>` or assertion on a field never written
- **Happy-path-only**: no test case for the error-handler branches
- **Missing `<munit-tools:verify-call>`**: assertion on payload but never verifies the connector was invoked the expected number of times
- **No assertion on side-effects**: test proves the response shape but not that the upstream call happened
- **Test depends on environment data**: queries against a live DB / org / queue at runtime

## Minor findings

- **Fixture is minimal `{}`** when the upstream actually returns a complex payload — increases false-positive risk
- **One suite covers many unrelated flows** — split per-flow for clarity
- **`<munit:before-suite>`** doing per-test setup that should be `<munit:before-test>` (or vice-versa)
- **Determinism**: `now()` in DW or system time used in fixtures without freezing — DST / parallel-worker collision risk
- **Auto-generated UUIDs in assertions** — match by deterministic field instead

## Mock conventions to verify

| Connector | Mock should cover |
|---|---|
| `<http:request>` | 200 (happy), 4xx, 5xx |
| `<db:select>` / `<db:insert>` | success, connection error, constraint violation |
| `<salesforce:query>` / `<salesforce:upsert>` | success, INVALID_FIELD, MALFORMED_QUERY |
| `<kafka:publish>` / `<jms:publish>` | success, broker unavailable |
| `<sftp:write>` / `<file:write>` | success, permission denied, disk full |
| `<email:send>` | success, SMTP unavailable |

## Scoring guidance

- 105-120 pts: production-ready test posture
- 90-104 pts: minor mock or assertion gaps; ship-with-followup
- 75-89 pts: significant gaps; needs revision before merge
- <75 pts: insufficient — block

## Common findings

| Finding | Severity | Fix |
|---|---|---|
| Flow has no MUnit suite | Critical | Author one via DX MCP `generate_munit_test` |
| External connector not mocked | Critical | Add `<munit-tools:mock-when>` for the operation |
| `Thread.sleep` in test | Major | Use `<munit-tools:sleep>` or assertion-based waits |
| Coverage below `flow_floor` | Critical (brownfield) | Add tests covering missing branches |
| Vacuous assertion | Major | Replace with assertion on real payload field |
| No `<munit-tools:verify-call>` | Major | Assert the upstream connector was invoked N times |

## Reference

- mulesoft-rules.md "MUnit Requirements" section
- partials/mule-quality-checklist.md (always-on baseline)
- DX MCP `generate_munit_test` / `modify_munit_test` are the canonical authoring path
