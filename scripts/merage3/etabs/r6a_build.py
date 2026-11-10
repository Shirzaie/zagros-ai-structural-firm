# -*- coding: utf-8 -*-
"""Merage3 Rev6a build (task 44, structural engineer, 2026-10-31).   python r6a_build.py
Starts from a FRESH copy of _backup\\Merage3_Rev6_before_T44.EDB (= Rev6) -> Merage3_Rev6a.EDB (Rev6 untouched).
Boss decisions (report 2026-10-24, accepted 2026-10-31) and boss order (penthouse roof to the cantilever end), applied
EXACTLY as written (coordinator 2026-10-31: nothing more, nothing less):
  1. Story1 (parking) columns 50x50: 16phi16 -> 16phi20 (new section C50X50/16T20; all 12 parking columns, as proposed in T42)
  2. cantilevers B3 / B5 / B6 (Story1-4): torsion stiffness modifier J = 0.1 (compatibility torsion, ACI 318-19 22.7.3.2),
     same as trial B of task 42
  3. stair landing on C2 / C6: vertical load only (point loads on the columns, no landing / stair frame in the model ->
     no lateral stiffness to the columns) -> model kept as Rev6 (checked, not changed)
  4. infill gap 70 mm, 5. stair slab t = 0.25 (already in the Rev6 stair loads), 6. C = 0.10: no model change
  7. Story5 (penthouse roof, ETABS z 17.80 = project +17.50) extended in Y from 13.50 to 20.01: columns C17 / C19 C40X40/12T16
     on the Story4 C17 / C19; beams BW40xH40 C16-C17, C18-C19, C17-C19, cantilevers 1.20 and the edge beam on axis 5;
     TIRCHEH slab (two panels) with the loads of the existing penthouse roof (SD 3.0 roof finish, Lr 1.5, as F17);
     roof curb 0.20 x 0.20 = 0.80 kN/m on the new edges and removed from the old back edge (Story5 B36), per architect
     note (first version) section 4.
  9. boss approval relayed by the coordinator (2nd message, 2026-10-31; overrides the later architect note on these items):
     numbers from the FINAL architect note (15:38): walls W-A 8.41 (parapet 4.20 replaced), SH-B2 8.41, SH-4 8.41, OV-B 6.96,
     OV-R 7.18 (as W17, point loads), OV-D 5.38 (lever rule), mass half / half; elevator overrun room removed (D 33 + 25, Lr 8);
     hook / rail 25 kN under the Story5 slab at (1.45, 14.65) -> new Story5 B31 / B33; curb K-J 0.45 m on Story5 B36.
  8. added mass: area mass of the new slab (SD as F17), curb as joint mass at Story5 (as Rev6), old B36 curb mass removed.
Writes: r6a_build_summary.json, geom_Rev6a.json, log_r6a_build.txt
"""
import sys, os, json, shutil
from r5_common import *
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
EDB6A = os.path.join(HERE, "Merage3_Rev6a.EDB")
SRC = os.path.join(HERE, "_backup", "Merage3_Rev6_before_T44.EDB")
CURB = 0.80
Z4, Z5 = 14.50, 17.80


def pt_at(pts, story, x, y):
    c = [q for q, v in pts.items() if v["story"] == story and abs(v["x"] - x) < 0.02 and abs(v["y"] - y) < 0.02]
    assert len(c) == 1, (story, x, y, c)
    return c[0]


