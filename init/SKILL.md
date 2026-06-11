---
name: init
description: Bootstrap .adlc/ structure in a new repo or subdirectory
argument-hint: Optional target directory (defaults to current directory)
---

# /init — Bootstrap ADLC Structure

You are setting up the `.adlc/` directory structure for spec-driven development.

## Ethos

!`sh .adlc/partials/ethos-include.sh 2>/dev/null || sh ~/.claude/skills-mulesoft/partials/ethos-include.sh`

## Input

Target: $ARGUMENTS

## Instructions

### Step 1: Determine Target Directory
1. If given a path, use that as the target
2. If no argument, use the current working directory
3. Check if `.adlc/` already exists — if so, report what's already there and ask if the user wants to reinitialize or fill gaps

### Step 1.5: Ensure the Target Directory is a Git Repo

The whole ADLC pipeline assumes a working git repo: `/proceed` Step 0 runs `git worktree add`, every phase commits, `/wrapup` opens PRs. Initializing `.adlc/` inside a non-git directory ships a project that cannot proceed past `/spec`. Treat git as a precondition: if the directory isn't a git repo, **`git init` it locally by default** — assume a remote will be wired in later.

```bash
# Detect git status. We use `git rev-parse --git-dir` rather than `[ -d .git ]`
# because a worktree's .git is a file, not a directory, and a parent-tracked
# subdirectory shouldn't get its own re-init.
if git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Target is already inside a git repo — skipping git init."
else
  echo "No git repo detected at target. Initializing one locally..."
  # Default branch: prefer the user's configured init.defaultBranch, else
  # `main` (matches GitHub's default since 2020 and what /proceed expects
  # when .adlc/config.yml does not declare a different integration branch).
  default_branch=$(git config --global --get init.defaultBranch 2>/dev/null || true)
  default_branch=${default_branch:-main}
  git init -b "$default_branch"
  echo "Initialized git repo on branch '$default_branch'. A remote can be wired in later via:"
  echo "  git remote add origin <url>"
  echo "  git push -u origin $default_branch"
fi
```

This step is idempotent and never destructive — it only runs `git init` when there is no existing git context, and never touches an existing one. After this step every subsequent step can safely assume a working `.git/` and a sane default branch.

### Step 1.6: Scaffold Claude Code Permissions Allowlist (FIRST — before everything else)

This is intentionally hoisted before every other Bash-using step. The permissions allowlist must be in place **before** the rest of `/init` runs `mkdir`, `cp`, `sed`, `awk`, `node`, etc. — otherwise every subsequent step interactively prompts for the permission its allowlist was supposed to grant. Running this after Step 2/3/4 turns `/init` into a 30-prompt experience; running it here makes the rest of the run silent.

```bash
# Verify source exists
if [ ! -f ~/.claude/skills-mulesoft/templates/claude-settings-template.json ]; then
  echo "ERROR: Settings template not found at ~/.claude/skills-mulesoft/templates/claude-settings-template.json. Ensure ~/.claude/skills is symlinked to the adlc-toolkit repo."
  exit 1
fi

# Ensure destination directory exists
mkdir -p .claude

# Idempotent copy: only copy if destination does not already exist
if [ ! -f .claude/settings.json ]; then
  cp ~/.claude/skills-mulesoft/templates/claude-settings-template.json .claude/settings.json
  echo "Created .claude/settings.json from canonical template (Step 1.6 — early scaffold)."
else
  echo "Preserved existing .claude/settings.json (idempotent — not overwritten)."
fi
```

The template pre-approves the routine `git`, `gh`, `npm`, Read/Write/Edit, and agent-dispatch operations the ADLC pipeline fires. Destructive operations (`rm -rf`, `git reset --hard`, `gh pr merge`, `./deploy.sh`, `terraform apply/destroy`, force-push to `main`) remain on the **ask** list so a human still confirms the one-way moves. Customize for project-specific commands (e.g., add `Bash(cd app && ./deploy.sh:*)` for iOS deploys) by editing `.claude/settings.json` directly.

The template also wires two Claude Code hooks (`Stop` and `UserPromptSubmit`) that emit one JSONL event per turn boundary to `~/.adlc/runtime/user-wait.jsonl`. The sprint dashboard tails this log to compute per-REQ "user wait" idle time. Zero overhead when the dashboard isn't running.

**How this takes effect.** Claude Code auto-reloads `.claude/settings.json` on file change — no `/clear`, no restart, no in-session reload command needed. The project-level `defaultMode` and allowlist take effect on the next Bash call after the file is written. For the few commands Step 1.6 itself runs (`mkdir -p .claude`, `cp ~/.claude/skills-mulesoft/templates/...`), you may see one or two prompts — those fire BEFORE the file exists. Everything after Step 1.6 runs silently.

**Per-developer mode override.** The template's `defaultMode` is `bypassPermissions` because `/sprint` and `/proceed` run unattended pipelines. Each developer can override per-project in `.claude/settings.local.json` (gitignored by Claude Code) — e.g., set `permissions.defaultMode` to `acceptEdits` if you want manual approval on Bash commands when you're hand-coding. User-level `~/.claude/settings.json` is the cross-project default; project `settings.json` overrides user; project `settings.local.json` overrides project.

Tell the user: "`.claude/settings.json` was scaffolded with a default allowlist plus user-wait hooks. **Commit this file** — it is team-shared. Use `.claude/settings.local.json` (gitignored) for personal overrides like a stricter `defaultMode`."

