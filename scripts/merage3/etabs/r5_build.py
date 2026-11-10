# -*- coding: utf-8 -*-
"""Merage3 Rev.5 model build (structural engineer, 2026-10-23).
Base: copy of Run 3 (A22 design combos, Omega0=3, mass method). Basis: architect plan Rev.5
(arch/Merage3_arch_plan_BASIS_geometry.json). Steps:
  1. grid: axis 4 18.75 -> 18.81, axis 5 19.95 -> 20.01 (table edit, numeric field only)
  2. geometry: move every joint at Y=18.75 / 19.95 by +0.06; joints of C19 line (X=2.35, Y=18.81/20.01) by +0.157 in X
  3. loads (pattern SuperDead): delete all SuperDead frame loads, apply new wall / parapet / facade / railing line loads,
     slab walls parallel to joists as point loads on the joist supports, equivalent partition on the slabs
  4. additional mass rebuilt (joint masses at beam ends + area masses), 1.0 D_added + 1.0 SD + 0.2 L
  5. Save (model only)
Writes: wall_loads_Rev5.csv, slab_wall_point_loads_Rev5.csv, partition_Rev5.json, build_summary.json, geom_after.json
"""
import sys, os, json, math, csv
from r5_common import *
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

GAMMA = {20: 2.9, 15: 2.4, 10: 1.8}       # kN/m2 of wall face: task05 (20, 15 cm) ; 10 cm = 1.8 (boss / vice proposal 5)
FACADE = 4.35 / 2.4                        # 1.8125 kN/m2 stone facade, as before (task05)
RAILING = 0.4                              # kN/m steel railing, front terrace (B10)
H_PARAPET_ROOF = 1.10 + 0.08               # parapet 1.10 above finish, from top of beam (ASSUMPTION: finish 0.08 as typical floors)
H_PH_WALL, H_PH_ROOF = 2.4, 0.6            # penthouse walls (as Run 2/3) ; penthouse roof wall 0.6 (vice proposal 6)
SD_BASE_FLOOR = 2.5                        # kN/m2 block + finish + ceiling (unchanged)
TYP = "typical (Story1..3 -> next)"
TYP_STORIES = ("Story1", "Story2", "Story3")
DY, DX_C19 = 0.06, 0.157
TOL = 1e-3


def edit_grid(m):
    key = "Grid Definitions - Grid Lines"
    db = m.DatabaseTables
    r = db.GetTableForEditingArray(key, "")
    ver, fields, n, data = r[0], list(r[1]), r[2], list(r[3])
    nf = len(fields)
    iid, iord = fields.index("ID"), fields.index("Ordinate")
    rows = [data[i * nf:(i + 1) * nf] for i in range(n)]
    new = {"4": "18/81", "5": "20/01"}
    for row in rows:
        if row[fields.index("LineType")].startswith("Y") and row[iid] in new:
            p("  grid", row[iid], row[iord], "->", new[row[iid]])
            row[iord] = new[row[iid]]
    # ETABS 19: editing works only with the field *display names* (GetAllFieldsInTable[3]); keys -> "LineType field not found"
    fi = db.GetAllFieldsInTable(key, 0, 0, [], [], [], [], [])
    fl = list(fi[3])
    assert len(fl) == nf
    flat = [v if v is not None else "" for row in rows for v in row]
    p("  SetTableForEditingArray", db.SetTableForEditingArray(key, ver, fl, n, flat)[-1])
    res = db.ApplyEditedTables(True)
    p("  ApplyEditedTables fatal/err/warn/info", res[0], res[1], res[2], res[3])
    if res[1]:
        p("  log:", str(res[4]).replace("\r\n", " | ")[:1200])
    gl = table(m, key)
    p(gl.to_string())
    ok = abs(float(gl[gl.ID.astype(str) == "4"]["Ordinate"].iloc[0]) - 18.81) < 1e-6 and abs(float(gl[gl.ID.astype(str) == "5"]["Ordinate"].iloc[0]) - 20.01) < 1e-6
    p("  CHECK grid 4=18.81, 5=20.01:", "OK" if ok else "FAILED")
    return ok


