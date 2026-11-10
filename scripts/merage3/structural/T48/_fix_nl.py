# -*- coding: utf-8 -*-
"""one-off: join string literals that were split by a real newline (shell turned \\n into a newline)"""
import os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "t48_report.py")
L = open(p, encoding="utf-8").read().split("\n")
out, k = [], 0
while k < len(L):
    line = L[k]
    if line.lstrip().startswith(('w("', 'w(f"')) and line.count('"') % 2 == 1 and k + 1 < len(L) and L[k + 1].startswith('")'):
        out.append(line + "\\n" + L[k + 1]); k += 2; continue
    if line.lstrip().startswith(('w("', 'w(f"')) and line.count('"') % 2 == 1 and k + 1 < len(L) and L[k + 1].startswith('**'):
        out.append(line + "\\n" + L[k + 1]); k += 2; continue
    out.append(line); k += 1
open(p, "w", encoding="utf-8").write("\n".join(out))
print("joined", len(L) - len(out))
