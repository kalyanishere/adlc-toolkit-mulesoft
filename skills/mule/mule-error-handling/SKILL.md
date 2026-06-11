---
name: mule-error-handling
description: Correctness rubric for Mule error-handler completeness. Loaded by the Phase 5 correctness-reviewer when the change set touches src/main/mule/**/*.xml.
glob: src/main/mule/**/*.xml
dimension: correctness
---

# mule-error-handling (correctness rubric)

Score Mule flow error-handling against this rubric. Focus: silent failure modes, swallowed errors, missing handlers, missing dead-letter pattern.

## Non-negotiables (any violation = Critical)

- **Every flow has an `<error-handler>`** — either inline `<error-handler>` block or referenced via `<flow-ref>` to a global error-handler sub-flow inside a wrapping `<error-handler>`
- **No silent `<try>` scopes** — every `<try>` has a paired `<error-handler>`
- **No empty `<on-error-*>` handlers** — every handler logs (with correlation-id) AND sets a structured error response payload OR re-raises
- **HTTP listener responses set status code** — handler that sets a body but returns the listener's default 200 OK is a defect

## Major findings

- **Catch-all `*` as the only handler** — lacks specific error-type matching; brittle when upstream errors evolve
- **Connector errors not surfaced** — `HTTP:CONNECTIVITY` / `DB:CONNECTIVITY` caught and discarded; caller never knows the upstream failed
- **No error-mapping for upstream-specific errors** — connector-emitted errors (`HTTP:UNAUTHORIZED`, `HTTP:NOT_FOUND`) without explicit handling fall into catch-all
- **Stack-trace exposure** — error response body includes `error.cause` / `error.errorMessage` raw (PII / internal detail leak)
- **No dead-letter queue** for async / batch unrecoverable failures — bad messages silently drop or infinite-loop
- **`<until-successful>` with no upper bound or no back-off** — infinite-retry storm risk

## Minor findings

- **`<error-handler>` not extracted to a global sub-flow** when the same error-mapping repeats across 3+ flows — consolidate to `error-handler-global` per project convention
- **Order of `<on-error-*>` handlers** — most-specific should come first; catch-all (`*`) should be last
- **`error.errorType.namespace`** check used where `error.errorType.identifier` would be more precise

## Routing primitives — error semantics to verify

| Primitive | Verify |
|---|---|
| `<batch:job>` | `max-failed-records` set intentionally; on-complete handler captures aborted records |
| `<scatter-gather>` | downstream consumer checks individual route results; doesn't blindly `<set-payload value="#[payload]"/>` |
| `<async>` | caller doesn't depend on async side-effects (race risk) |
| `<until-successful>` | `maxRetries` set; back-off configured; failure case has explicit handler |
| `<choice>` | `<otherwise>` present; default branch handles "none-of-the-above" payload safely |

## Common findings

| Finding | Severity | Fix |
|---|---|---|
| Flow has no `<error-handler>` | Critical | Add inline handler OR reference global handler sub-flow |
| `<try>` without paired handler | Critical | Wrap in `<error-handler>` block |
| Empty `<on-error-continue/>` | Critical | Add `<logger>` + `<set-payload>` setting structured error response |
| Catch-all `*` is the only handler | Major | Add specific error-type handlers above the catch-all |
| `<until-successful>` with `maxRetries="0"` | Major | Set realistic maxRetries (3-5) + back-off; OR document why retries are disabled |
| `<batch:job>` with no `on-complete` | Major | Add on-complete handler logging aborted-record count |
| Stack trace in error response body | Major | Strip `error.cause`; return only `errorType.identifier` + `error.description` (cleaned) |
| Specific error type below catch-all | Minor | Reorder — most-specific first |

## Reference

- mulesoft-rules.md "Error Handling Requirements" section
- partials/mule-quality-checklist.md (always-on baseline)
