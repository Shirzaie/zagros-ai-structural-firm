# -*- coding: utf-8 -*-
"""Diagnostic 4 (task 42): area offsets / local axes before & after SetHeight."""
import sys, os, shutil
from r5_common import *
from r6_test_heights import TD, SRC, HEIGHTS
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
e = None
try:
    a = os.path.join(TD, "T_h4.EDB"); shutil.copy2(SRC, a)
    e, m = connect(a); m.SetModelIsLocked(False)
    def dump(tag):
        for ar in ("17", "1", "4"):
            n, pts, _ = m.AreaObj.GetPoints(ar)
            p(tag, ar, m.AreaObj.GetLabelFromName(ar), [round(m.PointObj.GetCoordCartesian(q)[2], 3) for q in pts], "off", m.AreaObj.GetOffsets3(ar), "ax", m.AreaObj.GetLocalAxes(ar),
              "edge", m.AreaObj.GetEdgeConstraint(ar), "mod", m.AreaObj.GetModifiers(ar), "op", m.AreaObj.GetOpening(ar), "dia", m.AreaObj.GetDiaphragm(ar))
        for k in ("Area Assignments - Joint Offsets", "Area Assignments - Floor Auto Mesh Options", "Area Assignments - Local Axes", "Area Assignments - Section Properties"):
            t = table(m, k); p(tag, k, t.head(12).to_string())
    dump("BEFORE")
    for st, h in HEIGHTS.items():
        m.Story.SetHeight(st, h)
    dump("AFTER")
except Exception:
    import traceback; p(traceback.format_exc())
finish("r6_test4")
try: e.ApplicationExit(False)
except Exception: pass
os._exit(0)
