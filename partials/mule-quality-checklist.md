# Mule quality checklist

Always-on baseline applied at Phase 4 (`task-implementer`) and Phase 5 (review panel) for every MuleSoft consumer project. Generated from `.adlc/context/mulesoft-rules.md` — keep them in sync.

## CLI / Runtime

- [ ] Uses `anypoint-cli-v4` (never legacy `anypoint-cli`).
- [ ] Maven `mule-maven-plugin` ≥ 4.x in `pom.xml`.
- [ ] Mule runtime ≥ 4.6.0 declared in `pom.xml`.
- [ ] Java 17 (LTS) declared in `pom.xml`.
- [ ] Prefers DX MCP tools (`generate_mule_flow`, `generate_munit_test`, `deploy_mule_application`, etc.) over `anypoint-cli-v4` / raw `mvn` when both options exist.
- [ ] Reviewers call Platform MCP for runtime/governance verification (`view_api_instance_policies`, `check_policy_conformance`) — not static XML alone.

## Project shape

- [ ] `pom.xml` present with `<groupId>`, `<artifactId>`, `<version>`, `<packaging>mule-application</packaging>`.
- [ ] `mule-artifact.json` present.
- [ ] `src/main/mule/` present with at least one flow.
- [ ] `src/main/resources/api/` present for HTTP-facing apps (RAML or OAS).
- [ ] `src/test/munit/` present with at least one test suite.
- [ ] README.md present.
- [ ] `<api.layer>system|process|experience</api.layer>` declared in `pom.xml` `<properties>`.
- [ ] `.gitignore` excludes `target/` and any `*.secure.properties` decrypted local versions.

## Naming

- [ ] Flow / sub-flow / global-config names are kebab-case (`order-validation-flow`, `salesforce-config`).
- [ ] DataWeave types and module names are PascalCase.
- [ ] DataWeave variables and functions are lowerCamelCase.
- [ ] App identifier follows `[AppPrefix]_[Component]` analogue using `mulesoft.app_prefix` from `.adlc/config.yml`.

## Mule XML

- [ ] Every flow has a meaningful name (no `flow1`, `flow-copy`).
- [ ] Every flow has at least one MUnit test.
- [ ] Every flow has an explicit `<error-handler>` (inline or referenced) — no silent `<try>` scopes.
- [ ] HTTP-facing apps use APIkit (`<apikit:router>`) bound to RAML/OAS — not hand-rolled `<choice>` routing.
- [ ] `<choice>` blocks have explicit `when` predicates and a default `<otherwise>`.
- [ ] `when` conditions are DataWeave expressions (`#[ ... ]`), not MEL.
- [ ] Logic reused via `<flow-ref>` to sub-flows (no duplicated logic across flows).
- [ ] One responsibility per flow — validation and persistence in separate flows.

## Connector configuration

- [ ] One global-config element per upstream system.
- [ ] No inline credentials in operation elements — operations reference configs by `config-ref="..."`.
- [ ] `connectionTimeout` and `responseTimeout` declared on every `<http:request-config>`.
- [ ] Reconnection strategy declared on every network-facing config.
- [ ] Connection pooling sized to expected throughput.

## DataWeave

- [ ] DW 2.x — every script starts with `%dw 2.0`.
- [ ] Every script declares its `output` directive explicitly.
- [ ] Functional composition (`map` / `filter` / `reduce` / `groupBy`) preferred over imperative scripting.
- [ ] Type annotations on function parameters and return types where the type is non-obvious.
- [ ] No payload mutation.
- [ ] Shared transformations extracted to `dw/Modules/`.
- [ ] PII payloads pass through `dw/Modules/Redact.dwl` before logging.

## MUnit

- [ ] Coverage ≥ `mulesoft.coverage.munit_floor` from `.adlc/config.yml` (default 80).
- [ ] Per-changed-flow coverage ≥ `mulesoft.coverage.flow_floor` (default 75) in brownfield mode.
- [ ] **Every external connector is mocked** — HTTP, DB, Salesforce, Kafka, JMS, AMQP, SFTP, file. No real callouts in tests.
- [ ] Mocks cover both happy and error paths.
- [ ] Test suites named `<flow-name>-test-suite.xml`.
- [ ] `<munit:before-suite>` / `<munit:before-test>` for shared setup.
- [ ] Assertions on output payload, vars, and side-effects (`<munit-tools:verify-call>` for connector invocation count).
- [ ] No `Thread.sleep` in tests — use `<munit-tools:sleep>` or assertion-based waits.
- [ ] Test suites generated/modified via DX MCP `generate_munit_test` / `modify_munit_test` when scaffolding.

## Secrets / configuration

- [ ] `secure-properties-config` element used for sensitive properties (encrypted via `secure-mule-app` skill).
- [ ] Encryption key externalized — never committed to git.
- [ ] Property placeholders (`${...}`) for all environment-varying values.
- [ ] Property files under `src/main/resources/properties/{dev,sandbox,staging,prod}.properties`.
- [ ] **No hardcoded credentials** — preflight blocks any literal `password=`, `apiKey=`, `client_secret=`, `Bearer <token>`, `Basic <base64>`.
- [ ] **No hardcoded URLs** for upstream systems — use `${api.<name>.url}`.
- [ ] **No hardcoded record IDs** — fetch dynamically or pass as parameters.