If `.claude/settings.json` was preserved as-is, run the Step 8.5 hook backfill below now (don't wait for Step 8.5) — same idempotent merge logic.

### Step 2: Gather Project Context
Ask the user for the following (skip any that are already known from existing files):
1. **Project name** — What is this project called?
2. **What it does** — One paragraph description
3. **Tech stack** — Languages, frameworks, databases, cloud providers
4. **Project scope** — What's in scope vs out of scope
5. **Key architectural patterns** — Layered? Microservices? Monolith?

If a `CLAUDE.md`, `README.md`, or `package.json` exists, extract this info automatically and confirm with the user instead of asking.

### Step 3: Create Directory Structure
```
.adlc/
  ETHOS.md               # Copy of ~/.claude/skills-mulesoft/ETHOS.md — ensures skills work inside git worktrees
  context/
    project-overview.md    # What the project does, tech stack, scope
    architecture.md        # System diagram, layers, key patterns, ADRs
    conventions.md         # File organization, naming, testing, git conventions
    taxonomy.md            # Retrieval tag vocabulary (component/domain/stack/concerns)
    mule-skills-catalog.md # File-glob → skill+rubric dispatch table — required by /architect, task-implementer, Phase 5 reviewers
    mulesoft-rules.md      # Always-on rules baseline (anypoint-cli-v4, kebab-case names, error-handler per flow, DW 2.0, no Thread.sleep, etc.)
  specs/
    .gitkeep
  bugs/
    .gitkeep
  knowledge/
    assumptions/
      .gitkeep
    lessons/
      .gitkeep
  templates/             # Copies of ~/.claude/skills-mulesoft/templates/*.md — ensures skills work inside git worktrees
    assumption-template.md
    bug-template.md
    lesson-template.md
    requirement-template.md
    task-template.md
  partials/              # Copies of ~/.claude/skills-mulesoft/partials/*.sh — shared shell snippets sourced by SKILL.md files
    ethos-include.sh
  workflows/             # Copies of ~/.claude/skills-mulesoft/workflows/ RUNTIME files only — Dynamic Workflow scripts used by the workflow engine
    adlc-sprint.workflow.js   # ONE self-contained file: meta first, schemas + pure helpers inlined behind // ==== BEGIN/END PURE ==== (runtime has no require)
    README.md            # NOTE: workflows/tests/ is intentionally NOT copied — those are toolkit-internal node:test files (CommonJS require) that break Jest in "type":"module" consumer repos (see Step 6)
```

**Why the local copies of ETHOS.md, templates, partials, and workflows?** Claude Code's sandbox blocks the `Read` tool from accessing paths outside the current working directory. When a skill runs inside a git worktree (e.g., `.claude/worktrees/<name>/`), `~/.claude/skills-mulesoft/ETHOS.md`, `~/.claude/skills-mulesoft/templates/*.md`, `~/.claude/skills-mulesoft/partials/*.sh`, and `~/.claude/skills-mulesoft/workflows/*` become unreadable by subagents and any tool that uses `Read` mid-skill. Keeping copies under `.adlc/` makes the toolkit work identically in main checkouts and worktrees.

### Step 4: Populate Context Files

**project-overview.md** — Based on user input or existing docs:
```markdown
# {Project Name} — Project Overview

## What It Does
{description}

## Tech Stack
{tech stack table or list}

## Project Scope
{in scope / out of scope}
```

**architecture.md** — Initial structure:
```markdown
# {Project Name} — Architecture

## System Diagram
{ASCII diagram of major components}

## Layers
{description of architectural layers}

## Key Patterns
{important patterns used in the codebase}

## ADRs
(Add architectural decision records here as decisions are made)
```

**conventions.md** — Based on project analysis:
```markdown
# {Project Name} — Conventions

## File Organization
{directory structure}

## Naming
{naming conventions per language}

## Testing
{test framework, conventions, coverage requirements}

## Error Handling
{error handling patterns}

## Git Conventions
{branch naming, commit messages, PR process}
```

### Step 5: Update .gitignore
Add the following entries to the project's `.gitignore` (create it if it doesn't exist):
```
# ADLC worktrees (used by /proceed for parallel session isolation)
.worktrees/

# Claude Code per-user permission overrides (team settings live in .claude/settings.json)
.claude/settings.local.json

# ADLC per-project ID counters and locks — transient state; rebuilt on demand
# from existing artifacts (see partials/id-counter.sh). Do not commit.
.adlc/.next-req
.adlc/.next-bug
.adlc/.next-lesson
.adlc/.next-req.lock.d/
.adlc/.next-bug.lock.d/
.adlc/.next-lesson.lock.d/
.adlc/.cache/

# Playwright session tokens & test artifacts. storageState.json holds a live
# Salesforce session cookie — checking it in is a credential leak (test-auditor
# flags as Critical). reports/playwright/ holds traces/videos/HTML reports
# regenerated on every run.
tests/e2e/storageState.json
reports/playwright/
playwright-report/
test-results/
```

### Step 6: Copy ETHOS.md and Templates Into the Project

Copy the canonical ETHOS.md and all templates from the toolkit into the project so skills keep working inside git worktrees (where Read is sandboxed to the worktree root).

