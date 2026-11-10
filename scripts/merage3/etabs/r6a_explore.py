# -*- coding: utf-8 -*-
"""Task 44: read-only exploration of Merage3_Rev6a.EDB (fresh copy of Rev6) before the edits. Nothing is saved."""
import sys, os, json
from r5_common import *
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
EDB6A = os.path.join(HERE, "Merage3_Rev6a.EDB")
e = None
try:
    e, m = connect(EDB6A)
    pts, frs, ars = geometry(m)
    st = m.Story.GetStories(); p("stories", list(st[1]), list(st[2]), list(st[3]))
    p("patterns", {pt: m.LoadPatterns.GetLoadType(pt)[0] for pt in m.LoadPatterns.GetNameList()[1]})
    p("self wt mult", {pt: m.LoadPatterns.GetSelfWTMultiplier(pt)[0] for pt in m.LoadPatterns.GetNameList()[1]})
    for a, v in ars.items():
        if v["story"] in ("Story4", "Story5"):
            r = m.AreaObj.GetLoadUniform(a)
            p("AREA", a, v["label"], v["story"], v["prop"], "ax", m.AreaObj.GetLocalAxes(a)[0], "dia", m.AreaObj.GetDiaphragm(a)[0],
              "edge", m.AreaObj.GetEdgeConstraint(a)[0], "op", m.AreaObj.GetOpening(a)[0], "mod", list(m.AreaObj.GetModifiers(a)[0]),
              "mass", m.AreaObj.GetMass(a)[0], "loads", [(r[2][k], r[4][k], r[5][k]) for k in range(r[0])])
    p("deck prop TIRCHEH", m.PropArea.GetDeck("TIRCHEH") if hasattr(m.PropArea, "GetDeck") else None)
    try:
        p("GetSlab TIRCHEH", m.PropArea.GetSlab("TIRCHEH"))
    except Exception as ex:
        p("GetSlab err", ex)
    p("area props", m.PropArea.GetNameList())
    for f, v in frs.items():
        if v["story"] in ("Story4", "Story5") or (v["label"] in ("B3", "B5", "B6") and v["kind"] == "beam"):
            rd = m.FrameObj.GetLoadDistributed(f); rp_ = m.FrameObj.GetLoadPoint(f)
            ov = None
            try:
                ov = m.DesignConcrete.ACI318_19.GetOverwrite(f, 1)
            except Exception as ex:
                ov = str(ex)
            p("FRAME", f, v["label"], v["story"], v["kind"], v["sec"], "i", v["i"], "j", v["j"], "mods", [round(x, 3) for x in m.FrameObj.GetModifiers(f)[0]],
              "ins", m.FrameObj.GetInsertionPoint(f)[0], "ov FrameType", ov,
              "dist", [(rd[2][k], rd[5][k], round(rd[6][k], 3), round(rd[7][k], 3), round(rd[10][k], 3)) for k in range(rd[0])],
              "pt", [(rp_[2][k], rp_[4][k], rp_[5][k], round(rp_[6][k], 3), round(rp_[8][k], 3)) for k in range(rp_[0])])
    for q, v in pts.items():
        if v["story"] in ("Story4", "Story5"):
            ms = m.PointObj.GetMass(q)
            p("PT", q, v["label"], v["story"], v["x"], v["y"], v["z"], "mass", [round(x * G, 2) for x in ms[0][:3]] if ms[-1] == 0 else ms,
              "diaph", m.PointObj.GetDiaphragm(q)[:2] if hasattr(m.PointObj, "GetDiaphragm") else "")
    p("rect C40", m.PropFrame.GetRectangle("C40X40/12T16"), m.PropFrame.GetRebarColumn("C40X40/12T16"), list(m.PropFrame.GetModifiers("C40X40/12T16")[0]))
    p("rect C50", m.PropFrame.GetRectangle("C50X50/16T16"), m.PropFrame.GetRebarColumn("C50X50/16T16"), list(m.PropFrame.GetModifiers("C50X50/16T16")[0]))
    p("rect B40", m.PropFrame.GetRectangle("BW40xH40"), m.PropFrame.GetRebarBeam("BW40xH40"), list(m.PropFrame.GetModifiers("BW40xH40")[0]))
    p("frame props", [x for x in m.PropFrame.GetNameList()[1]])
    for mat in m.PropMaterial.GetNameList()[1]:
        try:
            p("mat", mat, m.PropMaterial.GetMPIsotropic(mat)[:3], m.PropMaterial.GetOConcrete_1(mat)[:2] if "C" in mat or "onc" in mat else m.PropMaterial.GetORebar_1(mat)[:2])
        except Exception as ex:
            p("mat", mat, ex)
    p("diaphragms", m.Diaphragm.GetNameList())
    p("grids", table(m, "Grid Definitions - Grid Lines").to_string())
    p("mass source", table(m, "Mass Source Definition").to_string())
    p("auto seismic", table(m, "Load Pattern Definitions - Auto Seismic - User Coefficient").to_string())
    p("pref", table(m, "Concrete Frame Design Preferences - ACI 318-19").T.to_string())
except Exception:
    import traceback; p(traceback.format_exc())
finish("r6a_explore")
try:
    e.ApplicationExit(False)
except Exception:
    pass
os._exit(0)
