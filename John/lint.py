#!/usr/bin/env python3
"""Catches Pine compile errors that are easy to miss by eye, on the built John/pine/John.pine:

  1. A function modifying a global variable (`x := …`, `x += …` inside a function body). Pine refuses
     this; globals must be changed at global scope, or held in an array/object whose contents change.
  2. A user function called before it is defined. Pine needs definitions first.
  3. A wrapped line indented by a multiple of 4 spaces (Pine reads it as a new block, not a continuation).
  4. A function using a global variable that is declared further down the file.

Usage:  python3 John/lint.py      (exit 1 and a list of problems if any are found)
"""
import pathlib
import re
import sys

SRC = pathlib.Path(__file__).resolve().parent / "pine" / "John.pine"
lines = SRC.read_text(encoding="utf-8").splitlines()

FUNC_HDR = re.compile(r"^([A-Za-z_]\w*)\(([^)]*)\)\s*=>")
DECL = re.compile(r"^\s*(?:var\s+|varip\s+)?(?:const\s+)?(?:[A-Za-z_][\w.]*(?:<[^>]*>)?\s+)?([A-Za-z_]\w*)\s*=(?!=)")
TUPLE = re.compile(r"^\s*\[([^\]]+)\]\s*=(?!=)")
FOR_VAR = re.compile(r"^\s*for\s+([A-Za-z_]\w*)\s*(?:=|in\b)")
ASSIGN = re.compile(r"^\s*([A-Za-z_]\w*)\s*(:=|\+=|-=|\*=|/=)")
KEYWORDS = {"if", "else", "for", "while", "switch", "var", "varip", "type", "export", "import", "method", "return"}

problems = []

# Globals and function definitions (column 0 only).
globals_, func_line, global_line = set(), {}, {}
for i, ln in enumerate(lines):
    if ln.startswith((" ", "\t", "//")) or not ln.strip():
        continue
    m = FUNC_HDR.match(ln)
    if m:
        func_line[m.group(1)] = i
        continue
    m = TUPLE.match(ln)
    if m:
        for n in m.group(1).split(","):
            globals_.add(n.strip())
            global_line.setdefault(n.strip(), i)
        continue
    m = DECL.match(ln)
    if m and m.group(1) not in KEYWORDS:
        globals_.add(m.group(1))
        global_line.setdefault(m.group(1), i)

# 1 · globals modified inside function bodies.
i = 0
while i < len(lines):
    m = FUNC_HDR.match(lines[i])
    if not m:
        i += 1
        continue
    name = m.group(1)
    local = {p.split()[-1].split("=")[0].strip() for p in m.group(2).split(",") if p.strip()}
    j = i + 1
    while j < len(lines) and (lines[j].startswith(" ") or not lines[j].strip()):
        body = lines[j]
        code = body.split("//")[0]
        for rx in (FOR_VAR, TUPLE):
            mm = rx.match(code)
            if mm:
                local.update(n.strip() for n in mm.group(1).split(","))
        mm = DECL.match(code)
        if mm and not ASSIGN.match(code):
            local.add(mm.group(1))
        mm = ASSIGN.match(code)
        if mm and mm.group(1) in globals_ and mm.group(1) not in local:
            problems.append(f"line {j + 1}: function {name}() modifies global '{mm.group(1)}'")
        # 4 · a global used here but declared further down the file
        for ident in re.findall(r"(?<![\w.])([A-Za-z_]\w*)\b(?!\s*\()", re.sub(r'"[^"]*"', '""', code)):
            if ident in global_line and ident not in local and global_line[ident] > i:
                problems.append(f"line {j + 1}: function {name}() uses global '{ident}' declared later (line {global_line[ident] + 1})")
        j += 1
    i = j

# 2 · user functions called before their definition.
CALL = re.compile(r"(?<![\w.])([A-Za-z_]\w*)\(")
for i, ln in enumerate(lines):
    code = re.sub(r'"[^"]*"', '""', ln.split("//")[0])
    for name in CALL.findall(code):
        if name in func_line and func_line[name] > i and not FUNC_HDR.match(ln):
            problems.append(f"line {i + 1}: {name}() is called before it is defined (line {func_line[name] + 1})")

# 3 · continuation lines indented by a multiple of 4.
for i in range(1, len(lines)):
    prev = lines[i - 1].split("//")[0].rstrip()
    if prev.endswith(("+", ",", "?", ":", "=", "(", " and", " or")) and not lines[i - 1].lstrip().startswith("//"):
        ind = len(lines[i]) - len(lines[i].lstrip(" "))
        if lines[i].strip() and ind % 4 == 0:
            problems.append(f"line {i + 1}: wrapped line indented by a multiple of 4 ({ind} spaces)")

if problems:
    print("\n".join(problems))
    sys.exit(1)
print(f"lint: no problems in {SRC.name} ({len(lines)} lines, {len(func_line)} functions, {len(globals_)} globals)")
