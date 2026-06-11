---
name: mule-flow-quality
description: 150-point quality rubric for Mule XML flows. Loaded by the Phase 5 quality-reviewer (and the Phase 4 task-implementer as a quality bar) when the change set touches src/main/mule/**/*.xml (excluding test suites).
glob: src/main/mule/**/*.xml
dimension: quality
---

# mule-flow-quality (150-pt rubric)

Score Mule flow XML files against this rubric. Pair with `mule-error-handling` (correctness) and `mule-connector-config-hygiene` (architecture) for full coverage.

## Categories (150 points total)

| Category | Points | Focus |
|---|---:|---|
| Naming & structure | 25 | kebab-case names, business-meaningful, one responsibility per flow, sub-flow extraction |
| Composition | 20 | `<flow-ref>` reuse, choice/routing patterns, no copy-paste |
| Documentation | 15 | `doc:description` ≤3 lines on every flow / sub-flow / connector op |
| Naming conventions | 15 | flow / sub-flow / global-config naming follows project pattern |
| File organization | 15 | newspaper rule (top-level entries first, sub-flows below); related flows grouped |
| Connector ops | 15 | every operation has `config-ref`; no inline config |
| Routing primitives | 15 | `<choice>` with explicit `<otherwise>`; `<scatter-gather>` / `<async>` used intentionally |
| Logging | 10 | `<logger>` uses DataWeave object payload; correlation-id propagated |
| Variable hygiene | 10 | `vars` named meaningfully; no leak across sub-flow boundaries |
| Streaming | 10 | `repeatable-file-store-stream` for >5MB payloads |

## Non-negotiables (rule-based; flag any violation)

- Every flow has a meaningful kebab-case name (no `flow1`, `flow-copy`, `Untitled-flow`)
- Every flow has at least one MUnit test (cross-checked by `munit-coverage` rubric)
- HTTP-facing apps use `<apikit:router>` bound to RAML/OAS — not hand-rolled `<choice>` routing for the main API entry flow (cross-checked by `apikit-contract-conformance`)
- One responsibility per flow — validation and persistence in separate flows
- Logic reused via `<flow-ref>` to sub-flows (no duplicated logic across flows)

## Scoring guidance

- 135-150 pts: production-ready; minor polish only
- 120-134 pts: ship-with-followup; flag improvements as Minor findings
- 100-119 pts: needs revision before merge; surface as Major findings
- <100 pts: significant rework; block merge

## Common findings

| Finding | Severity | Fix |
|---|---|---|
| Flow named `flow1` | Minor | Rename to `<system>-<intent>-flow` |
| Inline credentials on `<http:request>` | Critical | Move to global `<http:request-config>` |
| `<choice>` with no `<otherwise>` | Major | Add explicit otherwise branch |
| `doc:description` is multi-paragraph | Minor | Trim to ≤3 lines; link the spec |
| Two flows with copy-pasted body | Minor | Extract to a `<sub-flow>` |
| `<logger message="hello world"/>` | Minor | Use DW object: `<logger message="#[output application/json --- { ... }]"/>` |
| Sub-flow only called once | Minor | Inline (or document the future-reuse intent) |
| Newspaper rule violated (sub-flows above their callers) | Minor | Reorder |

## Reference

- mulesoft-rules.md "Mule XML / Flow Requirements" section
- partials/mule-quality-checklist.md (always-on baseline)
- The official `build-mule-integration` skill defines the canonical scaffolding shape — use it for new flows, not first-principles XML
