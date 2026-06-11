---
name: api-led-architecture
description: Architecture rubric for API-led layering. Loaded by Phase 5 architecture-reviewer when the change set touches src/main/mule/, src/main/resources/api/, or pom.xml api.layer property.
glob: src/main/mule/**, src/main/resources/api/**, pom.xml
dimension: architecture
---

# api-led-architecture (architecture rubric)

Score Mule apps against the System / Process / Experience layering convention.

## Non-negotiables

- **`<api.layer>` declared** in `pom.xml` `<properties>` — one of `system | process | experience`
- **System APIs** talk to systems-of-record only — no calls to other Process / Experience APIs
- **Process APIs** orchestrate System APIs — no direct calls to systems-of-record (bypasses the System layer)
- **Experience APIs** orchestrate Process APIs (and occasionally System APIs for read-through) — no business logic

## Layer responsibilities

| Layer | What it does | What it MUST NOT do |
|---|---|---|
| **System** | Wraps a system-of-record (Salesforce, Database, ERP). One per upstream. Exposes a clean canonical contract that hides the upstream's quirks. | Talk to other Process / Experience APIs. Contain business logic that's domain-specific to a process. |
| **Process** | Composes 2+ System APIs to fulfill a business operation. Owns transformations, validation, error mapping. | Call upstream systems-of-record directly. Render UI-shaped payloads. Be a thin pass-through (collapse to System). |
| **Experience** | Adapts Process APIs to a specific channel (web, mobile, partner). Owns response shaping, channel auth, throttling. | Contain business logic. Call System APIs directly (except for read-through cases). Be reusable across multiple channels. |

## Major findings (architecture violations)

- **Layer not declared** — `pom.xml` missing `<api.layer>` property → architect can't reason about the app's role
- **Process API directly invokes a system-of-record**: `<salesforce:query>` / `<db:select>` against the upstream rather than calling the System API
- **Experience API directly invokes a System API** for business logic (read-through is OK; orchestration is not)
- **System API depends on a Process API** (in `pom.xml` Exchange dependencies) — direction reversal
- **Two System APIs share a connector config** to the same upstream — should be ONE System API per upstream

## Minor findings

- **Reuse opportunity**: Experience API re-implements logic already exposed by an existing Process API
- **Layer naming inconsistency**: `<api.layer>` value not in {system, process, experience} (e.g., "core", "orchestrator")
- **`<asset>` artifact name** doesn't reflect layer (e.g., a Process API named `customers-api` instead of `customers-process-api`)
- **Documentation gap**: `architecture.md` doesn't list cross-API dependencies; reviewer can't trace the layer graph

## Live-state verification

Reviewers SHOULD call Platform MCP `view_api_version_details` for the deployed API instance to verify:
- The layer declared in `pom.xml` matches the layer registered in API Manager
- Cross-API dependencies (Exchange `<dependency>` blocks in `pom.xml`) resolve to actual deployed assets

## Common findings

| Finding | Severity | Fix |
|---|---|---|
| Process API directly invokes Salesforce | Critical | Replace `<salesforce:query>` with `<http:request config-ref="customers-system-api-config" .../>` |
| `<api.layer>` missing from pom.xml | Major | Add `<api.layer>process</api.layer>` (or appropriate layer) to `<properties>` |
| Experience API contains business logic | Major | Move logic to a Process API; Experience should adapt only |
| Two System APIs for same upstream | Major | Consolidate; one per upstream |
| Cross-layer reuse missed | Minor | Refactor Experience API to call existing Process API instead of re-implementing |

## Reference

- mulesoft-rules.md "MuleSoft Application Development Requirements" → Architectural Integrity
- API-led connectivity overview: https://www.mulesoft.com/resources/api/what-is-api-led-connectivity
- Companion rubric: `apikit-contract-conformance` (contract-first within a single API)
