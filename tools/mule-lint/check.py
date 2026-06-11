#!/usr/bin/env python3
"""mule-lint — static rule check for MuleSoft projects.

Walks the project tree (rooted at the directory containing pom.xml, or the
explicit path passed on the command line) and applies a focused subset of
mulesoft-rules.md that is statically checkable from XML / properties / .dwl.

Output formats: text (default, human-readable), json, junit.
Exits non-zero on any error-level violation. Warnings are reported but do
not fail the run.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET


# ---------- Rule definitions --------------------------------------------------

RULES = {
    "hardcoded-credentials": {
        "severity": "error",
        "summary": "Literal credentials/tokens detected (use ${...} placeholders + secure-properties-config).",
    },
    "missing-error-handler": {
        "severity": "error",
        "summary": "Flow has no <error-handler> — every flow needs an explicit handler.",
    },
    "inline-connector-config": {
        "severity": "error",
        "summary": "Connector operation lacks config-ref — externalize to a global-config element.",
    },
    "missing-http-timeouts": {
        "severity": "error",
        "summary": "<http:request-config> missing connectionTimeout / responseTimeout — defaults are too generous for prod.",
    },
    "weak-flow-name": {
        "severity": "warning",
        "summary": "Flow name is a placeholder (flow1, flow-copy, Untitled-flow) — use a business-meaningful name.",
    },
    "dw-missing-output": {
        "severity": "error",
        "summary": "DataWeave script missing explicit output directive.",
    },
    "dw-1x-syntax": {
        "severity": "error",
        "summary": "DataWeave 1.0 syntax — DW 2.0 is required.",
    },
    "thread-sleep-in-test": {
        "severity": "error",
        "summary": "Thread.sleep in MUnit test — use <munit-tools:sleep> or assertion-based waits.",
    },
    "logger-string-concat": {
        "severity": "warning",
        "summary": "<logger> uses literal string — prefer DataWeave object payload for structured logging.",
    },
    "production-basic-auth": {
        "severity": "error",
        "summary": "Basic Auth in a production-named flow/config — use OAuth2 or JWT in production.",
    },
}

CRED_PATTERNS = [
    # match key=value where the value isn't a placeholder ${...}
    re.compile(r"""(?ix) (^|[^a-z_])
                    (password|apiKey|api[_\-]?key|client[_\-]?secret|secret|access[_\-]?token|private[_\-]?key)
                    \s*=\s*
                    (?!\$\{)
                    ['"]?
                    [a-z0-9._\-+/=]{6,}
                    ['"]?
                """),
    re.compile(r"""(?i) Authorization\s*[:=]\s*['"]?\s*(Bearer|Basic)\s+[A-Za-z0-9._\-+/=]{6,}"""),
]

PLACEHOLDER_FLOW_NAMES = re.compile(r"""(?i) ^( flow\d* | sub[_\-]?flow\d* | flow[_\-]?copy | untitled[_\-]?flow | new[_\-]?flow )$""", re.VERBOSE)


# ---------- Models ------------------------------------------------------------

@dataclass
class Finding:
    rule: str
    severity: str
    file: str
    line: int
    message: str
    snippet: str = ""

    def asdict(self):
        return asdict(self)


@dataclass
class Report:
    root: str
    findings: list[Finding] = field(default_factory=list)

    def add(self, f: Finding):
        self.findings.append(f)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "warning"]


# ---------- Helpers -----------------------------------------------------------

def find_project_root(start: Path) -> Path:
    p = start.resolve()
    while p != p.parent:
        if (p / "pom.xml").exists():
            return p
        p = p.parent
    return start.resolve()


def iter_files(root: Path, pattern: str) -> Iterable[Path]:
    yield from root.rglob(pattern)


def read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def is_pragma_disabled(line: str, rule: str) -> bool:
    return f"mule-lint:disable={rule}" in line


def line_with_pragma(lines: list[str], idx: int, rule: str) -> bool:
    if idx > 0 and is_pragma_disabled(lines[idx - 1], rule):
        return True
    if is_pragma_disabled(lines[idx], rule):
        return True
    return False


# ---------- Rule implementations ----------------------------------------------

EXCLUDED_DIRS = {"target", "node_modules", ".git", ".idea", ".vscode", ".mvn"}


def walk_source(root: Path, suffixes: tuple[str, ...]) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for name in filenames:
            if name.endswith(suffixes):
                yield Path(dirpath) / name


def check_credentials(report: Report, root: Path):
    suffixes = (".xml", ".properties", ".yaml", ".yml", ".json", ".dwl")
    for path in walk_source(root, suffixes):
        if path.name.endswith(".secure.properties"):
            # decrypted local versions are gitignored; if it shows up, that's a separate problem
            continue
        lines = read_lines(path)
        for i, line in enumerate(lines):
            if line_with_pragma(lines, i, "hardcoded-credentials"):
                continue
            for pat in CRED_PATTERNS:
                if pat.search(line):
                    report.add(Finding(
                        rule="hardcoded-credentials",
                        severity=RULES["hardcoded-credentials"]["severity"],
                        file=str(path.relative_to(root)),
                        line=i + 1,
                        message=RULES["hardcoded-credentials"]["summary"],
                        snippet=line.strip()[:120],
                    ))
                    break


def parse_xml(path: Path) -> ET.ElementTree | None:
    try:
        return ET.parse(path)
    except ET.ParseError:
        return None


def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def find_line_number(lines: list[str], needle: str, start: int = 0) -> int:
    for i in range(start, len(lines)):
        if needle in lines[i]:
            return i + 1
    return 1


def check_xml_rules(report: Report, root: Path):
    main_mule_root = root / "src" / "main" / "mule"
    if not main_mule_root.exists():
        # No Mule sources — nothing to check beyond credentials.
        return

    for path in walk_source(main_mule_root, (".xml",)):
        tree = parse_xml(path)
        if tree is None:
            continue
        rel = str(path.relative_to(root))
        lines = read_lines(path)
        root_el = tree.getroot()
        check_flow_rules(report, root_el, rel, lines)
        check_connector_config_rules(report, root_el, rel, lines)
        check_logger_rule(report, root_el, rel, lines)


def check_flow_rules(report: Report, root_el: ET.Element, rel: str, lines: list[str]):
    for el in root_el.iter():
        tag = localname(el.tag)
        if tag != "flow":
            continue
        name = el.get("name", "").strip()
        line_no = find_line_number(lines, f'name="{name}"') if name else 1

        # Rule: weak-flow-name
        if name and PLACEHOLDER_FLOW_NAMES.match(name):
            if not (line_no - 1 < len(lines) and is_pragma_disabled(lines[line_no - 2] if line_no >= 2 else "", "weak-flow-name")):
                report.add(Finding(
                    rule="weak-flow-name",
                    severity=RULES["weak-flow-name"]["severity"],
                    file=rel, line=line_no,
                    message=RULES["weak-flow-name"]["summary"],
                    snippet=f'name="{name}"',
                ))

        # Rule: missing-error-handler
        # Flow must contain a child <error-handler> element OR a child <error-handler ref="..."/>.
        has_handler = any(localname(c.tag) == "error-handler" for c in el)
        if not has_handler:
            report.add(Finding(
                rule="missing-error-handler",
                severity=RULES["missing-error-handler"]["severity"],
                file=rel, line=line_no,
                message=RULES["missing-error-handler"]["summary"],
                snippet=f'<flow name="{name}">',
            ))

        # Rule: production-basic-auth
        is_prod_named = "prod" in name.lower() or "production" in name.lower()
        if is_prod_named:
            for descendant in el.iter():
                if "basic-authentication" in localname(descendant.tag).lower():
                    report.add(Finding(
                        rule="production-basic-auth",
                        severity=RULES["production-basic-auth"]["severity"],
                        file=rel, line=line_no,
                        message=RULES["production-basic-auth"]["summary"],
                        snippet=f'<flow name="{name}"> contains {localname(descendant.tag)}',
                    ))
                    break


def check_connector_config_rules(report: Report, root_el: ET.Element, rel: str, lines: list[str]):
    # Rule: missing-http-timeouts on http:request-config
    for el in root_el.iter():
        tag = localname(el.tag)
        if tag == "request-config" and "http" in (el.tag.split("}")[0] if "}" in el.tag else ""):
            if not el.get("connectionTimeout") or not el.get("responseTimeout"):
                cfg_name = el.get("name", "")
                line_no = find_line_number(lines, f'name="{cfg_name}"') if cfg_name else 1
                report.add(Finding(
                    rule="missing-http-timeouts",
                    severity=RULES["missing-http-timeouts"]["severity"],
                    file=rel, line=line_no,
                    message=RULES["missing-http-timeouts"]["summary"],
                    snippet=f'<http:request-config name="{cfg_name}">',
                ))

    # Rule: inline-connector-config
    # Look for elements that look like connector operations (e.g., http:request, db:select, salesforce:query)
    # and require they have a config-ref attribute.
    OP_NAMES = {"request", "send", "consume", "publish", "select", "insert", "update", "delete", "upsert", "query", "create", "execute"}
    for el in root_el.iter():
        tag = localname(el.tag)
        ns = el.tag.split("}")[0].lstrip("{") if "}" in el.tag else ""
        if tag in OP_NAMES and ns and "mule" not in ns and "core" not in ns:
            if not el.get("config-ref"):
                line_no = 1
                doc_name = el.get("doc:name") or el.get("{http://www.mulesoft.org/schema/mule/documentation}name") or tag
                report.add(Finding(
                    rule="inline-connector-config",
                    severity=RULES["inline-connector-config"]["severity"],
                    file=rel, line=line_no,
                    message=RULES["inline-connector-config"]["summary"],
                    snippet=f"<{tag}> ({doc_name})",
                ))


def check_logger_rule(report: Report, root_el: ET.Element, rel: str, lines: list[str]):
    for el in root_el.iter():
        if localname(el.tag) != "logger":
            continue
        msg = el.get("message", "")
        # If message is a literal string (no #[...]), warn.
        if msg and "#[" not in msg:
            line_no = find_line_number(lines, msg[:30]) if msg else 1
            report.add(Finding(
                rule="logger-string-concat",
                severity=RULES["logger-string-concat"]["severity"],
                file=rel, line=line_no,
                message=RULES["logger-string-concat"]["summary"],
                snippet=f'<logger message="{msg[:60]}">',
            ))


def check_dataweave(report: Report, root: Path):
    for path in walk_source(root, (".dwl",)):
        rel = str(path.relative_to(root))
        text = path.read_text(encoding="utf-8", errors="replace")
        first_real = next((ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("//")), "")

        if first_real.strip().startswith("%dw 1"):
            report.add(Finding(
                rule="dw-1x-syntax",
                severity=RULES["dw-1x-syntax"]["severity"],
                file=rel, line=1,
                message=RULES["dw-1x-syntax"]["summary"],
                snippet=first_real.strip()[:80],
            ))
            continue

        if not re.search(r"^output\s+\S+", text, re.MULTILINE):
            report.add(Finding(
                rule="dw-missing-output",
                severity=RULES["dw-missing-output"]["severity"],
                file=rel, line=1,
                message=RULES["dw-missing-output"]["summary"],
            ))


def check_thread_sleep(report: Report, root: Path):
    munit_root = root / "src" / "test" / "munit"
    if not munit_root.exists():
        return
    # Match Java/Groovy/DW form `Thread.sleep(...)` AND XML element forms `<Thread.sleep ...>`, `<thread:sleep ...>`.
    pat = re.compile(r"(\bThread\.sleep\s*\()|(<\s*[Tt]hread[.:]?[Ss]leep\b)")
    for path in walk_source(munit_root, (".xml", ".java", ".groovy", ".dwl")):
        rel = str(path.relative_to(root))
        lines = read_lines(path)
        for i, line in enumerate(lines):
            if line_with_pragma(lines, i, "thread-sleep-in-test"):
                continue
            if pat.search(line):
                report.add(Finding(
                    rule="thread-sleep-in-test",
                    severity=RULES["thread-sleep-in-test"]["severity"],
                    file=rel, line=i + 1,
                    message=RULES["thread-sleep-in-test"]["summary"],
                    snippet=line.strip()[:120],
                ))


# ---------- Output ------------------------------------------------------------

def emit_text(report: Report) -> str:
    out: list[str] = []
    if not report.findings:
        out.append(f"mule-lint: clean — no findings (root: {report.root})")
        return "\n".join(out)

    by_file: dict[str, list[Finding]] = {}
    for f in report.findings:
        by_file.setdefault(f.file, []).append(f)

    for path in sorted(by_file):
        out.append(path)
        for f in sorted(by_file[path], key=lambda x: x.line):
            out.append(f"  {f.severity:>7}  {path}:{f.line}  [{f.rule}] {f.message}")
            if f.snippet:
                out.append(f"           ↳ {f.snippet}")
    out.append("")
    out.append(f"summary: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return "\n".join(out)


def emit_json(report: Report) -> str:
    return json.dumps({
        "root": report.root,
        "errors": len(report.errors),
        "warnings": len(report.warnings),
        "findings": [f.asdict() for f in report.findings],
    }, indent=2)


def emit_junit(report: Report) -> str:
    rules_seen = sorted({f.rule for f in report.findings})
    cases: list[str] = []
    for rule in rules_seen:
        rule_findings = [f for f in report.findings if f.rule == rule]
        for f in rule_findings:
            cases.append(
                f'<testcase classname="mule-lint.{rule}" name="{f.file}:{f.line}">'
                f'<failure type="{f.severity}" message="{_xml_escape(f.message)}">'
                f'{_xml_escape(f.snippet)}'
                f'</failure></testcase>'
            )
    total = len(report.findings)
    failures = len(report.errors) + len(report.warnings)
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<testsuite name="mule-lint" tests="{total}" failures="{failures}">\n'
        + "\n".join(cases)
        + "\n</testsuite>\n"
    )


def _xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&apos;"))


# ---------- CLI ---------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mule-lint")
    parser.add_argument("path", nargs="?", default=".", help="Project path (defaults to cwd-resolved root)")
    parser.add_argument("--format", choices=["text", "json", "junit"], default="text")
    parser.add_argument("--rules", help="Comma-separated subset of rule ids to run; default: all")
    args = parser.parse_args(argv)

    root = find_project_root(Path(args.path))
    report = Report(root=str(root))

    enabled = set(RULES)
    if args.rules:
        enabled = set(r.strip() for r in args.rules.split(","))
        unknown = enabled - set(RULES)
        if unknown:
            print(f"mule-lint: unknown rule(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2

    if "hardcoded-credentials" in enabled:
        check_credentials(report, root)
    if any(r in enabled for r in ("missing-error-handler", "weak-flow-name", "production-basic-auth",
                                   "missing-http-timeouts", "inline-connector-config", "logger-string-concat")):
        check_xml_rules(report, root)
    if any(r in enabled for r in ("dw-1x-syntax", "dw-missing-output")):
        check_dataweave(report, root)
    if "thread-sleep-in-test" in enabled:
        check_thread_sleep(report, root)

    # Filter findings by enabled rule set (in case xml/dataweave checks emitted things outside the requested subset).
    report.findings = [f for f in report.findings if f.rule in enabled]

    if args.format == "json":
        print(emit_json(report))
    elif args.format == "junit":
        print(emit_junit(report))
    else:
        print(emit_text(report))

    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
