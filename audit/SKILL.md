---
name: audit
description: Whole-repo MuleSoft audit. Scores the existing codebase against mulesoft-rules.md, the 10 Mule review rubrics, governance scan, MUnit coverage, and secrets hygiene — independent of any open diff. Distinct from /review (diff-scoped pre-push gate) and /canary (deploy gate). Use when the user says "audit this repo", "check overall quality", "score the codebase", "find tech debt", "what's our governance posture", or wants a full health report before a customer demo / handoff / promotion.
argument-hint: Optional scope — "flows" | "tests" | "governance" | "secrets" | "all" (default), OR a path glob to scope the audit (e.g., "src/main/mule/orders/**")
---

# /audit — Whole-Repo MuleSoft Codebase Audit

You are auditing an *existing* MuleSoft codebase against the project's rules, rubrics, and governance posture. This is a **point-in-time health check**, not a pre-merge gate. Output is a prioritized findings report — no fixes are applied.

`/audit` is the third member of the review trio. Use the right tool for the job:

| Skill | Scope | When |
|---|---|---|
| `/review` | The current diff vs `main` | Pre-push gate, after implementing a change |
| `/canary` | A merged deployable | Deploy gate, before Sandbox push |
| `/audit` | The **whole repo** (or a specified subset) | Periodic health check, customer demo prep, hand-off, debt triage |

## Ethos

!`sh .adlc/partials/ethos-include.sh 2>/dev/null || sh ~/.claude/skills-mulesoft/partials/ethos-include.sh`

## Context

- Current directory: !`pwd`
- Current branch: !`git branch --show-current 2>/dev/null || echo "Not a git repo"`
- Project root pom.xml: !`test -f pom.xml && head -5 pom.xml | grep -E '<artifactId>|<version>' || echo "No pom.xml at repo root"`
- Mule sources: !`find src/main/mule -type f -name '*.xml' 2>/dev/null | wc -l | tr -d ' ' | xargs -I {} echo "{} Mule XML files"`
- MUnit suites: !`find src/test/munit -type f -name '*.xml' 2>/dev/null | wc -l | tr -d ' ' | xargs -I {} echo "{} MUnit suites"`
- DataWeave modules: !`find dw -type f -name '*.dwl' 2>/dev/null | wc -l | tr -d ' ' | xargs -I {} echo "{} DW modules"`
- API specs: !`find src/main/resources/api -type f \( -name '*.raml' -o -name '*.yaml' -o -name '*.yml' -o -name '*.json' \) 2>/dev/null | wc -l | tr -d ' ' | xargs -I {} echo "{} API specs"`
- Coverage policy: !`grep -E "^[[:space:]]*(mode|munit_floor|flow_floor|diff_only):" .adlc/config.yml 2>/dev/null | sed 's/^/  /' || echo "  (no .adlc/config.yml — defaults will apply)"`
- Governance config: !`grep -E "^[[:space:]]*(api_manager_enabled|governance_ruleset|required_policies):" .adlc/config.yml 2>/dev/null | sed 's/^/  /' || echo "  (no governance block configured)"`
- MuleSoft rules: !`cat .adlc/context/mulesoft-rules.md 2>/dev/null || cat ~/.claude/skills-mulesoft/.adlc/context/mulesoft-rules.md 2>/dev/null || echo "No mulesoft-rules.md found — /init not run?"`

## Input

Scope: $ARGUMENTS

Resolution rules:
- No argument or `all` → audit every dimension across the whole repo.
- `flows` | `tests` | `governance` | `secrets` | `coverage` | `dataweave` | `policies` | `deploy` → audit only that dimension (still whole-repo).
- Anything that looks like a path or glob (`src/main/mule/orders/**`, `experience-api/`) → audit every dimension but scoped to files matching the glob. Tell the user up front which files matched.

If the argument is none of the above and is not an obvious path, ask the user to clarify before doing any work.

## Prerequisites

