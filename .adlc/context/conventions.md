# Conventions — ADLC Toolkit (MuleSoft edition)

## Code is markdown, not code

Every skill and agent is a markdown file. No TypeScript, no Python, no package.json at the toolkit level. Claude Code interprets the markdown at invocation time. This matters:

- **No build step**: edits take effect immediately via the symlink install
- **No test runner for skills**: "tests" are dogfooding — invoke the skill on a real REQ and see if it produces the expected artifacts
- **Linting is minimal**: markdown formatting, frontmatter validity, and bash syntax in `!`...`` macros (see `tools/lint-skills/`)

**Exceptions — `tools/` and `workflows/`:** the `tools/` directory may contain real executable code (e.g. `tools/lint-skills/` Python, `tools/mule-lint/` Python or Node, `tools/mule-preflight/` shell+Node). Workflow scripts in `workflows/` are JS files run by Claude Code's Workflow primitive; they have their own node:test unit tests. Both are exempt from the markdown-only rule.

## MuleSoft-specific conventions

- **CLI**: always use `anypoint-cli-v4` (the modern Anypoint CLI). Never the legacy `anypoint-cli` (deprecated).
- **Maven**: `mule-maven-plugin` v4.x or higher; `mvn deploy -P<profile>` for deploys (cloudhub2, rtf, onprem).
- **Runtime**: Mule 4.6.0 minimum; Java 17 (LTS).
- **MCP-first**: prefer DX MCP (`mulesoft-mcp-server`) tools over `anypoint-cli-v4` invocations when both are available — the MCP server provides structured, auditable operations against the same Anypoint endpoints. Reviewer agents must use Platform MCP (`omni.mulesoft.com/mcp` via `mcp-remote`) for live API Manager / monitoring / governance state rather than static XML inspection alone.
- **Flow / subflow naming**: kebab-case names; `*-config` suffix for global configs (e.g., `salesforce-config`, `db-config`, `http-listener-config`); `*-impl` suffix for sub-flow modules.
- **DataWeave**: 2.x; `output application/json` (or other media-type) explicitly declared at the top of every script; functions/types in `dw/Modules/`; PII redaction utilities mandatory for any payload touching user data.
- **APIkit-first**: every HTTP-facing app has a contract under `src/main/resources/api/` (RAML 1.0 or OAS 3.0), bound to an `apikit:router` element. No hand-rolled request routing.
- **API-led layering**: every app declares `<api.layer>system|process|experience</api.layer>` in `pom.xml` `<properties>`. Skills branch on this for review-time architecture checks.
- **Secrets**: never hardcode credentials. Use `secure-properties-config` + Anypoint Secrets Manager OR property placeholders. Pre-flight blocks any literal `password=`, `apiKey=`, `client_secret=`, `Bearer `, etc. in committed XML/properties.
- **Error handling**: every flow has an explicit `<error-handler>` with `on-error-continue` / `on-error-propagate`. No silent `<try>` scopes without handler.
- **Logging**: structured `<logger>` calls (DataWeave object payload, not interpolated strings); correlation-id propagation across flows via `vars.correlationId`; level `INFO` for happy-path, `ERROR` in handler scopes.
- **Streaming**: `repeatable-file-store-stream` for payloads >5MB.
- **Connector configs**: one shared global config per upstream (e.g., one `<http:request-config>` per external API); never inline credentials in operation elements.
- **MUnit**: every flow has at least one MUnit test; coverage floor configurable in `.adlc/config.yml` `mulesoft.coverage` (`munit_floor`, default 80; `class_floor` analogue for changed flows in brownfield mode); ALL external connectors mocked (no real callouts in tests).
- **Naming — app prefix**: `[AppPrefix]_[Component]_[Type]` analogue for top-level identifiers (project name, API spec name, policy declaration). AppPrefix is a 3–8 char project-scoped identifier declared in `.adlc/config.yml` (`mulesoft.app_prefix`).
- **Coverage policy**: three-tier policy in `.adlc/config.yml` `mulesoft.coverage` — `munit_floor` (project floor, default 80), `flow_floor` (per-changed-flow in brownfield mode, default 75), `diff_only` (when true, gate only changed flows). Greenfield projects gate deploys on app-level coverage only; brownfield gates both app and per-changed-flow. Meaningful assertions required regardless. Skills MUST read from config, never hardcode 75/80.
- **Governance**: when `governance.api_manager_enabled: true`, every public API has API Manager policy declarations (`client-id-enforcement`, `rate-limiting`, JWT/OAuth2 as applicable) — required-policy list lives in `mulesoft.governance.required_policies`. `/wrapup` generates `Policies.md` for every feature that touches API artifacts.
- **Deploy targets**: `cloudhub2` is the default; `rtf` (Runtime Fabric) and `onprem` are opt-in via `mulesoft.deploy_target`. CloudHub 2.0 deploys go through DX MCP `deploy_mule_application` / `update_mule_application`; on-prem deploys go through `mvn deploy` against an Anypoint Runtime Manager target.

