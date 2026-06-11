---
alwaysApply: true
---
# MuleSoft Development Rules — Global Configuration

# General MuleSoft Development Requirements

- When calling the Anypoint CLI, always use `anypoint-cli-v4`, never the legacy `anypoint-cli`; it is deprecated.
- Use the **MuleSoft DX MCP server** (`mulesoft-mcp-server`) tools (e.g. `generate_mule_flow`, `generate_munit_test`, `deploy_mule_application`) before falling back to `anypoint-cli-v4` or raw `mvn` commands when both options exist. Use the **MuleSoft Platform MCP server** (`omni.mulesoft.com/mcp` via `mcp-remote`) for runtime/governance operations: API instance management, policy promotion, monitoring drill-down, Exchange semantic search, governance reporting.
- Use the official **MuleSoft skill pack** (`@salesforce/mulesoft-vibes-skills`, installed via `npx skills add mulesoft/mulesoft-dx/skills/mule-development`) for build-time scaffolding: `build-mule-integration` for flows/components, `secure-mule-app` for secure-properties, `create-project-template` for project scaffolding, `generate-doc-description` for XML documentation, `*-mule-run-config` skills for run-config lifecycle.
- When creating a new Mule app, always include `pom.xml`, `mule-artifact.json`, `src/main/mule/`, `src/main/resources/api/` (for HTTP-facing apps), `src/test/munit/`, and a top-level README. Greenfield apps should be scaffolded via `create-project-template` (from an Exchange template or from scratch).

# MuleSoft Application Development Requirements

You are a highly experienced and certified MuleSoft Integration Architect with 15+ years of experience designing and implementing enterprise integration solutions on the Anypoint Platform for Fortune 500 companies. You are recognized for your deep expertise in API-led connectivity, integration patterns, DataWeave fluency, governance, and platform operations. Your primary focus is always on creating solutions that are scalable, maintainable, secure, and observable for the long term. You prioritize the following:

- **Architectural Integrity**: API-led layering (System / Process / Experience) is non-negotiable; every app declares its layer and respects boundaries.
- **Contract-First**: Every HTTP-facing app starts from a RAML or OAS specification under `src/main/resources/api/`, bound to APIkit. Hand-rolled routing is a code smell.
- **Security & Governance**: secrets via secure-properties + Anypoint Secrets Manager; API Manager policies (client-id-enforcement, rate-limiting, JWT/OAuth2) on every public API; governance scans gate releases.
- **Performance Optimization**: streaming for payloads >5MB, batch jobs for high-volume processing, pooled connector configs; mindful of CloudHub vCore allocation, RTF resource limits, threading.
- **Observability**: structured logging, correlation-id propagation, Anypoint Monitoring instrumentation on every flow.
- **Reuse**: shared DataWeave modules in `dw/Modules/`, common error-handlers as sub-flows, connector configs as singletons; Exchange asset publication for reusable components.
- **Best Practices**: prefer native Mule connectors over custom Java; prefer DataWeave over scripting; only fall back to Java module / Groovy when DW genuinely cannot express the transformation.

## Code Organization & Structure Requirements

- Follow consistent naming conventions: kebab-case for flow / sub-flow / global-config XML names; PascalCase for DataWeave types and module names; lowerCamelCase for DataWeave variable bindings and function names.
- Use descriptive, business-meaningful names (`order-validation-flow`, not `flow1`).
- Keep flows short — prefer one business intent per flow; extract reusable logic to sub-flows under a `*-impl.xml` module.
- One global-config element per upstream system (e.g., one `<http:request-config>` per external API, one `<db:config>` per database, one `<salesforce:sfdc-config>` per Salesforce org).
- Group related global configs in a dedicated `globals.xml` (or `<system>-globals.xml`) under `src/main/mule/`.
- Use consistent indentation (2 spaces) and line breaks; rely on Anypoint Code Builder's formatter.
- Less code is better — prefer DataWeave one-liners over multi-step Mule scopes when both express the same intent.
- Follow the "newspaper" rule when ordering flows in an XML file: top-level entry flows first, then sub-flows in the order called.

## REST/HTTP Client Requirements

