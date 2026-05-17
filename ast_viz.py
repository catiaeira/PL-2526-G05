#!/usr/bin/env python3
"""
Fortran AST Raw Structure Visualizer
Shows the actual Python data structure produced by the parser.

Usage:
  python ast_viz.py              # built-in sample
  python ast_viz.py file.f       # a Fortran source file
  cat file.f | python ast_viz.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parser as fortran_parser

# ANSI
R = "\033[0m"
TREE  = "\033[38;5;238m"   # dark grey  – branch lines
KEY   = "\033[94m"         # blue       – dict keys
STR   = "\033[32m"         # green      – string values
NUM   = "\033[38;5;180m"   # tan        – int / float
BOOL  = "\033[35m"         # magenta    – bool
NONE  = "\033[90m"         # dark grey  – None
LIST  = "\033[36m"         # cyan       – list/dict markers
TYPE  = "\033[33m"         # yellow     – type annotations

def t(color, text): return color + str(text) + R

PIPE  = t(TREE, "│  ")
TEE   = t(TREE, "├─ ")
LAST_ = t(TREE, "└─ ")
BLANK = "   "

def _branch(prefix, is_last):
    return (prefix + (LAST_ if is_last else TEE),
            prefix + (BLANK  if is_last else PIPE))

def render(value, prefix="", is_last=True, label=None):
    """Recursively render any Python value as a tree."""
    line, child = _branch(prefix, is_last)
    lbl = (t(KEY, label) + t(TREE, ": ")) if label is not None else ""

    if value is None:
        print(line + lbl + t(NONE, "None"))

    elif isinstance(value, bool):
        print(line + lbl + t(BOOL, repr(value)))

    elif isinstance(value, (int, float)):
        print(line + lbl + t(NUM, repr(value)))

    elif isinstance(value, str):
        print(line + lbl + t(STR, repr(value)))

    elif isinstance(value, list):
        print(line + lbl + t(LIST, "list") + t(TREE, f"  [{len(value)} items]"))
        for i, item in enumerate(value):
            render(item, child, is_last=(i == len(value) - 1), label=str(i))

    elif isinstance(value, dict):
        # show type/node tag inline if present, for quick orientation
        #tag = value.get("type") or value.get("node") or ""
        #tag_str = ("  " + t(TYPE, f"<{tag}>")) if tag else ""
        tag_str = ""
        print(line + lbl + t(LIST, "dict") + tag_str)
        keys = list(value.keys())
        for i, k in enumerate(keys):
            render(value[k], child, is_last=(i == len(keys) - 1), label=k)

    else:
        print(line + lbl + t(NUM, repr(value)))


SAMPLE = """\
      PROGRAM MAIN
      INTEGER A, B
      READ(*,*) A
      B = A * 10
      IF (B .GT. 50) THEN
          PRINT *, 'HIGH'
      ELSE
          PRINT *, 'LOW'
      ENDIF
5     DO 20 I = 1, 5
          CALL LOGIT(I)
   20 CONTINUE
      END

      SUBROUTINE LOGIT(VAL)
      PRINT *, VAL
      END
"""

def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            source = f.read()
    elif not sys.stdin.isatty():
        source = sys.stdin.read()
    else:
        source = SAMPLE

    ast = fortran_parser.parse(source)
    print()
    render(ast, label="ast")
    print()

if __name__ == "__main__":
    main()
