# mule-lint

Static rule check for MuleSoft projects. Mirrors the role of `tools/sf-lint/` in the SFDC fork: enforce a focused subset of `mulesoft-rules.md` that is statically checkable from the XML, properties, and DataWeave files.

This is **not** a replacement for `anypoint-cli-v4 governance:validate` — that runs against API specs and is governance-policy-shaped. mule-lint runs against the project's source tree and catches the high-leverage anti-patterns BEFORE governance scan.

## Rules enforced

1. **No hardcoded credentials** in committed XML / properties / DataWeave. Blocks any literal `password=`, `apiKey=`, `client_secret=`, `Authorization: Bearer ...`, `Authorization: Basic ...`, `private_key=...`. Configured allowlist for known-safe placeholders (`${...}`).
2. **Every flow has an `<error-handler>`** — either inline `<error-handler>` block or a `<flow-ref>` to a global error-handler sub-flow inside a wrapping `<error-handler>`. Standalone `<try>` without handler is a violation.
3. **Every connector operation references a config by name** — `config-ref="..."` is non-empty. Inline credentials/host on operation elements is a violation.
4. **Every `<http:request-config>` declares `connectionTimeout` and `responseTimeout`** explicitly.
5. **Every flow has a meaningful name** — blocks `flow1`, `flow-copy`, `Untitled-flow`, etc.
6. **DW scripts declare `output` directive** — every `.dwl` file (or embedded `<dw:transform>` block) starts with `%dw 2.0` and has an explicit `output ...` line before the `---`.
7. **No DW 1.0** — blocks files that start with `%dw 1.0`.
8. **No `Thread.sleep`** in MUnit test files.
9. **Logger uses object payload, not string concatenation** — `<logger message="...">` with `#[ ... ]` DataWeave expression preferred; literal-only string `message=` produces a warning (not error).
10. **No production Basic Auth** — flags any `<http:basic-authentication>` operation in a flow whose name contains `production`, or in a config whose `name` contains `prod`.

## Usage

```sh
sh tools/mule-lint/check.sh [path]
```

`path` defaults to the project root (auto-detects `pom.xml`). Exits non-zero on any error-level violation; warnings print but do not fail the run.

To skip a specific rule for one violation, add a comment immediately above the offending line:
```xml
<!-- mule-lint:disable=hardcoded-credentials reason="reference to vendor docs only" -->
```
The pragma is per-file, per-rule, and requires a `reason=` attribute (so reviewers see the justification).

## Integration

- Pre-merge gate via `tools/mule-preflight/check.sh` (calls mule-lint as a stage).
- Phase 5 reviewers (security-auditor, correctness-reviewer) read the JSON output (`--format json`) to attach findings to the review report.
- GitHub Actions workflow runs `sh tools/mule-lint/check.sh --format junit > mule-lint.xml` and uploads as test results.