## Observability

- [ ] Every `<logger>` uses a DataWeave object payload — no interpolated string concatenation.
- [ ] Correlation-id propagated across flows via `vars.correlationId` (set at flow start from `MULE_CORRELATION_ID` header or `uuid()`).
- [ ] Correlation-id included in every downstream connector call as a header.
- [ ] Anypoint Monitoring instrumentation on every public API (custom dashboard).
- [ ] Log levels: INFO for happy-path, ERROR in handlers, DEBUG off in production, WARN for recoverable anomalies.
- [ ] No `System.out.println` / `System.err.println` in Java module code — SLF4J or `<logger>`.

## Performance

- [ ] No connector calls inside `<foreach>` for >100 records — use batch endpoints, pagination, or `<batch:job>`.
- [ ] `repeatable-file-store-stream` for payloads >5MB.
- [ ] Pagination on every list-fetching connector that can return >100 records.
- [ ] `<async>` for fire-and-forget downstream calls.
- [ ] No `Thread.sleep` in production code — use `<scheduler>` or `<until-successful>` with backoff.

## Error handling

- [ ] Every flow has an `<error-handler>` — no silent `<try>`.
- [ ] `on-error-continue` for recoverable errors with fallback response.
- [ ] `on-error-propagate` when caller should see the error.
- [ ] No empty handlers — every handler logs (with correlation-id) AND sets a structured error response payload.
- [ ] Specific error types matched (`type="HTTP:CONNECTIVITY"`); catch-all `*` only as the last handler.
- [ ] Custom error types declared via `<error-mapping>` for domain-specific error classes.
- [ ] Dead-letter queue pattern for async / batch unrecoverable failures.

## API Manager / Governance (when `governance.api_manager_enabled: true`)

- [ ] Every public API registered as an API instance in API Manager for the target environment.
- [ ] `client-id-enforcement` policy applied (or explicit waiver in `Policies.md`).
- [ ] `rate-limiting` policy applied with limits sized to the contract.
- [ ] JWT or OAuth 2.0 validation policy when authentication is required (no Basic Auth in production).
- [ ] Governance ruleset scan passing (`anypoint-cli-v4 governance:validate` OR Platform MCP `check_policy_conformance`).
- [ ] `Policies.md` generated from `templates/policies-template.md` for every feature touching API artifacts.
- [ ] Required-policy list comes from `mulesoft.governance.required_policies` in `.adlc/config.yml` — never hardcoded.

## Documentation

- [ ] `doc:description` on every flow / sub-flow / connector operation — ≤3 lines of prose.
- [ ] Long-form context lives in spec / architecture doc (linked via `See: ...`), not in `doc:description`.
- [ ] DataWeave functions have one-line header comment.
- [ ] README up to date for each significant module.

## Deployment

- [ ] Default deploy target `cloudhub2` unless `mulesoft.deploy_target` overrides.
- [ ] Deploy via `mvn deploy -P<profile>` OR DX MCP `deploy_mule_application` / `update_mule_application`.
- [ ] Worker count ≥ 2 in production (CloudHub) or replicas ≥ 2 (RTF).
- [ ] vCore allocation declared in `pom.xml` `<cloudhub2Deployment>`.
- [ ] Region matches `mulesoft.anypoint_region`.
- [ ] Sandbox → Staging → Prod promotion path (no direct prod deploy).
- [ ] Each environment has its own connected app credentials (separate property files).
- [ ] API Manager policies promoted via Platform MCP `apply_policy_to_instance`, not UI clicks.

## Exchange asset publishing

- [ ] Exchange search performed (Platform MCP `search_global_assets` / `search_assets_semantic`) before building a new reusable component.
- [ ] Asset published via DX MCP `create_and_manage_assets` (preferred) or `mvn exchange:publish`.
- [ ] Asset name follows `<AppPrefix>-<asset-type>-<intent>`.
- [ ] Asset version is semver — major bump on breaking change.
- [ ] Every published asset has README, examples, tests.

## MCP

- [ ] `.mcp.json` wires both DX MCP and Platform MCP.
- [ ] DX MCP env: `ANYPOINT_CLIENT_ID`, `ANYPOINT_CLIENT_SECRET`, `ANYPOINT_REGION`.
- [ ] Platform MCP uses `mcp-remote@latest` bridge with OAuth client info.
- [ ] Connected-app scopes match the operations the agents need to perform.
- [ ] Reviewer agents call Platform MCP for runtime / governance state — not static XML inspection alone.

## When this checklist is consulted

- **Phase 4** (`task-implementer`): every implementation pass cross-checks the checklist before marking the task complete.
- **Phase 5** (review panel): every reviewer dimension agent (correctness / quality / architecture / test-coverage / security) reads this in addition to its file-glob-matched Mule rubric.
- **Phase 7-8** (deploy / wrapup): preflight (`tools/mule-preflight`) verifies the gating subset before allowing deploy.
