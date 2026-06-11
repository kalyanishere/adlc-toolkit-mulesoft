# Project Overview — ADLC Toolkit (MuleSoft edition)

## What this project is

The ADLC Toolkit (MuleSoft edition) is a library of **skills, agents, templates, and quality gates** that enable spec-driven development for MuleSoft / Anypoint Platform projects with Claude Code. It is the source of `/spec`, `/architect`, `/proceed`, `/review`, `/bugfix`, `/wrapup`, and other skills that consumer MuleSoft projects use to run their own Agentic Development Life Cycle (ADLC) pipelines.

This is the MuleSoft-tuned fork of the generic ADLC toolkit, cloned from `adlc-toolkit-sfdc` on 2026-06-11. Where the SFDC fork vendored the `forcedotcom/afv-library` skill set, the MuleSoft fork **integrates with the official MuleSoft skill pack** (`@salesforce/mulesoft-vibes-skills`, installed at consumer init via `npx skills add mulesoft/mulesoft-dx/skills/mule-development`) and the **two MuleSoft MCP servers** (DX and Platform). The toolkit's contribution is the ADLC pipeline orchestration, the `mulesoft-rules.md` quality gate, the review-time rubric layer, and the file-glob → skill+rubric router.

This repo is itself a consumer of the toolkit only in the narrow sense that its own feature work is tracked in `.adlc/specs/`. No `.adlc/knowledge/lessons/`, `.adlc/bugs/`, or `.adlc/templates/` directory inside this repo (those live in consumer projects after `/init`). The toolkit's canonical `templates/` directory at the repo root is what `/init` copies into consumer projects.

## Who uses it

- **MuleSoft consumer projects** symlink this repo to `~/.claude/skills-mulesoft/` and `~/.claude/agents/`. Any improvement committed here is immediately visible to every Claude Code session on the machine — no publish step.
- **Toolkit maintainers** evolve the skills, add new ones, and fix bugs in the skill definitions themselves. REQs tracked here describe changes to the toolkit's own surface area: skill behavior, template schemas, agent prompts, quality-gate rules, documentation.

## Install model

Symlink-based live install. One canonical git clone on disk, symlinked at `~/.claude/skills-mulesoft/`. Edits to the clone are visible immediately. No separate installed copy, no sync step, no versioning at the install layer.

The symlink target is `skills-mulesoft` (not `skills`) to avoid colliding with `adlc-toolkit-sfdc` if both forks are installed on the same machine. Slash commands are namespaced via the symlink path.

## Primary surface areas

| Surface | Files | Purpose |
|---|---|---|
| Skills | `<skill-name>/SKILL.md` | Markdown files invoked by Claude Code as slash commands |
| Mule rubrics | `skills/mule/<rubric-name>/SKILL.md` | Toolkit-authored review-time rubrics. Build-time skills come from the official MuleSoft pack, installed at consumer init via `npx skills add` — not vendored here |
| Mule router | `skills/mule-router/SKILL.md` | File-glob → skill+rubric dispatch table |
| Agents | `agents/<agent-name>.md` | 11 specialized subagent definitions (5 Opus / 6 Sonnet) |
| Templates | `templates/*.md` | Canonical templates for requirements, bugs, lessons, tasks, assumptions, policies |
| Partials | `partials/*.{sh,md}` | Shared snippets sourced by SKILL.md files (ethos, mule-quality-checklist) |
| Workflows | `workflows/*.workflow.js` | Deterministic Dynamic Workflow scripts for orchestration |
| Tools | `tools/lint-skills/`, `tools/mule-lint/`, `tools/mule-preflight/` | SKILL.md hygiene linter; Mule-specific static rule check + pre-deploy gate |
| Presets | `presets/mule-*.yml` | Stack-shaped starter configs for `.adlc/config.yml` |
| Ethos | `ETHOS.md` | Six principles injected into every skill — the non-negotiable constitution |
| Models | `MODEL_ASSIGNMENTS.md` | Per-agent registry — Sonnet | Opus only |
| Docs | `README.md` | Install instructions and skill catalog |

