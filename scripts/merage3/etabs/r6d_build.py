# -*- coding: utf-8 -*-
"""Merage3 Rev6d build (task 50, boss order 2026-10-31).   python r6d_build.py
Fresh copy of _backup\\Merage3_Rev6c_before_T50.EDB (= Rev6c) -> Merage3_Rev6d.EDB (Rev6c untouched).
  1. joists of ALL bays of floors 1-3 and the roof in Y (the 7.5 m direction; boss: "in the 7.5 direction they stay"):
     deck local axis 90 deg for F12, F13, F14 (F1, F4 were 90 already). Cantilever panels F2 / F3 keep X (span between the
     cantilever beams; Y would make them 1.20 cantilever joists). Stair house keeps X (boss).
     Walls on the slabs that ran parallel to the old X joists (W8, W10, W13, W17; roof OV-R) were point loads on the Y beams:
     converted to partial line loads on the X beams by the lever rule along Y. Walls along Y on the slabs stay in the
     equivalent partition load (ASSUMPTION, question). Mass kept (same diaphragm).
  1b. elevator opening (A-B, Y 13.50-15.30) interrupts the Y joists of F14 over the full panel width: trimmer beam BT
     BW30xH50 at Y 15.30 between B31 and B33 on Story1-4 is structurally unavoidable (pinned ends).
  2. stair: t = 0.20 and an intermediate support (boss): stair beam BS BW30xH50 at floor level at Y 11.658 (parking arrival
     11.758 at Story1) between B30 and B32 on Story1-4, pinned ends; each strip = span landing beam (axis 2) -> BS (flight,
     sliding top end of the upper flight on BS) + span BS -> B36 (floor landing).
Writes r6d_build_summary.json, geom_Rev6d.json, stair_loads_Rev6d.csv, wall_loads_converted_Rev6d.csv, log_r6d_build.txt"""
import sys, os, json, shutil, csv, math
from r5_common import *
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
SRC6C = os.path.join(HERE, "Merage3_Rev6c.EDB")
BAK = os.path.join(HERE, "_backup", "Merage3_Rev6c_before_T50.EDB")
EDB6D = os.path.join(HERE, "Merage3_Rev6d.EDB")
ZS = {"Story1": 4.30, "Story2": 7.70, "Story3": 11.10, "Story4": 14.50}
# stair data (r6_build, architect T41), t = 0.20
GC, T, LL, RAIL = 25.0, 0.20, 4.79, 0.3
Y2, Y3, YHL = 7.50, 13.50, 8.958
FLW, LANDW = 1.10, 1.15
COS = {"typ": 0.870, "gnd": 0.850}; FIN = {"typ": 4.43, "gnd": 4.54}
QL = GC * T + 2.12
LBEAM_W = GC * 0.30 * 0.40 * (2.35 - 0.50)
YB_T, YB_G = 11.658, 11.758
S = {}
e = None


def span(segs, a, b):
    """simple span a..b, segs = [(y0, y1, q, w, rail)]: reactions (Ra, Rb) for D and L"""
    out = {}
    for case in ("D", "L"):
        Ra = Rb = 0.0
        for y0, y1, q, w, rail in segs:
            W = ((q if case == "D" else LL) * w + (RAIL if (case == "D" and rail) else 0.0)) * (y1 - y0)
            yc = (y0 + y1) / 2
            Rb += W * (yc - a) / (b - a); Ra += W * (b - yc) / (b - a)
        out[case] = (Ra, Rb)
    return out


def strip(ytop, kind, foot_on_grade=False):
    qf = GC * T / COS[kind] + FIN[kind]
    if foot_on_grade:
        s1 = span([(Y2, YHL, QL, LANDW, False), (YHL, ytop, qf, FLW, True)], Y2, ytop)
        return {"land": s1, "BS_flight": None, "BS_fl": None, "B36": None, "grade": s1}
    s1 = span([(Y2, YHL, QL, LANDW, False), (YHL, ytop, qf, FLW, True)], Y2, ytop)
    s2 = span([(ytop, Y3, QL, LANDW, False)], ytop, Y3)
    return {"land": s1, "BS_flight": s1, "BS_fl": s2, "B36": s2}