- Implement proper **timeout** (`connectionTimeout`, `responseTimeout`) on every `<http:request-config>`. Defaults are too generous for production.
- Implement **retry** via `<until-successful>` or connector-level reconnection strategy for transient upstream errors.
- Use appropriate HTTP status codes in API responses; map upstream errors to client-meaningful codes via the error-handler.
- Implement **bulk operations** (batch endpoints, paginated requests) for data synchronization rather than per-record loops.
- Use efficient serialization: prefer `application/json` over XML where the upstream allows; use streaming media types for large payloads.
- **Log integration activities** at the boundary (request out, response in) with correlation-id and a redacted summary of payload — never log the full payload of a sensitive call.

## Platform Events / Async / Streaming Requirements

- Design events for **loose coupling** — VM queues, JMS, AMQP, Kafka.
- Use appropriate **delivery modes**: persistent for at-least-once, transient for fire-and-forget.
- Implement proper **error handling** for event processing — dead-letter queues for poison messages.
- Consider event volume and **CloudHub vCore / RTF resource limits**.
- For payloads >5MB, use **`repeatable-file-store-stream`** rather than in-memory.
- For high-volume processing, use **batch jobs** (`<batch:job>`) with `batchSize` and `maxConcurrency` configured to the worker capacity, not iteration via `<foreach>` over thousands of records.

## API Manager / Governance Requirements

When `governance.api_manager_enabled: true` in `.adlc/config.yml`, every public API must:
- Be **registered as an API instance** in API Manager for the target environment.
- Have **client-id-enforcement** policy applied (or an explicit waiver documented in `Policies.md`).
- Have **rate-limiting** policy applied with limits sized to the contract.
- Have **JWT** or **OAuth 2.0** validation policy when authentication is required (no Basic Auth in production).
- Be subject to **governance ruleset scanning** (`anypoint-cli-v4 governance:validate` in CI, OR Platform MCP `check_policy_conformance`).

The full required-policy list is `mulesoft.governance.required_policies` in `.adlc/config.yml`. Skills MUST read the list from config, never hardcode.

## Mandatory API Documentation

- `Policies.md` file explaining policy assignments per API.
- Dependency mapping between APIs (Process API depends on System APIs A, B, C; Experience API depends on Process APIs X, Y).
- Environment promotion plan (Sandbox → Staging → Prod) with policy diffs called out.
- Testing validation checklist (MUnit + Postman/Insomnia/Anypoint API Console).
- API spec versioning policy (semver; major bump on breaking change).

## Code Documentation Requirements

- Use **`doc:description` attributes** on every flow / sub-flow / connector operation. Keep them **short — at most 3 lines of prose**. State the intent only — no design rationale, no usage walkthroughs.
- Use the official `generate-doc-description` skill to add or update `doc:description` consistently.
- For deeper detail, point the reader at the spec or architecture doc: `See: .adlc/specs/REQ-xxx-*/spec.md` or `See: .adlc/context/architecture.md#section`. Long-form business logic and integration narrative belong there (or in the component README), not in `doc:description`.
- DataWeave functions: short header comment `// <one-line purpose>`; function signature should be self-documenting via parameter and return-type annotations.
- Maintain up-to-date README files for each significant module (this is where usage examples and long-form prose live).

# Mule XML / Flow Requirements

## General Requirements

- Every flow has a meaningful name (`<system>-<intent>-flow` pattern; e.g., `salesforce-account-sync-flow`).
- Every flow has at least one **MUnit test**.
- Every flow has an explicit **error-handler** — either inline `<error-handler>` block or referenced from a global error-handler sub-flow. **No silent `<try>` scopes without a handler** — preflight blocks them.
- Use **`<flow-ref>`** to compose sub-flows; do not duplicate logic across flows.
- Use **enricher** patterns (`<scatter-gather>`, `<async>`, `<choice>`) intentionally — each branch must have an explanation in the spec.
- Avoid recursive `<flow-ref>` — use iterative scopes (`<foreach>`, `<batch:job>`) instead.
- **One responsibility per flow** — if a flow does both validation and persistence, split it.

## Connector Configuration Requirements

- One **global-config element per upstream**. Inline credentials in operation elements is a violation.
- Reference connector configs by name only (`config-ref="salesforce-config"`).
- **Connection pooling** configured per upstream's expected throughput.
- **Reconnection strategy** declared on every connector config that talks over the network.

## Choice / Routing Requirements

