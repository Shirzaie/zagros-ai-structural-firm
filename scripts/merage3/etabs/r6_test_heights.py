# -*- coding: utf-8 -*-
"""Diagnostic (task 42): run Rev5 copy as-is and with only SetHeight, compare T / story stiffness / drift.
Works on copies in C:\\ZagrosTemp\\r6test (Rev5 and Rev6 untouched).  python r6_test_heights.py [mode]"""
import sys, os, json, shutil
from r5_common import *
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
TD = r"C:\ZagrosTemp\r6test"
os.makedirs(TD, exist_ok=True)
SRC = os.path.join(HERE, "_backup", "Merage3_Rev5_before_T42.EDB")
HEIGHTS = {"Story1": 4.00, "Story2": 3.40, "Story3": 3.40, "Story4": 3.40, "Story5": 3.30}


def run(m, tag):
    m.Analyze.SetRunCaseFlag("", True, True)
    p(tag, "RunAnalysis", m.Analyze.RunAnalysis())
    db = m.DatabaseTables
    db.SetLoadCasesSelectedForDisplay(list(m.LoadCases.GetNameList()[1]))
    mod = table(m, "Modal Participating Mass Ratios")
    p(tag, "T", list(mod["Period"].head(4)), list(mod["UX"].head(4)), list(mod["UY"].head(4)))
    ss = table(m, "Story Stiffness")
    p(tag, "stiff\n", ss[ss["Output Case"].isin(["EXP", "EYP"])][["Story", "Output Case", "ShearX", "DriftX", "StiffX", "ShearY", "DriftY", "StiffY"]].to_string())
    ms = table(m, "Mass Summary by Story"); p(tag, "mass\n", ms.to_string())
    dr = table(m, "Story Drifts"); d = dr[dr["Output Case"].isin(["EXP", "EYP"])]
    p(tag, "drift\n", d.groupby(["Story", "Direction"])["Drift"].max().to_string())
    ec = table(m, "Frame Assignments - End Length Offsets"); p(tag, "offsets\n", ec.head(8).to_string())
    rl = table(m, "Frame Assignments - Releases and Partial Fixity"); p(tag, "releases\n", rl.head(20).to_string())
    md = table(m, "Frame Assignments - Property Modifiers"); p(tag, "mods\n", md.to_string())
    po = table(m, "P-Delta Options"); p(tag, "pdelta", po.to_string())
    pr = table(m, "Joint Assignments - Restraints"); p(tag, "restraints\n", pr.to_string())
    for f in ("4", "9", "56", "61"):
        p(tag, f, "GetPoints", m.FrameObj.GetPoints(f), "offsets", m.FrameObj.GetEndLengthOffset(f), "mods", m.FrameObj.GetModifiers(f), "rel", m.FrameObj.GetReleases(f))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    e = None
    try:
        a = os.path.join(TD, "T_rev5.EDB"); b = os.path.join(TD, "T_h.EDB")
        shutil.copy2(SRC, a); shutil.copy2(SRC, b)
        e, m = connect(a)
        m.SetModelIsLocked(False)
        run(m, "REV5")
        m.SetModelIsLocked(False)
        p("open b", m.File.OpenFile(b)); m.SetPresentUnits(6); m.SetModelIsLocked(False)
        for st, h in HEIGHTS.items():
            p("SetHeight", st, m.Story.SetHeight(st, h))
        run(m, "HEIGHTS")
    except Exception:
        import traceback; p(traceback.format_exc())
    finish("r6_test_heights")
    try:
        e.ApplicationExit(False)
    except Exception:
        pass
    os._exit(0)
