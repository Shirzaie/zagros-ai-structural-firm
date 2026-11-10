# -*- coding: utf-8 -*-
"""Merage3 Rev6c build (task 48, boss order 2026-10-31).   python r6c_build.py
Fresh copy of _backup\\Merage3_Rev6b_before_T48.EDB (= Rev6b) -> Merage3_Rev6c.EDB (Rev6b untouched).
  1. joists of the 7.5 m bay (axis 1 - 2, panels F1 A-B and F4 B-C, all levels): one-way span in Y (7.5 m).
     CHECKED, NOT CHANGED: r6c_deck_test.py shows that the TIRCHEH deck with local axis 90 deg (F1, F4) already
     distributes in Y (Lr test: B10 / B11 / B12 / B13 carry the load, B1 / B4 / B7 ~ 0). Tie beams = ribs inside the slab
     (not modelled, as the joists themselves). Bays 6.0 / 5.31 / cantilever / stair house: NOT changed (question to the boss).
  2. stair waist + landing slab t = 0.25 -> 0.20: stair loads rebuilt with r6_build.stair_actions (C2 / C6 landing point
     loads D / L, corbel moments P_D x e, B36 line loads D / L); added mass corrected by the same statics as Rev6.
  1b. stair-house roof (Story5): all joists in X (span 2.3; boss addendum): deck local axis of F17 90 -> 0 deg
      (0 deg = span in X, verified by r6c_deck_test.py); the extension panels were already 0 deg.
  3. elevator pit 2.00 m and hook 25 kN (approved): no effect on the superstructure model (pit is part of the foundation,
     SAFE; hook already on BH in Rev6b).
Writes r6c_build_summary.json, geom_Rev6c.json, stair_loads_Rev6c.csv, log_r6c_build.txt"""
import sys, os, json, shutil, csv
from r5_common import *
import r6_build as RB6
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
BAK = os.path.join(HERE, "_backup", "Merage3_Rev6b_before_T48.EDB")
EDB6C = os.path.join(HERE, "Merage3_Rev6c.EDB")
S = {}
e = None


def actions(t):
    RB6.T_SLAB = t
    RB6.Q_LAND = RB6.GC * t + 2.12
    return RB6.stair_actions()