def stair_actions():
    tA_g, tB_g, typ = strip(YB_G, "gnd"), strip(12.038, "gnd", True), strip(YB_T, "typ")
    col, bs, b36 = {}, {}, {}
    for st in ("Story1", "Story2", "Story3", "Story4"):
        a, b = (tA_g, tB_g) if st == "Story1" else (typ, typ)
        D = a["land"]["D"][0] + b["land"]["D"][0] + LBEAM_W; L = a["land"]["L"][0] + b["land"]["L"][0]
        col[st] = {"P_D_each": round(D / 2, 2), "P_L_each": round(L / 2, 2), "beam_total_D": round(D, 1), "beam_total_L": round(L, 1)}
    for lev in ("Story1", "Story2", "Story3", "Story4"):
        arr = tA_g if lev == "Story1" else typ
        dep = typ if lev != "Story4" else None
        D = arr["BS_flight"]["D"][1] + arr["BS_fl"]["D"][0] + (dep["BS_flight"]["D"][1] + dep["BS_fl"]["D"][0] if dep else 0.0)
        L = arr["BS_flight"]["L"][1] + arr["BS_fl"]["L"][0] + (dep["BS_flight"]["L"][1] + dep["BS_fl"]["L"][0] if dep else 0.0)
        # departing strip leaves the floor on BS (its flight foot) - same geometry as the arriving strip in plan (mirror in X)
        bs[lev] = {"D_total": round(D, 2), "L_total": round(L, 2), "y": YB_G if lev == "Story1" else YB_T}
        D3 = arr["B36"]["D"][1] + (dep["B36"]["D"][1] if dep else 0.0); L3 = arr["B36"]["L"][1] + (dep["B36"]["L"][1] if dep else 0.0)
        b36[lev] = {"D_total": round(D3, 2), "L_total": round(L3, 2)}
    return {"col": col, "BS": bs, "B36": b36, "grade_foot_D": round(tB_g["grade"]["D"][1], 2), "grade_foot_L": round(tB_g["grade"]["L"][1], 2),
            "q_flight": round(GC * T / COS["typ"] + FIN["typ"], 2), "q_landing": round(QL, 2)}


def pt_at(pts, story, x, y):
    c = [q for q, v in pts.items() if v["story"] == story and abs(v["x"] - x) < 0.02 and abs(v["y"] - y) < 0.02]
    assert len(c) == 1, (story, x, y, c)
    return c[0]


def xbeams(frs, story, Y):
    return [(f, v) for f, v in frs.items() if v["story"] == story and v["kind"] == "beam" and abs(v["yi"] - Y) < 0.02 and abs(v["yj"] - Y) < 0.02]