Before proceeding, verify:
1. `.adlc/context/mulesoft-rules.md` exists. If not, stop and tell the user: "Run `/init` first — `/audit` reads `mulesoft-rules.md` to know what to score against."
2. `.adlc/config.yml` exists. If not, stop and tell the user the same.
3. Either `pom.xml` (Mule app repo) or at least one `src/main/mule/**/*.xml` is present. If neither, the working directory isn't a Mule project — stop with a clear message.

`/audit` is read-only by design. It runs `mvn validate compile` (no deploy, no tests written, no policies promoted) and the read-only `anypoint-cli-v4 governance:validate` CLI. It must NOT call DX MCP `deploy_mule_application`, Platform MCP `apply_policy_to_instance`, or any other state-mutating tool.

## Instructions

### Step 1: Resolve scope and inventory the codebase

Establish what's being audited so the report can show before/after-this-audit context:

```sh
# Counts to surface in the executive summary
FLOW_COUNT=$(find src/main/mule -type f -name '*.xml' 2>/dev/null | wc -l | tr -d ' ')
SUITE_COUNT=$(find src/test/munit -type f -name '*.xml' 2>/dev/null | wc -l | tr -d ' ')
DW_COUNT=$(find dw -type f -name '*.dwl' 2>/dev/null | wc -l | tr -d ' ')
SPEC_COUNT=$(find src/main/resources/api -type f \( -name '*.raml' -o -name '*.yaml' -o -name '*.json' \) 2>/dev/null | wc -l | tr -d ' ')
PROPS_COUNT=$(find src/main/resources -type f -name '*.properties' 2>/dev/null | wc -l | tr -d ' ')
```

Also inventory:
- API layer per app (`mulesoft.api_layer` from `.adlc/config.yml`).
- Connectors in use (grep `<\(http\|db\|salesforce\|jms\|amqp\|kafka\|sftp\|file\)`-prefixed elements across `src/main/mule/**/*.xml`).
- Apps included if this is a multi-app monorepo (separate `pom.xml` under each app dir).

### Step 2: Run the read-only sweep tools

These are the same tools `/canary` runs, but `/audit` runs them with a **report-only flag** (no exit-on-first-failure). Each emits its findings as JSON or structured text the audit can ingest.

```sh
# Lint sweep — no early exit; collect every finding.
sh tools/mule-lint/check.sh --report all

# Coverage report — emit numbers per flow / per app, but don't gate.
sh tools/mule-coverage/check.sh --report

# Governance scan, when configured.
if grep -qE '^\s*governance_ruleset:\s*\S' .adlc/config.yml; then
  sh tools/mule-preflight/check.sh governance
fi

# Policy declarations vs API Manager live state, when api_manager_enabled.
if grep -qE '^\s*api_manager_enabled:\s*true' .adlc/config.yml; then
  sh tools/mule-preflight/check.sh policies
fi
```

If any tool is missing (project never installed `tools/` or symlink is broken), record that as a Critical finding under the toolchain dimension and proceed with what you have.

### Step 3: Launch audit agents in parallel

Launch **6 agents in parallel** using the Agent tool. Each agent reads the rubric for its dimension from `skills/mule/<rubric>/SKILL.md`, scores the in-scope files, and reports findings *with file paths and line numbers*. None of them apply fixes.

Pass these inline (REQ-E inline-context rule, same as `/review`): `mulesoft-rules.md` content, `mulesoft.coverage` block, `mulesoft.governance` block, the inventory from Step 1, and the tool sweep results from Step 2.

