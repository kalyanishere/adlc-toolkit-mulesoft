---
name: architect
description: Design architecture and break requirement into tasks
argument-hint: REQ-xxx ID or requirement description
---

# /architect — Architecture & Task Breakdown

You are designing architecture and breaking a requirement into implementable tasks.

## Ethos

!`sh .adlc/partials/ethos-include.sh 2>/dev/null || sh ~/.claude/skills-mulesoft/partials/ethos-include.sh`

## Context

- Task template: !`cat .adlc/templates/task-template.md 2>/dev/null || cat ~/.claude/skills-mulesoft/templates/task-template.md 2>/dev/null || echo "No task template found"`
- Active specs: !`grep -rl 'status: draft\|status: approved\|status: in-progress' .adlc/specs/*/requirement.md 2>/dev/null | head -20 || echo "No active specs"`

**Context files loaded on demand**: `.adlc/context/architecture.md` and `.adlc/context/conventions.md` are loaded by Step 1 below — **skip the Read if they are already in the current conversation** (e.g., when invoked from `/proceed`, which preloads them at Phase 0).

## Input

Requirement: $ARGUMENTS

## Prerequisites

Before proceeding, verify that `.adlc/context/architecture.md` and `.adlc/context/conventions.md` exist. If either is missing, stop and tell the user: "The `.adlc/` structure hasn't been fully initialized. Run `/init` first to set up the project context."

## Instructions

### Step 1: Locate and Read the Requirement
1. If given a REQ ID, read `.adlc/specs/REQ-xxx-*/requirement.md`
2. If given a description, search `.adlc/specs/` for the matching requirement
3. Verify the requirement status is `draft` or `approved` (not already `complete`)
4. **Context files**: if `.adlc/context/architecture.md` and `.adlc/context/conventions.md` are NOT already in your conversation context (e.g., this skill is being run standalone, not from `/proceed`), Read them now. Otherwise skip — they're already loaded.
5. Check `.adlc/knowledge/assumptions/` for prior decisions that may affect design
6. **Lessons — grep first, then read only matches**: use the Grep tool on `.adlc/knowledge/lessons/` with patterns like `component:.*<affected-area>` or `domain:.*<domain>` to identify matching files. Then Read ONLY those matched files. Do NOT read all lessons. Note applicable lessons in your architecture rationale so past mistakes aren't repeated and proven patterns are reused.

### Step 2: Explore the Codebase
1. Launch 3 formal exploration agents in parallel using the Agent tool. Each agent is defined in `~/.claude/agents/` with model selection (haiku for fast exploration) and read-only tool restrictions.

   - **feature-tracer** agent — provide the requirement description and key terms to search for similar existing implementations
   - **architecture-mapper** agent — provide the requirement and current architecture.md to map all files and layers that will be affected
   - **integration-explorer** agent — provide the affected areas to identify extension points, tests, and integration surfaces

2. Read the key files identified by agents

### Step 2.5: Load orchestrator MuleSoft skills that shape the architecture

`/architect` cannot reason about Mule-specific scaffolding from first principles — the official MuleSoft skill pack (installed at consumer init via `npx skills add mulesoft/mulesoft-dx/skills/mule-development`) plus the toolkit's review rubrics under `skills/mule/` define the canonical scaffolding commands, file shape, and rubric quality bar. If the architect ignores those skills and writes tasks like "create `pom.xml` and `src/main/mule/orders.xml` by hand" when `create-project-template` and `build-mule-integration` exist, the deploy will fail or the artifact will fail review. Load orchestrator skills BEFORE producing any task.

1. **Read the spec frontmatter and `.adlc/config.yml`** — extract `mulesoft.features`, `mulesoft.governance`, `mulesoft.api_layer`, `mulesoft.deploy_target`, the spec's `stack:` and `tags:`, and any keyword signals in the spec body (Description, External Dependencies, Acceptance Criteria).