```bash
# Verify source exists
if [ ! -f ~/.claude/skills-mulesoft/ETHOS.md ] || [ ! -d ~/.claude/skills-mulesoft/templates ] || [ ! -d ~/.claude/skills-mulesoft/partials ] || [ ! -d ~/.claude/skills-mulesoft/workflows ]; then
  echo "ERROR: Toolkit not found at ~/.claude/skills-mulesoft/. Ensure ~/.claude/skills is symlinked to the adlc-toolkit repo."
  exit 1
fi

# Copy ETHOS.md (overwrite — canonical is source of truth)
cp ~/.claude/skills-mulesoft/ETHOS.md .adlc/ETHOS.md

# Copy templates (overwrite — canonical is source of truth)
mkdir -p .adlc/templates
cp ~/.claude/skills-mulesoft/templates/*.md .adlc/templates/

# Copy partials (overwrite — canonical is source of truth). These are POSIX
# shell snippets sourced by SKILL.md files (e.g., ethos-include.sh).
mkdir -p .adlc/partials
cp ~/.claude/skills-mulesoft/partials/*.sh .adlc/partials/
chmod +x .adlc/partials/*.sh

# Copy workflows (overwrite — canonical is source of truth). These are the
# Dynamic Workflow scripts the workflow engine runs (e.g.,
# adlc-sprint.workflow.js — ONE self-contained file with schemas + pure helpers
# inlined, since the runtime has no require). Resolved via the two-level fallback
# (.adlc/workflows/... -> ~/.claude/skills-mulesoft/workflows/...) so the engine works
# inside git worktrees where Read is sandboxed to the worktree root.
#
# Copy ONLY the runtime files: the workflow script(s) and the top-level README.
# Do NOT copy workflows/tests/ — those are toolkit-internal `node:test` unit
# tests for the inlined PURE helpers (CommonJS `require('node:test')`). They have
# no purpose in a consumer repo, and shipping a `*.test.js` under .adlc/ is a
# trap: in any "type":"module" repo running Jest, the DEFAULT testMatch
# (**/?(*.)+(spec|test).[jt]s?(x)) discovers .adlc/workflows/tests/helpers.test.js,
# runs it as ESM, and fails it with "ReferenceError: require is not defined" —
# reddening `npm test` and any CI gate that runs it. The engine is ONE
# self-contained file (no require/import/fs), so globbing *.workflow.js captures
# everything the runtime ever resolves.
mkdir -p .adlc/workflows
cp ~/.claude/skills-mulesoft/workflows/*.workflow.js .adlc/workflows/
cp ~/.claude/skills-mulesoft/workflows/README.md .adlc/workflows/
# Idempotent cleanup: remove a stale tests/ dir left by an OLDER /init that did
# `cp -R` of the whole workflows tree. Heals already-initialized repos on re-run;
# safe no-op when absent. (Belt-and-suspenders to the explicit-file copy above.)
rm -rf .adlc/workflows/tests

# Clean up Finder-style duplicates if present. Matches:
#   - .md files: "requirement-template 2.md"
#   - non-.md files: "pipeline-state 2.json", ".next-bug 2"
#   - directories: "knowledge 2", "specs 2"
# The `-depth` flag processes directory contents before the directory itself,
# so `rm -rf` on a "* 2" dir doesn't fail due to prior deletions.
find .adlc -depth \( -name "* 2" -o -name "* 2.*" \) -exec rm -rf {} + 2>/dev/null

# Advisory (Jest repos): the copy above ships NO test files under .adlc/, so the
# default Jest testMatch stays green with no config change. Only a repo with a
# custom BROAD testMatch (e.g. "**/*.js") would pick up .adlc/ — those repos
# should add "<rootDir>/.adlc/" to testPathIgnorePatterns. Purely informational;
# this does not edit package.json or any jest config.
if grep -q '"jest"' package.json 2>/dev/null || find . -maxdepth 1 -name 'jest.config.*' 2>/dev/null | grep -q .; then
  echo "ADVISORY (Jest detected): .adlc/ contains no test files by design — default 'npm test' is unaffected. If you use a custom broad testMatch, add \"<rootDir>/.adlc/\" to testPathIgnorePatterns."
fi
```

If the user has previously made intentional customizations to their local `.adlc/ETHOS.md`, `.adlc/templates/*.md`, `.adlc/partials/*.sh`, or `.adlc/workflows/adlc-sprint.workflow.js`, confirm before overwriting. Use `/template-drift` to surface what differs (it also flags a stale `.adlc/workflows/tests/` left by an older `/init` — the Jest landmine fixed above). Typical drift (stale copies) should be overwritten silently.

### Step 7: Scaffold Retrieval Taxonomy

Copy the canonical taxonomy template to `.adlc/context/taxonomy.md` so authors of new REQs, bugs, and lessons have a reference vocabulary for retrieval tags.

**This step is idempotent — skip if the file already exists** (preserve any project-local customizations).

```bash
# Verify source exists
if [ ! -f ~/.claude/skills-mulesoft/templates/taxonomy-template.md ]; then
  echo "ERROR: Taxonomy template not found at ~/.claude/skills-mulesoft/templates/taxonomy-template.md. Ensure ~/.claude/skills is symlinked to the adlc-toolkit repo."
  exit 1
fi

# Ensure destination directory exists (safe if Step 3 already created it)
mkdir -p .adlc/context

# Idempotent copy: only copy if destination does not already exist
if [ ! -f .adlc/context/taxonomy.md ]; then
  cp ~/.claude/skills-mulesoft/templates/taxonomy-template.md .adlc/context/taxonomy.md
  echo "Created .adlc/context/taxonomy.md from canonical template."
else
  echo "Preserved existing .adlc/context/taxonomy.md (idempotent — not overwritten)."
fi
```

Advise the user: "Open `.adlc/context/taxonomy.md` and customize the example values for this codebase. Authors of new REQs, bugs, and lessons will reference this file when choosing tag values (`component`, `domain`, `stack`, `concerns`). The `tags` dimension stays free-form."

### Step 7.5: Scaffold MuleSoft skills catalog, rules, and quality checklist

Copy the canonical MuleSoft skill dispatch table (`mule-skills-catalog.md`), the rules baseline (`mulesoft-rules.md`), and the Mule quality checklist (`partials/mule-quality-checklist.md`) into the consumer repo. These are required by:
- `/architect` — to look up which orchestrator skills (official MuleSoft pack + toolkit rubrics) to load based on spec signals
- `task-implementer` agent — to look up rubrics from the **File-glob → rubric+skill dispatch** table
- Phase 5 reviewer agents — same lookup, applied to the diff
- `/proceed` Phase 5 — to know what counts as Mule artifacts for the validate gate

Without these files in the consumer repo, the architect/implementer/reviewers fall back to first-principles reasoning, which is the failure mode that ships hand-rolled `pom.xml` + `src/main/mule/` scaffolding instead of `create-project-template` output (and similar drift across every artifact family).

**This step is idempotent — these files are *templates*, not customization surfaces.** Overwrite existing copies silently to keep them in sync with the toolkit; if the user has hand-edited either, surface a `/template-drift` advisory.