1. **architecture-reviewer** — scope: API-led layering (`api-led-architecture`), APIkit contract conformance (`apikit-contract-conformance`), connector config hygiene (`mule-connector-config-hygiene`). Score against `architecture.md` if present. Flag layer violations (Experience calling System directly, Process API doing what an Experience should), missing APIkit binding, inline connector configs, missing reconnection strategies, missing pooling.
2. **correctness-reviewer** — scope: flow quality (`mule-flow-quality`), error handling (`mule-error-handling`), DataWeave (`dataweave-quality`). Flag missing `<error-handler>`, empty handlers, MEL expressions (deprecated), DW 1.0 syntax, missing `output` directives, `<flow-ref>` recursion, `Thread.sleep` in production code.
3. **security-auditor** — scope: secrets hygiene (`mule-secrets-hygiene`), governance/policies (`governance-policies`). Flag hardcoded credentials/URLs/IDs, plaintext secrets, missing secure-properties, prod Basic Auth, missing client-id-enforcement, missing rate-limiting, drift between `Policies.md` and live API Manager state (Platform MCP `view_api_instance_policies`).
4. **test-auditor** — scope: MUnit coverage (`munit-coverage`). Apply the three-tier coverage policy from `mulesoft.coverage`: app-level floor, per-flow floor in brownfield, diff-only mode. Flag flows without a suite, suites missing mock-when for external connectors, missing error-path mocks, `Thread.sleep` in tests, suites with no assertions.
5. **quality-reviewer** — scope: naming, doc:description completeness, deploy hygiene (`mule-deploy-hygiene`). Flag flow1/flow2/`mule-flow-1` style names, missing `doc:description` on flows/sub-flows, missing vCore/replica config in `pom.xml` `<cloudhub2Deployment>`, JDK <17, mule-runtime <4.6.0, missing `mule-artifact.json`.
6. **integration-explorer** — scope: connector inventory and external surface. List every external system the codebase talks to (HTTP endpoints, DBs, queues, Salesforce orgs, SaaS APIs), the config that fronts each, and whether each upstream has timeout / retry / pooling / reconnection declared. Cross-reference with API Manager registrations (Platform MCP `list_apis`) when api_manager_enabled.

