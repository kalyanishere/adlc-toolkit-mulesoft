---
name: mule-router
description: "Maps a MuleSoft change set (a list of touched files) to the official MuleSoft skills (build-time orchestrators) and the toolkit-authored Mule rubrics (review-time scoring) that should be loaded by the task-implementer (Phase 4) and the Phase 5 review panel. Read-only orchestration helper. Invoked by /proceed, /sprint, /architect, /review, and /bugfix. Returns a JSON object mapping each touched file to one or more skill / rubric names."
argument-hint: A newline-separated list of touched file paths, OR a glob/dir to scan.
---

# mule-router — file-glob → skill+rubric dispatch

You are a routing orchestrator. Given a list of touched files in a MuleSoft change set, you decide which **build skills** (official MuleSoft pack) and **review rubrics** (toolkit-authored under `skills/mule/`) the implementer and the review panel should consult. You do NOT run the rubrics yourself — your output is consumed by the calling skill, which then attaches the rubric content to the relevant agent prompts.

## Ethos

!`sh .adlc/partials/ethos-include.sh 2>/dev/null || sh ~/.claude/skills-mulesoft/partials/ethos-include.sh`

## Context

- Catalog: !`cat .adlc/context/mule-skills-catalog.md 2>/dev/null || cat ~/.claude/skills-mulesoft/.adlc/context/mule-skills-catalog.md 2>/dev/null || echo "No mule-skills catalog found"`
- MuleSoft rules: !`cat .adlc/context/mulesoft-rules.md 2>/dev/null || cat ~/.claude/skills-mulesoft/.adlc/context/mulesoft-rules.md 2>/dev/null || echo "No mulesoft-rules found"`
- Project config: !`cat .adlc/config.yml 2>/dev/null || echo "No .adlc/config.yml found"`

## Input

Touched files: `$ARGUMENTS`

Either a newline- or comma-separated list of relative file paths, OR a glob like `src/main/mule/**` (the skill will resolve it via Glob).

## Prerequisites

- `.adlc/context/mule-skills-catalog.md` must exist (run `/init` if missing).
- The official MuleSoft skill pack must be installed under `.claude/skills/mule-development/` (run `npx skills add mulesoft/mulesoft-dx/skills/mule-development` via `/init` if missing).
- Toolkit-authored review rubrics must exist under `skills/mule/<rubric>/SKILL.md` (vendored in this repo).

## Instructions

### Step 1: Resolve the touched-file list

If `$ARGUMENTS` looks like a list, use it directly. If it's a glob or directory, resolve it via Glob. Strip any path that does not resolve to a real file. Deduplicate.

### Step 2: Apply the dispatch table

For each touched file, walk the dispatch table from `.adlc/context/mule-skills-catalog.md` (the **File-glob → rubric+skill dispatch** section). The first matching glob row produces zero or more build skill names + zero or more review rubric names; record them.

The matching rule:
- A file matches a glob when fnmatch / Path.match accepts it
- Multiple globs may match a single file (e.g., a `<flow>-test-suite.xml` matches both the test-suite glob AND the generic XML glob — record all matches)
- A file with **no** matching glob is recorded as `unmatched` — the calling skill falls back to `partials/mule-quality-checklist.md` for that file

### Step 3: Honor `governance` opt-ins from `.adlc/config.yml`

Some skills are gated by the consumer's declared governance footprint:

- Governance / API Manager skills (`governance-policies` rubric, `manage_api_instance_policy` MCP tool, `apply_policy_to_instance` MCP tool) — only load when `mulesoft.governance.api_manager_enabled: true`
- Exchange-publishing skills (`create_and_manage_assets` MCP tool) — only load when `mulesoft.features.exchange_publishing: true`

If a touched file matches a gated skill but the relevant flag is **off**, surface a warning in the output (`unmatched-governance-gated`) so the calling skill can prompt the user to flip the flag rather than silently dropping the rubric.

### Step 4: Emit the routing manifest

Return a JSON object with this shape (keep it under 8 KB so it can be embedded in agent prompts):

```json
{
  "summary": {
    "files": <int>,
    "matched": <int>,
    "unmatched": <int>,
    "governance_gated_skipped": [<list of skill / rubric names skipped because governance flag is off>]
  },
  "by_file": {
    "<path>": {
      "build_skills": ["<skill-name>", ...],
      "review_rubrics": ["<rubric-name>", ...]
    }
  },
  "build_skills": [<unique sorted list of build skills the task-implementer should preload via the Skill tool>],
  "review_rubrics": {
    "correctness":   [<rubrics>],
    "quality":       [<rubrics>],
    "architecture":  [<rubrics>],
    "test-coverage": [<rubrics>],
    "security":      [<rubrics>]
  },
  "mcp_tools": {
    "dx":       [<list of DX MCP tools relevant to this change set>],
    "platform": [<list of Platform MCP tools relevant to this change set>]
  },
  "unmatched_files": [<paths>]
}
```

The dimension buckets (`correctness` / `quality` / `architecture` / `test-coverage` / `security`) come from the catalog's dispatch table column "Review-time rubrics" — split per dimension. The `build_skills` list is the union of "Build orchestrator (Phase 4)" entries across all touched files. The `mcp_tools` block surfaces the relevant DX / Platform MCP tools (e.g., `view_api_instance_policies` when the change touches API artifacts and governance is enabled).

### Step 5: Surface the manifest

Emit the manifest as the only stdout payload. Do not editorialize — the calling skill consumes the JSON directly.

## Quality checklist

- [ ] Every touched file appears in `by_file`, even if its value is `{ build_skills: [], review_rubrics: [] }` (unmatched)
- [ ] `build_skills` contains only skill names actually installed (verify under `.claude/skills/mule-development/` in the consumer or `~/.claude/skills/mule-development/` globally)
- [ ] `review_rubrics` dimension buckets contain only rubric names that exist under `skills/mule/`
- [ ] Governance-gated skips are recorded in `summary.governance_gated_skipped` (not silently dropped)
- [ ] `mcp_tools` lists only MCP tools available in the wired `.mcp.json` (DX MCP `mulesoft-dx` and Platform MCP `mulesoft-platform`)
- [ ] Output is valid JSON, single object, ≤8 KB

## When NOT to use this skill

- Don't use it for non-Mule file types — it ignores anything outside the dispatch table
- Don't use it as a content lint — it routes; it does not evaluate compliance. The mulesoft-rules compliance gate runs in `tools/mule-lint/`
- Don't use it as the only check in Phase 5 — `partials/mule-quality-checklist.md` is the always-on baseline for any file the router leaves unmatched
