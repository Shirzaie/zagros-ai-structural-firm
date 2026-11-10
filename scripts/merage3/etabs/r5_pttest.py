# -*- coding: utf-8 -*-
"""test: move joints by editing 'Point Object Connectivity' (X, Y) instead of EditGeneral.Move -> do labels survive? no save"""
import os, sys
from r5_common import *
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
e, m = connect()
p("reopen", m.File.OpenFile(EDB)); m.SetPresentUnits(6)
key = "Point Object Connectivity"
db = m.DatabaseTables
fi = db.GetAllFieldsInTable(key, 0, 0, [], [], [], [], [])
keys, names = list(fi[2]), list(fi[3])
r = db.GetTableForEditingArray(key, "")
ver, fields, n, data = r[0], list(r[1]), r[2], list(r[3])
nf = len(fields)
rows = [data[i * nf:(i + 1) * nf] for i in range(n)]
ix, iy = fields.index("X"), fields.index("Y")
f2 = lambda s: float(str(s).replace("/", "."))
fmt = lambda v: f"{v:.4f}".rstrip("0").rstrip(".").replace(".", "/")
k = 0
for row in rows:
    x, y = f2(row[ix]), f2(row[iy])
    ny = 18.81 if abs(y - 18.75) < 1e-4 else 20.01 if abs(y - 19.95) < 1e-4 else y
    nx = 2.507 if abs(x - 2.35) < 1e-4 and ny in (18.81, 20.01) else x
    if (nx, ny) != (x, y):
        row[ix], row[iy] = fmt(nx), fmt(ny); k += 1
p("changed", k)
fl = [names[keys.index(f)] for f in fields]
flat = [v if v is not None else "" for row in rows for v in row]
p("set", db.SetTableForEditingArray(key, ver, fl, n, flat)[-1])
res = db.ApplyEditedTables(True)
p("apply", res[0], res[1], res[2], res[3], str(res[4]).split("SUMMARY LOG")[-1].replace("\r\n", " | ")[:800])
pts, frs, ars = geometry(m)
p(sorted({v["label"] for v in frs.values()}))
p([(v["label"], v["story"], (v["xi"], v["yi"]), (v["xj"], v["yj"])) for v in frs.values() if v["story"] == "Story1" and (v["yi"] > 18 or v["yj"] > 18)])
p("areas", [(v["label"], v["xy"]) for v in ars.values() if v["story"] == "Story1"])
finish("pttest")
os._exit(0)