2. **Match signals to orchestrator skills** using this dispatch table. A signal MUST trigger a load — first-principles reasoning about a layer when its skill exists is a protocol violation:

   | Signal | Orchestrator skill(s) to invoke via the Skill tool |
   |---|---|
   | Greenfield project / new Mule app in scope | `create-project-template` (official) — scaffold from Exchange template or scratch |
   | New flow / sub-flow / component in scope | `build-mule-integration` (official) |
   | Spec mentions "secure properties" / "encryption" / "secret" / "credential" | `secure-mule-app` (official) |
   | Spec mentions "doc:description" / "documentation update" on flow XML | `generate-doc-description` (official) |
   | New API spec (RAML or OAS) in scope | DX MCP `generate_api_spec` (or `implement_api_spec` when binding flows to an existing spec) |
   | New MUnit suite in scope | DX MCP `generate_munit_test`; for modifications use `modify_munit_test` |
   | Spec mentions "MCP server" / "Model Context Protocol server" exposed by Mule | DX MCP `create_MCP_server` |
   | Spec mentions "API Manager policy" / "client-id-enforcement" / "rate-limiting" / "JWT" / "OAuth 2.0 validation" | DX MCP `manage_api_instance_policy` + Platform MCP `apply_policy_to_instance` (deploy time) |
   | `mulesoft.governance.api_manager_enabled: true` AND spec adds a public-facing API | `governance-policies` rubric (review-time, but architect must populate Policies.md scaffold per `templates/policies-template.md`) |
   | Spec mentions "Exchange asset" / "publish to Exchange" / "reusable connector" | DX MCP `create_and_manage_assets`; verify with Platform MCP `search_global_assets` |
   | Spec mentions "deploy to CloudHub" / "deploy to RTF" / "Runtime Fabric" | DX MCP `deploy_mule_application` / `update_mule_application` |
   | Spec mentions "DataWeave module" / "shared transformation" / "PII redaction" | `dataweave-quality` rubric (load at task time via `required_skills`) |
   | Spec mentions "API-led architecture" / "system / process / experience layer" | `api-led-architecture` rubric (architecture-shaping; reviewer-time guard) |
   | Spec mentions "batch job" / "scatter-gather" / "scheduler" | `mule-flow-quality`, `mule-error-handling` rubrics |

   Multiple matches → load all. Always cross-reference the catalog at `.adlc/context/mule-skills-catalog.md` (Phase mapping section) for any artifact type the spec implies; if a match is missing from the table above, prefer loading from the catalog over skipping.

3. **Invoke each matched orchestrator skill via the Skill tool** in this Step 2.5 — not at task time, not in Phase 4. The orchestrator's instructions tell you the canonical scaffolding command (e.g., for `build-mule-integration`: the validated steps to add a flow / sub-flow), the file shape the platform expects (`pom.xml`, `mule-artifact.json`, `src/main/mule/`, `src/test/munit/`), and the deploy quirks. The architecture you produce in Step 3 and the tasks you produce in Step 4 MUST reflect those instructions verbatim.

4. **Record the loaded orchestrators** in the architecture rationale so the lineage is auditable: a one-line `Orchestrator skills loaded: <comma-separated list>` block at the top of `architecture.md` (when one is created), or in the architecture summary surfaced at Phase 6 when no architecture.md is needed.

5. **If no signal matches** any row in the table AND the catalog yields nothing, record `Orchestrator skills loaded: none — change is generic Mule flow refactor and uses only the per-file rubrics at task time.` Do NOT silently skip.

### Step 3: Design Architecture (if needed)
1. If the requirement involves new architectural decisions, create `.adlc/specs/REQ-xxx-*/architecture.md`
2. Document:
   - **Approach**: High-level design and rationale
   - **API contract changes**: New or modified RAML/OAS endpoints, request/response schemas, traits
   - **Flow layout**: New or modified flows, sub-flows, batch jobs, schedulers
   - **DataWeave module additions**: shared `dw/Modules/*.dwl` files
   - **Connector configurations**: new global configs, reconnection strategies, pooling changes
   - **Properties / secrets**: new property keys, secure-properties additions
   - **Deploy / governance**: pom.xml profile changes, vCore / replica sizing, API Manager policy additions
   - **Cross-API dependencies**: which System APIs this Process API consumes, or which Process APIs this Experience API consumes
   - **Key decisions**: ADRs with rationale (follow the style in `.adlc/context/architecture.md`)
3. Propose any additions to `.adlc/context/architecture.md` with rationale

### Step 4: Break Into Tasks
1. Create `.adlc/specs/REQ-xxx-*/tasks/` directory
2. Determine the next TASK ID by checking existing tasks across ALL specs (not just this one)
3. **Detect repository mode**: check whether `.adlc/config.yml` exists in the primary repo and declares a `repos:` block with more than one entry.
   - **Single-repo mode** (no config or single entry): set `repo:` on each task to the primary repo id (or omit — `/proceed` will backfill). Files listed under "Files to Create/Modify" all live in the primary repo.
   - **Cross-repo mode** (config has siblings): **every task MUST declare a `repo:` field** naming one of the ids under `repos:`. Group files by repo — a single task should not modify files in multiple repos. If a piece of work spans repos (e.g., an API contract change requires matching backend and frontend edits), split it into at least two tasks with an explicit dependency between them.
