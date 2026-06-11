---
name: spec
description: Write requirement specs from feature requests
argument-hint: Feature description or request
---

# /spec — Requirement Specification

You are writing a requirement spec following the spec-driven ADLC process.

## Ethos

!`sh .adlc/partials/ethos-include.sh 2>/dev/null || sh ~/.claude/skills-mulesoft/partials/ethos-include.sh`

## Context

- ADLC context: !`cat .adlc/context/project-overview.md 2>/dev/null || echo "No project overview found"`
- Requirement template: !`cat .adlc/templates/requirement-template.md 2>/dev/null || cat ~/.claude/skills-mulesoft/templates/requirement-template.md 2>/dev/null || echo "No requirement template found"`
- Taxonomy: !`cat .adlc/context/taxonomy.md 2>/dev/null || echo "No taxonomy found — consider running /init to scaffold one"`
- Sprint dashboard: !`sh ~/.claude/skills-mulesoft/tools/sprint-dashboard/launch.sh`

## Input

Feature request: $ARGUMENTS

## Prerequisites

Before proceeding, verify that `.adlc/context/project-overview.md` exists. If it doesn't, stop and tell the user: "The `.adlc/` structure hasn't been initialized. Run `/init` first to set up the project context."

## Instructions

### Step 1: Understand the Request
1. Read `.adlc/context/project-overview.md` for grounding context (skip if already in conversation)
2. Read `.adlc/context/architecture.md` for existing patterns (skip if already in conversation)
3. If the feature request is vague or ambiguous, ask clarifying questions before proceeding. Wait for answers.

### Step 1.5: Derive Query Tags for Retrieval

Before retrieval fires, derive a structured query from the feature request. This query drives both context loading (Step 1.6) and the self-tagging of the new REQ (Step 3).

1. Read the feature request in `$ARGUMENTS` alongside any grounding context already in conversation. Extract likely area signals:
   - **component** — which narrow area this touches (e.g., `API/auth`, `iOS/SwiftUI`, `adlc/spec`)
   - **domain** — broader problem domain (e.g., `auth`, `payments`, `ui`, `adlc`)
   - **stack** — tech layers implicated (e.g., `express`, `firestore`, `swiftui`, `markdown`)
   - **concerns** — cross-cutting dimensions (e.g., `security`, `perf`, `a11y`, `retrieval`)
   - **tags** — free-form keywords from the feature description (e.g., `password-reset`, `pagination`, `caching`)
2. Construct the query object:
   ```
   query = {
     component: "<proposed>",
     domain: "<proposed>",
     stack: [<proposed>],
     concerns: [<proposed>],
     tags: [<proposed>]
   }
   ```
3. **Interactive mode** (manual `/spec` invocation): surface the proposed query to the user and wait for confirmation or edits:
   ```
   Proposed retrieval query for this feature:
     component: <value>
     domain:    <value>
     stack:     [<values>]
     concerns:  [<values>]
     tags:      [<values>]
   Confirm or edit any field before retrieval fires.
   ```
4. **Non-interactive / pipeline mode** — detect this when ANY of:
   - `$ARGUMENTS` already contains explicit tag values (e.g., a caller passed `component: X` or `tags: [...]` in the prompt)
   - The invocation prompt explicitly says "invoked from /proceed" or "pipeline mode" or supplies an inherited query object
   - Running inside a subagent context that cannot receive further user input (e.g., dispatched via the Agent tool)

   In any of these cases: do NOT block for confirmation. Use caller-supplied tag values verbatim; for any unspecified dimension, use the proposed value from sub-step 2. Proceed directly to Step 1.6.
