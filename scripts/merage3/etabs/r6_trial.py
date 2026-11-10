# -*- coding: utf-8 -*-
"""Task 42 trials on COPIES (C:\ZagrosTemp\r6trial) of Merage3_Rev6.EDB - options for the boss, Rev6 untouched.
 A: Story1 columns 16phi16 -> 16phi20 (same 50x50)   B: A + cantilevers B3/B5/B6 torsion modifier J = 0.1 (compatibility torsion,
 ACI 22.7.3.2 analogue)   C: Story1 columns 55x55 / 16phi20"""
import sys, os, shutil, json
from r5_common import *
import r5_run as R5
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
TD = r"C:\ZagrosTemp\r6trial"; os.makedirs(TD, exist_ok=True)
SRC = os.path.join(HERE, "Merage3_Rev6.EDB")


def mk_col(m, base, new, size, t2=None):
    rect = m.PropFrame.GetRectangle(base); rb = m.PropFrame.GetRebarColumn(base)
    p(" base", rect, rb)
    t = t2 or rect[2]
    p(" rect", new, m.PropFrame.SetRectangle(new, rect[1], t, t))
    args = list(rb[:-1]); args[8] = size
    p(" rebar", m.PropFrame.SetRebarColumn(new, *args))
    p(" mods", m.PropFrame.SetModifiers(new, list(m.PropFrame.GetModifiers(base)[0])))


def res(m, tag):
    m.Analyze.SetRunCaseFlag("", True, True); p(tag, "run", m.Analyze.RunAnalysis()); p(tag, "design", m.DesignConcrete.StartDesign())
    db = m.DatabaseTables
    db.SetLoadCasesSelectedForDisplay(list(m.LoadCases.GetNameList()[1])); db.SetLoadCombinationsSelectedForDisplay(list(m.RespCombo.GetNameList()[1]))
    c = R5.oldlab(table(m, "Concrete Column PMM Envelope - ACI 318-19"), "Label") if False else None
    cs = table(m, "Concrete Column Design Summary - ACI 318-19"); cs = R5.oldlab(cs, "Label")
    g = cs.groupby(["Story", "Label_project"])["PMMRatio"].max().sort_values(ascending=False)
    p(tag, "PMM top\n", g.head(10).to_string())
    bs = table(m, "Concrete Beam Design Summary - ACI 318-19"); bs = R5.oldlab(bs, "Label")
    msg = bs[bs["Status"] != "No Message"][["Story", "Label_project", "ErrMsg"]].drop_duplicates()
    p(tag, "beam msgs\n", msg.to_string())
    bs["Dem"] = (bs["VRebar"] + 2 * bs["TTrnRebar"]) * 1000
    cc = bs[bs.Label_project.isin(["B3", "B5", "B6"])].groupby(["Story", "Label_project"]).agg(Dem=("Dem", "max"), Al=("TLngRebar", "max"), AsTop=("AsTop", "max"))
    cc["Al"] *= 1e6; cc["AsTop"] *= 1e6
    p(tag, "cantilevers\n", cc.to_string())
    mod = table(m, "Modal Participating Mass Ratios"); p(tag, "T", list(mod["Period"].head(3)))
    dr = table(m, "Story Drifts"); d = dr[dr["Output Case"].isin(["EXP", "EXN", "EYP", "EYN"])]; p(tag, "drift max", d["Drift"].abs().max())
    return g


e = None
try:
    a = os.path.join(TD, "A.EDB"); shutil.copy2(SRC, a)
    e, m = connect(a); m.SetModelIsLocked(False)
    p("rebar names", m.PropRebar.GetNameList())
    mk_col(m, "C50X50/16T16", "C50X50/16T20", "20")
    pts, frs, ars = geometry(m)
    s1 = [f for f, v in frs.items() if v["kind"] == "column" and v["story"] == "Story1"]
    for f in s1:
        m.FrameObj.SetSection(f, "C50X50/16T20", 0)
    res(m, "A")
    m.SetModelIsLocked(False)
    cant = [f for f, v in frs.items() if v["kind"] == "beam" and v["label"] in ("B3", "B5", "B6")]
    for f in cant:
        mods = list(m.FrameObj.GetModifiers(f)[0]); mods[3] = 0.1
        m.FrameObj.SetModifiers(f, mods)
    res(m, "B")
    m.SetModelIsLocked(False)
    for f in cant:
        mods = list(m.FrameObj.GetModifiers(f)[0]); mods[3] = 1.0
        m.FrameObj.SetModifiers(f, mods)
    mk_col(m, "C50X50/16T16", "C55X55/16T20", "20", 0.55)
    for f in s1:
        m.FrameObj.SetSection(f, "C55X55/16T20", 0)
    res(m, "C")
except Exception:
    import traceback; p(traceback.format_exc())
finish("r6_trial")
try: e.ApplicationExit(False)
except Exception: pass
os._exit(0)
