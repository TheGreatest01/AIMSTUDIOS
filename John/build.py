#!/usr/bin/env python3
"""Builds John/pine/John.pine (the file pasted into TradingView) from the module files in John/src/.

Pine Script has no local imports, so the indicator is kept as one module per file in John/src/ and
joined here in the order listed in John/src/manifest.txt. Edit the modules, never John.pine itself.

Usage:
    python3 John/build.py            rebuild John/pine/John.pine
    python3 John/build.py --check    exit 1 if John.pine doesn't match the modules (e.g. it was hand-edited)
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "pine" / "John.pine"


def build() -> str:
    manifest = (SRC / "manifest.txt").read_text(encoding="utf-8").splitlines()
    order = [line.strip() for line in manifest if line.strip() and not line.strip().startswith("#")]
    on_disk = {p.name for p in SRC.glob("*.pine")}
    problems = []
    missing = [name for name in order if name not in on_disk]
    if missing:
        problems.append("listed in manifest but missing: " + ", ".join(missing))
    unlisted = sorted(on_disk - set(order))
    if unlisted:
        problems.append("in src/ but not in manifest: " + ", ".join(unlisted))
    dupes = sorted({name for name in order if order.count(name) > 1})
    if dupes:
        problems.append("listed more than once: " + ", ".join(dupes))
    if problems:
        sys.exit("build.py: " + "; ".join(problems))
    parts = []
    for name in order:
        text = (SRC / name).read_text(encoding="utf-8")
        parts.append(text if text.endswith("\n") else text + "\n")
    return "".join(parts)


def main() -> None:
    built = build()
    current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    if "--check" in sys.argv[1:]:
        if built != current:
            sys.exit("build.py: John.pine is out of date with John/src/ — run `python3 John/build.py`")
        print("John.pine matches John/src/")
        return
    if built != current:
        OUT.write_text(built, encoding="utf-8")
        print(f"John.pine rebuilt: {built.count(chr(10))} lines")
    else:
        print("John.pine already up to date")


if __name__ == "__main__":
    main()