Each agent returns structured findings with severity (`Critical | Major | Minor | Nit`), file path, line number, rubric reference, and a one-line "why this matters" — *no recommended fix code*. (Audit's job is to find; `/proceed` or `/bugfix` apply fixes downstream.)

**Hard rule**: No agent applies edits. If any agent attempts to write or call a state-mutating MCP tool, treat that as a tooling bug and surface it.

### Step 4: Score against rubric weights

For each dimension, compute a 0-100 score:
- Critical findings cost 10 points each (cap at 50).
- Major findings cost 4 points each (cap at 30).
- Minor findings cost 1 point each (cap at 15).
- Nits don't subtract from score; surfaced for awareness only.
- Floor at 0.

Weight the dimensions per the project's emphasis (defaults shown — read overrides from `.adlc/config.yml` `audit.weights` if present):

| Dimension | Default weight | Rubric source |
|---|---|---|
| Architecture | 0.20 | `api-led-architecture`, `apikit-contract-conformance`, `mule-connector-config-hygiene` |
| Correctness  | 0.20 | `mule-flow-quality`, `mule-error-handling`, `dataweave-quality` |
| Security     | 0.20 | `mule-secrets-hygiene`, `governance-policies` |
| Tests        | 0.15 | `munit-coverage` |
| Quality      | 0.15 | naming, doc:description, `mule-deploy-hygiene` |
| Integration  | 0.10 | connector inventory, upstream contract drift |

Roll up to a single **Codebase Health Score (0-100)**. Emit it prominently — it's the headline a stakeholder will quote.

### Step 5: Build the report

The report has six sections, in this order:

#### 1. Executive summary
- Codebase Health Score (0-100), with the dimension breakdown as a small table.
- Critical-finding count.
- Top three things to fix this week (highest-impact Critical or pattern-of-Major).
- API-led posture (System / Process / Experience layer mix).
- Coverage posture (current % vs floor, count of flows below per-flow floor).
- Governance posture (api_manager_enabled? scan result? policy drift count?).

#### 2. Findings by dimension
One subsection per dimension. Within each, group findings by severity. Each finding:

```
Severity | File:line | Rule (rubric ref) | One-line why
```

Don't suggest fixes. The point of `/audit` is to surface — `/bugfix` or `/proceed` is where the user fixes.

#### 3. External surface inventory
- Table of every upstream system (host, protocol, connector, config name, timeout, pool size, reconnection).
- Table of every API Manager registration (when api_manager_enabled), with policies applied vs declared.

#### 4. Coverage detail
- Per-app coverage % vs `munit_floor`.
- Per-flow coverage % for any flow below `flow_floor` (brownfield).
- Flows with zero MUnit suite, listed by file path.

#### 5. Pattern-level themes
After listing individual findings, look for **patterns** that span the codebase. Examples:
- "32 flows have no `doc:description` — this is a project-wide quality gap, not 32 isolated bugs."
- "Every Salesforce connector op uses the same cloned config — connector config hygiene is structural here."
- "Three different `<error-handler>` shapes across flows — pick one and apply consistently."

Patterns are more actionable than individual nits because they tell the team where to invest.

#### 6. Recommended next actions
Separate **what** the audit found from **what to do about it**. End with:
- Three to five concrete REQ-shaped action items the user could file (e.g., "REQ-XXX: Backfill `doc:description` across all flows via `generate-doc-description` skill").
- Whether any finding is severe enough to recommend `/bugfix` *now* (data exfiltration, hardcoded prod secret, ungoverned public API).
- A pointer to the current rubrics: "Run `/review` on the next change to enforce this going forward."

### Step 6: Persist the report

Write the report under `.adlc/audit-reports/`:

```
.adlc/audit-reports/AUDIT-<YYYY-MM-DD>-<short-scope>.md
```

Where `<short-scope>` is `all`, the dimension name, or a path-derived slug. If a report from the same date/scope already exists, suffix with `-2`, `-3`, etc.

The persisted report includes the findings table, the score, and the patterns. It does NOT include the in-progress agent transcripts.

Also append a one-line entry to `.adlc/knowledge/audits.log` so `/status` can surface it:

```
<YYYY-MM-DD> | scope=<scope> | score=<N>/100 | criticals=<N> | reportFile=.adlc/audit-reports/AUDIT-...md
```

Create the directory and log file if they don't exist.

### Step 7: Print the executive summary inline

Even though the full report is on disk, print sections 1, 5, and 6 verbatim in chat — those are the parts a human reads. Tell the user:

```
Full report: .adlc/audit-reports/AUDIT-<date>-<scope>.md
Audit log:   .adlc/knowledge/audits.log
```

## Output format

The user sees:
1. A single-line scope confirmation ("Auditing all of `src/main/mule/**` (84 flows, 47 MUnit suites).")
2. The Executive summary block.
3. A short note that detailed findings are in the persisted report, with the path.
4. The Patterns section.
5. The Next actions section.

Do not dump every finding inline — the report file is for that.

## Anti-patterns this skill avoids

- **No fix application.** `/audit` reports; it does not edit. Mixing audit and fix in the same skill ruins both.
- **No state-mutating MCP calls.** Read-only Platform MCP tools (`view_api_instance_policies`, `list_apis`, `check_policy_conformance`) are fine; `apply_policy_to_instance`, `deploy_mule_application` are forbidden.
- **No diff-only scope.** That's `/review`. `/audit`'s value is showing what's been there for months.
- **No silent skip on missing tools.** If `tools/mule-lint` is missing, that's a Critical toolchain finding — not an excuse to do less work.
- **No subjective scoring.** Every score deduction maps to a finding with a file:line and a rubric ref. If you can't cite the rubric, don't deduct.
- **No noise.** Nits go in the report file, not the chat output. The chat is for what the user will act on.

## Edge cases

- **Empty repo / scaffold-only**: surface "this looks like a fresh `/init` — no flows to audit yet" and exit cleanly. Don't fabricate findings.
- **Multi-app monorepo**: audit each app separately, then a cross-app section for shared `dw/Modules/`, shared globals, shared `pom.xml` parent.
- **Brownfield import**: if `mulesoft.coverage.mode: brownfield` and the per-flow floor is failing on dozens of legacy flows, group those into a single Pattern finding ("44 flows below `flow_floor` — recommend phased uplift in REQ-NNN") rather than 44 separate Majors.
- **api_manager_enabled: false**: skip the policy-drift dimension entirely, but still note in the executive summary that governance is opt-in and currently off.