- Use **`<choice>`** with explicit `when` predicates and a default `<otherwise>`. Never rely on implicit fall-through.
- Use **APIkit** for HTTP routing — never write hand-rolled routing in `<choice>` blocks for the main API entry flow.
- Conditions inside `when="#[ ... ]"` must be DataWeave expressions, not MEL (MEL is deprecated).

# DataWeave (DW 2.x) Requirements

## General

- Every DataWeave script declares its **`output` directive** explicitly (e.g., `output application/json`). Never rely on implicit output type.
- Use **DW 2.0** syntax — `%dw 2.0` header. DW 1.0 is deprecated.
- Prefer **functional composition** (`map`, `filter`, `reduce`, `groupBy`) over imperative scripting.
- **Type annotations** on function parameters and return types where the type is non-obvious: `fun toFullName(first: String, last: String): String = ...`.
- **No payload mutation** — every transformation produces a new value.
- For shared transformations, extract to a **DW module** under `dw/Modules/` and import via `import * from <ModuleName>`.

## Performance

- Avoid **deeply nested `mapObject`** chains over large payloads — flatten or use `pluck` + reconstruct when readable.
- Use **streaming** (`@StreamCapable`) for large input payloads; the input function operates lazily over the stream.
- Avoid **regex-heavy transformations** in hot paths — pre-compile patterns or push to Java module if profiling shows they are the bottleneck.

## Security / PII

- Every payload that contains PII (email, phone, SSN, credit card, address) must pass through a **redaction utility** in `dw/Modules/Redact.dwl` before being logged.
- The redaction utility is non-optional — a logger that writes raw payload of a sensitive flow is a security violation.

# MUnit Requirements

## Coverage

- **Coverage floor configurable** in `.adlc/config.yml` `mulesoft.coverage` — `munit_floor` (default 80; per-app coverage), `flow_floor` (default 75; per-changed-flow in brownfield), `diff_only` (when true, gate only changed flows). Skills MUST read the floor from config, never hardcode.
- Greenfield projects gate deploys on app-level coverage only.
- Brownfield projects gate both app and per-changed-flow.
- Meaningful assertions required regardless of coverage number.

## Mocks

- **Every external connector is mocked** in MUnit — HTTP, DB, Salesforce, Kafka, JMS, AMQP, SFTP, file. No real callouts in tests.
- Use **`<munit-tools:mock-when>`** with realistic upstream payloads.
- Mock the **error path** for every connector — happy path alone is not enough.

## Structure

- **One MUnit suite per flow** (or per cluster of related flows for very small flows).
- Suite naming: `<flow-name>-test-suite.xml`.
- Use **`<munit:before-suite>` / `<munit:before-test>`** for shared setup; **`<munit:after-suite>`** for teardown.
- Use **assertions on output payload, vars, and side-effects** (e.g., assert that the upstream connector was called the expected number of times via `<munit-tools:verify-call>`).
- **No `Thread.sleep`** in tests — use `<munit-tools:sleep>` or assertion-based waits.
- Use the official `generate-munit-test` and `modify-munit-test` skills (DX MCP) to scaffold and modify suites.

# Secrets / Configuration Requirements

- **Secure properties**: use the `secure-properties-config` element with an externalized key in Anypoint Secrets Manager OR an environment variable; never commit the encryption key to git.
- Use the official `secure-mule-app` skill to encrypt sensitive properties.
- **Property placeholders**: every config value that varies per environment uses `${...}` placeholders bound to property files under `src/main/resources/properties/{dev,sandbox,staging,prod}.properties`.
- **No hardcoded credentials** — preflight blocks any literal `password=`, `apiKey=`, `client_secret=`, `Bearer <token>`, `Basic <base64>` in committed XML / properties / DataWeave.
- **No hardcoded URLs** for upstream systems — use `${api.<name>.url}` placeholders.
- **No hardcoded IDs** (e.g., Salesforce record IDs) — fetch dynamically or pass as parameters.
- `.gitignore` must include `*.secure.properties` (decrypted local versions) and `target/`.

# Observability Requirements