try:
    act = stair_actions(); S["stair"] = act
    p("stair", json.dumps(act))
    shutil.copy2(SRC6C, BAK)
    shutil.copy2(BAK, EDB6D)
    for ext in (".$et", ".ebk", ".msh", ".ico", ".EDB.tlog", ".Y_"):
        pth = os.path.join(HERE, "Merage3_Rev6d" + ext)
        if os.path.exists(pth):
            os.remove(pth)
    e, m = connect(EDB6D); m.SetModelIsLocked(False)
    GJ = json.load(open(os.path.join(HERE, "geom_Rev6c.json"), encoding="utf-8"))
    newlab = GJ["new_objects_project_labels"]
    pts, frs, ars = geometry(m)
    for u, v in newlab["frames"].items():
        frs[u]["label_etabs"] = frs[u]["label"]; frs[u]["label"] = v["label"]
    # 1. deck axes
    ax = {}
    for a, v in ars.items():
        if v["story"] in ZS and v["label"] in ("F12", "F13", "F14"):
            assert m.AreaObj.SetLocalAxes(a, 90.0, 0) == 0
            ax[f"{v['story']} {v['label']}"] = m.AreaObj.GetLocalAxes(a)[0]
    S["deck_axes_set_90"] = ax; p("1. deck axes", ax)
    # new section BW30xH50
    r45 = m.PropFrame.GetRectangle("BW45xH50"); rb = m.PropFrame.GetRebarBeam("BW45xH50")
    m.PropFrame.SetRectangle("BW30xH50", r45[1], 0.50, 0.30)
    m.PropFrame.SetRebarBeam("BW30xH50", rb[0], rb[1], rb[2], rb[3], rb[4], rb[5], rb[6], rb[7])
    m.PropFrame.SetModifiers("BW30xH50", list(m.PropFrame.GetModifiers("BW45xH50")[0]))
    ref = [f for f, v in frs.items() if v["story"] == "Story1" and v["label"] == "B30"][0]
    ins = m.FrameObj.GetInsertionPoint(ref); mods = list(m.FrameObj.GetModifiers(ref)[0])
    added = {}

    def add_beam(story, x0, y0, x1, y1, lab):
        z = ZS[story]
        qa = m.PointObj.AddCartesian(x0, y0, z, "", "")[0]; qb = m.PointObj.AddCartesian(x1, y1, z, "", "")[0]
        r = m.FrameObj.AddByPoint(qa, qb, "", "BW30xH50", ""); f = r[0]; assert r[-1] == 0
        m.FrameObj.SetInsertionPoint(f, ins[0], ins[1], ins[2], list(ins[3]), list(ins[4]), ins[5])
        m.FrameObj.SetModifiers(f, mods)
        m.FrameObj.SetReleases(f, [False] * 5 + [True], [False, False, False, True, False, True], [0] * 6, [0] * 6, 0)
        m.DesignConcrete.ACI318_19.SetOverwrite(f, 1, 3, 0)
        added[f] = {"label": lab, "story": story, "i": qa, "j": qb}
        return f, qa, qb
    xb33 = lambda y: 2.35 + (y - 13.5) / 5.31 * 0.15
    BT, BSf = {}, {}
    for st in ZS:
        BT[st] = add_beam(st, 0.0, 15.30, xb33(15.30), 15.30, "BT")
        yb = act["BS"][st]["y"]
        BSf[st] = add_beam(st, 0.0, yb, 2.35, yb, "BS")
    p("added", added)
    pts, frs, ars = geometry(m)
    for u, v in newlab["frames"].items():
        frs[u]["label_etabs"] = frs[u]["label"]; frs[u]["label"] = v["label"]
    for u, v in added.items():
        frs[u]["label_etabs"] = frs[u]["label"]; frs[u]["label"] = v["label"]
    # 1c. walls parallel to the old joists -> X beams by the lever rule
    rows = list(csv.DictReader(open(os.path.join(HERE, "slab_wall_point_loads_Rev6.csv"), encoding="utf-8-sig")))
    removed, conv = [], []
    # remove the point loads (match unique name, rel and value) and keep the other SuperDead point loads
    by_f = {}
    for r in rows:
        by_f.setdefault(r["UniqueName"], []).append((float(r["RelDist"]), float(r["P_kN"])))
    for f, lst in by_f.items():
        rp = m.FrameObj.GetLoadPoint(f)
        items = [(rp[2][k], rp[3][k], rp[5][k], rp[6][k], rp[8][k]) for k in range(rp[0])]
        keep, hit = [], 0
        for it in items:
            if it[0] == "SuperDead" and it[1] == 1 and any(abs(it[3] - t) < 2e-3 and abs(it[4] - P) < 2e-3 for t, P in lst):
                hit += 1; continue
            keep.append(it)
        assert hit == len(lst), (f, items, lst)
        for pat in {it[0] for it in items}:
            m.FrameObj.DeleteLoadPoint(f, pat, 0)
        for pat, typ, dr, t, val in keep:
            assert m.FrameObj.SetLoadPoint(f, pat, typ, dr, t, val, "Global", True, False, 0) == 0
        removed.append((f, frs[f]["story"], frs[f]["label"], len(lst)))
    # group by (story, wall, seg) -> q, x-range, Y
    walls = {}
    for r in rows:
        k = (r["Story"], r["Wall"], r["seg"])
        walls.setdefault(k, {"Y": float(r["Y"]), "q": float(r["q_kN/m"]), "P": 0.0})
        walls[k]["P"] += float(r["P_kN"])
    # roof OV-R (Story4) point loads on B31 / B33 at rel 0.4008 (8.788 / 9.162): converted too
    for f, v in frs.items():
        if v["story"] == "Story4" and v["label"] in ("B31", "B33") and v["kind"] == "beam":
            rp = m.FrameObj.GetLoadPoint(f)
            items = [(rp[2][k], rp[3][k], rp[5][k], rp[6][k], rp[8][k]) for k in range(rp[0])]
            ovr = [it for it in items if it[0] == "SuperDead" and abs(it[3] - 0.4008) < 2e-3]
            assert len(ovr) == 1, (f, items)
            m.FrameObj.DeleteLoadPoint(f, "SuperDead", 0)
            for it in items:
                if it is not ovr[0] and it[0] == "SuperDead":
                    m.FrameObj.SetLoadPoint(f, it[0], it[1], it[2], it[3], it[4], "Global", True, False, 0)
            walls.setdefault(("Story4", "OV-R", "0.000-2.350"), {"Y": 15.628, "q": 0.0, "P": 0.0})
            walls[("Story4", "OV-R", "0.000-2.350")]["P"] += ovr[0][4]
            removed.append((f, "Story4", v["label"], 1))

    def beam_y_lines(x):
        return (15.30, 18.81) if x < 2.35 - 1e-6 and True else (13.5, 18.81)

    for (st, wid, seg), w in walls.items():
        x0, x1 = [float(t) for t in seg.split("-")]
        Yw = w["Y"]
        q = w["P"] / (x1 - x0)
        if Yw < 13.5:
            ylo, yhi = 7.5, 13.5
        elif x1 <= 2.35 + 1e-6:
            ylo, yhi = 15.30, 18.81                                       # A-B: between BT and B38
        else:
            ylo, yhi = 13.5, 18.81
        rlo = (yhi - Yw) / (yhi - ylo)
        for Yl, share in ((ylo, rlo), (yhi, 1 - rlo)):
            for f, v in xbeams(frs, st, Yl):
                lo, hi = sorted((v["xi"], v["xj"]))
                a_, b_ = max(lo, x0), min(hi, x1)
                if b_ - a_ < 1e-3:
                    continue
                t0, t1 = sorted(((a_ - v["xi"]) / (v["xj"] - v["xi"]), (b_ - v["xi"]) / (v["xj"] - v["xi"])))
                assert m.FrameObj.SetLoadDistributed(f, "SuperDead", 1, 10, t0, t1, q * share, q * share, "Global", True, False, 0) == 0
                conv.append({"Story": st, "Wall": wid, "Y": Yw, "x0": x0, "x1": x1, "Beam": v["label"], "UniqueName": f, "Yline": Yl,
                             "share": round(share, 4), "rel0": round(t0, 4), "rel1": round(t1, 4), "w_kN/m": round(q * share, 3), "W_kN": round(q * share * (b_ - a_), 2)})
    S["walls_removed_points"] = removed; S["walls_converted"] = conv
    tot_old = sum(w["P"] for w in walls.values()); tot_new = sum(c["W_kN"] for c in conv)
    S["wall_total_old_new_kN"] = (round(tot_old, 2), round(tot_new, 2))
    p("walls converted", len(conv), "total old/new", S["wall_total_old_new_kN"])
    assert abs(tot_old - tot_new) < 0.5, (tot_old, tot_new)
    with open(os.path.join(HERE, "wall_loads_converted_Rev6d.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(conv[0])); wr.writeheader(); wr.writerows(conv)
    # 2. stair loads
    dm, srows = {}, []

    def addm(q, dW):
        dm[q] = dm.get(q, 0.0) + dW
    for f, v in frs.items():
        if v["kind"] != "column" or v["label"] not in ("C2", "C6") or v["story"] not in ZS:
            continue
        st = v["story"]
        r = m.FrameObj.GetLoadPoint(f)
        items = [(r[2][k], r[3][k], r[5][k], r[6][k], r[8][k]) for k in range(r[0])]
        sdF = [x for x in items if x[0] == "SuperDead" and x[1] == 1][0]; sdM = [x for x in items if x[0] == "SuperDead" and x[1] == 2][0]
        lvF = [x for x in items if x[0] == "Live" and x[1] == 1][0]
        rel, ecc = sdF[3], sdM[4] / sdF[4]
        n_ = act["col"][st]
        for pat in ("SuperDead", "Live"):
            m.FrameObj.DeleteLoadPoint(f, pat, 0)
        m.FrameObj.SetLoadPoint(f, "SuperDead", 1, 10, rel, n_["P_D_each"], "Global", True, False, 0)
        m.FrameObj.SetLoadPoint(f, "Live", 1, 10, rel, n_["P_L_each"], "Global", True, False, 0)
        m.FrameObj.SetLoadPoint(f, "SuperDead", 2, 5, rel, n_["P_D_each"] * ecc, "Global", True, False, 0)
        i, j, _ = m.FrameObj.GetPoints(f)
        dP = n_["P_D_each"] - sdF[4]
        addm(i, dP * (1 - rel)); addm(j, dP * rel)
        srows.append({"Story": st, "Member": v["label"], "D_old": sdF[4], "D_new": n_["P_D_each"], "L_old": lvF[4], "L_new": n_["P_L_each"], "My": round(n_["P_D_each"] * ecc, 2)})
    old6c = json.load(open(os.path.join(HERE, "r6c_build_summary.json"), encoding="utf-8"))["stair_new_t020"]["B36"]
    for lev in ZS:
        f = [u for u, v in frs.items() if v["story"] == lev and v["label"] == "B36" and v["kind"] == "beam"][0]
        L = frs[f]["L"]
        wD0, wL0 = old6c[lev]["D_total"] / L, old6c[lev]["L_total"] / L
        wD1, wL1 = act["B36"][lev]["D_total"] / L, act["B36"][lev]["L_total"] / L
        rd = m.FrameObj.GetLoadDistributed(f)
        dist = [(rd[2][k], rd[5][k], rd[6][k], rd[7][k], rd[10][k], rd[11][k]) for k in range(rd[0])]
        hD = [x for x in dist if x[0] == "SuperDead" and abs(x[4] - wD0) < 0.01]; hL = [x for x in dist if x[0] == "Live" and abs(x[4] - wL0) < 0.01]
        assert len(hD) == 1 and len(hL) == 1, (lev, dist, wD0, wL0)
        for pat in ("SuperDead", "Live"):
            m.FrameObj.DeleteLoadDistributed(f, pat, 0)
        for pat, dr, d1, d2, w1, w2 in dist:
            if pat == "SuperDead" and abs(w1 - wD0) < 0.01:
                w1 = w2 = wD1
            elif pat == "Live" and abs(w1 - wL0) < 0.01:
                w1 = w2 = wL1
            if pat in ("SuperDead", "Live"):
                m.FrameObj.SetLoadDistributed(f, pat, 1, dr, d1, d2, w1, w2, "Global", True, False, 0)
        addm(frs[f]["i"], (wD1 - wD0) * L / 2); addm(frs[f]["j"], (wD1 - wD0) * L / 2)
        fb, qa, qb = BSf[lev]
        Lb = 2.35
        m.FrameObj.SetLoadDistributed(fb, "SuperDead", 1, 10, 0.0, 1.0, act["BS"][lev]["D_total"] / Lb, act["BS"][lev]["D_total"] / Lb, "Global", True, False, 0)
        m.FrameObj.SetLoadDistributed(fb, "Live", 1, 10, 0.0, 1.0, act["BS"][lev]["L_total"] / Lb, act["BS"][lev]["L_total"] / Lb, "Global", True, False, 0)
        addm(qa, act["BS"][lev]["D_total"] / 2); addm(qb, act["BS"][lev]["D_total"] / 2)
        srows.append({"Story": lev, "Member": "B36", "D_old": round(wD0 * L, 1), "D_new": round(wD1 * L, 1), "L_old": round(wL0 * L, 1), "L_new": round(wL1 * L, 1)})
        srows.append({"Story": lev, "Member": "BS", "D_new": act["BS"][lev]["D_total"], "L_new": act["BS"][lev]["L_total"], "y": act["BS"][lev]["y"]})
    for q, dW in dm.items():
        ms = m.PointObj.GetMass(q)
        o_ = list(ms[0]) if ms[-1] == 0 else [0.0] * 6
        nw = max(o_[0] + dW / G, 0.0)
        m.PointObj.SetMass(q, [nw, nw, 0, 0, 0, 0], 0, False, True)
    S["stair_rows"] = srows; S["mass_net_kN"] = round(sum(dm.values()), 2)
    for r_ in srows:
        p("  ", r_)
    with open(os.path.join(HERE, "stair_loads_Rev6d.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        keys = sorted({k for r_ in srows for k in r_})
        wr = csv.DictWriter(fh, fieldnames=keys); wr.writeheader(); wr.writerows(srows)
    pts, frs, ars = geometry(m)
    for u, v in added.items():
        newlab["frames"][u] = {"label": v["label"], "story": v["story"]}
        newlab["points"][v["i"]] = {"label": v["label"] + "-i"}; newlab["points"][v["j"]] = {"label": v["label"] + "-j"}
    json.dump({"points": pts, "frames": frs, "areas": ars, "new_objects_project_labels": newlab},
              open(os.path.join(HERE, "geom_Rev6d.json"), "w", encoding="utf-8"), indent=0, ensure_ascii=False)
    p("save", m.File.Save(EDB6D)); S["saved"] = True
except Exception:
    import traceback; p(traceback.format_exc())
json.dump(S, open(os.path.join(HERE, "r6d_build_summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
finish("r6d_build")
try:
    e.ApplicationExit(False)
except Exception:
    pass
os._exit(0)
