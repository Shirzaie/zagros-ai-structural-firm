# -*- coding: utf-8 -*-
"""Merage3 Rev6h build (task 55, boss order 2026-11-07: try 18 to 20 bars phi20 in C17 Story1, which failed in Rev6g with PMM 1.014).
   python r6h_build.py 18     (or 20)
Fresh copy of Merage3_Rev6g.EDB -> Merage3_Rev6h.EDB (overwrites an earlier Rev6h try). New section C50X50/<n>T20 = copy of
C50X50/16T20 (same concrete, cover, ties, check mode) with n bars: 18 = 6 x 5 per face pair, 20 = 6 x 6. Assigned only to
C17 Story1 (ETABS label C3). Own ETABS instance."""
import sys, os, json, shutil
import comtypes.client
from r5_common import HERE, EXE, p, finish
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
NB = int(sys.argv[1]) if len(sys.argv) > 1 else 18
LAY = {18: (6, 5), 20: (6, 6)}[NB]
SRC = os.path.join(HERE, "Merage3_Rev6g.EDB")
EDB = os.path.join(HERE, "Merage3_Rev6h.EDB")
OLD, NEW = "C50X50/16T20", f"C50X50/{NB}T20"
S = {"bars": NB, "layout": LAY}
e = None
try:
    shutil.copy2(SRC, EDB); p("fresh copy", SRC, "->", EDB)
    h = comtypes.client.CreateObject("ETABSv1.Helper").QueryInterface(comtypes.gen.ETABSv1.cHelper)
    e = h.CreateObject(EXE); p("ApplicationStart (own instance)", e.ApplicationStart()); m = e.SapModel
    assert m.File.OpenFile(EDB) == 0 and os.path.normcase(m.GetModelFilename()) == os.path.normcase(EDB)
    m.SetPresentUnits(6); m.SetModelIsLocked(False)
    g = m.PropFrame.GetRectangle(OLD, "", "", 0, 0, 0, "", "")
    p("rectangle", OLD, g)
    fname, mat, t3, t2 = g[0], g[1], g[2], g[3]
    rb = m.PropFrame.GetRebarColumn(OLD, "", "", 0, 0, 0, 0, 0, 0, "", "", 0, 0, 0, False)
    p("rebar", OLD, rb)
    matL, matC, pat, conf, cover, nC, n3, n2, size, tie, s_, n2t, n3t, design = rb[0:14]
    assert m.PropFrame.SetRectangle(NEW, mat, t3, t2) == 0
    r = m.PropFrame.SetRebarColumn(NEW, matL, matC, pat, conf, cover, 0, LAY[0], LAY[1], size, tie, s_, n2t, n3t, design)
    p("SetRebarColumn", NEW, r)
    rb2 = m.PropFrame.GetRebarColumn(NEW, "", "", 0, 0, 0, 0, 0, 0, "", "", 0, 0, 0, False); p("rebar", NEW, rb2)
    md = list(m.PropFrame.GetModifiers(OLD)[0]); m.PropFrame.SetModifiers(NEW, md)
    u = m.FrameObj.GetNameFromLabel("C3", "Story1"); p("C17 Story1 =", u)
    un = u[0]
    assert m.FrameObj.GetSection(un)[0] == OLD, m.FrameObj.GetSection(un)
    assert m.FrameObj.SetSection(un, NEW) == 0
    p("section now", m.FrameObj.GetSection(un)[0], "modifiers", list(m.FrameObj.GetModifiers(un)[0]))
    S.update({"frame": un, "section": NEW, "rebar": [str(x) for x in rb2]})
    p("save", m.File.Save(EDB)); S["saved"] = True
except Exception:
    import traceback
    p(traceback.format_exc()); S["error"] = traceback.format_exc()
json.dump(S, open(os.path.join(HERE, "r6h_build_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
finish("r6h_build")
try:
    e and p("ApplicationExit", e.ApplicationExit(False))
except Exception:
    pass
finish("r6h_build")
os._exit(0)
