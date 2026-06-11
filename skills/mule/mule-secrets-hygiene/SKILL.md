---
name: mule-secrets-hygiene
description: Security rubric for secrets handling. Loaded by Phase 5 security-auditor when the change set touches XML, properties, secure-properties, or DataWeave files.
glob: "**/*.{xml,properties,dwl}", "**/*.secure.properties"
dimension: security
---

# mule-secrets-hygiene (security rubric)

Score Mule projects against secrets-hygiene rules. mule-lint also catches static violations; this rubric scores severity + remediation depth.

## Non-negotiables (any violation = Critical)

- **No hardcoded credentials** in committed XML / properties / DataWeave (mule-lint blocks; auditor confirms severity)
- **`secure-properties-config`** present for any flow that reads sensitive properties
- **Encryption key externalized** — never committed to git (`.gitignore` excludes `*.key` files and any `secure.properties.key` path)
- **No hardcoded URLs** for upstream systems — use `${api.<name>.url}` placeholders
- **No hardcoded record IDs** — fetch dynamically or pass as parameters
- **`.gitignore`** includes `*.secure.properties` (decrypted local versions), `target/`, `.env`

## Major findings

- **Plaintext credential** in `dev.properties` (even non-prod credentials shouldn't be committed)
- **Secure-properties scope too narrow** — config encrypts only some properties when others are equally sensitive
- **Encryption algorithm legacy** (MD5 / DES) — must be AES-CBC or higher
- **Property placeholder resolves to literal at build time** — defeats the purpose
- **Secrets passed as command-line args** — visible in `ps` output; use env vars instead
- **No PII redaction** when payload contains email/phone/SSN/credit card AND `<logger>` outputs payload
- **Connected-app credentials in `.env` committed** — `.env` gitignore missing

## Patterns to flag

```
# Detected by mule-lint hardcoded-credentials rule (high-confidence):
password=plainvalue
api.client_secret=hunter2supersecret
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Authorization: Basic dXNlcjpwYXNzd29yZA==
private_key=-----BEGIN RSA PRIVATE KEY-----...

# Allowed (placeholder):
password=${secure::salesforce.password}
api.client_secret=${secure::api.client_secret}
```

## Production-specific rules

When `.adlc/config.yml` `mulesoft.anypoint_environment: "Production"` (or pom.xml profile is `cloudhub-prod` / `rtf-prod`):

- **No Basic Auth on production endpoints** — JWT or OAuth 2.0 only
- **mTLS material loaded from secure-properties only** — never inline / never committed certs
- **DEBUG log level disabled** — production properties have INFO or higher
- **Secrets manager (Anypoint Secrets Manager) preferred over file-based secure-properties** for prod

## Connected-app credentials (`/init` requirement)

The toolkit requires TWO Anypoint connected apps:
- DX MCP — client credentials grant
- Platform MCP — OAuth Authorization Code + Refresh Token

**Audit**:
- `.env` (or equivalent) holding `ANYPOINT_*_CLIENT_ID/SECRET` is gitignored
- Connected-app scopes match the operations the agents need to perform (least-privilege)
- Client secrets rotated per the team's secrets-rotation runbook

## Common findings

| Finding | Severity | Fix |
|---|---|---|
| `api.password=plainvalue` in committed properties | Critical | Move to secure-properties; rotate the credential |
| `<secure-properties:config>` element missing despite encrypted properties used | Critical | Add the config element; reference it from the flow |
| Encryption key path under `src/` | Critical | Externalize to env var (`SECURE_PROPS_KEY`) or Anypoint Secrets Manager |
| `.env` not gitignored | Critical | Add `.env` to `.gitignore`; rotate any committed secrets |
| `<logger message="#[payload]"/>` for PII payload | Major | Pipe through `dw/Modules/Redact.dwl` |
| Production endpoint with Basic Auth | Critical | Replace with OAuth 2.0 / JWT validation policy |
| Hardcoded record ID in flow | Major | Fetch dynamically or accept as parameter |

## Reference

- mulesoft-rules.md "Secrets / Configuration Requirements" section
- The official `secure-mule-app` skill is the canonical encryption path
- partials/mule-quality-checklist.md (always-on baseline)