```bash
# Verify sources exist
TOOLKIT_CTX="$HOME/.claude/skills-mulesoft/.adlc/context"
TOOLKIT_PARTIALS="$HOME/.claude/skills-mulesoft/partials"
if [ ! -f "$TOOLKIT_CTX/mule-skills-catalog.md" ] || [ ! -f "$TOOLKIT_CTX/mulesoft-rules.md" ] || [ ! -f "$TOOLKIT_PARTIALS/mule-quality-checklist.md" ]; then
  echo "ERROR: MuleSoft context files not found at $TOOLKIT_CTX or $TOOLKIT_PARTIALS. Ensure ~/.claude/skills-mulesoft is symlinked to the adlc-toolkit-mulesoft repo."
  exit 1
fi

mkdir -p .adlc/context .adlc/partials

# Catalog: overwrite — canonical, machine-consumed dispatch table
cp "$TOOLKIT_CTX/mule-skills-catalog.md" .adlc/context/mule-skills-catalog.md
echo "Synced .adlc/context/mule-skills-catalog.md from toolkit canonical."

# Rules: overwrite if missing or unchanged. Skip overwrite if hand-customized;
# surface a /template-drift advisory instead.
if [ ! -f .adlc/context/mulesoft-rules.md ]; then
  cp "$TOOLKIT_CTX/mulesoft-rules.md" .adlc/context/mulesoft-rules.md
  echo "Created .adlc/context/mulesoft-rules.md from toolkit canonical."
else
  if ! cmp -s "$TOOLKIT_CTX/mulesoft-rules.md" .adlc/context/mulesoft-rules.md; then
    echo "Preserved existing .adlc/context/mulesoft-rules.md (differs from toolkit). Run /template-drift to review and sync."
  else
    echo "Preserved existing .adlc/context/mulesoft-rules.md (already in sync)."
  fi
fi

# Quality checklist: overwrite — derived from rules, no customization expected.
cp "$TOOLKIT_PARTIALS/mule-quality-checklist.md" .adlc/partials/mule-quality-checklist.md
echo "Synced .adlc/partials/mule-quality-checklist.md from toolkit canonical."
```

For non-MuleSoft projects, `/init` should not have been run from this toolkit — use `adlc-toolkit-sfdc` for Salesforce projects or the generic ADLC toolkit for other stacks. This step is mandatory for every MuleSoft consumer.

### Step 7.6: Validate MuleSoft prerequisites & install official skill pack

The MuleSoft toolkit depends on:
1. Node.js 20+ (for `npx skills add`, `mulesoft-mcp-server`, `mcp-remote`)
2. JDK 17 (LTS) + Maven 3.8+
3. `anypoint-cli-v4` installed and authenticated (`anypoint-cli-v4 conf client_id <ID>` / `client_secret <SECRET>`)
4. `anypoint-cli-dx-mule-plugin` installed (validated by `build-mule-integration` skill at startup)
5. Anypoint Extension Pack 1.10.0+ in VSCode (advisory — required at IDE-time, not init-time)
6. TWO Anypoint connected apps:
   - **DX MCP** — connected app *acting on its own behalf* (client credentials). Scopes: Mule Developer Generative AI User, Monitoring Viewer, Manage API Configuration, View APIs Configuration, Manage Policies, Exchange Contributor (or higher), Read/Create Applications, Read Runtime Fabrics, CloudHub Network Viewer, Usage Viewer.
   - **Platform MCP** — connected app *acting on user's behalf* with Authorization Code + Refresh Token grant types. Scopes: Exchange Viewer/Contributor, API Manager Environment Viewer/Admin, Monitoring Viewer, Governance Viewer/Administrator, Manage Application Data; plus Background Access, Profile, Identity, Email.

Validate prerequisites and install the official MuleSoft skill pack at the consumer level via `npx skills add`:

```bash
# 1. Node version check
node_version=$(node --version 2>/dev/null | sed 's/^v//' | cut -d. -f1 || echo 0)
if [ "${node_version:-0}" -lt 20 ] 2>/dev/null; then
  echo "ERROR: Node.js 20+ required (found ${node_version:-none}). Install from https://nodejs.org/"
  exit 1
fi

# 2. Java version check
if ! command -v java >/dev/null 2>&1; then
  echo "ERROR: Java not found. Install JDK 17 (LTS)."
  exit 1
fi
java_version=$(java -version 2>&1 | head -1 | sed -E 's/.*"([0-9]+).*/\1/')
if [ "${java_version:-0}" -lt 17 ] 2>/dev/null; then
  echo "WARN: Java ${java_version:-unknown} detected — Mule 4.6+ runtime requires JDK 17 (LTS). Mule may fail to build."
fi

# 3. Maven check
if ! command -v mvn >/dev/null 2>&1; then
  echo "ERROR: Maven 3.8+ required. Install via brew/apt/sdkman."
  exit 1
fi

# 4. anypoint-cli-v4 check
if ! command -v anypoint-cli-v4 >/dev/null 2>&1; then
  echo "ERROR: anypoint-cli-v4 not found. Install: npm install -g @mulesoft/anypoint-cli-v4"
  echo "  Then authenticate: anypoint-cli-v4 conf client_id <ID>; anypoint-cli-v4 conf client_secret <SECRET>"
  exit 1
fi

# 5. Connected-app credentials check (env vars)
missing_creds=""
[ -z "${ANYPOINT_CLIENT_ID:-}" ] && missing_creds="${missing_creds}  - ANYPOINT_CLIENT_ID (DX MCP)\n"
[ -z "${ANYPOINT_CLIENT_SECRET:-}" ] && missing_creds="${missing_creds}  - ANYPOINT_CLIENT_SECRET (DX MCP)\n"
[ -z "${ANYPOINT_PLATFORM_CLIENT_ID:-}" ] && missing_creds="${missing_creds}  - ANYPOINT_PLATFORM_CLIENT_ID (Platform MCP)\n"
[ -z "${ANYPOINT_PLATFORM_CLIENT_SECRET:-}" ] && missing_creds="${missing_creds}  - ANYPOINT_PLATFORM_CLIENT_SECRET (Platform MCP)\n"
if [ -n "$missing_creds" ]; then
  echo "WARN: Missing connected-app credentials in environment:"
  printf "$missing_creds"
  echo "  Without these, the MCP servers wired in .mcp.json will fail to start."
  echo "  Two options:"
  echo "    1. Export them in your shell rc: export ANYPOINT_CLIENT_ID=..."
  echo "    2. Create a project-local .env (gitignored) and source before running Claude Code."
  echo "  See README.md 'Consumer prerequisites' for connected-app setup."
fi

# 6. Install the official MuleSoft skill pack
if [ -d .claude/skills/mule-development ] || [ -d .agents/skills/mule-development ]; then
  echo "Official MuleSoft skill pack already installed — skipping."
else
  echo "Installing official MuleSoft skill pack via npx skills add..."
  if npx -y skills add mulesoft/mulesoft-dx/skills/mule-development --target claude-code --scope project --method symlink; then
    echo "  Done."
  else
    echo "WARN: 'npx skills add mulesoft/mulesoft-dx/skills/mule-development' failed."
    echo "  Re-run manually after fixing the cause (commonly: anypoint-cli-v4 not authenticated, or anypoint-cli-dx-mule-plugin missing)."
  fi
fi
```

