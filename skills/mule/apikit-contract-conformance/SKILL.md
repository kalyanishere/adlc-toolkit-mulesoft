---
name: apikit-contract-conformance
description: Architecture rubric for APIkit-bound contracts. Loaded by Phase 5 architecture-reviewer when the change set touches src/main/resources/api/** OR an HTTP listener flow.
glob: src/main/resources/api/**, src/main/mule/**/*.xml
dimension: architecture
---

# apikit-contract-conformance (architecture rubric)

Score HTTP-facing Mule apps against contract-first / APIkit-router convention.

## Non-negotiables

- **Spec-first**: every HTTP-facing app has a contract under `src/main/resources/api/` (RAML 1.0 or OAS 3.0)
- **APIkit router bound**: the listener-flow contains an `<apikit:router>` element bound to that spec via `<apikit:config>`
- **No hand-rolled routing** in `<choice>` blocks for the main API entry flow — APIkit owns it
- **Generated flow names match spec**: APIkit-generated flows follow `<verb>:<path>:<application>` exactly

## Major findings

- **Spec / flow drift**: a flow returns a payload shape not declared in the RAML/OAS response model
- **Path mismatch**: APIkit `<flow>` name doesn't match the spec's `<verb>:<path>:<application>` pattern
- **Required field missing handling**: spec says `tier` is required but the flow accepts payloads without it (and APIkit didn't reject — config issue)
- **No `<api>-console` flow** in non-prod: self-service exploration is missing
- **Trait inconsistency**: same trait (`client-id-required`, `rate-limited`) declared inline in some endpoints, as a trait reference in others

## Minor findings

- **Examples not reused via `!include`**: copy-pasted JSON-Schema across endpoints
- **No data-types** declared — schemas inlined in every response model
- **Versioning inconsistent**: spec version + URL path + Accept header convention don't agree
- **Spec format mixed**: RAML 1.0 AND OAS 3.0 in the same project (pick one)
- **API title field missing** — Anypoint Exchange listing shows asset-id instead of human-readable title

## Spec quality (RAML/OAS specifics)

| Element | Verify |
|---|---|
| `title` | Human-readable name, not asset-id |
| `version` | Semver; bumps on breaking change |
| `mediaType` | Default declared (typically `application/json`) |
| `protocols` | Production: `HTTPS` only; Sandbox may include `HTTP` |
| `baseUri` | Parameterized via `{environment}` placeholder, not hardcoded |
| `securitySchemes` | Declared at root; applied per-endpoint via `securedBy` |
| Examples | Reused via `!include` from `examples/` |
| Data types | Reused via `!include` from `dataTypes/` |
| Traits | Cross-cutting concerns (client-id-required, rate-limited, paginated) extracted as traits |
| Resource-types | Boilerplate (CRUD shapes) extracted as resource-types |

## Live-state verification

Reviewers SHOULD call Platform MCP `view_api_version_details` for the deployed API instance to verify:
- The spec version registered in API Manager matches `pom.xml` / RAML version
- The deployed listener-flow path matches the spec's resource paths

## Common findings

| Finding | Severity | Fix |
|---|---|---|
| HTTP-facing app with no `<apikit:router>` | Critical | Bind the spec via `<apikit:config>` + `<apikit:router>`; remove hand-rolled `<choice>` routing |
| Flow name doesn't match `<verb>:<path>:<application>` | Major | Rename to APIkit's expected pattern or regenerate via DX MCP `implement_api_spec` |
| Spec response model doesn't match flow output | Major | Update spec OR update flow to match (depends on which is canonical) |
| Multi-format spec project (RAML + OAS) | Major | Standardize on one format |
| Spec version drift from `pom.xml` | Minor | Sync spec `version` with `pom.xml` `<version>` semver |

## Reference

- mulesoft-rules.md "Mule XML / Flow Requirements" → APIkit-first
- APIkit docs: https://docs.mulesoft.com/apikit/latest/
- DX MCP `generate_api_spec` and `implement_api_spec` are the canonical authoring path
