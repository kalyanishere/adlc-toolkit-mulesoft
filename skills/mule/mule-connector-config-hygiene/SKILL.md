---
name: mule-connector-config-hygiene
description: Architecture rubric for connector configuration patterns. Loaded by Phase 5 architecture-reviewer when the change set touches global-config XML elements (http:request-config, db:config, salesforce:sfdc-config, etc.).
glob: src/main/mule/**/*.xml
dimension: architecture
---

# mule-connector-config-hygiene (architecture rubric)

Score connector-config patterns: singletons per upstream, timeouts, reconnection, pooling.

## Non-negotiables

- **One global-config element per upstream system** — not one per flow
- **Operations reference configs by name** (`config-ref="..."`) — no inline credentials/host on operation elements
- **Every `<http:request-config>` declares `connectionTimeout` and `responseTimeout`** explicitly (defaults are too generous for prod)
- **Reconnection strategy** declared on every network-facing config

## Major findings

- **Inline config on operation element** — `<http:request host="api.example.com" path="/v1/orders"/>` instead of `<http:request config-ref="orders-config" path="/v1/orders"/>`
- **Two `<http:request-config>` elements targeting the same upstream** — consolidate; differentiate at operation level
- **No reconnection strategy** on a network-facing config — transient errors crash the flow
- **Connection pool sized to default** when high-volume traffic is expected — undersized pool throttles throughput
- **Configs scattered** across feature flow files instead of consolidated in `globals.xml` (or `<system>-globals.xml`)

## Minor findings

- **Config name not kebab-case** (e.g., `salesforceConfig` instead of `salesforce-config`)
- **Config name doesn't reflect upstream** (`config1` instead of `customers-system-api-config`)
- **Pooling not declared** even when defaults are appropriate — explicit is better
- **TLS config inlined** instead of referenced from a shared `<tls:context>` element

## Configuration to verify per connector

| Connector | Required attributes | Recommended additions |
|---|---|---|
| `<http:request-config>` | host (or baseUri), connectionTimeout, responseTimeout | reconnection strategy, TLS context, default-headers |
| `<http:listener-config>` | host, port, basePath | TLS context, response-streaming-mode |
| `<db:config>` | dataSource (or per-DB connection params), connection-pooling | reconnection strategy |
| `<salesforce:sfdc-config>` | username, password (secure-properties), token, environment | reconnection strategy |
| `<jms:config>` / `<amqp:config>` | broker, factory configuration | reconnection, consumer prefetch |
| `<kafka:producer-config>` / `<kafka:consumer-config>` | bootstrap servers, security protocol | acks, batch-size, max-in-flight |
| `<sftp:config>` | host, port, credentials (secure) | known-hosts strict checking |
| `<file:config>` | working directory | (none) |
| `<email:smtp-config>` | host, port, credentials (secure) | TLS context |

## Common findings

| Finding | Severity | Fix |
|---|---|---|
| Inline `host="api.example.com"` on `<http:request>` | Critical | Move to global `<http:request-config name="...-config" host="..."/>`; reference via `config-ref` |
| Two configs for the same upstream | Major | Consolidate; differentiate by operation path |
| No `connectionTimeout` / `responseTimeout` | Major | Add explicit values appropriate to the upstream's SLA |
| No reconnection strategy on network config | Major | Add `<reconnection><reconnect frequency="3000" count="3"/></reconnection>` (or strategy fitting the use case) |
| Config defined inside a feature flow file | Minor | Move to `globals.xml` or `<upstream>-globals.xml` |
| Config name `config1` | Minor | Rename to `<upstream-or-purpose>-config` |

## Reference

- mulesoft-rules.md "Mule XML / Flow Requirements" → Connector Configuration Requirements
- Companion rubric: `mule-secrets-hygiene` (no inline credentials)
- partials/mule-quality-checklist.md (always-on baseline)