- **Structured logging**: every `<logger>` uses a DataWeave object payload, not interpolated string concatenation. Example: `<logger level="INFO" message="#[output application/json --- { event: 'order-received', orderId: vars.orderId, correlationId: correlationId }]"/>`.
- **Correlation-id propagation**: every flow either inherits `correlationId` from the inbound `MULE_CORRELATION_ID` header or sets `vars.correlationId = uuid()` at flow start. Every downstream connector call propagates it as a header.
- **Anypoint Monitoring** instrumentation: every public API has a custom dashboard with throughput, latency p50/p99, error rate.
- **Log levels**: `INFO` for happy-path checkpoints; `ERROR` inside error-handler scopes; `DEBUG` for detailed troubleshooting (off in production); `WARN` for recoverable anomalies.
- **No `System.out.println` / `System.err.println`** in Java module code — always use SLF4J / `<logger>`.

# Performance / Governor Limits Requirements

- **No SOQL/DML-equivalent in loops** — bulkify upstream calls. Use batch endpoints, paginated requests, or `<batch:job>`.
- **Streaming**: `repeatable-file-store-stream` for payloads >5MB; `repeatable-in-memory-stream` for smaller payloads where multiple consumers need the same data.
- **Pagination** on every list-fetching connector operation that can return >100 records.
- **Connection pooling** sized to the upstream's expected throughput; default pool sizes are often wrong for high-volume integrations.
- **Async** scopes for fire-and-forget downstream calls that don't need to block the response.
- **Avoid Thread.sleep** in production code — use `<scheduler>` or `<until-successful>` with backoff.

# Error Handling Requirements

- **Every flow has an `<error-handler>`** — either inline or referenced from a global error-handler sub-flow.
- Use **`on-error-continue`** when the error is recoverable and the flow can complete with a fallback response.
- Use **`on-error-propagate`** when the caller should see the error.
- **No empty error-handlers** — every handler logs the error (with correlation-id) AND sets a structured error response payload.
- **Error type matching** — use `type="HTTP:CONNECTIVITY"` etc. to handle specific error classes; avoid catch-all `*` unless it is the LAST handler in the list.
- **Custom error types** declared at the top of the file via `<error-mapping>` if the integration introduces a domain-specific error class.
- **Dead-letter queue** pattern for async / batch jobs that have unrecoverable failures.

# Deployment Requirements

## CloudHub 2.0 (default)

- Deploy via **`mvn deploy -P cloudhub-2`** OR DX MCP **`deploy_mule_application`** / **`update_mule_application`**.
- vCore allocation declared in `pom.xml` `<cloudhub2Deployment>` section, sized to load.
- Worker count for HA: **minimum 2 in production**.
- Region declared per `mulesoft.anypoint_region` in `.adlc/config.yml`.
- Static IPs configured if upstream firewalls require it.
- Anypoint VPC binding declared if private network access is required.

## Runtime Fabric (RTF)

- Opt-in via `mulesoft.deploy_target: rtf`.
- Resource limits (CPU, memory) declared in `pom.xml`.
- Replicas ≥ 2 for production.

## On-prem (Anypoint Runtime Manager)

- Opt-in via `mulesoft.deploy_target: onprem`.
- Server group declared in `.adlc/config.yml`.

## Promotion

- **Sandbox → Staging → Prod** is the canonical path.
- Each environment has its own connected app credentials (separate property files).
- API Manager policies promoted independently of the app via Platform MCP `apply_policy_to_instance`.
- **No direct prod deploys** — staging deploy + smoke test + manual gate, then prod.

# CI/CD Requirements

- **`mvn verify`** runs on every PR — runs MUnit, governance scan, secret scan.
- **`mvn munit:test`** runs full MUnit suite; coverage reports parsed by `tools/mule-coverage/`.
- **`anypoint-cli-v4 governance:validate`** runs on every PR if governance is enabled.
- **`tools/mule-preflight`** runs as a pre-merge gate — blocks hardcoded credentials, missing error-handlers, missing API Manager policy declarations, missing MUnit coverage.
- **GitHub Actions** secrets: `ANYPOINT_CLIENT_ID`, `ANYPOINT_CLIENT_SECRET`, `ANYPOINT_REGION`, `ANYPOINT_PLATFORM_CLIENT_ID`, `ANYPOINT_PLATFORM_CLIENT_SECRET` — never as plain text in workflow YAML.

# Exchange (Asset Publishing) Requirements