### Step 7.7: Wire `.mcp.json` for DX MCP and Platform MCP

The `templates/claude-settings-template.json` already includes the `mcpServers` block. Step 1.6 copied that to `.claude/settings.json`. This step generates a project-local `.env.example` so contributors know which env vars to populate, and confirms `.env` is gitignored.

```bash
# Create .env.example documenting the required env vars
if [ ! -f .env.example ]; then
  cat > .env.example <<'EOF'
# MuleSoft connected-app credentials. Copy this file to .env (gitignored)
# and fill in your Client ID / Secret values from Anypoint Platform.
#
# DX MCP — connected app acting on its own behalf (client credentials grant).
# Scopes: Mule Developer Generative AI User, Monitoring Viewer, Manage API
# Configuration, View APIs Configuration, Manage Policies, Exchange
# Contributor, Read/Create Applications, Read Runtime Fabrics, CloudHub
# Network Viewer, Usage Viewer.
ANYPOINT_CLIENT_ID=
ANYPOINT_CLIENT_SECRET=
# PROD_US | PROD_EU | PROD_CA | PROD_JP | PROD_IN
ANYPOINT_REGION=PROD_US

# Platform MCP — connected app acting on user's behalf (Authorization Code +
# Refresh Token grant). Scopes: Exchange Viewer/Contributor, API Manager
# Environment Viewer/Admin, Monitoring Viewer, Governance Viewer/Administrator,
# Manage Application Data; plus Background Access, Profile, Identity, Email.
ANYPOINT_PLATFORM_CLIENT_ID=
ANYPOINT_PLATFORM_CLIENT_SECRET=
EOF
  echo "Created .env.example documenting required MCP env vars."
fi

# Ensure .env is gitignored
if [ -f .gitignore ] && ! grep -q '^\.env$' .gitignore; then
  echo ".env" >> .gitignore
  echo "Added '.env' to .gitignore."
fi
```

After Step 7.6 + 7.7, the consumer has:
- Official MuleSoft skill pack installed under `.claude/skills/`
- `.claude/settings.json` with `mcpServers` block wiring DX MCP (stdio) and Platform MCP (remote via `mcp-remote@latest`)
- `.env.example` documenting the four required connected-app env vars
- `.env` gitignored

Document the connected-app setup steps in the project README so other developers can configure their machines:

```
# Anypoint connected app — DX MCP (one acting on its own behalf)
1. Anypoint Platform → Access Management → Connected Apps → Create Connected App
2. App acts on its own behalf (client credentials)
3. Apply scopes per Step 7.6 list
4. Copy Client ID + Client Secret → set as ANYPOINT_CLIENT_ID / ANYPOINT_CLIENT_SECRET in .env

# Anypoint connected app — Platform MCP (one acting on user's behalf)
1. Same Connected Apps page → Create another
2. App acts on behalf of user; grant types: Authorization Code + Refresh Token
3. Apply scopes per Step 7.6 list
4. Redirect URLs: add a localhost:* URL (mcp-remote auto-assigns a port; the docs suggest http://localhost:12148/oauth/callback as a starting point)
5. Copy Client ID + Client Secret → set as ANYPOINT_PLATFORM_CLIENT_ID / ANYPOINT_PLATFORM_CLIENT_SECRET in .env
```

### Step 8: (moved to Step 1.6 — verify only)

The settings allowlist scaffold now runs at Step 1.6, before the bulk of `/init`'s shell work, so subsequent steps don't trigger permission prompts. This step is now a verification gate: confirm `.claude/settings.json` exists. If it doesn't (e.g., Step 1.6 was skipped or hand-removed), run the Step 1.6 scaffold block now — same idempotent logic.

```bash
if [ ! -f .claude/settings.json ]; then
  echo "WARN: .claude/settings.json missing — Step 1.6 should have created it. Re-running scaffold."
  mkdir -p .claude
  cp ~/.claude/skills-mulesoft/templates/claude-settings-template.json .claude/settings.json
  echo "Created .claude/settings.json from canonical template (late fallback)."
else
  echo "Verified .claude/settings.json present (created in Step 1.6)."
fi
```

### Step 8.5: Backfill user-wait hooks into pre-existing settings

When `.claude/settings.json` already existed (Step 8 preserved it), it may pre-date the user-wait hooks added in this version of the template. Detect that case and merge in just the hook block — never overwrite the user's allowlist customizations.

```bash
if [ -f .claude/settings.json ] && ! grep -q '"UserPromptSubmit"' .claude/settings.json; then
  echo "Backfilling user-wait hooks into existing .claude/settings.json..."
  node -e '
    const fs = require("fs");
    const file = ".claude/settings.json";
    const cur = JSON.parse(fs.readFileSync(file, "utf8"));
    cur.hooks = cur.hooks || {};
    const stopCmd = "mkdir -p ~/.adlc/runtime && printf \x27{\\\"ts\\\":\\\"%s\\\",\\\"kind\\\":\\\"stop\\\",\\\"session\\\":\\\"%s\\\",\\\"cwd\\\":\\\"%s\\\"}\\\\n\x27 \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\" \"${CLAUDE_SESSION_ID:-unknown}\" \"${CLAUDE_PROJECT_DIR:-$PWD}\" >> ~/.adlc/runtime/user-wait.jsonl";
    const submitCmd = stopCmd.replace("\\\"kind\\\":\\\"stop\\\"", "\\\"kind\\\":\\\"submit\\\"");
    cur.hooks.Stop = cur.hooks.Stop || [];
    cur.hooks.UserPromptSubmit = cur.hooks.UserPromptSubmit || [];
    cur.hooks.Stop.push({matcher:"*", hooks:[{type:"command", command:stopCmd}]});
    cur.hooks.UserPromptSubmit.push({matcher:"*", hooks:[{type:"command", command:submitCmd}]});
    fs.writeFileSync(file, JSON.stringify(cur, null, 2) + "\n");
    console.log("OK: appended Stop + UserPromptSubmit hooks");
  '
fi
```