def move_points(m):
    pts, frs, ars = geometry(m)
    p("  joints at Y=18.75 / 19.95 after grid edit (must be unchanged, no glue):",
      sum(abs(v["y"] - 18.75) < TOL for v in pts.values()), sum(abs(v["y"] - 19.95) < TOL for v in pts.values()))
    sel_y = [q for q, v in pts.items() if abs(v["y"] - 18.75) < TOL or abs(v["y"] - 19.95) < TOL]
    m.SelectObj.ClearSelection()
    for q in sel_y:
        m.PointObj.SetSelected(q, True)
    p(f"  move +{DY} in Y: {len(sel_y)} joints ->", m.EditGeneral.Move(0, DY, 0))
    m.SelectObj.ClearSelection()
    pts, frs, ars = geometry(m)
    sel_x = [q for q, v in pts.items() if abs(v["x"] - 2.35) < TOL and (abs(v["y"] - 18.81) < TOL or abs(v["y"] - 20.01) < TOL)]
    for q in sel_x:
        m.PointObj.SetSelected(q, True)
    p(f"  move +{DX_C19} in X (C19 line, B5 cantilever): {len(sel_x)} joints ->", m.EditGeneral.Move(DX_C19, 0, 0))
    m.SelectObj.ClearSelection()
    pts, frs, ars = geometry(m)
    # checks
    bad = [q for q, v in pts.items() if abs(v["y"] - 18.75) < TOL or abs(v["y"] - 19.95) < TOL]
    c19 = [(v["story"], v["xi"], v["yi"]) for f, v in frs.items() if v["label"] == "C19"]
    p("  C19:", c19)
    for lab in ("B33", "B5", "B38", "B39", "B2", "B3", "B6", "B31", "B35"):
        p("  ", lab, [(v["story"], v["label_etabs"], (v["xi"], v["yi"]), (v["xj"], v["yj"]), v["L"]) for v in frs.values() if v["label"] == lab][:1])
    ok = not bad and len(c19) == 4 and all(abs(x - 2.507) < TOL and abs(y - 18.81) < TOL for _, x, y in c19) and len(sel_y) > 0
    p("  CHECK geometry:", "OK" if ok else "FAILED", "left at old Y:", bad)
    return ok, len(sel_y), len(sel_x)


def beam_on(frs, story, label):
    c = [f for f, v in frs.items() if v["story"] == story and v["label"] == label and v["kind"] == "beam"]
    assert len(c) == 1, (story, label, c)
    return c[0]


def beam_at(frs, story, line_x, y):
    """beam running in Y on line X ~ line_x (allows the slanted B33) that covers y; returns (frame, rel)"""
    for f, v in frs.items():
        if v["story"] != story or v["kind"] != "beam":
            continue
        if abs(v["yi"] - v["yj"]) < TOL:
            continue
        lo, hi = sorted((v["yi"], v["yj"]))
        if not (lo - TOL <= y <= hi + TOL):
            continue
        t = (y - v["yi"]) / (v["yj"] - v["yi"])
        x = v["xi"] + t * (v["xj"] - v["xi"])
        if abs(x - line_x) < 0.2:
            return f, t, x
    raise RuntimeError(f"no beam at {story} x={line_x} y={y}")