4. Create `TASK-xxx-description.md` for each task using the template from `.adlc/templates/task-template.md`
5. Each task must specify:
   - **Frontmatter**: id, title, status (`draft`), parent REQ, created/updated dates, dependencies, `required_skills` (see below), `repo:` (required in cross-repo mode)
   - **`required_skills:` (mandatory population)** — for each task, intersect the orchestrator skills loaded in Step 2.5 with the layer this task implements, AND walk the task's `Files to Create/Modify` list against `.adlc/context/mule-skills-catalog.md`'s **File-glob → rubric dispatch** table. Put the resulting union into the task's `required_skills:` frontmatter array. Examples:
     - A task that scaffolds a new Mule app MUST list `[create-project-template]` so the implementer is forced to use the official scaffolding skill instead of hand-rolling `pom.xml` + `src/main/mule/`. Hand-rolling is a protocol violation that the review panel will flag — populating `required_skills` correctly prevents it from happening in the first place.
     - A task that adds a new flow / sub-flow lists `[build-mule-integration]` (official orchestrator) plus the relevant rubrics (`mule-flow-quality`, `mule-error-handling`).
     - A task that adds DataWeave logic lists `[build-mule-integration]` plus `[dataweave-quality]` rubric.
     - A task that adds a new MUnit suite lists `[generate_munit_test]` (DX MCP) plus `[munit-coverage]` rubric.
     - A task that adds a new API spec lists `[generate_api_spec, implement_api_spec]` (DX MCP) plus `[apikit-contract-conformance, api-led-architecture]` rubrics.
     - A task that adds secure-properties lists `[secure-mule-app]` (official) plus `[mule-secrets-hygiene]` rubric.
     - A task that updates `pom.xml` deploy config lists `[mule-deploy-hygiene]` rubric only.
     - A task that adds an API Manager policy declaration lists `[manage_api_instance_policy, apply_policy_to_instance]` (DX MCP / Platform MCP) plus `[governance-policies]` rubric.
   - **Description**: What this task accomplishes
   - **Files to Create/Modify**: Specific file paths with descriptions of changes — all paths must live in the task's target repo
   - **Acceptance Criteria**: Concrete, testable criteria
   - **Technical Notes**: Implementation details, patterns to follow, edge cases. When `required_skills` includes an orchestrator (e.g., `building-ui-bundle-app`), reference its canonical scaffolding command verbatim here so the implementer does not improvise. In cross-repo mode, call out any cross-repo contracts this task establishes or consumes.
   - **Dependencies**: Other tasks that must complete first — dependencies may cross repos (a frontend task can depend on a backend task)
6. Tasks must form a valid dependency graph (no cycles), even when spanning repos
7. Order tasks so foundational work comes first (data layer → service → routes → UI). In cross-repo mode, backend/API tasks typically precede their frontend consumers.
8. **MUnit test obligation** — every task that adds or modifies a Mule flow MUST list a corresponding MUnit suite under `src/test/munit/<flow-name>-test-suite.xml` in **Files to Create/Modify** and include an acceptance criterion of the form "MUnit suite `<flow-name>-test-suite.xml` passes with all external connectors mocked, coverage ≥ project floor". Mocks must cover happy and error paths. If `.adlc/config.yml` does not declare `munit_specs:`, note in Technical Notes that the project's MUnit convention is missing; otherwise reference the configured directory. **Playwright** spec obligation only applies when an Experience API renders HTML AND `playwright_specs:` is declared in `.adlc/config.yml` (rare for Mule).

### Step 5: Update Requirement Status
1. Update the requirement's frontmatter status from `draft` to `approved`
2. Update the `updated` date

### Step 6: Present for Review
1. Display the architecture decisions (if any)
2. Display the task breakdown as a dependency graph
3. Summarize the implementation plan
4. Remind the user to run `/validate` before starting implementation

## Quality Checklist
- [ ] Architecture follows existing patterns (layered: routes → services → repositories)
- [ ] Tasks are small enough to implement in a single session
- [ ] Task dependencies form a valid DAG (no cycles), including cross-repo edges
- [ ] Every file to be modified is listed in at least one task
- [ ] Tests are included in task acceptance criteria
- [ ] Every flow-touching task lists an MUnit suite in Files to Create/Modify and an acceptance criterion that runs it; coverage threshold from `mulesoft.coverage.munit_floor`
- [ ] No task has more than 3 dependencies
- [ ] In cross-repo mode: every task has a `repo:` field naming a valid repo id from `.adlc/config.yml`, and all files in that task live in that repo
- [ ] Step 2.5 ran — orchestrator skills loaded and recorded; OR explicitly recorded as "none" with justification
- [ ] Every task that touches Mule artifacts (`src/main/mule/**`, `src/main/resources/api/**`, `src/test/munit/**`, `pom.xml`, `mule-artifact.json`, `*.dwl`, `*.properties`) has a non-empty `required_skills:` array. Tasks that scaffold a new Mule app MUST include `create-project-template`; tasks that add flows/sub-flows MUST include `build-mule-integration` — hand-rolling these artifacts is a protocol violation
