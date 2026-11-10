# -*- coding: utf-8 -*-
"""reopen Rev5 from disk (discard in-memory changes) and test the grid-line table edit; does NOT save"""
import os, sys
from r5_common import *
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
mode = sys.argv[1] if len(sys.argv) > 1 else "all"
e, m = connect()
m.File.OpenFile(EDB)
m.SetPresentUnits(6)
key = "Grid Definitions - Grid Lines"
db = m.DatabaseTables
fi = db.GetAllFieldsInTable(key, 0, 0, [], [], [], [], [])
p("fields", fi); fi = [None, None, None, list(fi[2]) if mode != "names" else list(fi[3])]
r = db.GetTableForEditingArray(key, "")
ver, fields, n, data = r[0], list(r[1]), r[2], list(r[3])
p("edit", fields, n, data[:22])
nf = len(fields)
rows = [data[i * nf:(i + 1) * nf] for i in range(n)]
for row in rows:
    if row[1].startswith("Y") and row[2] == "4": row[3] = "18/81"
    if row[1].startswith("Y") and row[2] == "5": row[3] = "20/01"
if True:
    fl = list(fi[3]) if mode != "keysonly" else [f for f in fields]
    flat = [v if v is not None else "" for row in rows for v in row]
p("write fields", fl)
p("set", db.SetTableForEditingArray(key, ver, fl, n, flat)[0])
res = db.ApplyEditedTables(True)
p("apply", res[0], res[1], res[2], res[3])
p(str(res[4]).split("DETAILED LOG")[-1].replace("\r\n", " | ")[:2000])
p(table(m, key).to_string())
finish("gridtest")
os._exit(0)