def wall_rows(arch, frs):
    """line loads on beams (kN/m over the full beam length) for Story1..5"""
    rows = []
    walls = arch["walls"]
    for st in TYP_STORIES:
        per = {}
        for w in walls:
            if not str(w.get("on", "")).startswith("beam") or TYP not in w["storeys"]:
                continue
            lab = w["on"].split()[1]
            per.setdefault(lab, []).append(w)
        for lab, ws in sorted(per.items()):
            f = beam_on(frs, st, lab)
            L = frs[f]["L"]
            wl = sum(w["storeys"][TYP]["net_area"] * GAMMA[w["thick_cm"]] for w in ws) / L
            fac = 0.0
            if lab == "B11":
                fac = sum(w["storeys"][TYP]["net_area"] for w in ws) * FACADE / L
            rows.append({"Story": st, "Beam": lab, "UniqueName": f, "L_m": L, "Walls": "+".join(w["id"] for w in ws),
                         "NetArea_m2": round(sum(w["storeys"][TYP]["net_area"] for w in ws), 3),
                         "Thick_cm": "/".join(str(w["thick_cm"]) for w in ws),
                         "WallLoad_kN/m": round(wl, 3), "Facade_kN/m": round(fac, 3), "Railing_kN/m": 0.0,
                         "Total_kN/m": round(wl + fac, 3), "Source": "arch JSON Rev.5, net area x unit weight / beam length"})
        f = beam_on(frs, st, "B10")
        rows.append({"Story": st, "Beam": "B10", "UniqueName": f, "L_m": frs[f]["L"], "Walls": "R1 (steel railing)", "NetArea_m2": 0,
                     "Thick_cm": "-", "WallLoad_kN/m": 0.0, "Facade_kN/m": 0.0, "Railing_kN/m": RAILING, "Total_kN/m": RAILING,
                     "Source": "front terrace steel railing h=1.10 (boss 2026-10-23), 0.4 kN/m"})
    # roof (Story4): parapet 1.10 on the perimeter, penthouse walls on A-B x 2-3; Story5: penthouse roof wall
    par = ["B1", "B31", "B3", "B7", "B34", "B35", "B6", "B2", "B10", "B11"]
    for lab in par:
        f = beam_on(frs, "Story4", lab)
        wl = GAMMA[20] * H_PARAPET_ROOF
        fac = FACADE * H_PARAPET_ROOF if lab in ("B10", "B11") else 0.0
        rows.append({"Story": "Story4", "Beam": lab, "UniqueName": f, "L_m": frs[f]["L"], "Walls": "roof parapet", "NetArea_m2": round(H_PARAPET_ROOF * frs[f]["L"], 3),
                     "Thick_cm": "20", "WallLoad_kN/m": round(wl, 3), "Facade_kN/m": round(fac, 3), "Railing_kN/m": 0.0, "Total_kN/m": round(wl + fac, 3),
                     "Source": f"parapet 1.10 above finish (h={H_PARAPET_ROOF} from beam top, ASSUMPTION); facade on front"})
    for st, h, note in (("Story4", H_PH_WALL, "penthouse perimeter wall (as Run 3)"), ("Story5", H_PH_ROOF, "penthouse roof wall h=0.6 (ASSUMPTION, vice proposal 6)")):
        for lab in ("B30", "B32", "B12", "B36"):
            f = beam_on(frs, st, lab)
            rows.append({"Story": st, "Beam": lab, "UniqueName": f, "L_m": frs[f]["L"], "Walls": note, "NetArea_m2": round(h * frs[f]["L"], 3),
                         "Thick_cm": "20", "WallLoad_kN/m": round(GAMMA[20] * h, 3), "Facade_kN/m": 0.0, "Railing_kN/m": 0.0,
                         "Total_kN/m": round(GAMMA[20] * h, 3), "Source": note})
    return rows


def slab_parallel_point_loads(arch, frs):
    """walls on slabs parallel to the joists (joists span in X between the beams on axes A, B, C):
    uniform wall line load on a double joist -> reactions on the two supporting beams at the wall's Y."""
    out = []
    supports = [(0.0, 2.35), (2.35, 7.15)]   # joist spans A-B and B-C (beam centre lines)
    for w in arch["walls"]:
        if w.get("joists") != "PARALLEL" or TYP not in w["storeys"]:
            continue
        assert w["dir"] == "X"
        y, a, b = w["line"], w["frm"], w["to"]
        q = w["storeys"][TYP]["net_area"] * GAMMA[w["thick_cm"]] / w["length"]   # kN/m along the wall
        for xs, xe in supports:
            lo, hi = max(a, xs), min(b, xe)
            if hi - lo < 1e-6:
                continue
            Wseg, xc = q * (hi - lo), (lo + hi) / 2
            Re = Wseg * (xc - xs) / (xe - xs)
            Rs = Wseg - Re
            for st in TYP_STORIES:
                for xl, R in ((xs, Rs), (xe, Re)):
                    f, t, x = beam_at(frs, st, xl, y)
                    out.append({"Story": st, "Wall": w["id"], "Y": y, "seg": f"{lo:.3f}-{hi:.3f}", "q_kN/m": round(q, 3), "SupportLine_X": xl,
                                "Beam": frs[f]["label"], "UniqueName": f, "RelDist": round(t, 4), "P_kN": round(R, 3)})
    return out


