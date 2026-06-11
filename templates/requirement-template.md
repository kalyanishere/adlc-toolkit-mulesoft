---
id: XYZ-REQ-001       # `<project.shortname>-REQ-NNN` from .adlc/config.yml; allocated by /spec Step 2 via partials/id-counter.sh
title: "Feature Title"
status: draft
deployable: true
complexity: small   # trivial | small | medium | large — drives /proceed phase shape (REQ-C)
dependencies: []    # other REQ ids this one waits on (set by /spec Step 1.8.4 when decomposed; empty for standalone REQs). /sprint respects these edges.
created: YYYY-MM-DD
updated: YYYY-MM-DD
component: ""       # narrow area, e.g., "API/auth", "iOS/SwiftUI", "adlc/spec"
domain: ""          # broad area, e.g., "auth", "payments", "ui"
stack: []           # tech layers touched, e.g., ["express", "firestore"]
concerns: []        # cross-cutting dimensions, e.g., ["security", "performance", "a11y"]
tags: []            # free-form keywords, e.g., ["password-reset", "tokens"]
---

<!--
  complexity tiers (REQ-C):
    trivial — single-file config change, no flow logic, no architectural decisions
              (e.g., property value bump, deploy-profile vCore tweak, doc:description
              touch-up, governance-ruleset version update).
              /proceed: skip validate gates, no architect fan-out, no implementer
              agent, reflect-only review, sandbox-only canary.
    small   — ≤3 files, no new pattern (e.g., 1 flow + 1 MUnit suite, 1 DataWeave
              module, 1 sub-flow extraction). /proceed: inline architect,
              implementer per task, 2-agent review (reflect + quality),
              sandbox-only canary.
    medium  — 4-10 files OR introduces a new pattern (new connector config + flow,
              new System or Process API spec + APIkit binding, first integration
              with an upstream system, new batch job). /proceed: full pipeline.
            large   — >10 files OR cross-API-tier (System + Process + Experience together,
              new shared dw/Modules/, multi-app monorepo). /proceed: full pipeline
              + ADR capture.
-->


## Description

What the feature does and why.

## Decomposition Context

_Present only when this REQ was allocated as a child of a multi-layer feature decomposition (`/spec` Step 1.8). Delete this section for standalone REQs._

- **Parent feature request:** [the original prompt the user gave to `/spec`]
- **Layer this REQ owns:** [layer key from `/spec` Step 1.8.1, e.g., `mule-flow`, `api-spec-system`, `dataweave-module`]
- **Sibling REQs:** [list other child REQ ids and their layers]
- **Anypoint Platform hand-offs (operational work routed off the pipeline):** [API Manager policy applications, secure-property rotations, deploy-profile changes, governance-ruleset updates, or "none"]

## API layer

_Pick one when this REQ touches an HTTP-facing API. Skills branch on this in Phase 4. Required when the layer key is `api-spec-system`, `api-spec-process`, `api-spec-experience`, or `mule-flow` and the flow is invoked by APIkit; omit otherwise (batch / scheduler / event-driven flows)._

- [ ] **System API** — direct integration with one upstream system of record (Salesforce, ERP, DB). One config per upstream.
- [ ] **Process API** — orchestrates 2+ System APIs to fulfill a business process. No direct upstream connectors here.
- [ ] **Experience API** — caller-shaped (mobile / web / partner). Sits in front of Process APIs; never talks to Systems directly.

## System Model

_Define the structured data model for this feature. Remove sections that don't apply._

### Entities

| Entity | Field | Type | Constraints |
|--------|-------|------|-------------|
| [EntityName] | [field] | [string/number/boolean/timestamp] | [required, unique, max length, etc.] |

### Events

| Event | Trigger | Payload |
|-------|---------|---------|
| [event_name] | [What causes it] | [Key data included] |

### Permissions

| Action | Roles Allowed |
|--------|---------------|
| [action_name] | [authenticated, owner, admin, etc.] |

## Business Rules

_Explicit, testable constraints governing this feature's behavior._

- [ ] BR-1: [Rule statement — e.g., "Only item owner can delete wardrobe items"]
- [ ] BR-2: [Rule statement]

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## External Dependencies

- None

<!--
  Anypoint Platform operational artifacts (Connected Apps, secure-property
  encryption keys, API Manager policy templates, governance rulesets, Exchange
  asset publications) are NEVER pipelined — they live in Anypoint Platform UI
  / config repos / ops runbooks. If this feature needs any of them, list each
  one above by exact name, then mirror it as a pre-deploy assumption below.
  /canary Step 2a verifies presence before deploy.
-->

## Assumptions

- Any required DX MCP / Platform MCP connected apps, secure-property encryption keys, API Manager policy templates, governance rulesets, and Exchange asset publications are pre-provisioned in the target Anypoint org before deploy starts. The pipeline will not create or modify them. List each artifact by exact name in External Dependencies above so `/canary` can verify presence.

## Open Questions

- [ ] Open question 1

## Out of Scope

- Items explicitly excluded
