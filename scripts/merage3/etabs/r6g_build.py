# -*- coding: utf-8 -*-
"""Merage3 Rev6g build (task 54, boss decision 2026-11-07: rho = 1.0 per Standard 2800 ed.4, which has no rho in the load
combinations; option C). Fresh copy of Merage3_Rev6f.EDB -> Merage3_Rev6g.EDB (Rev6f untouched); in every A22 and ASD
combination the seismic factors of EXP, EXN, EYP, EYN are divided by 1.3. Everything else of Rev6f stays (drift patterns,
EV on the cantilevers, k = 1.05, deleted combos). Own ETABS instance.   python r6g_build.py"""
import sys, os, json, shutil
import comtypes.client
from r5_common import HERE, EXE, p, finish
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
SRC = os.path.join(HERE, "Merage3_Rev6f.EDB")
EDB = os.path.join(HERE, "Merage3_Rev6g.EDB")
SEIS = ["EXP", "EXN", "EYP", "EYN"]
S = {"rho": 1.0}
e = None
try:
    assert not os.path.exists(EDB), "Rev6g already exists"
    shutil.copy2(SRC, EDB); p("fresh copy", SRC, "->", EDB)
    h = comtypes.client.CreateObject("ETABSv1.Helper").QueryInterface(comtypes.gen.ETABSv1.cHelper)
    e = h.CreateObject(EXE); p("ApplicationStart (own instance)", e.ApplicationStart()); m = e.SapModel
    assert m.File.OpenFile(EDB) == 0 and os.path.normcase(m.GetModelFilename()) == os.path.normcase(EDB)
    m.SetPresentUnits(6); m.SetModelIsLocked(False)
    n = 0
    for nm in list(m.RespCombo.GetNameList(0, [])[1]):
        r = m.RespCombo.GetCaseList(nm)
        for c, sf in zip(r[2], r[3]):
            if c in SEIS:
                assert m.RespCombo.SetCaseList(nm, 0, c, round(sf / 1.3, 6))[-1] == 0; n += 1
    S["terms"] = n; p("rho 1.3 -> 1.0 on", n, "terms")
    for nm in ("A22-6_EXP+_EYP+", "A22-7-EXP", "ASD-8-EXP", "ASD-10_EXP+_EYP-"):
        r = m.RespCombo.GetCaseList(nm); p(" ", nm, list(zip(r[2], r[3])))
    p("save", m.File.Save(EDB)); S["saved"] = True
except Exception:
    import traceback
    p(traceback.format_exc()); S["error"] = traceback.format_exc()
json.dump(S, open(os.path.join(HERE, "r6g_build_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
finish("r6g_build")
try:
    e and p("ApplicationExit", e.ApplicationExit(False))
except Exception:
    pass
finish("r6g_build")
os._exit(0)