This step is safe to re-run: the `grep -q '"UserPromptSubmit"'` guard skips when the hooks are already present. If the user has hand-customized hooks in another shape, the merge will append rather than replace — verify with `cat .claude/settings.json` afterward.

### Step 9: Scaffold `.adlc/config.yml` and set `project.shortname`

`.adlc/config.yml` is **required for every project** because the ADLC ID allocator (`partials/id-counter.sh`) reads `project.shortname` to namespace REQ / BUG / LESSON ids as `<XYZ>-REQ-NNN`. Without a shortname, `/spec`, `/bugfix`, and `/wrapup` all hard-fail. So this step is no longer optional.

```bash
# Verify source exists
if [ ! -f ~/.claude/skills-mulesoft/templates/config-template.yml ]; then
  echo "ERROR: Config template not found at ~/.claude/skills-mulesoft/templates/config-template.yml."
  exit 1
fi

if [ ! -f .adlc/config.yml ]; then
  cp ~/.claude/skills-mulesoft/templates/config-template.yml .adlc/config.yml
  echo "Created .adlc/config.yml from template."
else
  echo "Preserved existing .adlc/config.yml."
fi
```

Then **resolve `project.shortname`** AND auto-fill the dependent placeholders so the config is usable end-to-end without any manual editing:

1. Ask the user: "Pick a 3-uppercase-letter shortname for this project (used in IDs like `XYZ-REQ-001`). Examples: `MUL` for MuleSoft-Integrations, `ORD` for Order-Process-API, `BNK` for Banking-Experience-API. Pick something unique across every repo on your machine — once specs exist, changing it requires a migration."
2. Validate against `^[A-Z]{3}$`. Reject anything else and re-prompt.
3. Write it under `project.shortname` in `.adlc/config.yml`. If a value already exists and matches the regex, preserve it; if it's the placeholder `XYZ`, prompt the user to set a real value.
4. **Auto-fill the dependent fields** — these always derive from shortname + repo path, so there's no point asking for them separately:
   - `mulesoft.app_prefix` → set to the resolved shortname (asset / policy / flow naming uses this prefix).
   - `orgs.sandbox` → set to `basename(REPO_ROOT)` (the project directory name; CloudHub 2.0 / RTF deploys reference this as the default app name).

   The user can override any of these by hand-editing `.adlc/config.yml` after `/init` completes — the auto-fill is a "good default" only. Re-running `/init` does not overwrite an already-customized value (the substitute runs only when the field still equals the template placeholder).

The user must still **manually configure** these values per their Anypoint org (no sensible auto-default exists):
- `mulesoft.anypoint_org_id` — the Anypoint Platform organization id (UUID)
- `mulesoft.anypoint_environment` — Sandbox | Staging | Production
- `mulesoft.anypoint_region` — PROD_US | PROD_EU | PROD_CA | PROD_JP | PROD_IN
- `mulesoft.api_layer` — system | process | experience
- `mulesoft.governance.required_policies` — when api_manager_enabled is true

```bash
# Auto-fill dependent placeholders. Each substitution is gated on the field
# still being the template placeholder, so re-running /init never clobbers
# a user-customized value.
PROJECT_DIR=$(basename "$(pwd)")
SHORTNAME="$shortname"   # set by the prior validation block

# mulesoft.app_prefix — default to project.shortname.
if grep -qE '^[[:space:]]*app_prefix:[[:space:]]*"XYZ"[[:space:]]*$' .adlc/config.yml; then
  sed -i.bak -E "s|^([[:space:]]*app_prefix:[[:space:]]*)\"XYZ\"|\1\"$SHORTNAME\"|" .adlc/config.yml && rm .adlc/config.yml.bak
  echo "Set mulesoft.app_prefix='$SHORTNAME'"
fi

# orgs.sandbox — default to basename of repo root.
if grep -qE '^[[:space:]]*sandbox:[[:space:]]*"<repo-basename>"[[:space:]]*$' .adlc/config.yml; then
  sed -i.bak -E "s|^([[:space:]]*sandbox:[[:space:]]*)\"<repo-basename>\"|\1\"$PROJECT_DIR\"|" .adlc/config.yml && rm .adlc/config.yml.bak
  echo "Set orgs.sandbox='$PROJECT_DIR'"
fi
```

After this block, the config has:
- `project.shortname` = user input (e.g., `MUL`)
- `mulesoft.app_prefix` = same as shortname (`MUL`)
- `orgs.sandbox` = `basename($PWD)` (e.g., `orders-process-api`)

Manual follow-up still required: edit `.adlc/config.yml` to set `anypoint_org_id`, `anypoint_environment`, `anypoint_region`, `api_layer`, and (if governance is on) `required_policies`. The skills will fail loudly when these fields hold placeholder values.

```bash
# Verify the shortname field is set and valid
shortname=$(awk '
  /^project:/                  { in_project=1; next }
  in_project && /^[^[:space:]#]/ { in_project=0 }
  in_project && /^[[:space:]]+shortname:/ {
    sub(/^[[:space:]]+shortname:[[:space:]]*/, "")
    gsub(/["'\'']/, "")
    sub(/[[:space:]]*#.*$/, "")
    print
    exit
  }
' .adlc/config.yml)
case "$shortname" in
  [A-Z][A-Z][A-Z])
    if [ "$shortname" = "XYZ" ]; then
      echo "WARNING: project.shortname='XYZ' is the placeholder — replace with a real value before /spec."
    else
      echo "OK: project.shortname='$shortname'"
    fi
    ;;
  *)
    echo "ERROR: project.shortname is missing or invalid in .adlc/config.yml. Set it to 3 uppercase letters before running /spec, /bugfix, or /wrapup."
    ;;
esac
```

**Cross-repo (optional add-on)**. If the user says this repo will ever share features with other repos (admin app + its API + an iOS app, etc.), edit the `repos:` block in the same `.adlc/config.yml` to list siblings. The cross-repo conceptual model:

