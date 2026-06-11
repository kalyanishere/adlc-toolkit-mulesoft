# ADLC Toolkit — MuleSoft edition

Skills, agents, templates, and quality gates for spec-driven development on **MuleSoft / Anypoint Platform** projects with [Claude Code](https://claude.com/claude-code). Wraps the ADLC orchestration around the official [`@salesforce/mulesoft-vibes-skills`](https://docs.mulesoft.com/anypoint-code-builder/vibes-skills) skill pack and the two MuleSoft MCP servers (DX MCP and Platform MCP) so reviewers and the implementer consume Mule-specific rubrics by file glob.

> **Status (2026-06-11)**: cloned from `adlc-toolkit-sfdc` and rebuilt for MuleSoft. Phase 0 complete (context rewrite + `mulesoft-rules.md` baseline + `mule-skills-catalog.md`). Subsequent phases — agent rewrites, skill SKILL.md rewrites, Mule presets, `skills/mule/` review rubrics, `tools/mule-lint`, `tools/mule-preflight` — are tracked but not yet authored. Until those land, **this toolkit is not yet usable end-to-end on a consumer project**. Use `adlc-toolkit-sfdc` as the reference for what each skill should look like once rewritten.

## What's Planned

### Orchestration skills (carry over from SFDC, will be rewritten)

| Skill | Description |
|-------|-------------|
| `/init` | Bootstrap `.adlc/` in a new MuleSoft repo. Validates Node 20+/JDK 17/Maven/`anypoint-cli-v4`, runs `npx skills add mulesoft/mulesoft-dx/skills/mule-development`, writes `.mcp.json` wiring DX MCP + Platform MCP. |
| `/spec` | Write requirement specs from feature requests |
| `/architect` | Design architecture and break requirements into tasks |
| `/validate` | Validate any ADLC phase output before advancing |
| `/proceed` | End-to-end pipeline: validate → architect → implement → reflect → review → PR → wrapup |
| `/sprint` | Parallel pipeline orchestrator — multiple `/proceed` sessions across REQs (`--workflow` engine + legacy fallback) |
| `/reflect` | Post-implementation self-review walking `mulesoft-rules` + Mule rubrics |
| `/review` | 6-agent panel (correctness, quality, architecture, tests, security, reflector) loading Mule rubrics by file glob; reviewers also call DX/Platform MCP for runtime/governance evidence |
| `/canary` | Anypoint Sandbox → Staging → Prod promotion gate (`mvn deploy -P<env>` + MUnit + Postman/API console smoke). **Prod is validate-only** — surfaces the validation id and instructs the user to run the deploy manually. |
| `/wrapup` | Close out a feature — merge, `Policies.md` gate, API Manager policy promotion via Platform MCP, knowledge capture, `mvn deploy` / DX MCP `deploy_mule_application` |
| `/bugfix` | End-to-end bug-fix workflow (analyze → fix → verify → ship → capture lesson) |
| `/audit` | Codebase audit (test coverage, governance compliance, secrets hygiene) |

### MuleSoft skill / MCP integration

- **Official skill pack** (`@salesforce/mulesoft-vibes-skills`) — installed at consumer init via `npx skills add mulesoft/mulesoft-dx/skills/mule-development`. Provides `build-mule-integration`, `secure-mule-app`, `generate-doc-description`, `create-mule-run-config`, `create-project-template`, etc.
- **DX MCP server** (`mulesoft-mcp-server` stdio, client-credentials connected app) — provides `generate_mule_flow`, `generate_munit_test`, `deploy_mule_application`, `create_and_manage_assets`, etc.
- **Platform MCP server** (`omni.mulesoft.com/mcp` via `mcp-remote@latest`, OAuth Authorization Code + Refresh Token) — provides `list_apis`, `view_api_instance_policies`, `apply_policy_to_instance`, `check_policy_conformance`, `fetch_monitoring_drill_down`, `search_assets_semantic`, etc.

See `.adlc/context/mule-skills-catalog.md` for the full file-glob → skill+rubric dispatch table.

### Toolkit-authored Mule rubrics (planned, `skills/mule/`)

| Rubric | Purpose |
|---|---|
| `mule-flow-quality` | Quality bar for Mule XML flows |
| `mule-error-handling` | Error-handler completeness (correctness) |
| `dataweave-quality` | DW 2.x syntax, output directive, functional composition |
| `munit-coverage` | Coverage bar, mock completeness, assertion quality |
| `api-led-architecture` | System / Process / Experience layering |
| `apikit-contract-conformance` | APIkit-bound RAML/OAS, contract-first |
| `mule-secrets-hygiene` | Secure-properties, no hardcoded credentials |
| `mule-connector-config-hygiene` | One config per upstream, timeout/retry, pooling |
| `mule-deploy-hygiene` | `pom.xml`, `mule-artifact.json`, vCore/replica sizing |
| `governance-policies` | API Manager policy declarations, governance scan conformance |

## Install (when complete)

```bash
git clone https://github.com/<org>/adlc-toolkit-mulesoft.git ~/.claude/skills-mulesoft
ln -s ~/.claude/skills-mulesoft/agents ~/.claude/agents-mulesoft
```

The symlink target is `skills-mulesoft` (not `skills`) to avoid colliding with `adlc-toolkit-sfdc` if both forks are installed on the same machine.

## Consumer prerequisites (when complete)

- Node.js 20+
- Java 17 (LTS)
- Maven 3.8+
- `anypoint-cli-v4` installed and authenticated:
  ```bash
  anypoint-cli-v4 conf client_id <ID>
  anypoint-cli-v4 conf client_secret <SECRET>
  ```
- `anypoint-cli-dx-mule-plugin` installed
- Anypoint Extension Pack 1.10.0+ (VSCode)
- TWO Anypoint connected apps configured:
  - **DX MCP** — connected app *acting on its own behalf* (client credentials), with scopes for Code Builder, Monitoring, API Manager, Exchange, Runtime Manager
  - **Platform MCP** — connected app *acting on user's behalf* with Authorization Code + Refresh Token grant types, with scopes for Exchange, API Manager, Monitoring, Governance, Runtime Manager

## Models policy

Only `sonnet` and `opus` are permitted in any agent's `model:` frontmatter. Haiku and any third-party model are out of scope. See `MODEL_ASSIGNMENTS.md`.

## Ethos

The six builder principles in `ETHOS.md` are injected into every skill at invocation time. Spec first; knowledge compounds; parallel by default; verify, don't trust; process is not optional; if it's broken, fix it.

## Related

- **`adlc-toolkit-sfdc`** — the Salesforce sibling fork. Consumer projects should pick ONE toolkit per repo (not both — they're symlinked at different `skills-*` targets to avoid command collision, but each `/init` is mutually exclusive at the consumer level).
