# Architecture — ADLC Toolkit (MuleSoft edition)

## Top-level layout

```
adlc-toolkit-mulesoft/
├── ETHOS.md                    # 6 principles — injected into every skill
├── README.md                   # Install + skill catalog
├── MODEL_ASSIGNMENTS.md        # Per-agent model registry (Sonnet | Opus only)
├── <skill>/SKILL.md            # One directory per skill (spec/, architect/, proceed/, etc.)
├── agents/<agent>.md           # Specialized subagent definitions (11 total, 5 Opus / 6 Sonnet)
├── skills/mule/                # Toolkit-authored review-time rubrics for Mule artifacts
├── skills/mule-router/SKILL.md # File-glob → skill+rubric dispatch
├── templates/*.md              # Canonical templates (copied into consumer projects by /init)
├── partials/                   # Shared snippets (ethos macro, mule-quality-checklist) sourced by SKILL.md files
├── workflows/                  # Deterministic Dynamic Workflow scripts + schemas
├── tools/                      # Standalone CLIs (lint-skills SKILL.md hygiene linter, mule-lint, mule-preflight)
├── presets/                    # Stack-shaped starter configs for .adlc/config.yml (mule-core, mule-anypoint)
└── .adlc/                      # Minimal self-tracking for toolkit-internal REQs
    ├── context/                # This directory — project-overview, architecture, conventions, mulesoft-rules, mule-skills-catalog
    └── specs/REQ-xxx-*/        # Requirement specs for toolkit changes
```

**Build-time MuleSoft skills are NOT vendored in this repo.** They are installed in each consumer project at `/init` time via `npx skills add mulesoft/mulesoft-dx/skills/mule-development`, which lays them down under the consumer's `.claude/skills/` directory. This is a deliberate departure from the SFDC fork's vendoring approach: the official MuleSoft pack is npm-distributed and updated upstream; vendoring would create drift risk.

## Skill anatomy

Every toolkit skill is a single markdown file at `<skill-name>/SKILL.md` with this shape:

1. **Frontmatter**: `name`, `description`, optional `argument-hint`
2. **Title + one-line framing** — what the skill does
3. **Ethos injection**: `!`cat .adlc/ETHOS.md ...` bash macro that inlines the six principles at invocation time (consumer-project path preferred, toolkit-root path as fallback)
4. **Context loading**: explicit `!bash` commands to read project-overview, architecture, conventions, mulesoft-rules, relevant knowledge
5. **Input**: how the skill reads `$ARGUMENTS`
6. **Prerequisites**: blocking checks (e.g., "verify `.adlc/context/project-overview.md` exists")
7. **Instructions**: numbered steps, often with sub-steps and explicit bash for deterministic operations (each ```sh fenced block may be an independent shell — a shared shell function must be re-sourced from a partial in the same block that calls it; see "Partials")
8. **Quality checklist**: post-run self-check items

Skills are pure markdown — no code, no package dependencies. Claude Code loads them at invocation time and executes the instructions in-context.

## Agent anatomy

Agents live in `agents/<agent-name>.md` and have frontmatter declaring:
- `name` — identifier used when dispatching
- `description` — tells the parent agent when to use this one
- `tools` — explicit allowlist (or `*` for general-purpose agents)
- `model` — required, must be one of `sonnet` or `opus`. Haiku and any third-party model are out of scope for this toolkit by policy. The single registry is `MODEL_ASSIGNMENTS.md`.

Agent bodies contain specialized instructions: role, focus areas, reporting format. The `/review` and `/proceed` skills dispatch the 6-member review panel in parallel (correctness-reviewer, quality-reviewer, architecture-reviewer, test-auditor, security-auditor, reflector).

## MuleSoft-aware reviewers (Phase 5 panel)

Each Phase 5 reviewer is dimension-shaped, not artifact-shaped. The reviewer loads the relevant **toolkit-authored Mule rubric** by file glob, and may also call **MCP tools** (DX MCP for build artifacts, Platform MCP for runtime/governance state) to verify findings against live state.

| Dimension | Rubric loaded by file glob | MCP tools available |
|---|---|---|
| correctness | mule-error-handling (XML), dataweave-quality (.dwl) | DX MCP `generate_munit_test`, `modify_munit_test` |
| quality | mule-flow-quality (XML), dataweave-quality (.dwl), munit-coverage (test XML) | DX MCP `get_platform_insights` |
| architecture | api-led-architecture, apikit-contract-conformance, mule-connector-config-hygiene, mule-deploy-hygiene | DX MCP `list_applications`, Platform MCP `view_api_version_details`, `list_apis` |
| test-coverage | munit-coverage | DX MCP `generate_munit_test` |
| security | mule-secrets-hygiene, governance-policies | Platform MCP `view_api_instance_policies`, `check_policy_conformance` |

