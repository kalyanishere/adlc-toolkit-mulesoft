# Model assignments

Single registry of which model each agent runs on. Edit `agents/<name>.md` frontmatter to change a pick; mirror the change here so the registry stays auditable.

Only `sonnet` and `opus` are permitted. `haiku` and any third-party model (Kimi K2.5 etc.) are out of scope for this toolkit by policy.

| Agent | Model | Phase | Role |
|---|---|---|---|
| `architecture-mapper`  | sonnet | 1–2 (discovery) | Maps Mule artifact graph touched by a proposed change (flows, subflows, DataWeave modules, API specs, connector configs, MUnit suites, API Manager policies). |
| `feature-tracer`       | sonnet | 1–2 (discovery) | Finds analogous Mule flow / DW / MUnit / policy patterns in the project; reads `.adlc/knowledge/lessons/` and prior REQs. |
| `integration-explorer` | sonnet | 1–2 (discovery) | Catalogues HTTP/DB/SFDC/Kafka/JMS/AMQP/SFTP connector configs, Anypoint Exchange dependencies, API Manager policies, MCP-server provisioning, and Platform-MCP-discoverable services that a change touches. |
| `task-implementer`     | opus   | 4 (build)       | Phase 4 worker. Loads `partials/mule-quality-checklist.md` + relevant Mule rubric per artifact type. Invokes official MuleSoft skills (`build-mule-integration`, `secure-mule-app`, etc.) via the Skill tool. Enforces mulesoft-rules.md inline. |
| `pipeline-runner`      | opus   | orchestrator    | Runs the complete `/proceed` pipeline sequentially in subagent mode. |
| `correctness-reviewer` | opus   | 5 (review)      | Logic, race, security adversarial pass. Mule flavor: error-handler completeness, DataWeave null-safety, payload-mutation pitfalls, async/streaming correctness, batch-job completion semantics. |
| `quality-reviewer`     | sonnet | 5 (review)      | Convention + code quality. Loads mule-flow-quality, dataweave-quality, munit-coverage rubrics by file glob. |
| `architecture-reviewer`| sonnet | 5 (review)      | Architectural compliance. Mule flavor: API-led layering (system/process/experience), APIkit contract conformance, connector-config singleton pattern, deploy-hygiene (pom.xml, mule-artifact.json). May call Platform MCP `list_apis`, `view_api_version_details` for runtime evidence. |
| `test-auditor`         | sonnet | 5 (review)      | Test coverage + assertion quality. Loads munit-coverage rubric. Verifies all external connectors are mocked, assertions are meaningful, coverage ≥ project floor. |
| `security-auditor`     | opus   | 5 (review)      | Secrets hygiene (no hardcoded credentials in XML/properties), secure-properties-config usage, API Manager policy declarations, OAuth/JWT/client-id-enforcement coverage, governance conformance. May call Platform MCP `view_api_instance_policies`, `check_policy_conformance` to verify against live state. |
| `reflector`            | opus   | 5 (self-review) | Walks mulesoft-rules checklist + touched-artifact's Mule rubric end-to-end before formal review fans out. |

## Distribution

- **Opus (5):** task-implementer, pipeline-runner, correctness-reviewer, security-auditor, reflector
- **Sonnet (6):** architecture-mapper, feature-tracer, integration-explorer, architecture-reviewer, quality-reviewer, test-auditor

## How to change a pick

1. Edit `agents/<name>.md` and update the `model:` frontmatter line.
2. Update the row in the table above.
3. Run `python3 tools/lint-skills/check.py --root .` to confirm no agent has an unresolved `model:` (any string outside `sonnet`/`opus` is a project policy violation; the linter will be taught to enforce this in a later batch).