The full set is in `.adlc/context/mulesoft-rules.md`. Phase 4 (task-implementer) and Phase 5 (review panel) both source `partials/mule-quality-checklist.md`, which is generated from mulesoft-rules.md and is the single source of truth.

## File and directory naming

- Skill directories: lowercase, single word or hyphenated (`spec`, `bugfix`, `template-drift`)
- Skill files: always `SKILL.md` (uppercase, singular) inside the skill directory
- Agent files: `agents/<agent-name>.md`, hyphenated lowercase
- Templates: `templates/<artifact>-template.md`
- IDs: namespaced by `project.shortname` from `.adlc/config.yml` (3-uppercase-letter prefix). Format: `<XYZ>-REQ-NNN`, `<XYZ>-BUG-NNN`, `<XYZ>-LESSON-NNN`, `TASK-NNN` (TASK ids stay un-namespaced — they live inside a parent REQ directory). NNN is zero-padded to 3 digits minimum. Example: `MUL-REQ-007`, `MUL-BUG-014`, `MUL-LESSON-022`. Allocated by `partials/id-counter.sh` against a per-project counter at `.adlc/.next-{req,bug,lesson}` — bootstrap from existing high-water mark on first allocation, never resets to 1 if artifacts exist. Legacy un-namespaced ids (`REQ-475-foo` from before the shortname era) remain valid history; the bootstrap reads them so new allocations resume above their high-water.
- Slugs: lowercase kebab-case, ≤6 words, no dates, no bare numbers
- MuleSoft artifacts follow Mule-native naming (kebab-case for flow/config names, PascalCase for DW types/functions, lowerCamelCase for DW variables) — those rules are owned by mulesoft-rules.md, not this file.

## Frontmatter conventions

All artifact types use YAML frontmatter. Dates in ISO format (`YYYY-MM-DD`). Arrays use JSON inline syntax (`tags: [a, b, c]`). Status enum values are lowercase strings.

**Required vs optional** varies per template. Generally: `id`, `title`, `status`, `created` are required; everything else is optional. When adding new fields, prefer additive — do not rename existing fields without a migration plan.

## Ethos injection pattern

Every skill begins with:

```markdown
## Ethos

!`sh .adlc/partials/ethos-include.sh 2>/dev/null || sh ~/.claude/skills-mulesoft/partials/ethos-include.sh`
```

The partial itself emits the canonical fallback chain (consumer-project ETHOS.md first, then toolkit-root, then graceful "No ethos found" message). The two-level fallback at the call site (project `partials/` first, then global `~/.claude/skills-mulesoft/partials/`) ensures the macro still works in consumer projects that haven't re-run `/init` after the toolkit shipped the partial.

## Context loading pattern

Skills load context via `!bash` macros under a `## Context` section. Use the same fallback chain: prefer consumer-project `.adlc/...`, fall back to `~/.claude/skills-mulesoft/...`. Example:

```markdown
- Conventions: !`cat .adlc/context/conventions.md 2>/dev/null || echo "No conventions found"`
- MuleSoft rules: !`cat .adlc/context/mulesoft-rules.md 2>/dev/null || echo "No mulesoft-rules found"`
```

Never hardcode paths; always allow the skill to degrade gracefully when a file is absent.

For shared multi-line snippets that would otherwise duplicate across many SKILL.md files, extract a POSIX shell partial under `partials/<name>.sh` and source it from each call site (see "Ethos injection pattern" above and the architecture.md "Partials" subsection).

## Prerequisites block

Every skill that depends on the `.adlc/` scaffold must have a `## Prerequisites` section that stops with a clear "run `/init` first" message if required files are missing. Do not silently produce broken output when context is absent.

## Bash in skills

- Keep bash minimal — prefer Claude's own tool calls (Read, Grep, Glob, Edit, Write) over shell
- Bash is fine for deterministic operations: counter increments, directory creation, git/gh/mvn/anypoint-cli-v4 commands, file globbing
- **POSIX-only**: no GNU-specific flags. Use `grep -oE` (not `-oP`), use `mkdir` locks (not `flock`), use `sed 's/old/new/'` not `-i ''` on macOS directly — prefer `perl` for in-place edits or write a temp file
- Quote file paths with spaces: `"$path"`
- Avoid `cd` — prefer absolute paths so commands work from any working directory