The `task-implementer` (Phase 4) loads the same rubrics by glob plus `partials/mule-quality-checklist.md` so it generates rule-compliant code on the first pass. It also invokes the **official MuleSoft skills** via the Skill tool (e.g., `Skill(skill: "build-mule-integration")`) for scaffolding/generation — the toolkit's rubrics tell the implementer the QUALITY bar; the official skills tell it HOW to scaffold.

## Template anatomy

Templates at `templates/*.md` are the canonical shape for each artifact type:

- `requirement-template.md` — REQ specs (id, title, status, deployable, dates; Description, System Model, Business Rules, Acceptance Criteria, etc.)
- `task-template.md` — implementation tasks (id, title, req, status, dependencies)
- `bug-template.md` — bug reports (id, title, status, severity, dates; Description, Reproduction, Root Cause, Resolution)
- `lesson-template.md` — lessons learned (id, title, domain, component, tags, req, created)
- `assumption-template.md` — validated-assumption knowledge entries
- `policies-template.md` — Policies.md generated by /wrapup for every feature that touches API artifacts (API Manager policy assignments + governance compliance, per mulesoft-rules)
- `config-template.yml` — `.adlc/config.yml` skeleton with MuleSoft fields

Templates are copied into consumer projects by `/init` (into `.adlc/templates/`). Consumer projects may customize their local copies; `/template-drift` detects divergence from the canonical set.

## Partials

Partials at `partials/*.sh` and `partials/*.md` are shared snippets sourced by multiple SKILL.md files via Claude Code's `!`...`` macro syntax (executable partials) or POSIX `.` (sourceable function partials). Skills invoke a partial with a two-level fallback — `!`sh .adlc/partials/<name>.sh 2>/dev/null || sh ~/.claude/skills-mulesoft/partials/<name>.sh`` — so the pattern works whether or not `/init` has copied the partials into the consumer repo. The `/init` skill copies `partials/` into `.adlc/partials/` alongside `templates/`. Keep partials trivially auditable: one snippet per file, no aggregator (`lib.sh`) until there are more than five.

A sourceable partial is also the **only** sanctioned mechanism for sharing a shell *function* across steps, because SKILL.md fenced blocks do not share shell state across steps — each may be an independent shell invocation, so a function defined in one fenced block is undefined in another (the silent telemetry-loss class). A shared function must be re-sourced at *each* call site in the same fenced block as its invocation. This invariant is enforced structurally rather than by prose: the `tools/lint-skills` `cross-fence-fn` check flags any function defined in one fence but called from a different fenced block. See conventions.md "Bash in skills" for the call-site rule.

## ADLC pipeline shape (consumer-project view)

When a consumer project runs `/proceed REQ-xxx`, the pipeline phases are:

```
/validate (spec)
   ↓
/architect  ← creates .adlc/specs/REQ-xxx/tasks/TASK-yyy.md
   ↓
/validate (architecture + tasks)
   ↓
Implement (task-implementer agents per dependency tier; loads mule-quality-checklist + Mule rubric per artifact + invokes official MuleSoft skills via Skill tool)
   ↓
/verify (reflector + 5 reviewer agents in parallel; each reviewer loads relevant Mule rubric per touched file; reviewers may call DX/Platform MCP tools to verify against live state)
   ↓
/review findings fixed in single pass
   ↓
Create PR
   ↓
PR cleanup + CI (mvn verify + mvn munit:test as pre-merge gate; tools/mule-preflight)
   ↓
/wrapup (merge, artifact updates, knowledge capture, mvn deploy + DX MCP deploy_mule_application to staging/prod, Policies.md gate, API Manager policy promotion via Platform MCP when applicable)
```

Each phase has a validation gate. Failed validation loops up to 3 times before pausing for human input.

`proceed/SKILL.md` keeps Step 0, the Pipeline State Tracking gate protocol, and Phase 5 (Verify) inline, but extracts the thinner phases to companion files referenced via `<!-- companion: <path> -->` markers in SKILL.md:

- `proceed/phases-1-3-validation.md` — Phases 1–3 (spec validation, architect, architecture/tasks validation)
- `proceed/phase-4-implementation.md` — Phase 4 (implement)
- `proceed/phases-6-8-ship.md` — Phases 6–8 (PR creation, cleanup/CI, wrapup/merge)

The companion marker is documentation-only — Claude Code does not auto-load referenced files. SKILL.md's inline summary is sufficient to execute each extracted phase; the companion holds the full step list for maintainers and for in-depth reference.

## Workflow engine

Some orchestration is too dispatch-heavy for a single subagent (a subagent cannot nest further subagents). For those cases the toolkit ships **deterministic Dynamic Workflow scripts** under `workflows/` — a JS orchestration script plus the JSON-Schema literals it validates agent output against. Scripts are reached via the skills symlink (`~/.claude/skills-mulesoft/workflows/<name>.workflow.js`) and `/init` vendors them into a consumer's `.adlc/workflows/` alongside `templates/` and `partials/`. A skill resolves a script with the same **two-level fallback** used everywhere else — consumer copy first (`.adlc/workflows/<name>.workflow.js`), toolkit-symlink copy as fallback (`~/.claude/skills-mulesoft/workflows/<name>.workflow.js`) — so it works whether or not `/init` has run.