5. Retain the confirmed `query` object. It is reused by Step 1.6 (retrieval) and Step 3 (self-tagging the new REQ's frontmatter).

### Step 1.6: Unified Retrieval Across Corpora

Run a weighted-score retrieval over three corpora using the query from Step 1.5. This is the only retrieval behavior — the prior 3-tier lesson grep is removed.

1. **Enumerate candidate files** with three Grep passes (paths relative to project root):
   - `.adlc/knowledge/lessons/*.md` — no status filter, all lessons are candidates
   - `.adlc/specs/*/requirement.md` — include only where frontmatter `status` is `approved`, `in-progress`, or `deployed`
   - `.adlc/bugs/*.md` — include only where frontmatter `status` is `resolved`

   If any directory is empty or missing, skip it and continue (cold-start path).

2. **Read the frontmatter of every candidate** using Read with `limit: 30` (enough to cover full frontmatter block including any leading HTML comments, e.g., the lesson template's naming-convention comment). Parse these fields: `component`, `domain`, `stack`, `concerns`, `tags`, `updated`, `created`, `status`. If the frontmatter is malformed (missing `---` delimiters, unparseable YAML), skip that doc and continue — do not crash.

3. **Compute a weighted score per candidate** using the following rule:
   - `+3` if `doc.component == query.component`
   - `+2` if `doc.domain == query.domain`
   - `+2 × |doc.concerns ∩ query.concerns|`
   - `+1 × |doc.stack ∩ query.stack|`
   - `+1 × |doc.tags ∩ query.tags|`
   - `+1` foundational floor **only for lesson documents** with none of the five tag fields populated. Specs and bugs with zero tag overlap score `0`.

4. **Filter** out every doc with final score `0`.

5. **Sort** using a strict lexicographic key `(score DESC, effective_date DESC, corpus_priority ASC, id ASC)`:
   - `effective_date` per doc is the first non-empty value in this chain: `updated` → `created` → file mtime → epoch-minimum (if all are absent)
   - `corpus_priority` maps `lesson=0`, `bug=1`, `spec=2`
   - Interpretation: highest score first; among equal scores, newest `effective_date` wins; among equal scores **and** equal dates, corpus priority `lesson > bug > spec` applies; final tiebreak is alphabetical `id`
   - Missing dates never cause retrieval failures — they are treated as oldest and lose date tiebreaks

6. **Take the top 15 globally** across all corpora. There are no per-corpus quotas (no minimum-lesson floor, no maximum-bug cap). If fewer than 15 candidates survive filtering, take what is available.

7. **Body-read of top-15 docs** — read each surviving doc's full body directly with the Read tool. There is no delegation step; Claude reads the bodies itself.

8. **Surface the retrieval summary** to the user before authoring continues. This is always shown — there is no verbose flag gate:
   ```
   Retrieved context for this REQ:
     LESSON-034 (lesson, score 5): Silent failure remediation
     BUG-012    (bug,    score 5): Auth rate-limit bypass
     REQ-019    (spec,   score 3): Prior login redesign
     ... (etc.)
   ```

9. **Cold-start path**: if every corpus is empty, or all candidates filter out to zero, skip retrieval and record this explicitly when Step 3 writes the `## Retrieved Context` section. Proceed to authoring without retrieved bodies.

### Step 1.7: Exclude Anypoint Platform Operational Artifacts (never pipeline these)

Some Anypoint Platform artifacts are **operational config**, not code, and pipelining them is more expensive than provisioning them through the platform UI / ops runbook — secrets leak into committed properties files, OAuth client credentials need ops approval, encryption keys rotate on a different cadence, and a failed deploy on any of them blocks the whole feature for an hour while a human untangles it.

**These artifacts are NEVER child REQs and NEVER appear in `Files to Create/Modify`:**

- DX MCP / Platform MCP connected apps (client-credentials + Authorization Code) and their client_id/client_secret
- secure-properties encryption keys (the AES key itself; encrypted property *values* DO live in committed properties files)
- Anypoint Secrets Manager entries (the entries themselves; the placeholders that reference them DO live in code)
- API Manager API instance registrations created by hand in the UI (use Platform MCP `create_api_instance` from the deploy gate, not from a code REQ)
- Governance ruleset definitions hosted on Exchange (consume rulesets in code; create them via Anypoint Governance UI / ops repo)
- Exchange organization-level entitlements / private-Exchange membership grants
- CloudHub 2.0 region or VPC configuration; Runtime Fabric cluster provisioning
- Anypoint user / group / role assignments

**What to do instead** when the feature request implies any of the above (e.g., "call the Stripe API", "rotate the Salesforce client secret", "stand up a new Sandbox VPC"):

1. Do NOT spawn a child REQ for the operational artifact.
2. Add the artifact to the spec's `## Assumptions` section in the form: `<ArtifactType> '<Name>' is pre-provisioned in the target Anypoint org before deploy starts.` Be specific — name the connected app, the secrets-manager entry, the encryption-key alias, etc., so `/canary` can verify presence.
3. Add the artifact to `## External Dependencies` so the gate in `/canary` Step 2a can read it.
4. If the user's request is *exclusively* about operational artifacts (e.g., "create a connected app for the new Anypoint org"), tell the user: *"Anypoint connected apps, secrets-manager entries, encryption keys, and VPC / region configuration are intentionally excluded from the ADLC pipeline. Provision them via Anypoint Platform UI or your ops repo — it's a 2-minute click-through and avoids exposing secrets in committed code."* Do NOT allocate a REQ.

This rule overrides the general decomposition heuristic — even if the user explicitly asks for the operational artifact in a deployable form, refuse and route to ops.

### Step 1.8: Decompose Multi-Layer Requests

A single MuleSoft feature request often spans multiple layers — System API spec, Process API flow logic, MUnit tests, governance policy declaration, Exchange asset publication — and bundling them into one REQ inflates complexity tier, balloons the review panel, mixes API-led layers (which should ship independently), and forces every layer to ride the slowest one's gates. Decompose at the spec phase so each layer can be tested, reviewed, and shipped independently.

#### Step 1.8.1 — Detect layers

After Step 1.7 has stripped any environment-config references, classify the **remaining** scope against this MuleSoft-specific cleavage table:

| Layer | Signals in the request |
|---|---|
| `api-spec-system` | new System API contract (RAML/OAS) for systems-of-record |
| `api-spec-process` | new Process API contract orchestrating System APIs |
| `api-spec-experience` | new Experience API contract for end-user / consumer endpoints |
| `mule-flow` | new flow / sub-flow / batch job inside an existing app |
| `mule-app-greenfield` | new Mule app project (`pom.xml` + `src/main/mule/` from scratch or Exchange template) |
| `dataweave-module` | new shared `dw/Modules/*.dwl` (transformation logic, redaction utilities) |
| `connector-config` | new global config (`<http:request-config>`, `<db:config>`, `<salesforce:sfdc-config>`, etc.) |
| `munit-suite` | new MUnit suite covering an existing flow |
| `api-manager-policy` | API Manager policy declaration / promotion (client-id-enforcement, rate-limiting, JWT/OAuth2) |
| `governance-rule` | governance ruleset addition / modification |
| `exchange-asset` | reusable Mule asset published to Anypoint Exchange (connector, template, fragment) |
| `secure-properties` | new secure-properties config / encryption-key rotation |
| `deploy-config` | `pom.xml` profile changes (vCore, replicas, region, deploy-target) |
| `mcp-server` | Mule app exposing an MCP server (per `create_MCP_server`) |

Tag every layer the request implies. A layer that only exists to *use* an artifact from another layer (e.g., a Process API consuming a new System API) is a separate layer — that's the whole point of decomposing.

#### Step 1.8.2 — Decide whether to decompose

- **Single layer detected** → do NOT decompose. Continue to Step 2 with one REQ. Today's behavior.
- **Two or more layers detected** → propose a decomposition (Step 1.8.3). The exception below still applies.

**Configuration-only layers (`api-manager-policy`, `secure-properties`, `deploy-config`)** that ride alongside code layers should usually be **routed to Anypoint Platform UI / config repos, not pipelined as code REQs**. Policy applications take seconds via Platform MCP `apply_policy_to_instance`; secure-property rotations are operational; deploy-config tweaks may live in a separate ops repo. Prefer this routing unless the project explicitly tracks every change through the pipeline (e.g., regulated industries with full audit trails — common in banking / healthcare).

Treat these layers like the env-config artifacts in Step 1.7: capture them as a Platform hand-off note, not a child REQ:

> *API Manager `client-id-enforcement` policy on the new endpoint is excluded from the pipeline — apply via Platform MCP `apply_policy_to_instance` after deploy. Secure-property `salesforce.client_secret` rotation is operational — coordinate with the team's secrets-rotation runbook.*

When the user explicitly insists a config layer be pipelined (e.g., "I want the policy declaration in `Policies.md` for audit"), allocate it as a child REQ with `complexity: trivial` so it gets the cheapest phase shape.

#### Step 1.8.3 — Propose the decomposition

Build a child-REQ plan from the surviving (non-Anypoint-Platform-routed) layers. For each layer:

- **Title**: `<Layer purpose> <object/feature>` — e.g., `Orders System API spec`, `Orders Process API flow`, `Orders MUnit suite`.
- **Layer tag**: the layer key from Step 1.8.1 — recorded in the spec's `tags:` frontmatter.
- **Complexity (Step 2.5 preview)**: `trivial` for any pipelined config-only layer; `small` for a single flow + its MUnit suite, a single API spec + its APIkit binding, a single DataWeave module; `medium` if the layer introduces a new pattern (new connector config, new batch job, first integration with an upstream system); `large` only when the layer itself spans cross-API-tier work.
- **Dependencies**: order layers by what consumes what. Typical chains:
  - `api-spec-system` → `mule-flow` (System API impl) → `api-spec-process` → `mule-flow` (Process API impl) → `api-spec-experience` → `mule-flow` (Experience API impl)
  - `connector-config` → `mule-flow` (consumer) → `munit-suite` (test)
  - `dataweave-module` → `mule-flow` (consumer) → `munit-suite` (test with mocked DW)
  - `exchange-asset` (reusable connector / template) → consumer Mule app

Surface the plan to the user in **interactive mode** (manual `/spec` invocation):

```
Proposed decomposition for "<feature request>":

  <id-1>  <Title 1>            [<complexity>, <layer>]
  <id-2>  <Title 2>            [<complexity>, <layer>, depends: <id-1>]
  <id-3>  <Title 3>            [<complexity>, <layer>, depends: <id-2>]

Routed to Anypoint Platform (NOT pipelined — provision out-of-band):
  - DX MCP connected app 'X' with Code Builder + Runtime Manager scopes
  - Secure-property 'salesforce.client_secret' rotation in Anypoint Secrets Manager
  - API Manager `client-id-enforcement` policy applied via Platform MCP `apply_policy_to_instance` post-deploy

Confirm to allocate, edit titles/order, or reply 'collapse' to bundle into one REQ.
```

Wait for confirmation. Acceptable replies:
- `confirm` / silence-with-affirmation → proceed with the plan as shown.
- `collapse` → fall back to a single REQ; treat the original request as one unit. Note in `## Out of Scope` that the layers were considered and bundled deliberately.
- `edit <free text>` → apply the user's adjustments (rename, reorder, drop a child) and re-surface.

In **non-interactive / pipeline mode** (same detection rules as Step 1.5 sub-step 4 — caller-supplied tags, "invoked from /proceed" / "pipeline mode" hints, or subagent dispatch with no user channel): default to **collapse** (single REQ, today's behavior). Decomposition is a deliberate, user-confirmed choice; never silently fan a `/proceed` invocation into N REQs without the user opting in. The user can re-run `/spec` interactively if they want the plan.

#### Step 1.8.4 — Allocate the children

When the plan is confirmed:

1. Loop Step 2 (REQ-ID allocation) **once per child REQ** — each gets its own `<XYZ>-REQ-NNN` id from `allocate_req`.
2. For each child, execute Step 2.5 with the layer's pre-decided complexity (override only if Step 2.5's heuristic disagrees by more than one tier — then surface the disagreement).
3. Run Step 3 once per child to write `requirement.md`. Each child's frontmatter MUST include:
   - `dependencies: [<parent or sibling REQ ids>]` — the ordering edges from the plan.
   - A `## Decomposition Context` section directly after `## Description` listing the parent feature request, the sibling REQ ids, and which layer this child owns. This makes each child self-describing for retrieval and review.
4. Each child carries the **same** retrieval-context block from Step 1.6 — they share the parent feature's grounding.
5. Skip the standalone presentation in Step 4; instead, after all children are written, present the full set together and report the dependency graph (one line per child with its `depends:` chain). Tell the user the next move is `/sprint <id-1> <id-2> ...` (which will run them in parallel up to the dependency edges) or `/proceed <id-1>` (which will run a single child).

When the plan was **collapsed** to a single REQ, this step is a no-op — Steps 2 / 2.5 / 3 run once as today.

### Step 2: Determine the Next REQ ID

Allocation is **per-project, namespaced by `project.shortname` from `.adlc/config.yml`** — IDs look like `<XYZ>-REQ-NNN` (e.g., `SFC-REQ-007`). The counter lives at `.adlc/.next-req` inside the project. First allocation in a project bootstraps from the highest existing `<XYZ>-REQ-NNN` (and legacy `REQ-NNN`) found under `.adlc/specs/` so re-running `/init` mid-project never resets to 1.

1. Source the canonical allocator partial and request the next REQ id:
   ```bash
   . .adlc/partials/id-counter.sh 2>/dev/null || . ~/.claude/skills-mulesoft/partials/id-counter.sh
   REQ_ID=$(allocate_req)
   # `allocate_req` runs in $(...). `return 1` from the partial only exits the
   # subshell — guard the parent context (LESSON-015):
   [ -n "$REQ_ID" ] || { echo "ERROR: failed to allocate REQ id — aborting before writing malformed spec" >&2; exit 1; }
   # Extract the numeric suffix when you need REQ_NUM in templates / paths:
   REQ_NUM=${REQ_ID##*-}
   ```
2. The partial enforces:
   - `project.shortname` present in `.adlc/config.yml` and matching `^[A-Z]{3}$` — hard fail otherwise.
   - POSIX `mkdir`-based lock at `.adlc/.next-req.lock.d` with `[ -L ]` symlink pre-check (LESSON-014).
   - Empty/missing counter inside the lock fails loud (never silently resets).
   - First-run bootstrap scans `.adlc/specs/` for the highest existing id (matches BOTH `<XYZ>-REQ-NNN` and legacy `REQ-NNN`) and seeds the counter at `high-water + 1`. Result: `/init` after specs already exist resumes numbering, never restarts at 1.
3. `mkdir` is atomic on all POSIX filesystems — if another process holds the lock the retry loop waits up to ~5 seconds. Concurrent `/sprint` allocations get distinct IDs.
4. **Migrating from the legacy global counter**: the old `~/.claude/.global-next-req` is no longer read or written. New IDs are project-scoped via the shortname; existing un-namespaced specs (`REQ-475-foo`) keep their names — the bootstrap reads them so the next id picks up above their high-water mark.

### Step 2.5: Pick the complexity tier (REQ-C)

Before writing the spec, classify the work into one of `trivial | small | medium | large`. This drives `/proceed`'s phase shape — the wrong tier either wastes hours of orchestration or skips genuinely-needed gates.

Apply this heuristic to the user's feature description plus any retrieval signal:

| Tier | Pick when |
|---|---|
| `trivial` | Single-file config change (property value, doc:description tweak, pom.xml dependency bump, governance ruleset addition). No flow / DW / MUnit logic change. No architectural decision. Author is confident from the description alone. |
| `small` | ≤3 files. No new pattern introduced. Existing connector config / existing flow / existing API spec. 1 sub-flow + 1 MUnit suite; or 1 DW module; or 1 API endpoint addition. |
| `medium` | 4-10 files OR introduces a new pattern (new connector config, new batch job, first-time integration with an upstream system, new API instance registration in API Manager). |
| `large` | >10 files OR cross-API-tier (System API + Process API + Experience API in one feature, multi-repo, new Exchange asset published, new MCP server exposed by Mule). Always includes an ADR. |

Set `complexity:` in the spec's frontmatter. When in doubt, pick the **higher** tier — over-classifying costs minutes of orchestration; under-classifying can ship bad code.

In **interactive mode**, surface the proposed tier and let the user override. In **non-interactive / pipeline mode** (caller passed an explicit value, or running inside a subagent), accept the caller's value verbatim; if absent, use `small` as the safe default.

### Step 3: Create the Requirement Spec

**Loop note (decomposition)**: when Step 1.8 proposed a multi-REQ decomposition that the user confirmed, run all of Step 3 **once per child REQ** — each child gets its own directory, frontmatter, and body. Children share the retrieval context from Step 1.6 but carry their own layer-specific tags, dependencies, and complexity tier. When Step 1.8 collapsed (or did not trigger), Step 3 runs exactly once.

1. Create directory: `.adlc/specs/<REQ_ID>-feature-slug/` where `<REQ_ID>` is the value returned by `allocate_req` in Step 2 (e.g., `.adlc/specs/MUL-REQ-007-add-orders-process-api/`). The directory name MUST start with the full namespaced id, including the shortname prefix.
2. Create `requirement.md` using the template from `.adlc/templates/requirement-template.md`
3. Fill in all sections:
   - **Frontmatter**: id, title, status (`draft`), `deployable` (carry the template default unless the feature is explicitly non-deployable — e.g., docs-only), `complexity` (from Step 2.5), `dependencies` (sibling/parent REQ ids when this REQ was allocated as a child in Step 1.8.4 — empty list otherwise), created date, updated date, AND the five query tags from Step 1.5 — `component`, `domain`, `stack`, `concerns`, `tags` (the layer key from Step 1.8.1 is appended to `tags` for decomposed children, e.g., `mule-flow`, `api-spec-system`, `dataweave-module`, `munit-suite`). This self-tagging makes the new REQ retrievable for future `/spec` invocations.
   - **Description**: What the feature does and why — be specific and grounded in the project context
   - **System Model**: Structured data model — Entities (fields, types, constraints), Events (triggers, payloads), Permissions (actions, roles). Remove sub-sections that don't apply to this feature.
   - **Business Rules**: Explicit, testable constraints governing behavior (e.g., "Only authenticated callers with role=order-admin may POST /orders"). Numbered BR-1, BR-2, etc.
   - **Acceptance Criteria**: Concrete, testable criteria as checkboxes
   - **External Dependencies**: Any new APIs, services, or libraries needed. If the feature talks to an external system, list the connected-app / secure-property entry / API Manager policy template / Exchange asset that brokers it — these are excluded from the pipeline per Step 1.7 and must already be provisioned in the target Anypoint org.
   - **Assumptions**: Things assumed to be true that could affect the design. If Step 1.7 routed any operational artifact here, the assumption MUST follow the form: `<ArtifactType> '<Name>' is pre-provisioned in the target Anypoint org before deploy starts.`
   - **Open Questions**: Questions that need answers before implementation
   - **Out of Scope**: Items explicitly excluded to prevent scope creep
   - **Retrieved Context** (NEW, always present): append a `## Retrieved Context` section at the end of the spec listing every retrieved source from the retrieval summary produced in Step 1.6 in the form `ID (corpus, score): title`. If no context was retrieved (cold-start path — either the corpus is empty or no documents scored above zero), write exactly: `No prior context retrieved — no tagged documents matched this area.`
4. **Inline citations**: when a retrieved doc directly informed a Business Rule, Assumption, or Acceptance Criterion, add an inline citation in the form `(informed by BUG-012)` or `(informed by REQ-019, LESSON-034)` at the end of that line. Citations are required when the retrieved doc is load-bearing for the rule; optional when the doc was background reading only.

### Step 4: Present for Review
1. Display the full requirement spec to the user. When Step 1.8 produced multiple children, display each child briefly and then a **dependency graph summary** of the form `<id-1> → <id-2> → <id-3>` (chains) or a small DAG when fan-out exists.
2. Highlight any assumptions or open questions that need input.
3. Remind the user of next moves:
   - Single REQ: run `/validate` then `/architect`.
   - Decomposed (multiple children): run `/validate <id>` per child, then `/sprint <id-1> <id-2> ...` to run them in parallel respecting `dependencies:`, or `/proceed <id-1>` to run one at a time. Anypoint-Platform-routed operational items (connected-app provisioning, API Manager policy applications, secure-property rotations from Step 1.8.2 / 1.7) need the user to action them in Anypoint Platform (UI or Platform MCP) once their producer REQ deploys — call those out explicitly here so they aren't forgotten.

## Quality Checklist
- [ ] Acceptance criteria are specific and testable (not vague)
- [ ] Description explains the "why" not just the "what"
- [ ] Assumptions are explicitly stated
- [ ] Out of scope items prevent scope creep
- [ ] No implementation details leaked into the requirement (that's for architecture phase)
- [ ] Retrieved Context section present
- [ ] No DX/Platform MCP connected app, secure-properties encryption key, Anypoint Secrets Manager entry, Exchange entitlement, or CloudHub region/VPC config appears as a deliverable — each is captured as a pre-deploy assumption per Step 1.7
- [ ] If the request spans ≥2 layers from Step 1.8.1, a decomposition was proposed and either confirmed (children allocated with `dependencies:`) or explicitly collapsed by the user
- [ ] Configuration-only layers (`api-manager-policy`, `secure-properties`, `deploy-config`) are routed to Anypoint Platform UI / ops repos unless the user opted to pipeline them — and when pipelined, they sit at `complexity: trivial`
- [ ] Each decomposed child has its layer key recorded in `tags:` and a `## Decomposition Context` section linking parent and siblings