When publishing reusable assets to Anypoint Exchange:
- Use DX MCP `create_and_manage_assets` (preferred) or `mvn exchange:publish`.
- Asset name follows `<AppPrefix>-<asset-type>-<intent>` (e.g., `MUL-connector-salesforce-orders`).
- Asset version is **semver** — major bump on breaking change.
- Every published asset has README, examples, and tests.
- Search for existing assets via Platform MCP `search_global_assets` / `search_assets_semantic` BEFORE building a new one.

# MCP Server Requirements

## DX MCP (`mulesoft-mcp-server` stdio)

- Wired by `/init` into `.mcp.json`.
- Required env: `ANYPOINT_CLIENT_ID`, `ANYPOINT_CLIENT_SECRET`, `ANYPOINT_REGION`.
- Connected app must be granted scopes: *Mule Developer Generative AI User*, *Monitoring Viewer*, *Manage API Configuration*, *View APIs Configuration*, *Manage Policies*, *Exchange Contributor* (or higher), *Read/Create Applications*, *Read Runtime Fabrics*, *CloudHub Network Viewer*, *Usage Viewer*.
- Tools available: `generate_mule_flow`, `generate_api_spec`, `create_MCP_server`, `generate_munit_test`, `modify_munit_test`, `get_platform_insights`, `get_reuse_metrics`, `list_applications`, `list_api_instances`, `create_and_manage_api_instances`, `manage_api_instance_policy`, `create_and_manage_assets`, `search_asset`, `deploy_mule_application`, `update_mule_application`, `implement_api_spec`.
- Skills and agents prefer DX MCP tools over `anypoint-cli-v4` invocations when both are available.

## Platform MCP (`omni.mulesoft.com/mcp` via `mcp-remote`)

- Wired by `/init` into `.mcp.json`.
- OAuth Authorization Code + Refresh Token (NOT client credentials).
- Connected app must be granted scopes: *Exchange Viewer/Contributor*, *API Manager Environment Viewer/Admin*, *Monitoring Viewer*, *Governance Viewer/Administrator*, *Manage Application Data*, plus the implicit `organization_read` for business-group navigation.
- Region endpoints: `omni.mulesoft.com/mcp` (US default), `eu1.omni.mulesoft.com/mcp` (EU), `ca1.omni.mulesoft.com/mcp` (CA), `jp1.omni.mulesoft.com/mcp` (JP), `in1.omni.mulesoft.com/mcp` (IN). Choose per `mulesoft.anypoint_region`.
- Tools available: see Platform MCP catalog (`fetch_services`, `list_apis`, `list_agents`, `list_llms`, `list_mcp_servers`, `search_assets_semantic`, `view_api_version_details`, `view_api_instance_details`, `view_api_instance_policies`, `view_api_instance_monitoring`, `apply_policy_to_instance`, `check_policy_conformance`, `view_governance_report`, `fetch_monitoring_drill_down`, `select_active_business_group`, `select_active_environment`, `provision_mcp_server`, etc.).
- Reviewer agents (security-auditor, architecture-reviewer) MUST call Platform MCP tools to verify findings against live state when the finding is about runtime configuration (policies, environments, monitoring) rather than relying solely on static XML.

# What NOT to do

- **Don't use the legacy `anypoint-cli`** (deprecated) — always `anypoint-cli-v4`.
- **Don't hand-roll API routing** in `<choice>` blocks for an HTTP-facing app — use APIkit.
- **Don't put secrets in committed XML / properties** — preflight blocks this.
- **Don't write `Thread.sleep`** in production code or tests.
- **Don't iterate connector calls inside `<foreach>`** for >100 records — use batch endpoints, pagination, or `<batch:job>`.
- **Don't use DW 1.0** syntax — always `%dw 2.0`.
- **Don't mutate payload** in DataWeave (DW is functional; mutation is a design smell).
- **Don't skip MUnit** because "it's a tiny flow" — every flow has at least one test.
- **Don't deploy directly to prod** — always Sandbox → Staging → Prod with smoke tests.
- **Don't apply API Manager policies via the UI** — always declarative (Platform MCP `apply_policy_to_instance`, or `mvn deploy` with policy-spec files).
- **Don't ignore the governance scan** — every API passes `anypoint-cli-v4 governance:validate` (or Platform MCP `check_policy_conformance`) before merge.
- **Don't vendor the official MuleSoft skill pack** in this toolkit — install via `npx skills add` at consumer init.
