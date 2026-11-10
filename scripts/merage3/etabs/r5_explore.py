# -*- coding: utf-8 -*-
"""Dump geometry, grids, slab props and loads of the Rev5 copy (before any change)."""
import sys, json, os
from r5_common import *
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
e, m = connect()
pts, frs, ars = geometry(m)
json.dump({"points": pts, "frames": frs, "areas": ars}, open(os.path.join(HERE, "geom_before.json"), "w", encoding="utf-8"), indent=0, ensure_ascii=False)
gl = table(m, "Grid Definitions - Grid Lines")
p("GRID LINES", gl.to_string())
r = m.DatabaseTables.GetTableForEditingArray("Grid Definitions - Grid Lines", "")
p("grid edit fields", list(r[1]), "rows", r[2])
for prop in sorted({a["prop"] for a in ars.values()}):
    try:
        p("slab prop", prop, m.PropArea.GetSlab(prop))
    except Exception as ex:
        p("slab prop", prop, "err", ex)
for k in ("Area Assignments - Slab One-Way Load Distribution", "Area Assignments - Local Axes", "Frame Assignments - Section Properties"):
    t = table(m, k)
    p(k, len(t), t.head(40).to_string() if not t.empty else "")
for k, v in ars.items():
    if v["story"] == "Story1":
        p("area", k, v["label"], v["prop"], v["A"], v["xy"])
for k, v in frs.items():
    if v["story"] in ("Story1", "Base") or v["kind"] == "column" and v["story"] == "Story1":
        p("frame", k, v["label"], v["kind"], v["sec"], (v["xi"], v["yi"]), (v["xj"], v["yj"]), v["L"])
p("point loads on frames:", sum(m.FrameObj.GetLoadPoint(f)[0] for f in frs))
p("joint loads:", sum(m.PointObj.GetLoadForce(q)[0] for q in pts))
finish("explore")
os._exit(0)