## Relationship to consumer projects

`/init` is the bridge. When a MuleSoft consumer project runs `/init`, it:

1. **Validates prerequisites** — Node.js 20+, JDK 17, Maven 3.8+, `anypoint-cli-v4` configured (`anypoint-cli-v4 conf client_id` / `client_secret`), `anypoint-cli-dx-mule-plugin` installed, Anypoint Extension Pack 1.10.0+
2. **Validates connected-app credentials** — the consumer must have TWO Anypoint connected apps configured:
   - One **acting on its own behalf** (for DX MCP — client credentials)
   - One **acting on user's behalf** with Authorization Code + Refresh Token (for Platform MCP — OAuth)
3. **Installs the official MuleSoft skill pack**: `npx -y skills add mulesoft/mulesoft-dx/skills/mule-development --target claude-code --scope project --method symlink`
4. **Writes `.mcp.json`** wiring both `mulesoft-mcp-server` (stdio) and `mulesoft-platform` (remote, via `mcp-remote@latest` bridge)
5. **Creates `.adlc/context/`, `.adlc/specs/`, `.adlc/bugs/`, `.adlc/knowledge/`, and `.adlc/templates/`** in that project, copying from the toolkit's `templates/` directory

After `/init`, the consumer project uses skills that read from **its** `.adlc/` structure — not the toolkit's.

The consumer's `.adlc/config.yml` declares MuleSoft-specific values: `app_prefix` (3–8 char identifier, used in flow/policy naming), `mule_runtime` (4.6.0+ floor), `java_version` (17), `anypoint_org_id`, `anypoint_environment` (Sandbox|Staging|Prod), `anypoint_region` (PROD_US|PROD_EU|PROD_CA|PROD_JP|PROD_IN), `deploy_target` (cloudhub2|rtf|onprem), `api_layer` (system|process|experience), `governance.api_manager_enabled`, `governance.required_policies`, and `coverage` (mode/floor/diff_only). Skills branch on those flags — the API Manager policy gate fires only when `governance.api_manager_enabled: true`; the RTF deploy path activates only when `deploy_target: rtf` is declared.

The toolkit's own `.adlc/` (containing only `specs/`, `context/`) is minimal by design. The toolkit doesn't track lessons or bugs for itself; that may change if the toolkit's internal work grows.

## Current scope

The toolkit was cloned from `adlc-toolkit-sfdc` on 2026-06-11 and is being rebuilt for MuleSoft. As of v1:

- Skill set: **official MuleSoft pack** (build-time orchestration, installed at consumer init) + **toolkit-authored rubrics** under `skills/mule/` (review-time scoring)
- MCP wiring: **DX MCP** (`mulesoft-mcp-server` npm; stdio) for Anypoint Code Builder operations; **Platform MCP** (`omni.mulesoft.com/mcp` via `mcp-remote@latest`) for governance/monitoring/Exchange
- Promotes `mulesoft-rules.md` to an enforced quality gate at Phase 4 (build) and Phase 5 (review)
- Models restricted to Sonnet/Opus only (Haiku eliminated, no third-party models)
- Presets: `mule-core.yml` (Mule app + MUnit + CloudHub deploy) and `mule-anypoint.yml` (Core + API Manager + Governance + Exchange + RTF)

## Permitted models

Only `sonnet` and `opus` are permitted in any agent's `model:` frontmatter. The single registry mapping every agent to a model is `MODEL_ASSIGNMENTS.md` at the repo root. Haiku and any third-party model are out of scope by policy.

## REQ-numbering policy (cross-project global counter)

This repo shares a **global** REQ counter at `~/.claude/.global-next-req` with all consumer projects on the machine. Future REQ allocations from this toolkit MUST take the next slot above the global high-water, not above this toolkit's local high-water. Existing toolkit specs keep their numbers — the policy applies to new allocations only.

Rationale: a single REQ id should resolve to one work item across every repo on the machine, so cross-repo references (links, lessons, branch names, PR titles) are unambiguous.
