---
name: canary
description: MuleSoft Sandbox deploy gate. Runs mule-preflight + mvn munit:test + governance:validate, then deploys to the Sandbox environment via DX MCP `deploy_mule_application` (CloudHub 2.0) or `mvn deploy -P <env>` (RTF / on-prem), with API Manager policy promotion via Platform MCP `apply_policy_to_instance` and Postman/Newman smoke as the post-deploy gate. **Sandbox-only by design** — Staging and Production deploys are intentionally out of scope (the project's CI/CD pipeline owns those promotions). Use when the user says "canary deploy", "deploy to sandbox", "smoke test the deploy", or wants validation + deploy confidence after a merge.
argument-hint: (no arguments — always targets the Sandbox environment from `.adlc/config.yml`)
---

# /canary — MuleSoft Sandbox deploy gate

You are deploying a merged Mule change set to the project's Sandbox environment so the team can smoke-test it before any further promotion.

`/canary` runs the canonical sequence: `tools/mule-preflight` (lint + munit + coverage + secrets + policies + governance:validate) → deploy via DX MCP `deploy_mule_application` (CloudHub 2.0 default) or `mvn deploy -P <env>` (RTF / on-prem) → API Manager policy promotion via Platform MCP → Postman/Newman smoke → coverage / governance verification. Each gate halts on first failure with a forward-fix recommendation. **Staging and production deploys are out of scope** — they belong to the project's CI/CD pipeline (GitHub Actions + Anypoint, Gearset for Anypoint, etc.). The ADLC pipeline ships changes to Sandbox; humans + CI promote from there.

## Ethos

!`sh .adlc/partials/ethos-include.sh 2>/dev/null || sh ~/.claude/skills-mulesoft/partials/ethos-include.sh`

## Context

- Current directory: !`pwd`
- Current branch: !`git branch --show-current 2>/dev/null || echo "Not a git repo"`
- Configured Sandbox environment: !`grep -E "^[[:space:]]*anypoint_environment:" .adlc/config.yml 2>/dev/null | head -1 || echo "No .adlc/config.yml — Anypoint environment not configured"`
- Configured deploy target: !`grep -E "^[[:space:]]*deploy_target:" .adlc/config.yml 2>/dev/null | head -1 || echo "No deploy_target configured"`
- anypoint-cli-v4 status: !`anypoint-cli-v4 account user describe --output json 2>/dev/null | jq -r '.username // "not authenticated"' || echo "anypoint-cli-v4 not configured"`
- MuleSoft rules: !`cat .adlc/context/mulesoft-rules.md 2>/dev/null || cat ~/.claude/skills-mulesoft/.adlc/context/mulesoft-rules.md 2>/dev/null || echo "No mulesoft-rules found"`
- Mule quality checklist: !`cat .adlc/partials/mule-quality-checklist.md 2>/dev/null || cat ~/.claude/skills-mulesoft/partials/mule-quality-checklist.md 2>/dev/null || echo "No mule-quality-checklist found"`

## Input

`/canary` takes no arguments. The target is always the Sandbox environment from `.adlc/config.yml` (`mulesoft.anypoint_environment` set to `Sandbox`). If the user types `/canary staging`, `/canary prod`, or any other env name, refuse and point them at their CI/CD pipeline.

## Prerequisites

1. `anypoint-cli-v4` installed and authenticated (`anypoint-cli-v4 conf client_id <ID>` / `client_secret <SECRET>`).
2. `.adlc/config.yml` declares `mulesoft.anypoint_environment: "Sandbox"` and `mulesoft.deploy_target: cloudhub2|rtf|onprem`.
3. The `.mcp.json` wires DX MCP (for CloudHub 2.0 deploys) and Platform MCP (for governance / policy promotion). Two connected apps configured per `/init` requirements.
4. JDK 17 + Maven 3.8+ on PATH; `pom.xml` builds cleanly via `mvn validate compile`.
5. The branch under test is merged-or-ready and the working tree is clean.

If `.adlc/config.yml` is absent OR the required `mulesoft.*` fields are missing, stop and tell the user to add them (see `presets/mule-core.yml` / `presets/mule-anypoint.yml` for the shape).

## Environment resolution

```sh
ENV=$(awk '/^[[:space:]]*anypoint_environment:/{sub(/^[[:space:]]*anypoint_environment:[[:space:]]*/,""); gsub(/["'\'']/,""); sub(/[[:space:]]*#.*$/,""); print; exit}' .adlc/config.yml)
[ "$ENV" = "Sandbox" ] || { echo "ERROR: /canary requires mulesoft.anypoint_environment='Sandbox' (got '$ENV'). Production / Staging promotions belong to your CI/CD pipeline."; exit 1; }

DEPLOY_TARGET=$(awk '/^[[:space:]]*deploy_target:/{sub(/^[[:space:]]*deploy_target:[[:space:]]*/,""); gsub(/["'\'']/,""); sub(/[[:space:]]*#.*$/,""); print; exit}' .adlc/config.yml)
DEPLOY_TARGET=${DEPLOY_TARGET:-cloudhub2}

ORG_ID=$(awk '/^[[:space:]]*anypoint_org_id:/{sub(/^[[:space:]]*anypoint_org_id:[[:space:]]*/,""); gsub(/["'\'']/,""); sub(/[[:space:]]*#.*$/,""); print; exit}' .adlc/config.yml)
[ -n "$ORG_ID" ] || { echo "ERROR: mulesoft.anypoint_org_id is missing or empty in .adlc/config.yml"; exit 1; }
```

Surface the org id, env, and deploy target to the user before any deploy.

## Instructions

### Step 1: Local pre-flight (mule-preflight stages)

Run the full mule-preflight pipeline before any server-side validate. Each stage is fast; together they catch lint / coverage / secrets / policies / governance issues that otherwise burn 60-90s per CloudHub deploy attempt.

```sh
sh tools/mule-preflight/check.sh   # lint -> mvn munit:test -> coverage -> secrets -> policies -> governance
```

Stages and what each catches:
- **lint** (`tools/mule-lint`): hardcoded credentials, missing error-handlers, inline connector configs, missing http timeouts, weak flow names, DW 1.0 syntax, DW missing output, Thread.sleep in tests, logger string concat, production basic auth.
- **test** (`mvn validate compile munit:test`): pom.xml well-formed, sources compile, full MUnit suite passes.
- **coverage** (`tools/mule-coverage`): coverage ≥ `mulesoft.coverage.munit_floor` (default 80); per-changed-flow ≥ `mulesoft.coverage.flow_floor` (default 75) in brownfield mode.
- **secrets** (lint hardcoded-credentials re-run): defense-in-depth scan across the full source tree.
- **policies**: when `governance.api_manager_enabled: true`, asserts that every API instance touched by the change has a `Policies.md` declaration.
- **governance**: when `governance.governance_ruleset` is set, runs `anypoint-cli-v4 governance:validate` against every API spec.

If any stage exits non-zero, **STOP** — surface the findings verbatim and refuse to deploy. Address each finding inline; re-run the affected stage individually with `sh tools/mule-preflight/check.sh <stage>`.

### Step 2: Build the deployable artifact

```sh
mvn clean package -DskipMunitTests
# -DskipMunitTests because Step 1 already ran the suite; re-running here is wasted CI time.
```

Capture the resulting `target/<artifactId>-<version>-mule-application.jar`. On any build failure, STOP — surface the Maven error.

### Step 3: Deploy to Sandbox

Choose the deploy actor based on `mulesoft.deploy_target`:

#### CloudHub 2.0 (default)

Use **DX MCP `deploy_mule_application`** (preferred) or `update_mule_application` (when the app is already deployed). Both surface the deploy id + per-replica status.

```
# Via DX MCP
deploy_mule_application(
  applicationName: "${app_prefix}-${artifact-id}",
  environment: "Sandbox",
  organizationId: "${anypoint_org_id}",
  artifactPath: "target/<artifactId>-<version>-mule-application.jar",
  replicas: 2,
  vCores: 0.1
)
```

If the app is already deployed in Sandbox, prefer `update_mule_application` to preserve the deployment id and avoid re-creating the API Manager registration.

CLI fallback when DX MCP is unavailable:
```sh
anypoint-cli-v4 runtime-mgr cloudhub-application deploy \
  --environment Sandbox \
  --organization "$ORG_ID" \
  --runtime-version "${mule_runtime}" \
  --target cloudhub2 \
  "${app_prefix}-${artifact-id}" "target/<artifact>-mule-application.jar"
```

#### Runtime Fabric (RTF)

```sh
mvn deploy -P rtf-sandbox \
  -Danypoint.org.id="$ORG_ID" \
  -Danypoint.environment=Sandbox \
  -Dcloudhub.workers=2
```

The `Bash(mvn deploy:*)` permission is on the project's allow list for unattended pipeline runs — move it to `ask` if you want a human gate.

#### On-prem (Anypoint Runtime Manager)

```sh
mvn deploy -P onprem-sandbox \
  -Danypoint.org.id="$ORG_ID" \
  -Danypoint.environment=Sandbox \
  -Dserver.group="${onprem_server_group}"
```

Capture the deploy id and the full result. Surface succeeded/failed component counts. On any failure, STOP with the deployment errors verbatim.

### Step 4: API Manager policy promotion (when governance enabled)

When `mulesoft.governance.api_manager_enabled: true` AND `Policies.md` declares policies for this REQ, promote each declared policy to the Sandbox API instance via Platform MCP:

```
# Via Platform MCP
apply_policy_to_instance(
  apiInstanceId: <id-from-list_apis>,
  policy: { templateId: "client-id-enforcement", configuration: {...} }
)
```

After applying, verify with `view_api_instance_policies` that the live state matches the `Policies.md` declaration. If drift is detected (declared but not applied, or applied but not declared), surface as a Critical finding and STOP.

CLI fallback:
```sh
anypoint-cli-v4 api-mgr policy apply \
  --environment Sandbox \
  --apiInstanceId <id> \
  <policy-spec-file>
```

### Step 5: Smoke gates

Run smoke tests against the deployed Sandbox endpoint.

#### Postman/Newman (when `mulesoft.smoke_tests` is configured)

When `.adlc/config.yml` `mulesoft.smoke_tests:` lists Newman collection paths, run each against the Sandbox endpoint:

```sh
SANDBOX_BASE_URL=$(anypoint-cli-v4 runtime-mgr cloudhub-application describe \
  --environment Sandbox --organization "$ORG_ID" \
  "${app_prefix}-${artifact-id}" --output json | jq -r '.endpoint.url')

for collection in $smoke_tests; do
  npx newman run "$collection" \
    --env-var "baseUrl=$SANDBOX_BASE_URL" \
    --reporters cli,json \
    --reporter-json-export "reports/newman/sandbox/$(basename $collection .json).json"
done
```

Roll up pass/fail per collection. On any failure, **STOP** — surface the failing request, response status, and assertion message.

### Step 6: Verify — governance scan + coverage check

After deploy + smoke gates, run a final verification:

```sh
# Governance scan against the live API instance
ANYPOINT_RULESET=$(awk '/^[[:space:]]*governance_ruleset:/{sub(/^[[:space:]]*governance_ruleset:[[:space:]]*/,""); gsub(/["'\'']/,""); sub(/[[:space:]]*#.*$/,""); print; exit}' .adlc/config.yml)
if [ -n "$ANYPOINT_RULESET" ]; then
  anypoint-cli-v4 governance:validate \
    --rulesets "$ANYPOINT_RULESET" \
    src/main/resources/api/*.{raml,json,yaml} 2>/dev/null
  # Or via Platform MCP check_policy_conformance for the live instance
fi

# Coverage report from the deployed Mule app — re-confirms that the deployed
# version matches the version mule-coverage scored in Step 1.
sh tools/mule-coverage/check.sh
```

**Read the coverage policy from `.adlc/config.yml`:**

```sh
MUNIT_FLOOR=$(awk '/^[[:space:]]*coverage:/{f=1} f && /^[[:space:]]*munit_floor:/{print $2; exit}' .adlc/config.yml)
FLOW_FLOOR=$(awk '/^[[:space:]]*coverage:/{f=1} f && /^[[:space:]]*flow_floor:/{print $2; exit}' .adlc/config.yml)
MODE=$(awk '/^[[:space:]]*coverage:/{f=1} f && /^[[:space:]]*mode:/{print $2; exit}' .adlc/config.yml | tr -d '"')
MUNIT_FLOOR=${MUNIT_FLOOR:-80}
FLOW_FLOOR=${FLOW_FLOOR:-75}
MODE=${MODE:-brownfield}
```

**Apply:**

1. **App-level (always):** `APP_COV < MUNIT_FLOOR` blocks; `APP_COV ≥ MUNIT_FLOOR` passes.
2. **Per-flow (brownfield mode only)** — for each flow in the diff, query `target/site/munit/coverage/munit-summary.json` and assert `pct ≥ FLOW_FLOOR`. Below floor blocks.
3. **Greenfield mode** — skip step 2; emit per-flow numbers as informational only.

### Step 7: Record state

If `pipeline-state.json` exists for the current REQ (we're inside `/proceed`):
1. Add a `canary` entry to `phaseHistory` with the result (passed/failed) and per-step timings.
2. Include: target environment, deploy target, deploy id, mvn build duration, MUnit pass/fail count, Newman result, governance scan result, coverage %.
3. The entry's `startedAt` and `completedAt` MUST be the literal output of `date -u +"%Y-%m-%dT%H:%M:%SZ"` run via Bash — once at canary entry start, once at completion. Do NOT type a timestamp.

Otherwise, just emit the report to stdout.

## Output

```
## Canary Sandbox Deploy Report

REQ: REQ-xxx
Target: Sandbox
Deploy target: <cloudhub2 | rtf | onprem>
Anypoint org: <org-id>
Mule runtime: <version>

### Pre-flight
- mule-lint: ✓ clean (or N findings)
- MUnit: NNN tests, NNN passed, 0 failed
- Coverage: NN.N% (floor: NN%)
- Secrets scan: ✓ clean
- Policies declaration: ✓ present (or skipped — governance not enabled)
- Governance: ✓ pass (or skipped — no ruleset)

### Build
- Maven: ✓ clean
- Artifact: target/<artifact>-mule-application.jar
- Wall time: NNs

### Deploy
- Deploy id: <id>
- Replicas / workers: 2
- Components succeeded: NNN
- Components failed: 0
- Wall time: NNs

### API Manager policy promotion (if enabled)
- Policies declared: NNN
- Policies applied: NNN
- Drift detected: 0 (or list)
- Live state matches declaration: ✓

### Smoke (Postman/Newman)
- Collections run: NNN
- Pass: NNN
- Fail: 0
- Result: ✓ clean

### Verification — governance + coverage
- Governance scan: ✓ pass (ruleset: <id>)
- Mode: <greenfield | brownfield>
- App coverage: NN.N% (munit_floor NN — ✓ pass | ✗ block)
- Per-changed-flow (brownfield only):
  - <flow-name>: NN.N% (flow_floor NN — ✓/✗)
- Final status: <status>

Next step: <Sandbox deploy clean — promote via your CI/CD pipeline | halted because of <reason>>
```

## Failure modes

- **mule-preflight stage fails:** stop. Surface the findings verbatim. Do NOT attempt the deploy.
- **mvn package fails:** stop. Surface the Maven error.
- **Deploy fails:** the corrective action is a forward-fix deploy; investigate the deploy log via DX MCP `list_applications` / Platform MCP `view_api_instance_details` or the Anypoint Runtime Manager UI.
- **Policy promotion drift:** Critical finding. The declared `Policies.md` doesn't match the live API instance state. Re-run policy promotion or update `Policies.md` to match reality.
- **Newman smoke fails:** stop. Surface the failing request and response status; recommend forward-fix.
- **Coverage drops below floor:** Critical block (see Step 6).
- **Governance scan fails:** Critical block. Address the ruleset violations before promotion.

## What This Skill Does NOT Do

- **Does NOT deploy to Staging or Production.** Sandbox is the only target. Staging and prod promotions are owned by the project's CI/CD pipeline. If the user types `/canary staging` or `/canary prod`, refuse and point them at the CI workflow file or release manager.
- Does NOT roll back a deploy. The corrective action is a forward-fix.
- Does NOT manage Anypoint org / environment / business-group provisioning (use Platform MCP `select_active_environment` / `select_active_business_group` directly when needed).
- Does NOT modify source code. It validates, builds, deploys, runs tests, reports.
- Does NOT bypass `.claude/settings.json` ask-prompts when configured.