if __name__ == "__main__":
    S = {}
    e = None
    try:
        assert not os.path.exists(EDB6A + ".lock") and not os.path.exists(os.path.join(HERE, "Merage3_Rev6a.lock"))
        shutil.copy2(SRC, EDB6A)
        for ext in (".$et", ".ebk", ".msh", ".ico", ".EDB.tlog", ".Y_"):
            pth = os.path.join(HERE, "Merage3_Rev6a" + ext)
            if os.path.exists(pth):
                os.remove(pth)
        p("fresh copy", SRC, "->", EDB6A)
        e, m = connect(EDB6A)
        m.SetModelIsLocked(False)
        pts, frs, ars = geometry(m)
        # ---- 1. parking columns 16phi20
        base, new = "C50X50/16T16", "C50X50/16T20"
        rect = m.PropFrame.GetRectangle(base); rb = m.PropFrame.GetRebarColumn(base)
        p(" base", rect, rb)
        p(" SetRectangle", new, m.PropFrame.SetRectangle(new, rect[1], rect[2], rect[3]))
        args = list(rb[:-1]); args[8] = "20"
        p(" SetRebarColumn", m.PropFrame.SetRebarColumn(new, *args), m.PropFrame.GetRebarColumn(new))
        p(" SetModifiers", m.PropFrame.SetModifiers(new, list(m.PropFrame.GetModifiers(base)[0])))
        s1 = sorted((v["label"], f) for f, v in frs.items() if v["kind"] == "column" and v["story"] == "Story1")
        assert len(s1) == 12 and all(frs[f]["sec"] == base for _, f in s1)
        for lab, f in s1:
            assert m.FrameObj.SetSection(f, new, 0) == 0
        S["story1_columns_16T20"] = [lab for lab, _ in s1]
        p("1. Story1 columns ->", new, S["story1_columns_16T20"])
        # ---- 2. cantilever torsion J = 0.1
        cant = sorted((v["story"], v["label"], f) for f, v in frs.items() if v["kind"] == "beam" and v["label"] in ("B3", "B5", "B6"))
        assert len(cant) == 12, cant
        for st, lab, f in cant:
            mods = list(m.FrameObj.GetModifiers(f)[0]); mods[3] = 0.1
            assert m.FrameObj.SetModifiers(f, mods)[-1] == 0
        S["cantilevers_J0.1"] = [f"{st} {lab} ({f})" for st, lab, f in cant]
        p("2. J = 0.1 on", S["cantilevers_J0.1"])
        # ---- 3. landing: verify the model has only vertical point loads on C2 / C6 and no landing frame
        chk = []
        for f, v in frs.items():
            if v["kind"] == "column" and v["label"] in ("C2", "C6") and v["story"] != "Story5":
                r = m.FrameObj.GetLoadPoint(f)
                chk.append((v["story"], v["label"], [(r[2][k], r[5][k], round(r[6][k], 3), round(r[8][k], 2)) for k in range(r[0])]))
        inclined = [f for f, v in frs.items() if abs(v["zi"] - v["zj"]) > 0.01 and v["kind"] == "beam"]
        S["landing_check"] = {"column_point_loads": chk, "inclined_or_landing_frames": inclined}
        p("3. landing loads", chk, "inclined frames:", inclined)
        # ---- 7. penthouse extension
        c16, c18 = pt_at(pts, "Story5", 0.0, 13.5), pt_at(pts, "Story5", 2.35, 13.5)
        b17, b19 = pt_at(pts, "Story4", 0.0, 18.81), pt_at(pts, "Story4", 2.5, 18.81)
        t17, t19 = pt_at(pts, "Story4", 0.0, 20.01), pt_at(pts, "Story4", 2.5, 20.01)
        xyz = {k: m.PointObj.GetCoordCartesian(q)[:3] for k, q in (("b17", b17), ("b19", b19), ("t17", t17), ("t19", t19))}
        p("  ref points", c16, c18, b17, b19, t17, t19, xyz)
        newp = {}
        for k, src in (("P17", "b17"), ("P19", "b19"), ("E17", "t17"), ("E19", "t19")):
            x, y, _ = xyz[src]
            r = m.PointObj.AddCartesian(x, y, Z5, "", "")
            newp[k] = r[0]; p("  AddCartesian", k, x, y, Z5, r)
        ref_c = beam_c = None
        for f, v in frs.items():
            if v["story"] == "Story5" and v["label"] == "C16" and v["kind"] == "column":
                ref_c = f
            if v["story"] == "Story5" and v["label"] == "B30" and v["kind"] == "beam":
                beam_c = f
        ins_c, ins_b = m.FrameObj.GetInsertionPoint(ref_c), m.FrameObj.GetInsertionPoint(beam_c)
        mod_c, mod_b = list(m.FrameObj.GetModifiers(ref_c)[0]), list(m.FrameObj.GetModifiers(beam_c)[0])
        ax_c, ax_b = m.FrameObj.GetLocalAxes(ref_c)[0], m.FrameObj.GetLocalAxes(beam_c)[0]
        p("  ref column", ref_c, ins_c, mod_c, ax_c, "ref beam", beam_c, ins_b, mod_b, ax_b)
        added = {}
        for lab, i, j, sec, kind in (("C17", b17, newp["P17"], "C40X40/12T16", "c"), ("C19", b19, newp["P19"], "C40X40/12T16", "c"),
                                     ("B31", c16, newp["P17"], "BW40xH40", "b"), ("B33", c18, newp["P19"], "BW40xH40", "b"),
                                     ("B38", newp["P17"], newp["P19"], "BW40xH40", "b"), ("B3", newp["P17"], newp["E17"], "BW40xH40", "b"),
                                     ("B5", newp["P19"], newp["E19"], "BW40xH40", "b"), ("B2", newp["E17"], newp["E19"], "BW40xH40", "b")):
            r = m.FrameObj.AddByPoint(i, j, "", sec, "")
            f = r[0]; assert r[-1] == 0, r
            ins, mod, ax = (ins_c, mod_c, ax_c) if kind == "c" else (ins_b, mod_b, ax_b)
            m.FrameObj.SetInsertionPoint(f, ins[0], ins[1], ins[2], list(ins[3]), list(ins[4]), ins[5])
            m.FrameObj.SetModifiers(f, mod)
            m.FrameObj.SetLocalAxes(f, ax)
            added[f] = lab
            p("  AddByPoint", lab, i, j, sec, "->", f, m.FrameObj.GetLabelFromName(f)[:2])
        S["frames_added"] = added
        # slab panels (TIRCHEH, local axes as the panels below at Story4: F14 / F2; diaphragm D1; loads as F17)
        f17 = [a for a, v in ars.items() if v["story"] == "Story5" and v["label"] == "F17"][0]
        r = m.AreaObj.GetLoadUniform(f17)
        loads17 = [(r[2][k], r[3][k], r[4][k], r[5][k]) for k in range(r[0])]
        mass17 = m.AreaObj.GetMass(f17)[0]
        ax_below = {lab: m.AreaObj.GetLocalAxes([a for a, v in ars.items() if v["story"] == "Story4" and v["label"] == lab][0])[0] for lab in ("F14", "F2")}
        p("  F17 loads", loads17, "mass", mass17, "axes below", ax_below)
        anew = {}
        for lab, pp in (("F14", [c16, c18, newp["P19"], newp["P17"]]), ("F2", [newp["P17"], newp["P19"], newp["E19"], newp["E17"]])):
            r = m.AreaObj.AddByPoint(4, pp, "", "TIRCHEH", "")
            a = r[1] if isinstance(r[1], str) else r[-2]
            assert r[-1] == 0, r
            m.AreaObj.SetLocalAxes(a, ax_below[lab], 0)
            m.AreaObj.SetDiaphragm(a, "D1")
            m.AreaObj.SetEdgeConstraint(a, True, 0)
            for pat, cs, dr, val in loads17:
                assert m.AreaObj.SetLoadUniform(a, pat, val, dr, True, cs, 0) == 0
            m.AreaObj.SetMass(a, mass17, True)
            anew[a] = lab
            p("  area", lab, pp, "->", a, m.AreaObj.GetLabelFromName(a)[:2], "mass", m.AreaObj.GetMass(a)[0])
        S["areas_added"] = anew
        # curb 0.80: new edges on, old back edge (Story5 B36) off; joint masses at Story5
        b36 = [f for f, v in frs.items() if v["story"] == "Story5" and v["label"] == "B36" and v["kind"] == "beam"][0]
        rd = m.FrameObj.GetLoadDistributed(b36)
        p("  Story5 B36 loads before", [(rd[2][k], rd[10][k]) for k in range(rd[0])])
        assert rd[0] == 1 and rd[2][0] == "SuperDead" and abs(rd[10][0] - CURB) < 1e-6
        m.FrameObj.DeleteLoadDistributed(b36, "SuperDead", 0)
        dm = {}
        Lb36 = frs[b36]["L"]
        dm[frs[b36]["i"]] = -CURB * Lb36 / 2; dm[frs[b36]["j"]] = -CURB * Lb36 / 2
        curb_rows = [{"Story": "Story5", "Beam": "B36 (old back edge)", "UniqueName": b36, "L": Lb36, "w": -CURB}]
        for f, lab in added.items():
            if lab in ("B31", "B33", "B3", "B5", "B2"):
                assert m.FrameObj.SetLoadDistributed(f, "SuperDead", 1, 10, 0.0, 1.0, CURB, CURB, "Global", True, False, 0) == 0
                i, j, _ = m.FrameObj.GetPoints(f)
                a_, b_ = m.PointObj.GetCoordCartesian(i)[:3], m.PointObj.GetCoordCartesian(j)[:3]
                L = math.dist(a_, b_)
                dm[i] = dm.get(i, 0.0) + CURB * L / 2; dm[j] = dm.get(j, 0.0) + CURB * L / 2
                curb_rows.append({"Story": "Story5", "Beam": lab, "UniqueName": f, "L": round(L, 3), "w": CURB})
        mlog = []
        for q, dW in dm.items():
            ms = m.PointObj.GetMass(q)
            old = list(ms[0]) if ms[-1] == 0 else [0.0] * 6
            nw = max(old[0] + dW / G, 0.0)
            m.PointObj.SetMass(q, [nw, nw, 0, 0, 0, 0], 0, False, True)
            mlog.append((q, round(old[0] * G, 3), round(dW, 3), round(nw * G, 3)))
        S["curb"] = curb_rows; S["joint_mass_changes_kN"] = mlog
        p("  curb", curb_rows, "joint mass", mlog)
        # ---- 9. boss approval (coordinator, 2026-10-31, 2nd message): penthouse walls around the new part on the Story4 beams
        #      numbers from the FINAL architect note T43 (15:38): W-A / SH-B2 / SH-4 / OV-B / OV-R / OV-D, overrun removed,
        #      hook 25 kN under the Story5 slab at (1.45, 14.65), curb K-J. Story4 B36 wall (OV-F, existing) unchanged.
        dm2, rows9 = {}, []

        def fpts(f):
            i, j, _ = m.FrameObj.GetPoints(f)
            return i, j, math.dist(m.PointObj.GetCoordCartesian(i)[:3], m.PointObj.GetCoordCartesian(j)[:3])

        def addm(q, dW):
            dm2[q] = dm2.get(q, 0.0) + dW

        def rewrite(f, keep_fn, pats=("SuperDead", "Lr", "Live")):
            """delete the distributed + point loads of pats on f and re-add those keep_fn accepts; returns removed items"""
            i, j, L = fpts(f)
            rd = m.FrameObj.GetLoadDistributed(f); rp_ = m.FrameObj.GetLoadPoint(f)
            dist = [(rd[2][k], rd[5][k], rd[6][k], rd[7][k], rd[10][k], rd[11][k]) for k in range(rd[0]) if rd[2][k] in pats]
            pnt = [(rp_[2][k], rp_[5][k], rp_[6][k], rp_[8][k]) for k in range(rp_[0]) if rp_[2][k] in pats]
            for pat in pats:
                m.FrameObj.DeleteLoadDistributed(f, pat, 0); m.FrameObj.DeleteLoadPoint(f, pat, 0)
            removed = []
            for pat, dr, d1, d2, w1, w2 in dist:
                if keep_fn("d", pat, d1, d2, w1):
                    assert m.FrameObj.SetLoadDistributed(f, pat, 1, dr, d1, d2, w1, w2, "Global", True, False, 0) == 0
                else:
                    removed.append(("d", pat, round(d1, 4), round(d2, 4), round(w1, 3)))
                    if pat == "SuperDead":
                        W = w1 * (d2 - d1) * L; xc = (d1 + d2) / 2
                        addm(i, -W * (1 - xc)); addm(j, -W * xc)
            for pat, dr, t, P in pnt:
                if keep_fn("p", pat, t, t, P):
                    assert m.FrameObj.SetLoadPoint(f, pat, 1, dr, t, P, "Global", True, False, 0) == 0
                else:
                    removed.append(("p", pat, round(t, 4), round(P, 3)))
                    if pat == "SuperDead":
                        addm(i, -P * (1 - t)); addm(j, -P * t)
            return removed

        def is_ovr(kind, pat, d1, d2, w):
            if kind == "p":
                return True                                              # only the overrun back-wall point loads exist on B31/B33
            return (pat == "SuperDead" and (abs(w - 6.885) < 0.01 or abs(w - 5.828) < 0.01 or abs(w - 5.825) < 0.01)) or \
                   (pat == "Lr" and (abs(w - 0.95) < 0.01 or abs(w - 0.804) < 0.01))

        pts, frs, ars = geometry(m)
        s4 = {v["label"]: f for f, v in frs.items() if v["story"] == "Story4" and v["kind"] == "beam"}
        up = {}
        for q, v in pts.items():
            up[(v["story"], round(v["x"], 3), round(v["y"], 3))] = q
        for lab in ("B36", "B31", "B33"):
            rem = rewrite(s4[lab], lambda k, pat, d1, d2, w: not is_ovr(k, pat, d1, d2, w))
            rows9.append({"Story": "Story4", "Beam": lab, "UniqueName": s4[lab], "action": "elevator overrun removed", "removed": rem})
        # architect note T43 final (15:38, governs the numbers): walls on the Story4 beams, net lengths, mass half / half
        def up_of(q):
            return up[("Story5", round(pts[q]["x"], 3), round(pts[q]["y"], 3))]

        def add_line(f, w, r1, r2, half_up, what):
            i, j, L = fpts(f)
            assert m.FrameObj.SetLoadDistributed(f, "SuperDead", 1, 10, r1, r2, w, w, "Global", True, False, 0) == 0
            W = w * (r2 - r1) * L; xc = (r1 + r2) / 2
            k = 0.5 if half_up else 1.0
            addm(i, k * W * (1 - xc)); addm(j, k * W * xc)
            if half_up:
                addm(up_of(i), 0.5 * W * (1 - xc)); addm(up_of(j), 0.5 * W * xc)
            rows9.append({"Beam": frs[f]["label"], "Story": frs[f]["story"], "UniqueName": f, "what": what, "w_kN/m": w, "rel": (round(r1, 4), round(r2, 4)), "W_kN": round(W, 2)})

        def add_point(f, P, t, half_up, what):
            i, j, L = fpts(f)
            assert m.FrameObj.SetLoadPoint(f, "SuperDead", 1, 10, t, P, "Global", True, False, 0) == 0
            k = 0.5 if half_up else 1.0
            addm(i, k * P * (1 - t)); addm(j, k * P * t)
            if half_up:
                addm(up_of(i), 0.5 * P * (1 - t)); addm(up_of(j), 0.5 * P * t)
            rows9.append({"Beam": frs[f]["label"], "Story": frs[f]["story"], "UniqueName": f, "what": what, "P_kN": round(P, 3), "rel": round(t, 4)})

        def rel(f, y=None, x=None):
            v = frs[f]
            return (y - v["yi"]) / (v["yj"] - v["yi"]) if y is not None else (x - v["xi"]) / (v["xj"] - v["xi"])
        f31, f33, f38 = s4["B31"], s4["B33"], s4["B38"]
        # W-A: parapet 4.20 removed over Y 13.703-18.606 (kept on the column-face stubs), wall 8.41 there
        rem = rewrite(f31, lambda k, pat, d1, d2, w: not (k == "d" and pat == "SuperDead" and abs(w - 4.20) < 0.01 and d1 == 0 and d2 == 1))
        rows9.append({"Beam": "B31", "Story": "Story4", "UniqueName": f31, "what": "roof parapet 4.20 removed (full length, stubs re-added)", "removed": rem})
        ra, rb_ = rel(f31, y=13.703), rel(f31, y=18.606)
        add_line(f31, 4.20, 0.0, ra, False, "parapet stub (kept)"); add_line(f31, 4.20, rb_, 1.0, False, "parapet stub (kept)")
        add_line(f31, 8.41, ra, rb_, True, "W-A 20 cm h 2.90 (4.903 m)")
        add_line(f33, 8.41, rel(f33, y=15.703), rel(f33, y=18.606), True, "SH-B2 20 cm h 2.90 (2.903 m)")
        add_line(f33, 6.96, rel(f33, y=13.703), rel(f33, y=15.703), True, "OV-B 15 cm h 2.90 (2.000 m)")
        add_line(f38, 8.41, rel(f38, x=0.20), rel(f38, x=2.30), True, "SH-4 20 cm h 2.90 (2.100 m)")
        # OV-R (15 cm, h 2.99, 7.18 kN/m x 2.50 = 17.95 kN) on the slab parallel to the joists: like W17 -> point loads B31 / B33 at Y 15.628
        Wr = 7.18 * 2.50; xc = (-0.05 + 2.449) / 2
        R33 = Wr * min(max(xc / 2.35, 0), 1); R31 = Wr - R33
        add_point(f31, R31, rel(f31, y=15.628), True, "OV-R 15 cm h 2.99 (2.50 m) via joists, like W17")
        add_point(f33, R33, rel(f33, y=15.628), True, "OV-R 15 cm h 2.99 (2.50 m) via joists, like W17")
        # OV-D (10 cm, h 2.99, 5.38 kN/m x 1.80) perpendicular to the joists at X 0.399: lever rule to B31 / B33 over Y 13.754-15.553
        r1, r2 = rel(f31, y=13.754), rel(f31, y=15.553)
        add_line(f31, 5.38 * (1 - 0.399 / 2.35), r1, r2, True, "OV-D 10 cm h 2.99 (1.80 m), lever share")
        add_line(f33, 5.38 * (0.399 / 2.35), rel(f33, y=13.754), rel(f33, y=15.553), True, "OV-D 10 cm h 2.99 (1.80 m), lever share")
        # hook / rail 25 kN under the Story5 slab at (1.45, 14.65): joists span X -> new Story5 beams B31 / B33 at Y 14.65
        HOOK = 25.0
        n31 = [f for f, l in added.items() if l == "B31"][0]; n33 = [f for f, l in added.items() if l == "B33"][0]
        add_point(n31, HOOK * (1 - 1.45 / 2.38), rel(n31, y=14.65), False, "elevator hook / rail 25 kN (ASSUMPTION) at (1.45, 14.65), via joists")
        add_point(n33, HOOK * 1.45 / 2.38, rel(n33, y=14.65), False, "elevator hook / rail 25 kN (ASSUMPTION) at (1.45, 14.65), via joists")
        # curb K-J (0.45 m) on Story5 B36 east end
        add_point(b36, CURB * 0.45, 0.98, False, "curb K-J 0.20 x 0.20 (0.45 m, X 2.25-2.70, mostly on the slab edge) as a point load near C18")
        mlog2 = []
        for q, dW in dm2.items():
            ms = m.PointObj.GetMass(q)
            old = list(ms[0]) if ms[-1] == 0 else [0.0] * 6
            nw = old[0] + dW / G
            assert nw > -1e-6, (q, old[0] * G, dW)
            nw = max(nw, 0.0)
            m.PointObj.SetMass(q, [nw, nw, 0, 0, 0, 0], 0, False, True)
            mlog2.append((q, round(old[0] * G, 3), round(dW, 3), round(nw * G, 3)))
        S["step9_walls_overrun_hook"] = rows9; S["step9_joint_mass_kN"] = mlog2
        S["step9_mass_net_kN"] = round(sum(dm2.values()), 2)
        for r_ in rows9:
            p("  9.", r_)
        p("  9. joint mass", mlog2, "net", S["step9_mass_net_kN"])
        pts, frs, ars = geometry(m)
        lab_new = {"frames": {f: {"label": lab, "story": "Story5"} for f, lab in added.items()},
                   "areas": {a: {"label": lab, "story": "Story5"} for a, lab in anew.items()},
                   "points": {q: {"label": k} for k, q in newp.items()}}
        json.dump({"points": pts, "frames": frs, "areas": ars, "new_objects_project_labels": lab_new},
                  open(os.path.join(HERE, "geom_Rev6a.json"), "w", encoding="utf-8"), indent=0, ensure_ascii=False)
        S["new_objects_project_labels"] = lab_new
        p("save", m.File.Save(EDB6A)); S["saved"] = True
    except Exception:
        import traceback
        p(traceback.format_exc())
    json.dump(S, open(os.path.join(HERE, "r6a_build_summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    finish("r6a_build")
    try:
        e.ApplicationExit(False)
    except Exception:
        pass
    os._exit(0)