try:
    old, info_old = actions(0.25)
    new, info_new = actions(0.20)
    S["stair_old_t025"] = old; S["stair_new_t020"] = new; S["info_new"] = info_new
    p("old", json.dumps(old)); p("new", json.dumps(new))
    shutil.copy2(BAK, EDB6C)
    for ext in (".$et", ".ebk", ".msh", ".ico", ".EDB.tlog", ".Y_"):
        pth = os.path.join(HERE, "Merage3_Rev6c" + ext)
        if os.path.exists(pth):
            os.remove(pth)
    e, m = connect(EDB6C); m.SetModelIsLocked(False)
    GJ = json.load(open(os.path.join(HERE, "geom_Rev6b.json"), encoding="utf-8"))
    newlab = GJ["new_objects_project_labels"]
    pts, frs, ars = geometry(m)
    for u, v in newlab["frames"].items():
        frs[u]["label_etabs"] = frs[u]["label"]; frs[u]["label"] = v["label"]
    # deck check (no change)
    S["deck_axes"] = {f"{v['story']} {v['label']}": m.AreaObj.GetLocalAxes(a)[0] for a, v in ars.items() if v["label"] in ("F1", "F4")}
    assert all(abs(x - 90) < 1e-6 for x in S["deck_axes"].values()), S["deck_axes"]
    # 1b. boss (2026-10-31, addendum): ALL joists of the stair-house roof (Story5) in X (span 2.3): F17 90 -> 0 deg; F14', F2' already 0
    ph = {}
    for a, v in ars.items():
        if v["story"] == "Story5":
            before = m.AreaObj.GetLocalAxes(a)[0]
            if abs(before) > 1e-6:
                assert m.AreaObj.SetLocalAxes(a, 0.0, 0) == 0
            ph[f"{v['label']} ({a})"] = (before, m.AreaObj.GetLocalAxes(a)[0])
    S["story5_deck_axes_before_after"] = ph
    p("1b. Story5 deck axes", ph)
    dm, rows = {}, []

    def addm(q, dW):
        dm[q] = dm.get(q, 0.0) + dW
    # columns C2 / C6
    for f, v in frs.items():
        if v["kind"] != "column" or v["label"] not in ("C2", "C6") or v["story"] == "Story5":
            continue
        st = v["story"]
        r = m.FrameObj.GetLoadPoint(f)
        items = [(r[2][k], r[3][k], r[5][k], r[6][k], r[8][k]) for k in range(r[0])]       # pat, type, dir, rel, val
        sdF = [x for x in items if x[0] == "SuperDead" and x[1] == 1]; sdM = [x for x in items if x[0] == "SuperDead" and x[1] == 2]
        lvF = [x for x in items if x[0] == "Live" and x[1] == 1]
        assert len(sdF) == 1 and len(sdM) == 1 and len(lvF) == 1 and len(items) == 3, (f, items)
        rel = sdF[0][3]
        o, n_ = old["col"][st], new["col"][st]
        assert abs(sdF[0][4] - o["P_D_each"]) < 0.02 and abs(lvF[0][4] - o["P_L_each"]) < 0.02, (f, items, o)
        ecc = sdM[0][4] / sdF[0][4]
        for pat in ("SuperDead", "Live"):
            m.FrameObj.DeleteLoadPoint(f, pat, 0)
        assert m.FrameObj.SetLoadPoint(f, "SuperDead", 1, 10, rel, n_["P_D_each"], "Global", True, False, 0) == 0
        assert m.FrameObj.SetLoadPoint(f, "Live", 1, 10, rel, n_["P_L_each"], "Global", True, False, 0) == 0
        assert m.FrameObj.SetLoadPoint(f, "SuperDead", 2, 5, rel, n_["P_D_each"] * ecc, "Global", True, False, 0) == 0
        i, j, _ = m.FrameObj.GetPoints(f)
        zi, zj = m.PointObj.GetCoordCartesian(i)[2], m.PointObj.GetCoordCartesian(j)[2]
        dP = n_["P_D_each"] - o["P_D_each"]
        addm(i, dP * (1 - rel)); addm(j, dP * rel)
        rows.append({"Story": st, "Member": v["label"], "UniqueName": f, "rel": rel, "D_old": o["P_D_each"], "D_new": n_["P_D_each"],
                     "L_old": o["P_L_each"], "L_new": n_["P_L_each"], "My_new": round(n_["P_D_each"] * ecc, 2), "zi": zi, "zj": zj})
    # B36 line loads
    for lev in ("Story1", "Story2", "Story3", "Story4"):
        f = [u for u, v in frs.items() if v["story"] == lev and v["label"] == "B36" and v["kind"] == "beam"][0]
        L = frs[f]["L"]
        wD0, wL0 = old["B36"][lev]["D_total"] / L, old["B36"][lev]["L_total"] / L
        wD1, wL1 = new["B36"][lev]["D_total"] / L, new["B36"][lev]["L_total"] / L
        rd = m.FrameObj.GetLoadDistributed(f)
        dist = [(rd[2][k], rd[5][k], rd[6][k], rd[7][k], rd[10][k], rd[11][k]) for k in range(rd[0])]
        hitD = [x for x in dist if x[0] == "SuperDead" and abs(x[4] - wD0) < 0.01]; hitL = [x for x in dist if x[0] == "Live" and abs(x[4] - wL0) < 0.01]
        assert len(hitD) == 1 and len(hitL) == 1, (lev, dist, wD0, wL0)
        for pat in ("SuperDead", "Live"):
            m.FrameObj.DeleteLoadDistributed(f, pat, 0)
        for pat, dr, d1, d2, w1, w2 in dist:
            if (pat, w1) == ("SuperDead", hitD[0][4]):
                w1 = w2 = wD1
            elif (pat, w1) == ("Live", hitL[0][4]):
                w1 = w2 = wL1
            if pat in ("SuperDead", "Live"):
                assert m.FrameObj.SetLoadDistributed(f, pat, 1, dr, d1, d2, w1, w2, "Global", True, False, 0) == 0
        dW = (wD1 - wD0) * L
        addm(frs[f]["i"], dW / 2); addm(frs[f]["j"], dW / 2)
        rows.append({"Story": lev, "Member": "B36", "UniqueName": f, "D_old_kN/m": round(wD0, 3), "D_new_kN/m": round(wD1, 3),
                     "L_old_kN/m": round(wL0, 3), "L_new_kN/m": round(wL1, 3)})
    ml = []
    for q, dW in dm.items():
        ms = m.PointObj.GetMass(q)
        o_ = list(ms[0]) if ms[-1] == 0 else [0.0] * 6
        nw = o_[0] + dW / G
        assert nw > 0, (q, o_, dW)
        m.PointObj.SetMass(q, [nw, nw, 0, 0, 0, 0], 0, False, True)
        ml.append((q, round(o_[0] * G, 2), round(dW, 2)))
    S["stair_rows"] = rows; S["mass_changes_kN"] = ml; S["mass_net_kN"] = round(sum(dm.values()), 2)
    for r_ in rows:
        p("  ", r_)
    p("mass net", S["mass_net_kN"])
    with open(os.path.join(HERE, "stair_loads_Rev6c.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        keys = sorted({k for r_ in rows for k in r_})
        wr = csv.DictWriter(fh, fieldnames=keys); wr.writeheader(); wr.writerows(rows)
    pts, frs, ars = geometry(m)
    json.dump({"points": pts, "frames": frs, "areas": ars, "new_objects_project_labels": newlab},
              open(os.path.join(HERE, "geom_Rev6c.json"), "w", encoding="utf-8"), indent=0, ensure_ascii=False)
    p("save", m.File.Save(EDB6C)); S["saved"] = True
except Exception:
    import traceback; p(traceback.format_exc())
json.dump(S, open(os.path.join(HERE, "r6c_build_summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
finish("r6c_build")
try:
    e.ApplicationExit(False)
except Exception:
    pass
os._exit(0)
