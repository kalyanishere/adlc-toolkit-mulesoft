---
name: governance-policies
description: Security rubric for API Manager policy declarations and governance scan conformance. Loaded by Phase 5 security-auditor when the change set touches API specs, Policies.md, or pom.xml api-manager plugin config — only when mulesoft.governance.api_manager_enabled is true.
glob: src/main/resources/api/**, .adlc/specs/REQ-*/Policies.md
dimension: security
---

# governance-policies (security rubric)

Score API Manager policy declarations + governance scan compliance. **Gated** — only loaded when `.adlc/config.yml` `mulesoft.governance.api_manager_enabled: true`.

## Non-negotiables (any violation = Critical)

- **`Policies.md` exists for every REQ that touches public-facing API artifacts** — generated from `templates/policies-template.md`
- **Required-policy list applied** — every policy in `mulesoft.governance.required_policies` is either declared in `Policies.md` OR has an explicit waiver row with justification
- **Policy declarations versioned** — every applied policy has a corresponding spec under git; not UI-clicked
- **Governance ruleset configured** — `mulesoft.governance.governance_ruleset` set; `anypoint-cli-v4 governance:validate` runs in CI
- **Live state matches declaration** — Platform MCP `view_api_instance_policies` returns the declared set (drift = Critical)

## Major findings

- **Production endpoint with Basic Auth** — JWT or OAuth 2.0 required
- **`rate-limiting` configured at "unlimited"** — defeats the purpose
- **`rate-limiting` limits inconsistent with contract SLA** — over-throttle starves consumers; under-throttle exposes upstream
- **`client-id-enforcement` missing** without a documented waiver
- **JWT validation policy with hardcoded keys** — should reference an issuer URL with key rotation
- **OAuth 2.0 scopes too broad** — least-privilege violation (consumer gets `full` when it only reads)
- **Promotion plan skips Staging** — Sandbox → Production direct path

## Required-policy checklist (typical set)

```yaml
mulesoft:
  governance:
    required_policies:
      - client-id-enforcement     # always (with waiver if internal)
      - rate-limiting             # always (sized to contract)
      - jwt-validation            # OR oauth2-validation when authenticated
```

For each declared policy in `Policies.md`:
- ✅ Policy applied via Platform MCP `apply_policy_to_instance` (not UI-clicked)
- ✅ Configured params appropriate for the contract (rate limits, JWT issuer/audience, OAuth scope)
- ✅ Waiver justification recorded if a required policy is NOT applied
- ✅ Promotion plan covers Sandbox → Staging → Production with policy diffs called out

## Live-state verification (mandatory call)

For each API instance declared in `Policies.md`:

```
Platform MCP view_api_instance_policies(apiInstanceId: <id>) →
  compare against Policies.md "Policies applied" table →
  drift detected → Critical finding
```

Drift = (declared but not applied) OR (applied but not declared). Either direction is a Critical finding because the source of truth is unclear.

## Governance scan

When `mulesoft.governance.governance_ruleset` is set:

```sh
anypoint-cli-v4 governance:validate --rulesets <ruleset> src/main/resources/api/*.{raml,json,yaml}
```

OR via Platform MCP `check_policy_conformance` for the deployed API instance.

Failures are blocking — every API spec must pass before promotion.

## Common findings

| Finding | Severity | Fix |
|---|---|---|
| `Policies.md` missing despite api_manager_enabled=true | Critical | Generate from `templates/policies-template.md` |
| Live state drift (declared but not applied) | Critical | Apply via Platform MCP `apply_policy_to_instance` BEFORE merge |
| Live state drift (applied but not declared) | Critical | Update `Policies.md` to match reality, OR remove the un-declared policy via Platform MCP |
| Production endpoint with Basic Auth | Critical | Replace with OAuth 2.0 / JWT validation policy |
| `rate-limiting` at "unlimited" | Major | Set realistic limits sized to contract SLA |
| Required policy missing without waiver | Major | Apply the policy OR document justification in `Policies.md` |
| Governance scan fail | Critical (blocks promotion) | Address ruleset violations in API spec |
| Policy applied via UI without `Policies.md` entry | Major | Backfill `Policies.md`; commit before next deploy |

## Reference

- mulesoft-rules.md "API Manager / Governance Requirements" section
- Anypoint API Governance docs: https://docs.mulesoft.com/governance/
- Platform MCP `view_api_instance_policies`, `apply_policy_to_instance`, `check_policy_conformance` are the canonical live-state tools
- Companion rubric: `mule-secrets-hygiene` (encryption + secret-rotation hygiene)
