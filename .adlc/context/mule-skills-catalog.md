# mule-skills catalog

The MuleSoft skill set comes from **two sources**:

1. **Official MuleSoft skill pack** (`@salesforce/mulesoft-vibes-skills`) — installed at consumer init via `npx skills add mulesoft/mulesoft-dx/skills/mule-development`. Provides BUILD-time orchestration. NOT vendored in this repo.
2. **Toolkit-authored Mule rubrics** under `skills/mule/<rubric>/SKILL.md` — provide REVIEW-time scoring for the Phase 5 review panel and additive guidance for the Phase 4 task-implementer. Authored in this repo.

Plus the **two MuleSoft MCP servers** (DX MCP `mulesoft-mcp-server`, Platform MCP `omni.mulesoft.com/mcp`) which expose runtime tools the implementer and reviewers call directly.

The skill pack and rubrics are **rubrics**, not separately-dispatched agents. Each Phase 5 reviewer (correctness / quality / architecture / test-coverage / security) and the Phase 4 implementer load the relevant rubric by file glob — see the dispatch table below. The catalog is the single source of truth for that mapping.

## Sources

### Official MuleSoft skills (installed at consumer init)

Installer: `npx -y skills add mulesoft/mulesoft-dx/skills/mule-development --target claude-code --scope project --method symlink`

