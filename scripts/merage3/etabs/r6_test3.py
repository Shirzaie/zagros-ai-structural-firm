# -*- coding: utf-8 -*-
"""Diagnostic 3 (task 42): after SetHeight, shells mesh at old z. Try forcing area re-mesh (ChangeConnectivity / SetProperty)."""
import sys, os, shutil
from r5_common import *
from r6_test_heights import TD, SRC, HEIGHTS
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

def short(m, tag):
    m.Analyze.SetRunCaseFlag("", True, True)
    p(tag, "RunAnalysis", m.Analyze.RunAnalysis())
    m.DatabaseTables.SetLoadCasesSelectedForDisplay(list(m.LoadCases.GetNameList()[1]))
    mod = table(m, "Modal Participating Mass Ratios"); p(tag, "T", list(mod["Period"].head(3)))
    ss = table(m, "Story Stiffness"); p(tag, ss[ss["Output Case"] == "EXP"][["Story", "StiffX"]].to_string())
    ej = table(m, "Objects and Elements - Joints")
    p(tag, "shell node z:", sorted(set(ej[ej["ObjType"] == "Shell"]["GlobalZ"].round(3))) if "ObjType" in ej else ej.columns.tolist())
    ms = table(m, "Mass Summary by Story"); p(tag, ms.to_string())

e = None
try:
    a = os.path.join(TD, "T_h3.EDB"); shutil.copy2(SRC, a)
    e, m = connect(a); m.SetModelIsLocked(False)
    for st, h in HEIGHTS.items():
        m.Story.SetHeight(st, h)
    names = m.AreaObj.GetNameList()[1]
    for ar in names:
        n, pts, _ = m.AreaObj.GetPoints(ar)
        p(ar, [m.PointObj.GetCoordCartesian(q)[2] for q in pts], "chg", m.EditArea.ChangeConnectivity(ar, n, list(pts)))
    short(m, "CHG")
except Exception:
    import traceback; p(traceback.format_exc())
finish("r6_test3")
try: e.ApplicationExit(False)
except Exception: pass
os._exit(0)
