---
id: TASK-xxx
title: "Task Title"
status: draft
parent: REQ-xxx
created: YYYY-MM-DD
updated: YYYY-MM-DD
dependencies: []
required_skills: []   # MuleSoft skill / rubric names the implementer MUST load via the Skill tool BEFORE editing files.
                      # Populated by /architect from .adlc/context/mule-skills-catalog.md based on the
                      # touched-file globs. Examples:
                      #   [create-project-template] — scaffolding a new Mule app
                      #   [build-mule-integration, mule-flow-quality] — adding flows/sub-flows
                      #   [secure-mule-app, mule-secrets-hygiene] — secrets work
                      #   [generate_munit_test, munit-coverage] — MUnit suites
                      # When empty AND the task touches Mule artifacts (src/main/mule/**, src/test/munit/**,
                      # src/main/resources/api/**, *.dwl, pom.xml), task-implementer surfaces a "no skill
                      # declared — proceeding from first principles" warning.
# repo: <repo-id>   # REQUIRED in cross-repo projects (see .adlc/config.yml).
                    # One of the ids under `repos:` in .adlc/config.yml.
                    # In single-repo projects, omit or set to the primary repo id.
---

## Description

What this task accomplishes.

## Files to Create/Modify

- `src/main/mule/<flow>.xml` — description of changes (e.g., add new sub-flow, wire error-handler)
- `src/test/munit/<flow>-test-suite.xml` — MUnit suite covering the new/changed flow
- `dw/Modules/<Module>.dwl` — shared DataWeave transformations (when applicable)
- `src/main/resources/api/<asset>.raml|.yaml` — API spec changes (contract-first)
- `src/main/resources/properties/{dev,sandbox,staging,prod}.properties` — env-specific config
- `pom.xml` — dependency / deploy-profile changes (vCore, replicas, region)
- `mule-artifact.json` — runtime / shared-libs declarations

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Technical Notes

Implementation details, patterns to follow, edge cases.
