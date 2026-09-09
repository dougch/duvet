#!/usr/bin/env python3
"""Summarize requirement coverage per spec from a duvet JSON report.

Usage: python3 check_duvet.py [/tmp/duvet-report.json]

The v0.4 JSON report keys requirements by index into `statuses`. The status
entry's keys are what distinguish the outcomes, and there are four that matter:

  "citation"    -> CITED. Code is annotated as satisfying the requirement.
  "exception"   -> EXCPT. Annotated `type=exception`; duvet treats this as
                   *resolved* and drops it from the incomplete pool, so it
                   must not be lumped in with UNCITED.
  "todo"        -> TODO. Annotated `type=TODO`. Still carries "incomplete",
                   so it is genuinely uncited, but it is a *known* gap rather
                   than an unexamined one. Reported separately for that reason.
  "incomplete"  -> UNCITED, with no annotation of any kind.

Collapsing EXCPT and TODO into UNCITED (as this script originally did) hides
exactly the requirements a reviewer most needs to see.
"""
import json
import re
import sys
from collections import defaultdict

COLUMNS = ("CITED", "TODO", "EXCPT", "UNCITED")


def classify(status):
    if "citation" in status:
        return "CITED"
    if "exception" in status:
        return "EXCPT"
    if "todo" in status:
        return "TODO"
    return "UNCITED"


path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/duvet-report.json"
report = json.load(open(path))
statuses = report["statuses"]

agg = defaultdict(lambda: defaultdict(int))
for spec_path, spec in report["specifications"].items():
    m = re.search(r"(rfc\d+)", spec_path)
    name = m.group(1) if m else spec_path.rsplit("/", 1)[-1]
    for idx in spec["requirements"]:
        agg[name][classify(statuses.get(str(idx), {}))] += 1

header = f"{'spec':<14}" + "".join(f"{c:>8}" for c in COLUMNS)
print(header)
totals = defaultdict(int)
for name in sorted(agg):
    row = agg[name]
    for c in COLUMNS:
        totals[c] += row[c]
    print(f"{name[:14]:<14}" + "".join(f"{row[c]:>8}" for c in COLUMNS))
print("-" * len(header))
print(f"{'TOTAL':<14}" + "".join(f"{totals[c]:>8}" for c in COLUMNS))
