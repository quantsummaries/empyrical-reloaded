#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build pdoc HTML for ALL public modules of a package, bypassing __all__.

pdoc 16 only renders a standalone page for a submodule when the package's
`__all__` lists it (see pdoc/doc.py, Module.submodules). To document every
public module without changing the package's `__all__` (and therefore its
`import *` semantics), this script enumerates all importable modules from the
source tree (excluding private `_`-prefixed modules and `__main__`), and
passes the full list explicitly to pdoc so every module gets its own page.

Modules that cannot be imported (e.g. because they need an optional dependency
that is not installed, like TA-Lib for an example script) are skipped with a
warning instead of aborting the whole build.

Usage (from the repo root, with the repo venv's python):
    python docs/build_pdoc.py [-o docs/pdoc]

The package being documented is configured by PACKAGE below.
"""
from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys

PACKAGE = "empyrical"
# Path to the package source root, relative to this script.
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", PACKAGE)


def _is_private_segment(segment: str) -> bool:
    return segment.startswith("_")


def enumerate_modules() -> list[str]:
    """Return the fully-qualified name of every importable public module.

    Walks the package source directory: every `.py` file is a module, and
    every directory containing `__init__.py` is a (sub)package. Modules with
    an underscore-prefixed path segment are private and skipped; `.pyi` type
    stubs and `__main__` are skipped too.
    """
    root = os.path.abspath(SRC)
    names: set[str] = set()

    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        segs = [] if rel == "." else rel.split(os.sep)
        if any(_is_private_segment(s) for s in segs):
            continue
        base = PACKAGE + ("." + ".".join(segs) if segs else "")

        for fn in filenames:
            if fn == "__init__.py":
                # Directory is a package: add the package's own qualified name.
                names.add(base)
            elif fn.endswith(".py") and not fn.startswith("_"):
                names.add(base + "." + fn[:-3])
            # `.pyi` stubs, `__main__`, and underscore-prefixed private modules
            # are intentionally ignored.

    names.discard(PACKAGE + ".__main__")
    if PACKAGE not in names:
        names.add(PACKAGE)
    return sorted(names)


def filter_importable(mods: list[str]) -> tuple[list[str], list[tuple[str, str]]]:
    """Return (importable, [(module, error)]) by importing each module in this
    process. A module that raises on import is excluded so a single optional
    missing dependency cannot abort the whole documentation build."""
    ok: list[str] = []
    failed: list[tuple[str, str]] = []
    for m in mods:
        try:
            importlib.import_module(m)
            ok.append(m)
        except Exception as e:  # noqa: BLE001 - any import error excludes the module
            failed.append((m, repr(e)))
    return ok, failed


def main() -> int:
    ap = argparse.ArgumentParser(description="Build pdoc HTML for all public modules.")
    ap.add_argument("-o", "--output", default="docs/pdoc", help="pdoc output directory")
    args = ap.parse_args()

    all_mods = enumerate_modules()
    mods, failed = filter_importable(all_mods)
    print(f"[build_pdoc] {PACKAGE}: {len(all_mods)} module(s) enumerated, "
          f"{len(mods)} importable, {len(failed)} skipped")
    for m, err in failed:
        print(f"[build_pdoc] SKIP {m}: {err}")
    print("[build_pdoc] " + ", ".join(mods))

    # pdoc re-walks a passed package and re-imports every submodule it finds.
    # Tell pdoc to ignore the modules that failed to import, so a single missing
    # optional dependency cannot abort the whole build. Ignore specs must come
    # AFTER the packages that introduce the failing modules.
    ignores = [f"!{m}" for m, _ in failed]
    cmd = [sys.executable, "-m", "pdoc", "-o", args.output, *mods, *ignores]
    print("[build_pdoc] running:", " ".join(cmd[:6]), "...")
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
