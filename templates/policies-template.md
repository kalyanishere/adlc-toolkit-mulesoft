---
id: POLICIES-<REQ-id>
title: "Policies for <feature name>"
req: REQ-<id>
status: draft                       # draft | approved | deployed
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
app_prefix: <AppPrefix>              # from .adlc/config.yml mulesoft.app_prefix
environment: <Sandbox | Staging | Production>
---

# Policies — REQ-<id> <feature title>

Required by `mulesoft-rules.md`: every feature that touches a public API generates one or more API Manager policy assignments, with an environment-promotion plan and conformance evidence.

**Framework policy: declarative, not UI-clicked.** Policy assignments emitted/promoted via Platform MCP `apply_policy_to_instance` or via `mvn deploy` policy-spec files. They MUST NOT be applied through the API Manager UI ad-hoc — every applied policy needs a versioned spec under git so promotion across environments is auditable. Pre-flight (`tools/mule-preflight/check.sh policies`) BLOCKS any environment promotion that lacks a corresponding policy declaration in the repo.

## API instances covered

One row per API instance touched by this REQ. Naming format: `<AppPrefix>-<asset-name>-<version>` (e.g., `MUL-orders-process-api-v1`).

| API instance | Asset name | Version | Layer | Environment(s) |
|---|---|---|---|---|
| `<AppPrefix>-<asset>-v<N>` | <asset display name> | 1.0.0 | system / process / experience | Sandbox, Staging, Production |

## Policies applied

Per the rules: every public API has client-id-enforcement (or explicit waiver), rate-limiting, and JWT/OAuth 2.0 (when authenticated). Required-policy list comes from `.adlc/config.yml` `mulesoft.governance.required_policies` — never hardcoded.

| Policy | Configured params | Why this policy | Waiver justification (if any) |
|---|---|---|---|
| `client-id-enforcement` | (default) | Required by org policy for all public APIs | — |
| `rate-limiting`         | rateLimit: 100 / 1m | Sized to contract throughput SLA | — |
| `jwt-validation`        | issuer: <issuer-uri>; audience: <aud> | API requires authenticated callers | — |
| `header-injection`      | <headers> | Propagate correlation-id / tenant-id downstream | — |

## Policy promotion plan

| Stage | Trigger | Tool | Evidence |
|---|---|---|---|
| Sandbox  | PR merge to `main` | Platform MCP `apply_policy_to_instance` (env=Sandbox) | governance scan green; smoke tests green |
| Staging  | manual gate after Sandbox stable for ≥24h | Platform MCP `apply_policy_to_instance` (env=Staging) | governance scan green; load test green |
| Production | manual gate + change-management ticket | Platform MCP `apply_policy_to_instance` (env=Production) | governance scan green; smoke tests green; change ticket linked |

Document who is responsible for each promotion gate (admin runbook, automated post-deploy script, etc.).

## Governance scan

Required: `anypoint-cli-v4 governance:validate` (or Platform MCP `check_policy_conformance`) returns `pass` for the API instance in the target environment.

| Environment | Last scan | Result | Conformance report link |
|---|---|---|---|
| Sandbox    | <YYYY-MM-DD> | pass / fail | <link to fetch_governance_service_report output> |
| Staging    | <YYYY-MM-DD> | pass / fail | <link> |
| Production | <YYYY-MM-DD> | pass / fail | <link> |

If a scan returns fail, do not promote. File a follow-up REQ to remediate before re-attempting promotion.

## Anti-patterns this avoids

Verify each before sign-off:

- [ ] No policy applied through API Manager UI without a corresponding repo-tracked spec
- [ ] No public API without client-id-enforcement (or waiver justification recorded)
- [ ] No production API using Basic Auth — JWT or OAuth 2.0 only
- [ ] No `rate-limiting` configured at "unlimited" or with limits inconsistent with the contract SLA
- [ ] No environment promotion that skips Staging
- [ ] No promotion to Production without a green governance scan
- [ ] No policy assignment that lacks a documented "why" (every row in the Policies Applied table justified)

## Notes

Free-form notes from the implementer / reviewer: rationale for non-default policy params, deferred policies (e.g., "circuit-breaker deferred to follow-up REQ-NNN"), waiver context, governance-scan remediation history.
