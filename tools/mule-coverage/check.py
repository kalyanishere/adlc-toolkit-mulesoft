#!/usr/bin/env python3
"""mule-coverage — assert MUnit coverage meets the project's coverage floor.

Reads the MUnit coverage summary JSON emitted by `mvn munit:coverage-report`
and compares against the floors declared in .adlc/config.yml under
mulesoft.coverage.

Exit codes:
  0  pass
  1  coverage shortfall
  2  missing report, missing config, or other error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


COVERAGE_PATHS = [
    "target/site/munit/coverage/munit-summary.json",
    "target/site/munit/coverage/coverage-summary.json",
]


def find_project_root(start: Path) -> Path:
    p = start.resolve()
    while p != p.parent:
        if (p / "pom.xml").exists():
            return p
        p = p.parent
    return start.resolve()


def load_config(root: Path) -> dict:
    """Tiny YAML reader that handles the subset we need (no external deps).

    Reads the `mulesoft.coverage` block as a flat mapping. If config.yml is
    missing or unparseable, returns an empty dict — caller falls back to defaults.
    """
    cfg_path = root / ".adlc" / "config.yml"
    if not cfg_path.exists():
        return {}
    text = cfg_path.read_text(encoding="utf-8", errors="replace")
    out: dict = {}
    in_mulesoft = False
    in_coverage = False
    coverage_indent = -1
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)

        if stripped.startswith("mulesoft:"):
            in_mulesoft = True
            in_coverage = False
            coverage_indent = -1
            continue
        if in_mulesoft and indent == 0 and not stripped.startswith("mulesoft:"):
            # Left the mulesoft block.
            in_mulesoft = False
            continue
        if in_mulesoft and stripped.startswith("coverage:"):
            in_coverage = True
            coverage_indent = indent
            continue
        if in_coverage:
            if indent <= coverage_indent and stripped:
                in_coverage = False
            else:
                m = re.match(r"^([A-Za-z_][\w_]*)\s*:\s*(.*?)\s*(#.*)?$", stripped)
                if m:
                    key, val = m.group(1), m.group(2).strip()
                    val = val.strip('"').strip("'")
                    if val.lower() in ("true", "false"):
                        out[key] = val.lower() == "true"
                    else:
                        try:
                            out[key] = int(val)
                        except ValueError:
                            out[key] = val
    return out


def load_coverage(root: Path) -> dict | None:
    for rel in COVERAGE_PATHS:
        p = root / rel
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
    return None


def diff_flow_names(root: Path) -> set[str]:
    """Best-effort: list flow names that appear in `git diff --name-only` for
    files under src/main/mule/. Falls back to empty set when git is unavailable."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD~1...HEAD"],
            cwd=str(root),
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()
    flows: set[str] = set()
    for rel in out.splitlines():
        if not rel.startswith("src/main/mule/"):
            continue
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'<flow\s+[^>]*name="([^"]+)"', text):
            flows.add(m.group(1))
    return flows


def overall_percent(report: dict) -> float | None:
    # MUnit summary shape varies by version; try several keys.
    for key_path in (
        ["overall", "coverage"],
        ["summary", "coverage"],
        ["coverage"],
        ["overallCoverage"],
        ["totalCoverage"],
    ):
        cur: dict | float | None = report
        try:
            for k in key_path:
                cur = cur[k]  # type: ignore[index]
            if isinstance(cur, (int, float)):
                return float(cur)
            if isinstance(cur, str):
                return float(cur.rstrip("%"))
        except (KeyError, TypeError, ValueError):
            continue
    return None


def per_flow_percents(report: dict) -> dict[str, float]:
    flows: list[dict] = []
    for key in ("flows", "perFlow", "perFlowCoverage"):
        if key in report and isinstance(report[key], list):
            flows = report[key]
            break
    out: dict[str, float] = {}
    for f in flows:
        name = f.get("name") or f.get("flowName") or f.get("flow")
        cov = f.get("coverage") or f.get("percent") or f.get("coveragePercent")
        if name is None or cov is None:
            continue
        try:
            out[str(name)] = float(str(cov).rstrip("%"))
        except ValueError:
            continue
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mule-coverage")
    parser.add_argument("path", nargs="?", default=".", help="Project path")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    root = find_project_root(Path(args.path))
    cfg = load_config(root)

    munit_floor = cfg.get("munit_floor", 80)
    flow_floor = cfg.get("flow_floor", 75)
    diff_only = bool(cfg.get("diff_only", False))
    mode = cfg.get("mode", "brownfield")

    report = load_coverage(root)
    if report is None:
        msg = (
            "mule-coverage: no MUnit coverage report found.\n"
            f"  → looked for: {', '.join(COVERAGE_PATHS)}\n"
            "  → run `mvn munit:coverage-report` first"
        )
        if args.format == "json":
            print(json.dumps({"status": "missing-report"}))
        else:
            print(msg, file=sys.stderr)
        return 2

    overall = overall_percent(report)
    flow_cov = per_flow_percents(report)

    failures: list[str] = []
    summary: dict = {
        "root": str(root),
        "mode": mode,
        "munit_floor": munit_floor,
        "flow_floor": flow_floor,
        "diff_only": diff_only,
        "overall": overall,
        "flow_count": len(flow_cov),
    }

    if not diff_only:
        if overall is None:
            failures.append("could not parse overall coverage from MUnit report")
        elif overall < munit_floor:
            failures.append(f"overall coverage {overall}% < munit_floor {munit_floor}%")

    if mode == "brownfield":
        diff_flows = diff_flow_names(root)
        summary["diff_flows"] = sorted(diff_flows)
        for name in diff_flows:
            cov = flow_cov.get(name)
            if cov is None:
                failures.append(f"changed flow '{name}' has no coverage entry")
            elif cov < flow_floor:
                failures.append(f"changed flow '{name}' coverage {cov}% < flow_floor {flow_floor}%")

    summary["failures"] = failures
    summary["status"] = "pass" if not failures else "fail"

    if args.format == "json":
        print(json.dumps(summary, indent=2))
    else:
        print(f"mule-coverage: {summary['status']} (root: {root})")
        print(f"  mode={mode} munit_floor={munit_floor} flow_floor={flow_floor} diff_only={diff_only}")
        if overall is not None:
            print(f"  overall: {overall}%")
        if failures:
            print("  failures:")
            for f in failures:
                print(f"    - {f}")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