**Agents are leaves; the script is the orchestrator.** The Workflow primitive has no shell or filesystem of its own, so every git/gh/file/state operation runs *inside* an `agent()` call; the script owns only control flow (sequence, fan-out, loops, merge ordering). This is the model that dissolves the "a subagent can't dispatch subagents" constraint: the script dispatches the leaves and parallelizes the read/report phases that pay for fan-out while serializing the single writer.

**`/sprint` is a two-engine dispatcher.** It selects the **workflow** engine only when the `Workflow` tool is actually invocable in the session **and** the run opts in (`--workflow`); otherwise it uses the **legacy** background-runner engine with no behavior change.

**State has two layers.** The durable `pipeline-state.json` remains the cross-tool artifact that `/status` and the legacy engine read and that survives across sessions; the workflow **journal** is the in-run cache that powers `resumeFromRunId` (answer-a-halt-and-relaunch) within a single workflow run.

## MuleSoft stack assumptions

The toolkit assumes a MuleSoft Anypoint Platform development project. The consumer's `.adlc/config.yml` declares which parts of the Mule surface are in scope (Mule flows, DataWeave, MUnit always; API Manager governance, RTF deploy, Exchange publishing opt-in). Skill behavior conditions on those flags — e.g., the API Manager policy gate fires only when `governance.api_manager_enabled: true` is declared.

CLI: always `anypoint-cli-v4` (the modern Anypoint CLI), never the legacy `anypoint-cli`. Maven via `mule-maven-plugin` ≥ 4.x; Java 17 (LTS); Mule runtime 4.6.0+. Settings.json pre-approves routine `anypoint-cli-v4` and `mvn` invocations; production deploys (`mvn deploy -Pcloudhub-prod`, `anypoint-cli-v4 ... --environment Production`) and policy promotions are gated by ask-prompt.

**MCP integration.** Two MuleSoft MCP servers are wired by `/init`:
- **DX MCP** (`mulesoft-mcp-server` stdio): build/deploy operations — flow generation, MUnit test gen, app deploy, API spec implementation, Exchange asset publishing
- **Platform MCP** (`omni.mulesoft.com/mcp` via `mcp-remote`): runtime/governance — API instances, policy management, monitoring drill-down, Exchange semantic search, agent/MCP-server discovery, business-group/environment selection

Reviewer agents (security-auditor, architecture-reviewer) call Platform MCP tools to verify findings against live API Manager / governance state rather than relying solely on static XML inspection.

## Knowledge retrieval

Skills retrieve relevant prior knowledge at context-loading time via a **weighted-score retriever** over three corpora (lessons + specs + bugs), pooled globally to top-15. Used by `/spec`, `/review`, and others. See `spec/SKILL.md` Step 1.6 for the scoring rule.

## Key cross-cutting dependencies

- **Per-project ID allocator**: REQ / BUG / LESSON / ASSUME IDs are allocated per project, namespaced by `project.shortname` from `.adlc/config.yml` (e.g., `MUL-REQ-007`). The canonical implementation lives in `partials/id-counter.sh` and is sourced by `/spec` Step 2, `/bugfix` Phase 1 + lesson-capture, and `/wrapup` Step 4. Counters live at `.adlc/.next-{req,bug,lesson,assume}` per project. Each allocator:
  - hard-fails if `project.shortname` is missing or doesn't match `^[A-Z]{3}$`
  - holds a POSIX `mkdir`-based lock at `.adlc/.next-<kind>.lock.d` with a `[ -L ]` symlink pre-check (LESSON-014)
  - fails loud on missing/empty counter inside the lock (never silently resets to 1)
  - on first allocation, bootstraps from the highest existing `<XYZ>-<KIND>-NNN` AND legacy un-namespaced `<KIND>-NNN` artifact in the project — so re-running `/init` mid-project never resets to 1
  - relies on the caller to guard `[ -n "$ID" ]` after `$(allocate_*)` because `return 1` from the partial only exits the subshell (LESSON-015)
- The legacy machine-global counters (`~/.claude/.global-next-req`, `~/.claude/.global-next-bug`, `~/.claude/.global-next-lesson`) are no longer read or written. Existing files can be left in place.
- **Worktree isolation**: `/proceed` creates a git worktree per REQ at `.worktrees/REQ-xxx` so multiple pipelines run without collision. `/sprint` orchestrates parallel worktrees.
- **Symlink install**: changes committed to this repo are live immediately for every Claude Code session on the machine. No build, no deploy.
