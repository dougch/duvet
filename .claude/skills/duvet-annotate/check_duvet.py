#!/usr/bin/env python3
"""Summarize CITED vs UNCITED requirements per spec from a duvet JSON report.

Usage: python3 check_duvet.py [/tmp/duvet-report.json]

The v0.4 JSON report keys requirements by index into `statuses`; a requirement
is cited when its status entry carries a "citation" key (uncited entries carry
"incomplete" instead).
"""
import json
import re
import sys
from collections import defaultdict

path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/duvet-report.json"
report = json.load(open(path))
statuses = report["statuses"]

agg = defaultdict(lambda: defaultdict(int))
for spec_path, spec in report["specifications"].items():
    m = re.search(r"(rfc\d+)", spec_path)
    name = m.group(1) if m else spec_path.rsplit("/", 1)[-1]
    for idx in spec["requirements"]:
        status = statuses.get(str(idx), {})
        agg[name]["CITED" if "citation" in status else "UNCITED"] += 1

print(f"{'spec':<14} {'CITED':>6} {'UNCITED':>8}")
total_cited = total_uncited = 0
for name in sorted(agg):
    cited, uncited = agg[name]["CITED"], agg[name]["UNCITED"]
    total_cited += cited
    total_uncited += uncited
    print(f"{name[:14]:<14} {cited:>6} {uncited:>8}")
print(f"{'TOTAL':<14} {total_cited:>6} {total_uncited:>8}")