def partition(arch, ars):
    perp = [w for w in arch["walls"] if str(w.get("on", "")).startswith("slab") and w.get("joists") == "perpendicular" and TYP in w["storeys"] and "F3" not in w["on"]]
    W = sum(w["storeys"][TYP]["net_area"] * GAMMA[w["thick_cm"]] for w in perp)
    labs = ("F1", "F4", "F12", "F13", "F14")
    A = sum(v["A"] for v in ars.values() if v["story"] == "Story1" and v["label"] in labs)
    Aopen = sum(v["A"] for v in ars.values() if v["story"] == "Story1" and v["label"] == "A1")   # elevator opening inside F14
    q = W / (A - Aopen)
    w6 = [w for w in arch["walls"] if w["id"] == "W6"][0]
    AF3 = [v["A"] for v in ars.values() if v["story"] == "Story1" and v["label"] == "F3"][0]
    qF3 = w6["storeys"][TYP]["net_area"] * GAMMA[w6["thick_cm"]] / AF3
    par = [w for w in arch["walls"] if w.get("joists") == "PARALLEL" and TYP in w["storeys"]]
    Wpar = sum(w["storeys"][TYP]["net_area"] * GAMMA[w["thick_cm"]] for w in par)
    return {"walls": [w["id"] for w in perp], "W_perp_kN": round(W, 2), "A_slabs_m2": round(A, 3), "A_opening_m2": round(Aopen, 3),
            "q_partition_kN_m2": round(q, 3), "SD_slab_kN_m2": round(SD_BASE_FLOOR + q, 3), "W6_on_F3_kN": round(qF3 * AF3, 2),
            "q_F3_extra_kN_m2": round(qF3, 3), "parallel_walls": [w["id"] for w in par], "W_parallel_kN": round(Wpar, 2),
            "all_slab_walls_equiv_kN_m2": round((W + Wpar) / (A - Aopen), 3)}


def apply_loads(m, frs, ars, rows, pls, part):
    n = 0
    for f, v in frs.items():
        if v["kind"] == "beam":
            m.FrameObj.DeleteLoadDistributed(f, "SuperDead", 0)
            m.FrameObj.DeleteLoadPoint(f, "SuperDead", 0)
            n += 1
    p(f"  SuperDead frame loads deleted on {n} beams (Dead 1.912 untouched)")
    k = 0
    for r in rows:
        w = r["Total_kN/m"] if "Total_kN/m" in r else r["WallLoad_kN/m"]
        if w <= 0:
            continue
        ret = m.FrameObj.SetLoadDistributed(r["UniqueName"], "SuperDead", 1, 10, 0.0, 1.0, w, w, "Global", True, False, 0)
        assert ret == 0, r
        k += 1
    for r in pls:
        ret = m.FrameObj.SetLoadPoint(r["UniqueName"], "SuperDead", 1, 10, r["RelDist"], r["P_kN"], "Global", True, False, 0)
        assert ret == 0, r
    p(f"  line loads {k}, point loads {len(pls)}")
    na = 0
    for a, v in ars.items():
        if v["story"] in TYP_STORIES and v["label"] in ("F1", "F4", "F12", "F13", "F14"):
            assert m.AreaObj.SetLoadUniform(a, "SuperDead", part["SD_slab_kN_m2"], 10, True, "Global", 0) == 0
            na += 1
        if v["story"] in TYP_STORIES and v["label"] == "F3":
            assert m.AreaObj.SetLoadUniform(a, "SuperDead", SD_BASE_FLOOR + part["q_F3_extra_kN_m2"], 10, True, "Global", 0) == 0
            na += 1
    p(f"  slab SuperDead set on {na} areas: typical {part['SD_slab_kN_m2']}, F3 {SD_BASE_FLOOR + part['q_F3_extra_kN_m2']:.3f}")