Per [MuleSoft docs — Vibes Skills](https://docs.mulesoft.com/anypoint-code-builder/vibes-skills) (verified 2026-06-11), the default skill set includes:

| Skill | Purpose |
|---|---|
| `run-system-diagnostics` | Anypoint Code Builder diagnostics (RAM, CPU, IOPS, Windows optimizations) |
| `secure-mule-app` | Configure Mule secure properties to encrypt sensitive data |
| `generate-doc-description` | Add or update `doc:description` attributes in Mule XML configs |
| `create-mule-run-config` | Create a new Anypoint Code Builder run configuration |
| `update-mule-run-config` | Edit an existing run configuration |
| `delete-mule-run-config` | Delete an existing run configuration |
| `execute-mule-run-config` | Run or debug a Mule app via an existing run configuration |
| `build-mule-integration` | Create, update, or fix a Mule flow / sub-flow / component (validates that `anypoint-cli-dx-mule-plugin` is installed at startup) |
| `create-project-template` | Generate MuleSoft projects from Exchange templates or from scratch |

### DX MCP tools (`mulesoft-mcp-server` stdio)

Wired by `/init` into `.mcp.json`. Tools available (per docs):

- **Anypoint Code Builder** (scope *Mule Developer Generative AI User*): `generate_mule_flow`, `generate_api_spec`, `create_MCP_server`, `generate_munit_test`, `modify_munit_test`
- **Anypoint Monitoring** (scope *Monitoring Viewer*): `get_platform_insights`, `get_reuse_metrics`, `list_applications`
- **API Manager**: `create_and_manage_api_instances`, `manage_api_instance_policy`, `list_api_instances`
- **Exchange** (scopes Exchange Administrator/Contributor/Creator/Viewer): `create_and_manage_assets`, `search_asset`, `deploy_mule_application`, `update_mule_application`, `implement_api_spec`

### Platform MCP tools (`omni.mulesoft.com/mcp` via `mcp-remote`)

Wired by `/init` into `.mcp.json`. Tools available (per docs):

- **Exchange**: `fetch_service_facets`, `fetch_services`, `list_agents`, `list_apis`, `list_llms`, `list_mcp_servers`, `search_assets_semantic`, `search_global_assets`, `search_global_content`, `search_portfolio_services`, `search_repository_knowledge`, `view_agent_details`, `view_api_version_details`, `view_llm_details`, `view_mcp_server_details`, `get_mcp_server_state`, `get_provision_status`, `get_trusted_mcp_catalog`, `provision_mcp_server`, `resume_provision_job`, `update_mcp_server`
- **API Manager**: `check_guardrail_scope_targets`, `fetch_automated_policy_template`, `fetch_guardrail_ruleset`, `get_policy_template_form`, `list_governance_strategies`, `list_provider_gateways`, `prepare_automated_policy_creation`, `prepare_guardrail_creation`, `prepare_policy_creation`, `view_api_instance_details`, `view_api_instance_policies`, `view_api_version_instances`, `apply_policy_to_instance`, `create_automated_policy_strategy`, `delete_automated_policy_strategy`
- **Anypoint Monitoring**: `fetch_monitoring_drill_down`, `fetch_monitoring_instance`, `fetch_monitoring_overview`, `show_observability_performance`, `view_api_instance_monitoring`
- **Governance**: `check_policy_conformance`, `fetch_governance_service_report`, `fetch_governance_services`, `view_api_version_governance_report`, `view_governance_report`, `create_guardrail`, `delete_governance_strategy`
- **Runtime Manager**: `create_omni_gateway`, `create_scanner`, `get_omni_gateway_target_domains`, `get_omni_gateway_usage_report`, `list_omni_gateway_environments`, `list_omni_gateway_targets`, `list_scanner_providers`, `test_scanner_connection`
- **General**: `get_business_group`, `list_business_groups`, `select_active_business_group`, `select_active_environment`, `select_active_provider`, `select_api_version`

### Toolkit-authored Mule rubrics (`skills/mule/`, to be authored)

| Rubric | Purpose | Scoring weight |
|---|---|---|
| `mule-flow-quality` | Quality bar for Mule XML flows: naming, composition, choice/routing, doc:description completeness | quality |
| `mule-error-handling` | Error-handler completeness, on-error-continue vs propagate, type matching, dead-letter pattern | correctness |
| `dataweave-quality` | DW 2.x syntax, output directive, functional composition, type annotations, no payload mutation | quality + correctness |
| `munit-coverage` | Coverage bar, mock completeness, assertion quality, no Thread.sleep, suite structure | test-coverage |
| `api-led-architecture` | API layer declaration, dependency layering (system → process → experience boundary respect) | architecture |
| `apikit-contract-conformance` | APIkit-bound RAML/OAS, contract-first, no hand-rolled routing | architecture |
| `mule-secrets-hygiene` | Secure-properties, no hardcoded credentials/URLs/IDs, encryption-key externalization | security |
| `mule-connector-config-hygiene` | One config per upstream, timeout/retry, reconnection, pooling | architecture |
| `mule-deploy-hygiene` | pom.xml deploy section, vCore/replica sizing, region, environment-specific configs | architecture |
| `governance-policies` | API Manager policy declarations, governance ruleset conformance, Policies.md presence | security |

## Phase mapping

### Requirements (Phase 1) — grounding & estimation

| Source | Use when |
|---|---|
| Platform MCP `search_global_assets` / `search_assets_semantic` / `search_repository_knowledge` | Search Anypoint Exchange for existing reusable assets before building. |
| Platform MCP `list_apis` / `list_agents` / `list_mcp_servers` | Inventory existing services in scope. |
| `fetching-mulesoft-docs` (toolkit-authored, future) | Need authoritative grounding from docs.mulesoft.com / DataWeave docs. |

### Design (Phase 2 — Architect) — modeling & shape

| Source | Use when |
|---|---|
| Official `create-project-template` | Greenfield Mule app scaffolding (from Exchange template or scratch). |
| DX MCP `generate_api_spec` | New API contract (RAML / OAS). |
| Toolkit `api-led-architecture` rubric | Layer the change correctly across system/process/experience APIs. |
| Toolkit `apikit-contract-conformance` rubric | Verify contract-first design before implementation. |

### Build (Phase 4 — Implement) — code & metadata generation

| Source | Use when |
|---|---|
| Official `build-mule-integration` | Create / update / fix Mule flows, sub-flows, components. |
| Official `secure-mule-app` | Encrypt sensitive properties via secure-properties-config. |
| Official `generate-doc-description` | Add or update `doc:description` consistently. |
| Official `create-mule-run-config` / `update-mule-run-config` / `execute-mule-run-config` / `delete-mule-run-config` | Run-config lifecycle (Anypoint Code Builder runs). |
| DX MCP `generate_mule_flow` | Server-side flow generation (alternative to local build-mule-integration). |
| DX MCP `implement_api_spec` | Generate APIkit-bound flows from a published API spec. |
| DX MCP `create_MCP_server` | Provision an MCP server for the integration. |

### Test (Phase 5 — Test-coverage reviewer) — verification

| Source | Use when |
|---|---|
| DX MCP `generate_munit_test` / `modify_munit_test` | Author / refine MUnit suites. |
| Toolkit `munit-coverage` rubric | Score suite coverage, mock completeness, assertion quality. |

### Review (Phase 5 — quality / architecture / security) — analysis

| Source | Use when |
|---|---|
| Toolkit `mule-flow-quality` rubric | Quality scoring for `.xml` flows. |
| Toolkit `dataweave-quality` rubric | Quality + correctness for `.dwl`. |
| Toolkit `mule-error-handling` rubric | Correctness for error-handler completeness. |
| Toolkit `mule-connector-config-hygiene` rubric | Architecture scoring for connector configs. |
| Toolkit `mule-secrets-hygiene` rubric | Security scoring for properties / secrets. |
| Toolkit `governance-policies` rubric | Security scoring for API Manager policies. |
| Toolkit `mule-deploy-hygiene` rubric | Architecture scoring for `pom.xml` / `mule-artifact.json`. |
| Platform MCP `view_api_instance_policies` / `check_policy_conformance` | Verify policies against live API Manager state. |
| Platform MCP `view_governance_report` / `view_api_version_governance_report` | Governance compliance evidence. |
| Platform MCP `fetch_monitoring_drill_down` / `view_api_instance_monitoring` | Runtime evidence for performance / error-rate findings. |

### Deploy (Phase 7–8 — Ship) — promotion & rollout

| Source | Use when |
|---|---|
| DX MCP `deploy_mule_application` / `update_mule_application` | Push CloudHub 2.0 deploys. |
| DX MCP `create_and_manage_assets` | Publish reusable asset to Exchange. |
| Platform MCP `apply_policy_to_instance` | Promote API Manager policy to a target environment. |
| Platform MCP `select_active_environment` / `select_active_business_group` | Switch context before promotion. |
| `mvn deploy -P<profile>` | Maven-based deploys (RTF, on-prem). |

### Operate (Phase post-deploy) — runtime introspection

| Source | Use when |
|---|---|
| Platform MCP `fetch_monitoring_drill_down` / `fetch_monitoring_overview` / `show_observability_performance` | Runtime telemetry. |
| DX MCP `get_platform_insights` / `get_reuse_metrics` / `list_applications` | Platform-level metrics. |
| Platform MCP `view_api_instance_monitoring` | Per-API observability. |

## File-glob → rubric+skill dispatch

The `task-implementer` (Phase 4) and the Phase 5 review panel load the matching rubric whenever a file matching the glob is in the change set. Multiple matches: load each. The router skill at `skills/mule-router/SKILL.md` is the single authoritative implementation of this table.

| File-glob | Build orchestrator (Phase 4) | Review-time rubrics (Phase 5) |
|---|---|---|
| `src/main/mule/**/*.xml` (non-test) | `build-mule-integration` (official) | `mule-flow-quality` (quality), `mule-error-handling` (correctness), `mule-connector-config-hygiene` (architecture) |
| `**/*.dwl`, embedded `<dw:transform>` blocks | `build-mule-integration` (official) | `dataweave-quality` (quality + correctness) |
| `src/main/resources/api/**/*.{raml,json,yaml}` | DX MCP `generate_api_spec` / `implement_api_spec` | `apikit-contract-conformance` (architecture), `api-led-architecture` (architecture) |
| `src/test/munit/**/*.xml` | DX MCP `generate_munit_test` / `modify_munit_test` | `munit-coverage` (test-coverage) |
| `pom.xml`, `mule-artifact.json` | `create-project-template` (official) | `mule-deploy-hygiene` (architecture) |
| `**/*.properties`, `**/*.secure.properties` | `secure-mule-app` (official) | `mule-secrets-hygiene` (security) |
| API Manager policy declarations / spec sidecars | DX MCP `manage_api_instance_policy`, Platform MCP `apply_policy_to_instance` | `governance-policies` (security) |
| Exchange asset descriptors | DX MCP `create_and_manage_assets` | `mule-deploy-hygiene` (architecture) |
| Run-config YAML / VS Code launch configs | `create-mule-run-config` / `update-mule-run-config` (official) | (no review rubric — operational artifact) |

When **no** glob matches a touched file, the reviewer falls back to the `partials/mule-quality-checklist.md` baseline.

## Skills consumed at every Phase

These are reference / always-on tools that any phase may invoke regardless of the change set:

- Platform MCP `select_active_environment` — invoked at the start of any deploy / inspect operation
- Platform MCP `select_active_business_group` — invoked when crossing business-group boundaries
- Platform MCP `search_global_assets` — invoked at /spec time to surface existing reusable assets
- DX MCP `list_applications` — Phase 5 architecture reviewer always lists deployed apps for the target environment

## How agents reference this catalog

Reviewer agent prompts include this stub:

```
Touched files in the change set:
  - <path1>
  - <path2>
  ...

Per .adlc/context/mule-skills-catalog.md, load the rubrics matching these globs:
  - <rubric A> for <glob A>
  - <rubric B> for <glob B>

Each toolkit rubric lives at skills/mule/<rubric>/SKILL.md. Read it before evaluating findings.

For runtime/governance verification, the following MCP tools are available and SHOULD be called when the finding is about live state rather than static configuration:
  - Platform MCP: <tool list>
  - DX MCP: <tool list>
```

That stub is built mechanically by the `skills/mule-router/SKILL.md` orchestrator at dispatch time so individual reviewer agents do not need to know the dispatch table — they only need to read the rubrics handed to them and call the MCP tools when the rubric instructs them to.

## What this catalog does NOT cover

- The official skill pack is **installed at consumer init**, not vendored. Updates to the upstream pack flow in via `npx skills add` re-runs.
- Future MuleSoft skills shipped by Salesforce will appear in `npx skills add` output and should be added to this catalog when they prove relevant. Bumping the catalog is a normal toolkit-maintenance REQ, not an emergency.
- Build-time skills authored by the toolkit (e.g., a hypothetical `building-batch-job` rubric) would live in `skills/mule/` alongside the review rubrics — but in v1, the official pack covers build orchestration, and we focus on review.
