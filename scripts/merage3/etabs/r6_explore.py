# -*- coding: utf-8 -*-
"""Rev6 (task 42) exploration: read-only look at Merage3_Rev6.EDB (copy of Rev5). Nothing is saved."""
import sys, os, json
import r5_common as C
from r5_common import *
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
EDB6 = os.path.join(HERE, "Merage3_Rev6.EDB")

if __name__ == "__main__":
    try:
        e, m = connect(EDB6)
        r = m.Story.GetStories()
        p("GetStories", r)
        try:
            r2 = m.Story.GetStories_2()
            p("GetStories_2", r2)
        except Exception as ex:
            p("GetStories_2 err", ex)
        for s in ("Story1", "Story2", "Story3", "Story4", "Story5"):
            p(s, "height", m.Story.GetHeight(s), "elev", m.Story.GetElevation(s))
        for k in ("Story Definitions", "Tower and Base Story Definitions"):
            t = table(m, k); p(k); p(t.to_string())
        for sec in ("BW40xH50", "BW45xH50", "BW50xH50"):
            p(sec, "rect", m.PropFrame.GetRectangle(sec), "rebarBeam", m.PropFrame.GetRebarBeam(sec), "mod", m.PropFrame.GetModifiers(sec))
        p("frame sections", m.PropFrame.GetNameList())
        pts, frs, ars = geometry(m)
        for a, v in ars.items():
            if v["prop"] and v["prop"] != "None":
                r = m.AreaObj.GetLoadUniform(a)
                p("area", a, v["label"], v["story"], v["prop"], [(r[2][k], r[5][k]) for k in range(r[0])])
        for f, v in frs.items():
            if v["story"] in ("Story4", "Story5", "Story1"):
                r = m.FrameObj.GetLoadDistributed(f); rp = m.FrameObj.GetLoadPoint(f)
                if r[0] or rp[0]:
                    p("frame", f, v["label"], v["story"], v["kind"], v["sec"], [(r[2][k], round(r[10][k], 3), r[6][k], r[7][k]) for k in range(r[0])],
                      [(rp[2][k], rp[6][k], rp[8][k]) for k in range(rp[0])])
        p("patterns", [(pt, m.LoadPatterns.GetLoadType(pt)[0]) for pt in m.LoadPatterns.GetNameList()[1]])
        p("Lr areas:", [(ars[a]["label"], ars[a]["story"]) for a in ars if any(x == "Lr" for x in m.AreaObj.GetLoadUniform(a)[2])])
        p("mass source", table(m, "Mass Source Definition").to_string())
        aus = table(m, "Load Pattern Definitions - Auto Seismic - User Coefficient"); p(aus.to_string())
        p("pdelta", table(m, "P-Delta Options").to_string() if not table(m, "P-Delta Options").empty else "-")
        p("diaphragms", table(m, "Area Assignments - Diaphragms").head(40).to_string())
        p("modifiers", table(m, "Frame Assignments - Property Modifiers").head(10).to_string())
    except Exception:
        import traceback; p(traceback.format_exc())
    finish("r6_explore")
    try:
        e.ApplicationExit(False)
    except Exception:
        pass
    os._exit(0)
