#!/usr/bin/env python3
"""Validate .claude/agents/*.md against the official Claude Code subagent format + DMW rules.

python workflow/tools/validate_agents.py      (exit 0 = all valid)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / ".claude" / "agents"
KNOWN_TOOLS = {"Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch", "WebSearch", "TodoWrite",
               "NotebookEdit", "Skill", "Agent", "Task"}
MODELS = {"inherit", "sonnet", "opus", "haiku", "fable"}
COLORS = {"red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"}
SECTIONS = ["## Responsibilities", "## Input format", "## Output format", "## Files you own",
            "## Capability status", "## Shared rules", "## Brand rules"]
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")


def split_tools(s: str) -> list[str]:
    out, depth, cur = [], 0, ""
    for ch in s:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            out.append(cur.strip()); cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def main() -> int:
    errors, rows, owners = [], [], {}
    files = sorted(AGENTS.glob("*.md"))
    names = set()
    agent_targets: dict[str, list[str]] = {}
    for f in files:
        text = f.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
        if not m:
            errors.append(f"{f.name}: missing YAML frontmatter"); continue
        try:
            fm = yaml.safe_load(m.group(1))
        except yaml.YAMLError as e:
            errors.append(f"{f.name}: YAML error {e}"); continue
        body = m.group(2)
        name = fm.get("name")
        if not name or not NAME_RE.match(name):
            errors.append(f"{f.name}: invalid name {name!r}")
        if name != f.stem:
            errors.append(f"{f.name}: name '{name}' != filename")
        if name in names:
            errors.append(f"{f.name}: duplicate name")
        names.add(name)
        desc = fm.get("description", "")
        if not isinstance(desc, str) or len(desc) < 40:
            errors.append(f"{f.name}: description missing/too short")
        if fm.get("model") not in MODELS:
            errors.append(f"{f.name}: bad model {fm.get('model')}")
        if fm.get("color") not in COLORS:
            errors.append(f"{f.name}: bad color {fm.get('color')}")
        tools = split_tools(fm.get("tools", ""))
        if not tools:
            errors.append(f"{f.name}: tools missing")
        for t in tools:
            base = t.split("(")[0]
            if base not in KNOWN_TOOLS:
                errors.append(f"{f.name}: unknown tool {t}")
            if base in ("Agent", "Task"):
                inner = re.findall(r"\((.*)\)", t)
                agent_targets[name] = [x.strip() for x in inner[0].split(",")] if inner else ["*"]
        for s in SECTIONS:
            if s not in body:
                errors.append(f"{f.name}: missing section '{s}'")
        own = re.search(r"## Files you own.*?\n((?:- .*\n)+)", body)
        for line in (own.group(1).splitlines() if own else []):
            path = line[2:].strip("` ")
            if path in owners and owners[path] != name:
                errors.append(f"{f.name}: owns {path} which is also owned by {owners[path]}")
            owners[path] = name
        rows.append((name, fm.get("model"), len(tools), "Agent" in "".join(tools)))
    # delegation checks
    if "master-director" not in agent_targets:
        errors.append("master-director cannot delegate (no Agent tool)")
    else:
        tgt = set(agent_targets["master-director"])
        missing = (names - {"master-director"}) - tgt
        unknown = tgt - names
        if missing:
            errors.append(f"master-director cannot reach: {sorted(missing)}")
        if unknown:
            errors.append(f"master-director lists unknown agents: {sorted(unknown)}")
    extra = [n for n in agent_targets if n != "master-director"]
    if extra:
        errors.append(f"specialists must not spawn agents: {extra}")
    reg = json.loads((ROOT / "workflow" / "agent-registry.json").read_text(encoding="utf-8"))
    if {a["name"] for a in reg["agents"]} != names:
        errors.append("agent-registry.json does not match .claude/agents/")
    for n, model, nt, ag in rows:
        print(f"OK  {n:28} model={model:8} tools={nt}{'  (delegates)' if ag else ''}")
    print(f"\nAgents: {len(files)}  unique names: {len(names)}  owned paths: {len(owners)}")
    if errors:
        print("\nERRORS:")
        for e in errors:
            print(" -", e)
        return 1
    print("VALID: all agent configurations passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
