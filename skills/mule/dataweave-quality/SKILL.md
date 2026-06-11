---
name: dataweave-quality
description: 100-point quality + correctness rubric for DataWeave 2.x scripts. Loaded by Phase 5 quality-reviewer (style) and correctness-reviewer (null-safety, type-coercion) when the change set touches *.dwl files or embedded <dw:transform> blocks.
glob: "**/*.dwl"
dimension: quality + correctness
---

# dataweave-quality (100-pt rubric)

Score DataWeave 2.x scripts against this rubric. Applies to standalone `.dwl` files AND embedded `<dw:transform>` blocks inside Mule XML.

## Categories (100 points total)

| Category | Points | Focus |
|---|---:|---|
| Syntax / version | 15 | `%dw 2.0` header; explicit `output` directive; no DW 1.0 |
| Functional composition | 15 | `map` / `filter` / `reduce` / `groupBy` over imperative scripting |
| Type annotations | 10 | function params + return types annotated where non-obvious |
| Null safety | 15 | `default`, `?`, `as Type {default: ...}` — no NPE risk |
| Module decomposition | 10 | shared logic in `dw/Modules/`; imports named, not glob `*` |
| Naming | 10 | lowerCamelCase for variables/functions; PascalCase for types |
| Performance | 10 | no deeply nested `mapObject`; streaming for large input; no regex hot paths |
| PII redaction | 10 | sensitive payloads pass through `dw/Modules/Redact.dwl` before logging |
| Comments | 5 | header `// <one-line purpose>`; no multi-paragraph rationale (link the spec) |

## Non-negotiables (any violation = Critical)

- **`%dw 2.0` only** — DW 1.0 is deprecated; mule-lint blocks it
- **Explicit `output` directive** on every script — never rely on implicit output type
- **No payload mutation** — DW is functional; mutation is a smell that often hides a bug

## Major findings

- **Null-safety gap**: `payload.foo.bar` accessed without `default` or `?` operator when `foo` may be null
- **Missing type annotations** on function params / return types when the type is non-obvious from the body
- **Inline DW exceeds 30 lines** in a Mule XML `<dw:transform>` — extract to `dw/Modules/`
- **No PII redaction** when payload is logged AND payload contains email/phone/SSN/credit card
- **Glob import** (`import * from <Module>`) when only a few names are used — prefer explicit named import
- **`reduce` with wrong accumulator init** — `acc = 0` when `acc = []` was meant
- **Regex-heavy transformation** in a hot path — pre-compile or push to Java module if profiled

## Minor findings

- **Multi-line literal string** for what should be a header comment — collapse to one line + link the spec
- **Type annotation missing** on a function whose body is one expression (low ambiguity)
- **`as String`** coercion when `default ""` would be clearer

## Patterns to flag

| Pattern | Issue | Fix |
|---|---|---|
| `%dw 1.0` | DW 1.0 deprecated | Migrate to `%dw 2.0` syntax |
| No `output` directive | Implicit output type | Add `output application/json` (or media-type appropriate) |
| `payload.foo.bar.baz` | Null-safety gap | Use `payload.foo.?bar.?baz` or `default` chain |
| `fun classify(input)` (no types) | Non-obvious return type | `fun classify(input: Object): String = ...` |
| 80-line inline `<dw:transform>` | Untestable inline DW | Extract to `dw/Modules/<Name>.dwl` |
| `<logger message="#[payload]"/>` for PII payload | Unredacted PII in logs | Pipe through `dw/Modules/Redact.dwl` first |

## Scoring guidance

- 90-100 pts: production-ready DataWeave
- 80-89 pts: minor findings, ship-with-followup
- 70-79 pts: needs revision before merge
- <70 pts: significant rework

## Reference

- mulesoft-rules.md "DataWeave (DW 2.x) Requirements" section
- partials/mule-quality-checklist.md (always-on baseline)
- DataWeave 2.0 docs: https://docs.mulesoft.com/dataweave/latest/