- "Primary" is per-REQ, not a fixed role. The current repo is primary for REQs that originate here. Siblings are other repos that might participate when a cross-repo REQ starts here.
- If you also originate REQs from one of those siblings, you'll run `/init` there too — each repo that hosts REQs gets its own `.adlc/`, its own `config.yml`, and its own `project.shortname`. Configs are symmetric mirrors of each other.

Advise the user:
- "Edit `.adlc/config.yml`. The entry for THIS repo should have `primary: true` and no `path` (path is implicit since it's this repo). Each sibling entry gets a `path:` (relative to this repo root, or absolute). Every sibling must already be cloned locally at that path."
- "If this is a single-repo project (REQs only ever originate here and never touch other repos), leave `repos:` with the single primary entry. ADLC skills fall back to single-repo behavior when no siblings are declared."
- "After editing, verify with `cat .adlc/config.yml` and make sure each sibling path resolves: `git -C <sibling-path> rev-parse --git-dir`."

### Step 10: Scaffold Playwright UI harness (rare — only when an Experience API exposes a UI)

Most MuleSoft projects are headless (System / Process APIs return JSON); Playwright is irrelevant. Only Experience APIs that render HTML for end users need Playwright.

`/architect`'s "UI test obligation" requires every UI-bearing task to ship a paired Playwright spec when `.adlc/config.yml` declares `playwright_specs:`. The Mule presets (`mule-core.yml`, `mule-anypoint.yml`) seed `playwright_specs: ""` (empty), so by default this step is skipped.

**Skip this step entirely** when:
- `.adlc/config.yml` does not declare `playwright_specs:` (default — most Mule projects), OR
- `playwright_specs:` is set to empty string.

This step ONLY runs when the user has explicitly set `playwright_specs:` to a non-empty path (e.g., `"tests/e2e"`) — typical for Experience APIs returning HTML or single-page-app shells served from a Mule listener.

**This step is idempotent** — every file copy is gated on `[ ! -f <dest> ]` so a re-run preserves customizations. If the user has hand-edited any harness file, surface a `/template-drift` advisory rather than overwriting.

```bash
# Verify sources exist
TOOLKIT_PW="$HOME/.claude/skills/templates/playwright"
if [ ! -d "$TOOLKIT_PW" ]; then
  echo "ERROR: Playwright harness template not found at $TOOLKIT_PW. Ensure ~/.claude/skills is symlinked to the adlc-toolkit repo."
  exit 1
fi

# Decide whether to scaffold. Read playwright_specs from .adlc/config.yml; bail when unset/empty.
pw_specs=$(awk '/^playwright_specs:/ { sub(/^playwright_specs:[[:space:]]*/, ""); gsub(/["'\'']/, ""); sub(/[[:space:]]*#.*$/, ""); print; exit }' .adlc/config.yml 2>/dev/null)
if [ -z "$pw_specs" ]; then
  echo "Skipped Playwright harness scaffold — playwright_specs is not declared in .adlc/config.yml."
else
  # 1. playwright.config.ts at repo root — only if absent (preserve customizations).
  if [ ! -f playwright.config.ts ]; then
    cp "$TOOLKIT_PW/playwright.config.ts" playwright.config.ts
    echo "Created playwright.config.ts from canonical template."
  else
    echo "Preserved existing playwright.config.ts."
  fi

  # 2. tests/e2e/global-setup.ts — only if absent.
  mkdir -p "$pw_specs"
  if [ ! -f "$pw_specs/global-setup.ts" ]; then
    cp "$TOOLKIT_PW/tests/e2e/global-setup.ts" "$pw_specs/global-setup.ts"
    echo "Created $pw_specs/global-setup.ts from canonical template."
  else
    echo "Preserved existing $pw_specs/global-setup.ts."
  fi

  # 3. example.spec.ts.example — implementer copies this when authoring the
  # first spec. Always present, no-op if already there.
  if [ ! -f "$pw_specs/example.spec.ts.example" ]; then
    cp "$TOOLKIT_PW/tests/e2e/example.spec.ts.example" "$pw_specs/example.spec.ts.example"
    echo "Created $pw_specs/example.spec.ts.example."
  fi

  # 4. tests/e2e/.gitignore — defense in depth on top of root .gitignore.
  if [ ! -f "$pw_specs/.gitignore" ]; then
    cp "$TOOLKIT_PW/tests/e2e/.gitignore" "$pw_specs/.gitignore"
  fi

  # 5. README.md inside the harness dir — orientation for the next dev.
  if [ ! -f "$pw_specs/README.md" ]; then
    cp "$TOOLKIT_PW/README.md" "$pw_specs/README.md"
  fi

  # 6. Wire Playwright into package.json — install the dev dep, install the
  # chromium browser binary, and add the "test:e2e": "playwright test" script.
  # This step is mandatory by default so the harness is immediately usable;
  # set ADLC_INIT_SKIP_PLAYWRIGHT_INSTALL=1 to opt out (e.g. offline init,
  # CI bootstrap that handles deps separately, pnpm/yarn projects that
  # manage installs out-of-band).
  if [ "${ADLC_INIT_SKIP_PLAYWRIGHT_INSTALL:-0}" = "1" ]; then
    echo "Skipped Playwright npm install (ADLC_INIT_SKIP_PLAYWRIGHT_INSTALL=1). Run manually:"
    echo "  npm install --save-dev @playwright/test"
    echo "  npx playwright install --with-deps chromium"
    echo "  and add \"test:e2e\": \"playwright test\" to package.json scripts."
  elif [ ! -f package.json ]; then
    echo "Skipped Playwright npm install — no package.json at repo root. Run /init from the repo root, or scaffold one first."
  else
    # Install @playwright/test as a dev dep when not already present. Detect
    # via package.json (devDeps OR deps) rather than running `npm ls` so an
    # uninstalled lockfile state still triggers a clean install.
    pw_already_dep=$(node -e '
      try {
        const p = JSON.parse(require("fs").readFileSync("package.json","utf8"));
        const has = (p.devDependencies && p.devDependencies["@playwright/test"]) ||
                    (p.dependencies && p.dependencies["@playwright/test"]);
        process.stdout.write(has ? "1" : "0");
      } catch (_) { process.stdout.write("0"); }
    ')
    if [ "$pw_already_dep" = "1" ]; then
      echo "@playwright/test already declared in package.json — skipping npm install."
    else
      echo "Installing @playwright/test (npm install --save-dev @playwright/test)..."
      if npm install --save-dev @playwright/test; then
        echo "  Done."
      else
        echo "WARNING: 'npm install --save-dev @playwright/test' failed. Re-run manually after fixing the cause (often offline/registry/permissions)."
      fi
    fi

    # Install the chromium browser binary used by the harness. Idempotent —
    # Playwright's installer no-ops when the matching version is already
    # present. --with-deps pulls OS-level shared libs (Linux); on macOS it's
    # a no-op for the deps part. Honor a separate skip flag so CI runners
    # that pre-bake browsers can opt out.
    if [ "${ADLC_INIT_SKIP_PLAYWRIGHT_BROWSERS:-0}" = "1" ]; then
      echo "Skipped 'npx playwright install --with-deps chromium' (ADLC_INIT_SKIP_PLAYWRIGHT_BROWSERS=1)."
    else
      echo "Installing Chromium for Playwright (npx playwright install --with-deps chromium)..."
      if npx --yes playwright install --with-deps chromium; then
        echo "  Done."
      else
        echo "WARNING: 'npx playwright install --with-deps chromium' failed. Re-run manually before the first /architect on a UI REQ."
      fi
    fi

    # Add the test:e2e script to package.json without touching anything else.
    # Use Node so we don't risk breaking JSON formatting or losing an existing
    # scripts entry.
    test_e2e_added=$(node -e '
      const fs = require("fs");
      const p = JSON.parse(fs.readFileSync("package.json","utf8"));
      p.scripts = p.scripts || {};
      if (p.scripts["test:e2e"]) { process.stdout.write("kept"); return; }
      p.scripts["test:e2e"] = "playwright test";
      fs.writeFileSync("package.json", JSON.stringify(p, null, 2) + "\n");
      process.stdout.write("added");
    ')
    if [ "$test_e2e_added" = "added" ]; then
      echo "Added \"test:e2e\": \"playwright test\" to package.json scripts."
    else
      echo "Preserved existing \"test:e2e\" script in package.json."
    fi
  fi
fi
```