def rebuild_mass(m, factors):
    pts = m.PointObj.GetNameList()[1]
    for q in pts:
        m.PointObj.DeleteMass(q)
    areas = m.AreaObj.GetNameList()[1]
    for a in areas:
        m.AreaObj.DeleteMass(a)
    joint, tot, skipped = {}, 0.0, 0
    tot_by = {}
    for f in m.FrameObj.GetNameList()[1]:
        i, j, _ = m.FrameObj.GetPoints(f)
        a = m.PointObj.GetCoordCartesian(i)[:3]; b = m.PointObj.GetCoordCartesian(j)[:3]
        L = math.dist(a, b)
        r = m.FrameObj.GetLoadDistributed(f)
        for k in range(r[0]):
            fac = factors.get(r[2][k], 0.0)
            if not fac:
                continue
            if r[3][k] != 1 or r[5][k] not in (6, 10):
                skipped += 1
                continue
            # trapezoid between relative distances r[6], r[7] with values r[10], r[11]; split to ends by statics
            d1, d2, w1, w2 = r[6][k], r[7][k], abs(r[10][k]), abs(r[11][k])
            W = (w1 + w2) / 2 * (d2 - d1) * L * fac
            if W <= 0:
                continue
            xc = d1 + (d2 - d1) * ((w1 + 2 * w2) / (3 * (w1 + w2)) if (w1 + w2) > 0 else 0.5)
            joint[i] = joint.get(i, 0.0) + W * (1 - xc) / G
            joint[j] = joint.get(j, 0.0) + W * xc / G
            tot += W; tot_by[r[2][k]] = tot_by.get(r[2][k], 0.0) + W
        r = m.FrameObj.GetLoadPoint(f)
        for k in range(r[0]):
            fac = factors.get(r[2][k], 0.0)
            if not fac:
                continue
            if r[3][k] != 1 or r[5][k] not in (6, 10):   # GetLoadPoint: ..., MyType[3], CSys[4], Dir[5], RelDist[6], Dist[7], Val[8]
                skipped += 1
                continue
            P, t = abs(r[8][k]) * fac, r[6][k]
            joint[i] = joint.get(i, 0.0) + P * (1 - t) / G
            joint[j] = joint.get(j, 0.0) + P * t / G
            tot += P; tot_by[r[2][k] + "(point)"] = tot_by.get(r[2][k] + "(point)", 0.0) + P
    for q, ms in joint.items():
        m.PointObj.SetMass(q, [ms, ms, 0, 0, 0, 0], 0, False, True)
    nar = 0
    for a in areas:
        r = m.AreaObj.GetLoadUniform(a)
        if not r[0]:
            continue
        qv = sum(factors.get(r[2][k], 0.0) * abs(r[5][k]) for k in range(r[0]) if r[4][k] in (6, 10))
        if qv > 0:
            m.AreaObj.SetMass(a, qv / G, True)
            n, ap, _ = m.AreaObj.GetPoints(a)
            xy = [m.PointObj.GetCoordCartesian(x)[:2] for x in ap]
            A = abs(sum(xy[k][0] * xy[k - 1][1] - xy[k - 1][0] * xy[k][1] for k in range(n))) / 2
            tot += qv * A; tot_by["area"] = tot_by.get("area", 0.0) + qv * A
            nar += 1
    p(f"  mass rebuilt: {len(joint)} joint masses, {nar} area masses, added weight {tot:.0f} kN {({k: round(v) for k, v in tot_by.items()})}; skipped {skipped}")
    return tot, tot_by


if __name__ == "__main__":
    S = {}
    try:
        e, m = connect()
        p("reopen from disk (discard any in-memory test edits):", m.File.OpenFile(EDB)); m.SetPresentUnits(6)
        m.SetModelIsLocked(False)
        arch = json.load(open(ARCH, encoding="utf-8"))
        assert arch["rev"] == "Rev.5"
        p("1. grid"); S["grid_ok"] = edit_grid(m)
        p("2. geometry"); S["geom_ok"], S["moved_y"], S["moved_x"] = move_points(m)
        assert S["geom_ok"], "geometry check failed -> STOP (not saved)"
        pts, frs, ars = geometry(m)
        json.dump({"points": pts, "frames": frs, "areas": ars}, open(os.path.join(HERE, "geom_after.json"), "w", encoding="utf-8"), indent=0, ensure_ascii=False)
        p("3. loads")
        rows = wall_rows(arch, frs)
        pls = slab_parallel_point_loads(arch, frs)
        part = partition(arch, ars)
        p("  partition", json.dumps(part, ensure_ascii=False))
        with open(os.path.join(HERE, "wall_loads_Rev5.csv"), "w", newline="", encoding="utf-8-sig") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
        with open(os.path.join(HERE, "slab_wall_point_loads_Rev5.csv"), "w", newline="", encoding="utf-8-sig") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(pls[0])); wr.writeheader(); wr.writerows(pls)
        json.dump(part, open(os.path.join(HERE, "partition_Rev5.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        apply_loads(m, frs, ars, rows, pls, part)
        sums = {}
        for r in rows:
            sums[r["Story"]] = sums.get(r["Story"], 0.0) + r["Total_kN/m"] * r["L_m"]
        for r in pls:
            sums[r["Story"] + " slab-wall points"] = sums.get(r["Story"] + " slab-wall points", 0.0) + r["P_kN"]
        S["line_load_totals_kN"] = {k: round(v, 1) for k, v in sums.items()}
        p("  totals", S["line_load_totals_kN"])
        p("4. mass")
        S["added_weight_kN"], S["added_by"] = rebuild_mass(m, {"Dead": 1.0, "Dead part": 1.0, "SuperDead": 1.0, "Live": 0.2})
        S["partition"] = part
        p("5. save", m.File.Save(EDB))
    except Exception:
        import traceback
        p(traceback.format_exc())
    json.dump(S, open(os.path.join(HERE, "build_summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    finish("build")
    os._exit(0)
