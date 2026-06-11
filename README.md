# ADLC Toolkit — MuleSoft edition

Skills, agents, templates, and quality gates for spec-driven development on **MuleSoft / Anypoint Platform** projects with [Claude Code](https://claude.com/claude-code). Wraps the ADLC orchestration around the official [`@salesforce/mulesoft-vibes-skills`](https://docs.mulesoft.com/anypoint-code-builder/vibes-skills) skill pack and the two MuleSoft MCP servers (DX MCP and Platform MCP) so reviewers and the implementer consume Mule-specific rubrics by file glob.

> **Status (2026-06-11)**: cloned from `adlc-toolkit-sfdc` and rebuilt for MuleSoft. Phases 0a-g (context + agents + skill rewrites), 2 (11 review rubrics + `mule-router`), 4 (Mule presets + templates), and 7 (`mule-lint` / `mule-preflight` / `mule-coverage` tools) are landed. The 13 orchestration skills have substantive Mule-flavored `SKILL.md` content; rubrics carry real DataWeave 2.x / MUnit / APIkit / API Manager scoring. **Pre-consumer-launch sweep complete** (this date): `templates/requirement-template.md` tier examples rewritten for Mule; `spec/SKILL.md` Step 1.7 / 1.8.3 / Step 3 carve-outs replaced (Anypoint operational artifacts, not SFDC Setup); `agents/pipeline-runner.md` worktree description corrected; `templates/task-template.md` example uses real Mule artifact paths; `mule-observability` rubric authored to score correlation-id propagation + structured logging + Anypoint Monitoring instrumentation. **Remaining before consumer-ready**: end-to-end dry run on a real Mule project (no smoke-test recorded) and the planned `*-mule` rename + `adlc-router` shim (see below).
>
> **Naming collision plan**: this fork and `adlc-toolkit-sfdc` ship the same skill names (`/init`, `/proceed`, …), so a developer with both installed would see one silently shadow the other. Resolution (planned, separate pass): rename this fork's skills to `*-mule` (sfdc fork → `*-sfdc`) and stand up a small `adlc-router` repo whose skills own the unsuffixed names and prompt for stack when both forks are present. Single-fork users see no behavior change.

## What's Built

### Orchestration skills

| Skill | Description |
|-------|-------------|
| `/init` | Bootstrap `.adlc/` in a new MuleSoft repo. Validates Node 20+/JDK 17/Maven/`anypoint-cli-v4`, runs `npx skills add mulesoft/mulesoft-dx/skills/mule-development`, writes `.mcp.json` wiring DX MCP + Platform MCP. |
| `/spec` | Write requirement specs from feature requests |
| `/architect` | Design architecture and break requirements into tasks |
| `/validate` | Validate any ADLC phase output before advancing |
| `/proceed` | End-to-end pipeline: validate → architect → implement → reflect → review → PR → wrapup |
| `/sprint` | Parallel pipeline orchestrator — multiple `/proceed` sessions across REQs (`--workflow` engine + legacy fallback) |
| `/reflect` | Post-implementation self-review walking `mulesoft-rules` + Mule rubrics |
| `/review` | 5-agent panel (correctness, quality, architecture, tests, security) loading Mule rubrics by file glob; scoped to the current diff vs `main` |
| `/audit` | **Whole-repo health check** — scores the existing codebase against `mulesoft-rules.md` + the 10 rubrics + governance/coverage/secrets, persists report under `.adlc/audit-reports/`. Read-only; distinct from `/review` (diff-scoped) and `/canary` (deploy gate). |
| `/canary` | Anypoint Sandbox deploy gate (`mule-preflight` + `mvn deploy -P<env>` / DX MCP `deploy_mule_application` + Newman smoke + governance scan). **Sandbox-only by design** — Staging / Prod promotions belong to the project's CI/CD pipeline. |
| `/wrapup` | Close out a feature — merge, `Policies.md` gate, API Manager policy promotion via Platform MCP, knowledge capture, deploy hand-off |
| `/bugfix` | End-to-end bug-fix workflow (analyze → fix → verify → ship → capture lesson) |
| `/status` | ADLC dashboard across REQ specs, bugs, pipeline state |
| `/template-drift` | Detect drift between consumer `.adlc/` files and toolkit templates |

### MuleSoft skill / MCP integration

- **Official skill pack** (`@salesforce/mulesoft-vibes-skills`) — installed at consumer init via `npx skills add mulesoft/mulesoft-dx/skills/mule-development`. Provides `build-mule-integration`, `secure-mule-app`, `generate-doc-description`, `create-mule-run-config`, `create-project-template`, etc.
- **DX MCP server** (`mulesoft-mcp-server` stdio, client-credentials connected app) — provides `generate_mule_flow`, `generate_munit_test`, `deploy_mule_application`, `create_and_manage_assets`, etc.
- **Platform MCP server** (`omni.mulesoft.com/mcp` via `mcp-remote@latest`, OAuth Authorization Code + Refresh Token) — provides `list_apis`, `view_api_instance_policies`, `apply_policy_to_instance`, `check_policy_conformance`, `fetch_monitoring_drill_down`, `search_assets_semantic`, etc.

See `.adlc/context/mule-skills-catalog.md` for the full file-glob → skill+rubric dispatch table.

### Toolkit-authored Mule rubrics (`skills/mule/`)

All eleven rubrics carry scoring tables, file-glob dispatch from `mule-router`, and real Mule XML / DataWeave 2.x / MUnit examples — not skeleton placeholders.

| Rubric | Purpose |
|---|---|
| `mule-flow-quality` | 150-pt scoring on flow naming, newspaper rule, sub-flow reuse, choice/error structure |
| `mule-observability` | 100-pt scoring on correlation-id propagation, structured logging, log-level discipline, Anypoint Monitoring instrumentation |
| `mule-error-handling` | Error-handler completeness, `<until-successful>` / `<batch:job>` / `<scatter-gather>` semantics |
| `dataweave-quality` | 100-pt scoring on DW 2.0 syntax, output directives, null-safety, module reuse |
| `munit-coverage` | 120-pt scoring on coverage floors, mock completeness per connector, assertion quality |
| `api-led-architecture` | System / Process / Experience layering with Platform MCP cross-checks |
| `apikit-contract-conformance` | RAML/OAS spec quality, APIkit binding, contract-first enforcement |
| `mule-secrets-hygiene` | secure-properties, AES requirement, prod-Basic-Auth ban, two-connected-app audit |
| `mule-connector-config-hygiene` | One config per upstream (HTTP / DB / Salesforce / JMS / Kafka / SFTP), pooling, reconnection |
| `mule-deploy-hygiene` | CloudHub 2.0 + RTF deploy XML, vCore/replica sizing, JDK 17, mule-maven-plugin 4.x |
| `governance-policies` | API Manager policy declarations vs live state, governance ruleset scan, drift detection |

### Quality tools (`tools/`)

| Tool | What it does |
|---|---|
| `mule-lint/check.sh` (+ `check.py`) | 474-line linter: hardcoded creds, missing error-handlers, DW 1.0, missing output, `Thread.sleep`, weak names, prod Basic Auth |
| `mule-preflight/check.sh` | Pre-deploy gate: lint → `mvn validate compile munit:test` → coverage → secrets → policies → `anypoint-cli-v4 governance:validate` |
| `mule-coverage/check.sh` (+ `check.py`) | Parses MUnit coverage XML, applies `mulesoft.coverage` floor policy from `.adlc/config.yml` |

## Install (when ready for consumer use)

```bash
git clone https://github.com/<org>/adlc-toolkit-mulesoft.git ~/.claude/skills-mulesoft
ln -s ~/.claude/skills-mulesoft/agents ~/.claude/agents-mulesoft
```

The symlink target is `skills-mulesoft` (not `skills`) to avoid colliding with `adlc-toolkit-sfdc` *files* on the same machine. Note that this does NOT solve the slash-command collision (both forks register `/init`, `/proceed`, etc.) — that's resolved by the planned `*-mule` / `*-sfdc` rename + `adlc-router` shim. Until that lands, consumer projects must install only one fork.

## Consumer prerequisites

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

- **`adlc-toolkit-sfdc`** — the Salesforce sibling fork. Until the rename + `adlc-router` lands, consumer projects must pick ONE toolkit per machine (slash-command names collide). Once it lands, both can coexist and `/init` will prompt for stack when both are installed.
- **`adlc-router`** (planned) — small shim repo whose skills own the unsuffixed names (`/init`, `/spec`, `/proceed`, …) and dispatch to `*-mule` or `*-sfdc` underlying skills. Single-fork users never see the dispatch prompt.
