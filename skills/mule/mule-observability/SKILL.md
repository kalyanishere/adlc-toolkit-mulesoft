---
name: mule-observability
description: 100-point observability rubric for Mule flows and DataWeave loggers. Loaded by the Phase 5 quality-reviewer + correctness-reviewer (and the Phase 4 task-implementer as a quality bar) when the change set touches src/main/mule/**/*.xml or any flow that emits a `<logger>`. Scores correlation-id propagation, structured logging, log-level discipline, and Anypoint Monitoring instrumentation. Pairs with `mule-flow-quality` (general flow quality) and `mule-error-handling` (handler completeness).
glob: src/main/mule/**/*.xml
dimension: quality
---

# mule-observability (100-pt rubric)

Score Mule flow XML files against this rubric. Observability is non-negotiable per `mulesoft-rules.md` ("Observability Requirements") — yet without a rubric scoring it, reviewers default to flow / error / connector-config concerns and observability gaps slip through. This closes that gap.

## Scope

This rubric scores how well a Mule app emits and propagates the signals an oncall engineer needs at 3 AM:
- structured log payloads that can be parsed and queried in Anypoint Monitoring
- a correlation-id stamped at every flow boundary so a single request can be traced end-to-end
- log-level discipline (so production isn't drowning in DEBUG)
- explicit metric / monitoring touchpoints on public APIs

It does NOT score: business-logic correctness (`mule-error-handling`), DataWeave hygiene (`dataweave-quality`), or general flow shape (`mule-flow-quality`). When a finding overlaps, defer the severity to whichever rubric scores it more heavily.

## Categories (100 points total)

| Category | Points | Focus |
|---|---:|---|
| Correlation-id propagation | 25 | Inbound `MULE_CORRELATION_ID` honored; `vars.correlationId` set at flow start; propagated as header on every downstream connector call |
| Structured logging | 25 | `<logger>` uses DataWeave object payload (not interpolated string concatenation); JSON-shaped output for ingest by Anypoint Monitoring / Splunk / ELK |
| Log-level discipline | 15 | INFO for happy-path checkpoints; ERROR inside `<error-handler>`; WARN for recoverable anomalies; DEBUG off in production |
| Anypoint Monitoring instrumentation | 15 | Public APIs declare a custom dashboard (throughput / latency p50/p99 / error rate); `monitoring-config` element present where SLOs apply |
| Boundary logging | 10 | Inbound request and downstream response logged at the flow boundary (with correlation-id and a redacted summary — not the full payload of a sensitive call) |
| Trace-context handling | 10 | If the inbound carries `traceparent` (W3C Trace Context), it's propagated to every downstream call; if not, a new traceparent is minted and logged |

## Non-negotiables (rule-based; flag any violation as Critical)

- **No raw `<logger message="..."/>`** with string concatenation — every logger emits a DataWeave object payload (cross-checked by `mule-flow-quality` "Logging" row, which deducts 10 of 150)
- **No flow logs raw payload of a PII-flagged operation** (cross-checked by `mule-secrets-hygiene` and `dataweave-quality` Security/PII section). Boundary logs reference `dw/Modules/Redact.dwl` for redaction
- **Every flow either inherits `vars.correlationId` from `MULE_CORRELATION_ID` OR mints one at flow start** — a flow that sets `correlationId = null` or never sets it AT ALL fails the gate
- **No `System.out.println` / `System.err.println`** in any embedded Java module code — always use SLF4J / `<logger>` (also enforced by `tools/mule-lint/check.py`)
- **Public APIs with `governance.api_manager_enabled: true`** must also declare an Anypoint Monitoring dashboard reference (URL or dashboard id) in the spec / Policies.md — when `api_manager_enabled: false`, this is a Minor instead of Critical

## Scoring guidance

- 90-100 pts: production-ready; logs are queryable, traces are stitchable, oncall has the data they need
- 75-89 pts: ship-with-followup; flag improvements as Minor findings (e.g., missing trace-context handling, monitoring dashboard not yet wired)
- 60-74 pts: needs revision before merge; surface as Major findings (e.g., string-concat loggers, missing correlation-id propagation)
- <60 pts: significant rework; block merge — the app is effectively unobservable

## Common findings

| Finding | Severity | Fix |
|---|---|---|
| `<logger message="Order received: #[payload.orderId]"/>` (string concat) | Major | Switch to DW object: `<logger message="#[output application/json --- { event: 'order-received', orderId: payload.orderId, correlationId: vars.correlationId }]"/>` |
| Flow does not set `vars.correlationId` and inbound has no `MULE_CORRELATION_ID` | Critical | Add `<set-variable variableName="correlationId" value="#[uuid()]"/>` at flow start |
| Downstream HTTP request omits `X-Correlation-Id` header | Major | Add `<http:header headerName="X-Correlation-Id" value="#{vars.correlationId}"/>` |
| `<logger level="DEBUG">` in production-deployed flow with no env-conditional | Minor | Wrap in `<choice>` keyed off env property OR demote to TRACE OR remove |
| Boundary log dumps full payload (including PII) | Critical | Pass through `Redact.dwl` before logging; cross-check `mule-secrets-hygiene` |
| Public API has no Anypoint Monitoring dashboard reference | Minor (Major when `api_manager_enabled: true`) | Add `monitoring-dashboard-id` to Policies.md; cross-check `governance-policies` |
| Inbound `traceparent` ignored on every downstream call | Minor | Propagate via `<http:header headerName="traceparent" value="#{attributes.headers.traceparent default uuid()}"/>` |
| Error-handler emits `<logger level="INFO">` | Minor | Promote to `<logger level="ERROR">` — error-paths must surface at ERROR or fatal |
| `<logger>` in tight loop emits per-iteration record | Minor | Aggregate at the end of the loop; per-iteration logs flood Anypoint Monitoring quotas |
| `System.out.println` / `e.printStackTrace()` in embedded Java module | Critical | Replace with SLF4J logger; the lint already flags this — it should never reach review |

## Cross-rubric notes

- **`mule-flow-quality` overlap**: the "Logging" row of `mule-flow-quality` (10 of 150) checks the same string-concat-vs-DW-object dimension. When both rubrics fire on the same logger, the higher severity wins; do not double-count.
- **`mule-error-handling` overlap**: error-handler logging is partially scored by `mule-error-handling`'s "no empty handler" requirement. This rubric scores the *level* and *shape* of the error log; the other scores its *presence*.
- **`mule-secrets-hygiene` overlap**: PII-redaction-before-log is scored by both; defer Critical severity to `mule-secrets-hygiene`.
- **`governance-policies` overlap**: monitoring-dashboard reference per Policies.md row is scored by `governance-policies`; this rubric scores whether the *flow itself* declares monitoring instrumentation.

## Reference

- `.adlc/context/mulesoft-rules.md` "Observability Requirements" section (the source of truth this rubric scores against)
- `partials/mule-quality-checklist.md` (always-on baseline)
- W3C Trace Context spec (`traceparent` / `tracestate` headers)
- Anypoint Monitoring documentation: custom dashboards, alerting, SLO instrumentation