**Fenced blocks do not share shell state across steps.** Each ```sh fenced block in a SKILL.md may be an independent shell invocation — shell functions and non-exported variables defined in one fenced block are NOT visible in another. Therefore a shared shell **function** MUST be sourced from a `partials/*.sh` at *each* call site, in the **same fenced block as the invocation**, and MUST NEVER be defined in one fenced block and invoked from another. This is enforced structurally by the `tools/lint-skills` `cross-fence-fn` check.

## Agent dispatch patterns

- **Parallel review**: dispatch the 6-member panel in a single message (`reflector`, `correctness-reviewer`, `quality-reviewer`, `architecture-reviewer`, `test-auditor`, `security-auditor`). Read-only mandate: every agent must be told "Report findings only. Do not apply fixes."
- **Parallel implementation**: `task-implementer` agents dispatched one per independent task. Group into dependency tiers.
- **Subagent mode**: when a skill runs inside a subagent (e.g., via `/sprint`'s `pipeline-runner`), do NOT dispatch further subagents. Execute sequentially in-context instead.
- **Mule rubrics**: consumed as **rubrics**, not as separate agents. Reviewers and the implementer load the relevant rubric file by file glob (e.g. `.dwl` → dataweave-quality rubric).
- **Official MuleSoft skills**: invoked via the Skill tool by the implementer (e.g., `Skill(skill: "build-mule-integration")`). These are installed at consumer init via `npx skills add`, not vendored in this repo.
- **MCP tool calls**: reviewer agents (security-auditor, architecture-reviewer) call Platform MCP tools to verify findings against live state. Document which MCP tool answers which reviewer question in each agent's `## MCP tools` section.

## Pipeline state

Skills that span multiple phases (`/proceed`) write a `pipeline-state.json` next to the REQ spec. This lets a long-running pipeline resume from interruption without replaying phases. Every phase update writes the state file atomically.

## Commits and branches

- Branch naming: `feat/REQ-xxx-short-description` for features, `fix/bug-xxx-short-description` for bugs
- Commit message format: `<type>(<scope>): <description> [TASK-xxx]` — types are `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
- The TASK-xxx (or REQ-xxx) trailer is required for work tracked through the pipeline
- Co-author trailer is added by Claude Code automatically when committing on behalf of the user

## Models policy

- Only `sonnet` and `opus` are permitted in any agent's `model:` frontmatter. `haiku` and any third-party model are out of scope.
- Per-agent picks live in `MODEL_ASSIGNMENTS.md` at the repo root. Update both files in lockstep.

## What NOT to do

- **Don't create new skill directories casually**: each new skill is a commitment to maintain. Prefer extending an existing skill unless the new responsibility is genuinely orthogonal.
- **Don't bypass ethos**: the six principles (especially #4 Verify, Don't Trust and #5 Process Is Not Optional) exist because shortcuts silently fail.
- **Don't duplicate context loading logic**: if the same bash macro appears in three or more skills, extract it to `partials/<name>.sh` and source it from each call site.
- **Don't hardcode project-specific paths or values**: skills must work for any MuleSoft consumer project. AppPrefix, runtime version, Anypoint org id, environment, region, deploy target — all read from `.adlc/config.yml`, never hardcoded.
- **Don't edit `templates/` without considering downstream**: consumer projects that ran `/init` got a copy of the templates. Template changes propagate via `/template-drift` detection, not auto-update.
- **Don't introduce a third-party model or delegation tool**: the toolkit explicitly excludes Kimi K2.5 / Moonshot AI / any non-Anthropic model. Reasoning stays on Sonnet/Opus.
- **Don't vendor the official MuleSoft skill pack**: it's installed via `npx skills add` at consumer init. Vendoring creates drift risk against the upstream `@salesforce/mulesoft-vibes-skills` package.

## Testing changes

Because this is a symlink-install, there is no staging layer. To validate a skill change:

1. Commit the change in this repo
2. Open a Claude Code session in a MuleSoft consumer project
3. Invoke the changed skill on a real or synthetic REQ
4. Verify the artifacts it produces match the intended behavior
5. Revert if it breaks

For workflow scripts: `node --test workflows/tests/*.test.js` from the toolkit root. For lint-skills: `pytest tools/lint-skills/tests/ -q`. For mule-lint / mule-preflight: their own test runners under `tools/mule-lint/tests/` and `tools/mule-preflight/tests/`.
