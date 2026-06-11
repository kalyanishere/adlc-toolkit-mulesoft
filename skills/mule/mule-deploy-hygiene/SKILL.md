---
name: mule-deploy-hygiene
description: Architecture rubric for deploy-shape (pom.xml mule-maven-plugin config, mule-artifact.json, environment-specific configs). Loaded by Phase 5 architecture-reviewer when the change set touches pom.xml, mule-artifact.json, or env-specific properties.
glob: pom.xml, mule-artifact.json, src/main/resources/properties/**
dimension: architecture
---

# mule-deploy-hygiene (architecture rubric)

Score deploy configuration: pom.xml structure, environment profiles, vCore / replica sizing, region, secure-properties wiring.

## Non-negotiables

- **`mule-maven-plugin` ≥ 4.x** in `pom.xml`
- **Mule runtime ≥ project floor** (`mulesoft.mule_runtime` from `.adlc/config.yml`, default 4.6.0)
- **Java 17** declared in `<maven.compiler.source>` and `<maven.compiler.target>`
- **`<api.layer>` declared** in `<properties>` (cross-checked by `api-led-architecture` rubric)
- **Maven profile per environment**: `cloudhub-dev`, `cloudhub-sandbox`, `cloudhub-prod` (or RTF / on-prem analogues)
- **Workers ≥ 2 in production** (CloudHub) or replicas ≥ 2 (RTF) — HA requirement

## Major findings

- **Single-worker production deploy** — `<workers>1</workers>` in cloudhub-prod profile
- **vCore allocation not declared** — relies on Anypoint Platform default which may not match the load
- **Region missing or inconsistent** with `mulesoft.anypoint_region` from `.adlc/config.yml`
- **`mule-artifact.json` lists secure properties not referenced** by `secure-properties-config` (drift) — or vice versa
- **Build / runtime version mismatch**: `pom.xml` `<app.runtime>` and `mule-artifact.json` `minMuleVersion` disagree
- **Static IPs not declared** when upstream firewalls require IP whitelisting
- **Anypoint VPC binding missing** when private network access is required

## Minor findings

- **Maven profile names don't follow `<target>-<env>` pattern** — e.g., `prod` vs `cloudhub-prod`
- **`<deploymentName>`** not parameterized via `${app_prefix}` from `.adlc/config.yml`
- **`<exchange-modeling>` block missing** when the project publishes to Exchange
- **vCore allocation matches between dev and prod** — usually wrong; prod typically needs 2-4× dev

## CloudHub 2.0 deploy section to verify

```xml
<cloudhub2Deployment>
  <muleVersion>${app.runtime}</muleVersion>
  <organizationId>${anypoint.org.id}</organizationId>
  <environment>${anypoint.environment}</environment>
  <target>${cloudhub.target}</target>           <!-- e.g., cloudhub-us-east-1 -->
  <workers>${cloudhub.workers}</workers>        <!-- ≥2 in prod -->
  <vCores>${cloudhub.vcores}</vCores>
  <replicationFactor>${cloudhub.replicas}</replicationFactor>
  <applicationName>${app_prefix}-${project.artifactId}</applicationName>
  <properties>
    <anypoint.environment>${anypoint.environment}</anypoint.environment>
  </properties>
</cloudhub2Deployment>
```

## RTF deploy section to verify

```xml
<rtfDeployment>
  <muleVersion>${app.runtime}</muleVersion>
  <organizationId>${anypoint.org.id}</organizationId>
  <environment>${anypoint.environment}</environment>
  <target>${rtf.target}</target>                 <!-- target id from Runtime Manager -->
  <replicas>${rtf.replicas}</replicas>           <!-- ≥2 in prod -->
  <cpuReserved>${rtf.cpu.reserved}</cpuReserved>
  <memoryReserved>${rtf.memory.reserved}</memoryReserved>
  <applicationName>${app_prefix}-${project.artifactId}</applicationName>
</rtfDeployment>
```

## Live-state verification

Reviewers SHOULD call DX MCP `list_applications` for the target environment to verify:
- Deployed app version matches `pom.xml` `<version>`
- Worker / replica count matches the profile declaration
- Region matches `mulesoft.anypoint_region`

## Common findings

| Finding | Severity | Fix |
|---|---|---|
| `<workers>1</workers>` in cloudhub-prod | Major | Set to ≥2 for HA; size vCore accordingly |
| No `<api.layer>` in `<properties>` | Major | Add `<api.layer>system|process|experience</api.layer>` |
| `mule-maven-plugin` 3.x | Critical | Upgrade to 4.x |
| Java 11 declared | Major | Upgrade to Java 17 (Mule 4.6+ requires it) |
| Profile-named `prod` (no qualifier) | Minor | Rename to `cloudhub-prod` / `rtf-prod` per project convention |
| Secure-property listed in mule-artifact.json but not referenced in flows | Minor | Remove from manifest, or wire it up |

## Reference

- mulesoft-rules.md "Deployment Requirements" section
- mule-maven-plugin docs: https://docs.mulesoft.com/mule-runtime/latest/mmp-concept
- partials/mule-quality-checklist.md (always-on baseline)