After this step, Playwright is installed (`@playwright/test` + chromium browser binary) and `npm run test:e2e` is wired up. The next `/architect` run on a UI-bearing REQ lands its required `tests/e2e/<feature>.spec.ts` into an immediately-runnable harness — no manual `npm install` follow-up needed. Set `ADLC_INIT_SKIP_PLAYWRIGHT_INSTALL=1` to opt out of the npm install (e.g. offline init); set `ADLC_INIT_SKIP_PLAYWRIGHT_BROWSERS=1` to opt out of just the browser-binary download (e.g. CI runner with pre-baked browsers).

### Step 10.5: Register the project with the sprint dashboard & open it in Chrome

Tell the shared dashboard (running on this host, shared across every project) about this project so its REQs show up alongside everything else. Then launch / surface the dashboard URL in the user's default browser (Chrome preferred on macOS) so they can immediately see this project listed.

The launcher script is idempotent: it upserts the current `ADLC_ROOT` into `~/.adlc/dashboard-registry.json`, no-ops if the dashboard is already running, and never fails the parent skill on error. Setting `ADLC_DASHBOARD_OPEN=1` tells it to open the dashboard URL in the browser after registration.

```bash
# Resolve the launcher. Prefer the locally-copied .adlc/ path so this works
# inside git worktrees; fall back to the canonical toolkit location.
LAUNCHER=""
if [ -x .adlc/tools/sprint-dashboard/launch.sh ]; then
  LAUNCHER=".adlc/tools/sprint-dashboard/launch.sh"
elif [ -x "$HOME/.claude/skills/tools/sprint-dashboard/launch.sh" ]; then
  LAUNCHER="$HOME/.claude/skills/tools/sprint-dashboard/launch.sh"
fi

if [ -n "$LAUNCHER" ]; then
  ADLC_ROOT="$(pwd)" ADLC_DASHBOARD_OPEN=1 sh "$LAUNCHER" || true
else
  echo "[init] sprint-dashboard launcher not found — skipping dashboard registration."
fi
```

After this step, the user should see `<project-name>` listed at `http://127.0.0.1:5174` (default port; override with `ADLC_DASHBOARD_PORT`). The server picks up the new entry from the registry on its next ~1.5s poll, so even when the launcher reports "already running", the project shows up within seconds.

### Step 11: Summary
1. Display the created directory structure. If Step 1.5 ran `git init`, call that out and remind the user to wire in a remote (`git remote add origin <url>`).
2. Confirm the official MuleSoft skill pack is installed under `.claude/skills/`. If Step 7.6 reported a WARNING, surface that line in the summary so the user can re-run `npx skills add mulesoft/mulesoft-dx/skills/mule-development` manually.
3. Confirm `.mcp.json` (via `.claude/settings.json`) wires both DX MCP and Platform MCP. Remind the user to populate `.env` from `.env.example` with the four connected-app credentials before running Claude Code.
4. Confirm the rules and catalog files are in place: `.adlc/context/mulesoft-rules.md`, `.adlc/context/mule-skills-catalog.md`, `.adlc/partials/mule-quality-checklist.md`.
5. Explain the ADLC workflow: `/spec` → `/validate` → `/architect` → `/validate` → implement → `/reflect` → `/review` → `/wrapup` (or use `/proceed` to run the full pipeline automatically).
6. If cross-repo config was scaffolded, remind the user that `/proceed` will create worktrees in every touched sibling and open one PR per repo.
7. If the Playwright harness was scaffolded (rare for Mule), confirm `npm run test:e2e` is wired.
8. Remind the user to manually populate the remaining `.adlc/config.yml` MuleSoft fields: `anypoint_org_id`, `anypoint_environment`, `anypoint_region`, `api_layer`, and (when `governance.api_manager_enabled: true`) `governance.required_policies` + `governance.governance_ruleset`.
9. Suggest adding ADLC skill references to the project's `CLAUDE.md` if one exists.
