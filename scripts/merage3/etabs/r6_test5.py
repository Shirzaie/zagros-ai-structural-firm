# -*- coding: utf-8 -*-
"""Diagnostic 5 (task 42): stale shell mesh after SetHeight - try remedies, check element z + T."""
import sys, os, shutil
from r5_common import *
from r6_test_heights import TD, SRC, HEIGHTS
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

def chk(m, tag, run=False):
    if run:
        m.Analyze.SetRunCaseFlag("", True, True); p(tag, "Run", m.Analyze.RunAnalysis())
        m.DatabaseTables.SetLoadCasesSelectedForDisplay(list(m.LoadCases.GetNameList()[1]))
        mod = table(m, "Modal Participating Mass Ratios"); p(tag, "T", list(mod["Period"].head(3)))
    ej = table(m, "Objects and Elements - Joints")
    p(tag, "shell z", sorted(set(ej[ej["ObjType"] == "Shell"]["GlobalZ"].round(3))), "all z", sorted(set(ej["GlobalZ"].round(3))))

if __name__ == '__main__':
    e = None
    try:
        a = os.path.join(TD, "T_h5.EDB"); shutil.copy2(SRC, a)
        e, m = connect(a); m.SetModelIsLocked(False)
        for st, h in HEIGHTS.items():
            m.Story.SetHeight(st, h)
        p("CreateAnalysisModel", m.Analyze.CreateAnalysisModel()); chk(m, "A")
        m.SetModelIsLocked(False)
        for ar in m.AreaObj.GetNameList()[1]:
            pr = m.AreaObj.GetProperty(ar)[0]
            if pr and pr != "None":
                m.AreaObj.SetProperty(ar, pr)
        p("CreateAnalysisModel", m.Analyze.CreateAnalysisModel()); chk(m, "B")
        m.SetModelIsLocked(False)
        m.SelectObj.ClearSelection()
        for ar in m.AreaObj.GetNameList()[1]:
            m.AreaObj.SetSelected(ar, True)
        p("move up", m.EditGeneral.Move(0, 0, 0.01)); m.SelectObj.ClearSelection()
        for ar in m.AreaObj.GetNameList()[1]:
            m.AreaObj.SetSelected(ar, True)
        p("move down", m.EditGeneral.Move(0, 0, -0.01)); m.SelectObj.ClearSelection()
        p("stories", m.Story.GetStories()[2])
        z = sorted({round(m.PointObj.GetCoordCartesian(q)[2], 4) for q in m.PointObj.GetNameList()[1]}); p("point z", z)
        p("CreateAnalysisModel", m.Analyze.CreateAnalysisModel()); chk(m, "C", run=True)
    except Exception:
        import traceback; p(traceback.format_exc())
    finish("r6_test5")
    try: e.ApplicationExit(False)
    except Exception: pass
    os._exit(0)
