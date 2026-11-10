# -*- coding: utf-8 -*-
"""Task 48: on a TEMP copy of Rev6b, find the one-way span direction of the TIRCHEH deck for the local-axis angles used
(F1/F4 = 90 deg, F12/F13/F14 = 0 deg): Lr-only uniform 1.0 kN/m2 on the Story4 roof slabs, read end shears of the bounding beams."""
import sys, os, shutil, json
from r5_common import *
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
TD = r"C:\ZagrosTemp\r6c_test"; os.makedirs(TD, exist_ok=True)
TMP = os.path.join(TD, "deck_test.EDB"); shutil.copy2(os.path.join(HERE, "Merage3_Rev6b.EDB"), TMP)
e = None
try:
    e, m = connect(TMP); m.SetModelIsLocked(False)
    pts, frs, ars = geometry(m)
    p("deck", m.PropArea.GetDeck("TIRCHEH"))
    for a, v in ars.items():
        if v["story"] == "Story4":
            p("area", a, v["label"], m.AreaObj.GetLocalAxes(a)[0], v["xy"])
    m.Analyze.SetRunCaseFlag("", False, True); m.Analyze.SetRunCaseFlag("Lr", True, False); m.Analyze.SetRunCaseFlag("Modal", True, False)
    p("run", m.Analyze.RunAnalysis())
    rs = m.Results.Setup; rs.DeselectAllCasesAndCombosForOutput(); rs.SetCaseSelectedForOutput("Lr", True)
    out = {}
    for f, v in frs.items():
        if v["story"] == "Story4" and v["kind"] == "beam" and v["label"] in ("B1", "B4", "B7", "B10", "B11", "B12", "B13", "B30", "B32", "B34", "B36", "B37", "B31", "B33", "B35", "B38", "B39"):
            r = m.Results.FrameForce(f, 0)
            V = [r[9][k] for k in range(r[0])]
            out[v["label"]] = (round(v["L"], 2), round(max(abs(x) for x in V), 2) if V else None)
    p("Lr end shear (kN) by beam (L, |V|max):", json.dumps(out))
except Exception:
    import traceback; p(traceback.format_exc())
finish("r6c_deck_test")
try: e.ApplicationExit(False)
except Exception: pass
os._exit(0)
