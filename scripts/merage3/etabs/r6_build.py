# -*- coding: utf-8 -*-
"""Merage3 Rev6 build (task 42, structural engineer, 2026-10-24).   python r6_build.py
Starts every time from a FRESH copy of _backup\\Merage3_Rev5_before_T42.EDB -> Merage3_Rev6.EDB (Rev5 untouched).
  1. storey heights = clear height + beam (boss, board "اصلاح مهم رئیس"): Story1 4.00, Story2-4 3.40, Story5 3.30;
     Base elevation 0.30 -> 0.00 (+-0.00 = top of foundation concrete = Base), if ETABS accepts it (checked, else kept)
  2. penthouse (Story5) beams BW40xH50 -> BW40xH40 (boss T40: stair-house beam 0.40)
  3. SuperDead rebuilt: walls with the new net heights (beam walls 2.40 -> 2.90, slab walls 2.59 -> 3.09; openings that
     reached the soffit grow with the wall, doors / lift door unchanged, parapets W4/W6 unchanged); roof parapet
     0.20 x 1.20 = 4.20 kN/m (+ stone facade on front); stair-house walls 2.90 (8.41 kN/m); stair-house roof curb
     0.20 x 0.20 (0.58 kN/m); elevator overrun on the roof; STAIR loads (new); equivalent partition recomputed
  4. added mass rebuilt, walls split HALF / HALF between the level below and the level above (incl. upper half of the
     ground-floor walls -> Story1); 1.0 D_added + 1.0 SD + 0.2 L
  5. save (model only). Results: r6_run.py
Writes: wall_loads_Rev6.csv, slab_wall_point_loads_Rev6.csv, partition_Rev6.json, stair_loads_Rev6.csv,
        ground_walls_SAFE_Rev6.csv, mass_Rev6.json, geom_Rev6.json, r6_build_summary.json, log_r6_build.txt
"""
import sys, os, json, math, csv, copy, shutil
import r5_common as RC
from r5_common import *
import r5_build as RB
from r5_build import wall_rows, slab_parallel_point_loads, partition, apply_loads, beam_on, beam_at, GAMMA, FACADE, TYP, TOL

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
EDB6 = os.path.join(HERE, "Merage3_Rev6.EDB")
SRC = os.path.join(HERE, "_backup", "Merage3_Rev5_before_T42.EDB")
GROUND = os.path.join(HERE, "..", "arch", "Merage3_arch_Rev8_ground_geometry.json")
HEIGHTS = {"Story1": 4.00, "Story2": 3.40, "Story3": 3.40, "Story4": 3.40, "Story5": 3.30}
BASE_ELEV = 0.0
BEAM_H, PH_BEAM_H, SLAB_T = 0.50, 0.40, 0.31
DH = 0.50                                  # typical wall height increase (3.40 - 2.90)
# roof items (boss T40 + vice task 42)
PARAPET_H = 1.20                           # from top of roof slab / beam (boss: 0.20 x 1.20)
PARAPET_W = GAMMA[20] * PARAPET_H + 0.72   # 3.48 wall + 0.72 (outer cement render + membrane upturn + coping) = 4.20 kN/m
PH_WALL_H = HEIGHTS["Story5"] - PH_BEAM_H  # 2.90 clear, stair-house walls on the roof beams
PH_CURB_H = 0.20                           # wall 0.20 x 0.20 on the stair-house roof (boss T40)
PH_CURB_W = 0.80                           # 2.9 x 0.20 + coping (architect T41)
OVR_D, OVR_EQ, OVR_LR = 33.0, 25.0, 8.0    # elevator overrun: slab+walls (architect T41), machine/hook allowance 20-30 (ASSUMPTION), roof live
# STAIR (architect T41, work/architecture/2026-10-24_T41_for_structural.md, coordination 66): core A-B, axis 2 -> W19.
# typical 20 x 0.170 / 0.30 (going 2.70, Y 8.958-11.658), parking 23 x 0.1739 / 0.28 (flight B 3.08 from grade Y 12.038,
# flight A 2.80 to Y 11.758). Structural scheme (architect's proposal, adopted): one-way inclined slab strips spanning in Y
# from the axis-3 beam (B36, floor level) to a half-landing beam on axis 2 (A2-B2 = C2-C6) at mid storey; landing beam
# 0.30 x 0.40 framed into C2 / C6 (boss T38d). Waist / landing slab t = 0.25 (ACI 318-19 Table 7.3.1.1, l/24 one end
# continuous for the ~6.0 m span; architect assumed 0.20) - DECISION of the structural engineer.
GC = 25.0                                  # reinforced concrete kN/m3 (Mabhas 6)
LL_STAIR = 4.79                            # ASCE 7-22 Table 4.3-1, stairs and exits 100 psf
T_SLAB = 0.25
Y2, Y3, Y_HL = 7.50, 13.50, 8.958          # axis 2, axis 3, half-landing edge
FLW, LANDW = 1.10, 1.15                    # flight width; landing width per strip (2.30 / 2)
RAIL = 0.3                                 # kN/m railing along the inner edge of each flight
LBEAM_W = GC * 0.30 * 0.40 * (2.35 - 0.50) # landing beam self weight 5.55 kN
COS = {"typ": 0.870, "gnd": 0.850}
FIN = {"typ": 4.43, "gnd": 4.54}           # steps + stone/mortar + render (architect table)
Q_LAND = GC * T_SLAB + 2.12                # 8.37 kN/m2


def strip(y_top, y_foot, kind, y3_support=True):
    """one strip: landing Y2..Y_HL, flight Y_HL..y_top, floor landing y_top..Y3 (if y3_support), foot at y_top (grade) otherwise.
    Simply supported between Y2 (landing beam) and the far support. Returns reactions (D, L) at axis 2 and at the far support."""
    qf = GC * T_SLAB / COS[kind] + FIN[kind]
    segs = [(Y2, Y_HL, Q_LAND, LANDW), (Y_HL, y_top, qf, FLW)]
    far = Y3 if y3_support else y_top
    if y3_support:
        segs.append((y_top, Y3, Q_LAND, LANDW))
    span = far - Y2
    out = {}
    for case in ("D", "L"):
        R2 = Rf = 0.0
        for y0, y1, q, w in segs:
            W = ((q if case == "D" else LL_STAIR) * w + (RAIL if (case == "D" and q == qf) else 0.0)) * (y1 - y0)
            yc = (y0 + y1) / 2
            Rf += W * (yc - Y2) / span; R2 += W * (far - yc) / span
        out[case] = (round(R2, 2), round(Rf, 2))
    return {"q_flight": round(qf, 2), "q_landing": round(Q_LAND, 2), "span": round(span, 3), "R": out}


def stair_actions():
    """landing-beam point loads on C2 / C6 (each) and axis-3 beam (B36) line loads, per level"""
    sA_t = strip(11.658, None, "typ"); sB_t = strip(11.658, None, "typ")            # typical: both strips span 7.50 -> 13.50
    sA_g = strip(11.758, None, "gnd")                                                  # parking flight A -> axis 3 at Story1
    sB_g = strip(12.038, None, "gnd", y3_support=False)                                # parking flight B, foot on grade
    out, info = {"col": {}, "B36": {}, "grade": {}}, {"typ": sA_t, "gnd_A": sA_g, "gnd_B": sB_g, "t_slab": T_SLAB, "landing_beam_kN": round(LBEAM_W, 2)}
    rel = {"Story1": 2.09 / 4.00, "Story2": 0.5, "Story3": 0.5, "Story4": 0.5}
    for st in ("Story1", "Story2", "Story3", "Story4"):
        a, b = (sA_g, sB_g) if st == "Story1" else (sA_t, sB_t)
        D = a["R"]["D"][0] + b["R"]["D"][0] + LBEAM_W
        L = a["R"]["L"][0] + b["R"]["L"][0]
        out["col"][st] = {"P_D_each": round(D / 2, 2), "P_L_each": round(L / 2, 2), "rel": round(rel[st], 4), "beam_total_D": round(D, 1), "beam_total_L": round(L, 1)}
    for lev in ("Story1", "Story2", "Story3", "Story4"):
        arr = sA_g if lev == "Story1" else sA_t                       # strip arriving at this level
        dep = sB_t if lev != "Story4" else None                       # strip leaving this level (none at the roof)
        D = arr["R"]["D"][1] + (dep["R"]["D"][1] if dep else 0.0)
        L = arr["R"]["L"][1] + (dep["R"]["L"][1] if dep else 0.0)
        out["B36"][lev] = {"D_total": round(D, 2), "L_total": round(L, 2)}
    out["grade"] = {"flight_B_foot_D": sB_g["R"]["D"][1], "flight_B_foot_L": sB_g["R"]["L"][1], "note": "strip footing / slab on grade at Y 12.04 (SAFE)"}
    return out, info


def arch_rev6():
    """arch JSON Rev.6 with the typical walls re-measured for the 3.40 storeys"""
    a = copy.deepcopy(json.load(open(ARCH, encoding="utf-8")))
    assert a["rev"] == "Rev.6", a["rev"]
    log = []
    for w in a["walls"]:
        s = w["storeys"].get(TYP)
        if not s:
            continue
        H = s["H_wall"]
        if H < 2.0:                     # parapets W4 / W6 (1.18 from the slab): unchanged
            log.append((w["id"], "parapet unchanged", H)); continue
        Hn = round(H + DH, 3)
        for o in s["openings"]:
            if abs(o["top"] - H) < 0.011:   # window / door-window / steel door up to the soffit -> grows with the wall
                o["top"] = Hn
            o["height"] = round(o["top"] - o["bottom"], 3)
            o["area"] = round(o["width"] * o["height"], 3)
        s["H_wall"] = Hn
        s["gross_area"] = round(w["length"] * Hn, 3)
        s["opening_area"] = round(sum(o["area"] for o in s["openings"]), 3)
        old = s["net_area"]
        s["net_area"] = round(s["gross_area"] - s["opening_area"], 3)
        log.append((w["id"], H, Hn, old, s["net_area"]))
    a["heights"]["storeys"] = {"ground (Base->Story1)": 4.00, "typical (Story1..3 -> next)": 3.40}
    return a, log


def roof_rows(rows, frs):
    """replace the Rev5 roof / penthouse rows of wall_rows() with the T40/T42 values"""
    out = [r for r in rows if r["Story"] in ("Story1", "Story2", "Story3")]
    for lab in ["B1", "B31", "B3", "B7", "B34", "B35", "B6", "B2", "B10", "B11"]:
        f = beam_on(frs, "Story4", lab)
        fac = FACADE * PARAPET_H if lab in ("B10", "B11") else 0.0
        out.append({"Story": "Story4", "Beam": lab, "UniqueName": f, "L_m": frs[f]["L"], "Walls": "roof parapet 0.20 x 1.20", "NetArea_m2": round(PARAPET_H * frs[f]["L"], 3),
                    "Thick_cm": "20", "WallLoad_kN/m": round(PARAPET_W, 3), "Facade_kN/m": round(fac, 3), "Railing_kN/m": 0.0, "Total_kN/m": round(PARAPET_W + fac, 3),
                    "Source": "boss T40: parapet 0.20 x 1.20 from TOS; 2.9 x 1.20 + 0.72 render/upturn/coping (ASSUMPTION) = 4.20; stone facade front"})
    for st, h, note in (("Story4", PH_WALL_H, "stair-house wall h 2.90 (3.30 - beam 0.40), no opening deducted (as Rev5)"),
                        ("Story5", PH_CURB_H, "stair-house roof wall 0.20 x 0.20 (boss T40)")):
        for lab in ("B30", "B32", "B12", "B36"):
            f = beam_on(frs, st, lab)
            out.append({"Story": st, "Beam": lab, "UniqueName": f, "L_m": frs[f]["L"], "Walls": note, "NetArea_m2": round(h * frs[f]["L"], 3),
                        "Thick_cm": "20", "WallLoad_kN/m": round(GAMMA[20] * h, 3), "Facade_kN/m": 0.0, "Railing_kN/m": 0.0,
                        "Total_kN/m": round(GAMMA[20] * h if st == "Story4" else PH_CURB_W, 3), "Source": note})
    return out


def wall_eligible(r):
    """full-height walls whose mass is split half / half (parapets, railing, roof parapet, curb: all at their own level)"""
    if r["Story"] in ("Story1", "Story2", "Story3"):
        return r["Beam"] not in ("B2", "B10")          # W4 parapet on B2, railing on B10
    return r["Story"] == "Story4" and r["Beam"] in ("B30", "B32", "B12", "B36")


def set_stories(m):
    S = {}
    r = m.Story.GetStories()
    S["before"] = {"base": r[2][0], "names": list(r[1]), "elev": list(r[2]), "h": list(r[3])}
    p("  stories before", S["before"])
    # base elevation -> 0.00 through the table (numeric field, display names)
    key = "Tower and Base Story Definitions"
    db = m.DatabaseTables
    try:
        rr = db.GetTableForEditingArray(key, "")
        ver, fields, n, data = rr[0], list(rr[1]), rr[2], list(rr[3])
        nf = len(fields); p("  base table fields", fields, data)
        rows = [list(data[i * nf:(i + 1) * nf]) for i in range(n)]
        ie = fields.index("BSElev")
        rows[0][ie] = "0"
        fi = db.GetAllFieldsInTable(key, 0, 0, [], [], [], [], [])
        fl = list(fi[3]); assert len(fl) == nf
        flat = [v if v is not None else "" for row in rows for v in row]
        p("  Set base table", db.SetTableForEditingArray(key, ver, fl, n, flat)[-1])
        res = db.ApplyEditedTables(True)
        p("  ApplyEditedTables fatal/err/warn/info", res[0], res[1], res[2], res[3], str(res[4]).replace("\r\n", " | ")[:600])
    except Exception as ex:
        p("  base elevation edit failed:", ex)
    for st, h in HEIGHTS.items():
        try:
            ret = m.Story.SetHeight(st, h)
        except Exception as ex:
            ret = f"err {ex}"
        p("  SetHeight", st, h, ret)
    r = m.Story.GetStories()
    S["after"] = {"base": r[2][0], "names": list(r[1]), "elev": [round(x, 4) for x in r[2]], "h": [round(x, 4) for x in r[3]]}
    p("  stories after", S["after"])
    hok = all(abs(dict(zip(r[1], r[3]))[s] - h) < 1e-6 for s, h in HEIGHTS.items())
    S["base_ok"] = abs(r[2][0] - BASE_ELEV) < 1e-6
    S["heights_ok"] = hok
    return S


def penthouse_beams(m, frs):
    rect = m.PropFrame.GetRectangle("BW40xH50")
    rb = m.PropFrame.GetRebarBeam("BW40xH50")
    p("  BW40xH50", rect, rb)
    p("  SetRectangle BW40xH40", m.PropFrame.SetRectangle("BW40xH40", rect[1], 0.40, 0.40))
    p("  SetRebarBeam", m.PropFrame.SetRebarBeam("BW40xH40", rb[0], rb[1], rb[2], rb[3], rb[4], rb[5], rb[6], rb[7]))
    mods = list(m.PropFrame.GetModifiers("BW40xH50")[0])
    p("  SetModifiers", m.PropFrame.SetModifiers("BW40xH40", mods))
    ch = []
    for f, v in frs.items():
        if v["story"] == "Story5" and v["kind"] == "beam":
            assert v["sec"] == "BW40xH50", (f, v["sec"])
            assert m.FrameObj.SetSection(f, "BW40xH40", 0) == 0
            ch.append((f, v["label"]))
    p("  Story5 beams -> BW40xH40:", ch)
    return ch


def apply_stair_overrun(m, frs, act):
    rows = []
    for st, c in act["col"].items():
        for lab in ("C2", "C6"):
            f = [u for u, v in frs.items() if v["story"] == st and v["label"] == lab and v["kind"] == "column"]
            assert len(f) == 1, (st, lab, f)
            f = f[0]
            for pat, val in (("SuperDead", c["P_D_each"]), ("Live", c["P_L_each"])):
                assert m.FrameObj.SetLoadPoint(f, pat, 1, 10, c["rel"], val, "Global", True, False, 0) == 0
                rows.append({"Story": st, "Member": lab, "UniqueName": f, "Kind": "half landing on column (landing beam)", "Pattern": pat,
                             "Type": "point", "Rel1": c["rel"], "Rel2": "", "Value": val, "Unit": "kN"})
    for lev, d in act["B36"].items():
        f = beam_on(frs, lev, "B36")
        for pat, tot in (("SuperDead", d["D_total"]), ("Live", d["L_total"])):
            w = tot / frs[f]["L"]
            assert m.FrameObj.SetLoadDistributed(f, pat, 1, 10, 0.0, 1.0, w, w, "Global", True, False, 0) == 0
            rows.append({"Story": lev, "Member": "B36", "UniqueName": f, "Kind": "stair strips at axis 3 (floor landing + flight)", "Pattern": pat,
                         "Type": "line", "Rel1": 0, "Rel2": 1, "Value": round(w, 3), "Unit": "kN/m"})
    # elevator overrun on the roof (Story4): 4 sides, shares by length
    sides = {"B36": 2.65, "B31": 2.10, "B33": 2.10, "back": 2.65}
    Ls = sum(sides.values())
    yb = 15.628
    for pat, tot in (("SuperDead", OVR_D + OVR_EQ), ("Lr", OVR_LR)):
        f = beam_on(frs, "Story4", "B36")
        w = tot * sides["B36"] / Ls / frs[f]["L"]
        assert m.FrameObj.SetLoadDistributed(f, pat, 1, 10, 0.0, 1.0, w, w, "Global", True, False, 0) == 0
        rows.append({"Story": "Story4", "Member": "B36", "UniqueName": f, "Kind": "elevator overrun front", "Pattern": pat, "Type": "line", "Rel1": 0, "Rel2": 1, "Value": round(w, 3), "Unit": "kN/m"})
        for lab, xl in (("B31", 0.0), ("B33", 2.35)):
            f, t, x = beam_at(frs, "Story4", xl, 13.5 + 2.2)
            t0 = (13.5 - frs[f]["yi"]) / (frs[f]["yj"] - frs[f]["yi"])
            a, b = sorted((t0, t))
            w = tot * sides[lab] / Ls / (abs(b - a) * frs[f]["L"])
            assert m.FrameObj.SetLoadDistributed(f, pat, 1, 10, round(a, 4), round(b, 4), w, w, "Global", True, False, 0) == 0
            rows.append({"Story": "Story4", "Member": frs[f]["label"], "UniqueName": f, "Kind": "elevator overrun side", "Pattern": pat, "Type": "partial line",
                         "Rel1": round(a, 4), "Rel2": round(b, 4), "Value": round(w, 3), "Unit": "kN/m"})
            f, t, x = beam_at(frs, "Story4", xl, yb)
            P = tot * sides["back"] / Ls / 2
            assert m.FrameObj.SetLoadPoint(f, pat, 1, 10, round(t, 4), P, "Global", True, False, 0) == 0
            rows.append({"Story": "Story4", "Member": frs[f]["label"], "UniqueName": f, "Kind": "elevator overrun back wall (on slab, to the beams)", "Pattern": pat,
                         "Type": "point", "Rel1": round(t, 4), "Rel2": "", "Value": round(P, 3), "Unit": "kN"})
    return rows


def ground_walls(frs, pts):
    """ground-floor walls (Rev.8, on foundation): line loads for SAFE and the upper half of their mass for Story1"""
    gj = json.load(open(GROUND, encoding="utf-8"))
    H_b, H_s = HEIGHTS["Story1"] - BEAM_H, HEIGHTS["Story1"] - SLAB_T
    beams1 = {f: v for f, v in frs.items() if v["story"] == "Story1" and v["kind"] == "beam"}
    rows, jm = [], {}
    for w in gj["walls"]:
        x0, x1 = w["x"]; y0, y1 = w["y"]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        dirx = (x1 - x0) > (y1 - y0)
        best = None
        for f, v in beams1.items():
            bx = abs(v["xi"] - v["xj"]) > TOL
            if bx != dirx:
                continue
            if dirx:
                if abs(v["yi"] - v["yj"]) > TOL:
                    continue
                d = abs(cy - v["yi"]); lo, hi = sorted((v["xi"], v["xj"])); inside = lo - 0.3 <= cx <= hi + 0.3
            else:
                lo, hi = sorted((v["yi"], v["yj"]))
                if not (lo - 0.3 <= cy <= hi + 0.3):
                    continue
                t = (cy - v["yi"]) / (v["yj"] - v["yi"])
                d = abs(cx - (v["xi"] + t * (v["xj"] - v["xi"]))); inside = True
            if inside and d <= 0.30 and (best is None or d < best[1]):
                best = (f, d)
        H = H_b if best else H_s
        g = GAMMA[w["thick_cm"]]
        fac = FACADE if w["id"] == "G-F2" else 0.0
        q = (g + fac) * H                                       # kN/m along the net wall length
        W = q * w["net_length"]
        shares = []
        if best:
            f = best[0]; v = frs[f]
            if dirx:
                t = (cx - v["xi"]) / (v["xj"] - v["xi"])
            else:
                t = (cy - v["yi"]) / (v["yj"] - v["yi"])
            t = min(max(t, 0.0), 1.0)
            shares = [(v["i"], (1 - t)), (v["j"], t)]
            on = f"beam {v['label']} (Story1 above)"
        else:   # under a slab: split to the two Story1 beams on the X lines (0.00 / ~2.40) at the wall's Y, lever rule
            fa, ta, xa = beam_at(frs, "Story1", 0.0, cy)
            fb, tb, xb = beam_at(frs, "Story1", 2.35, cy)
            r = min(max((cx - xa) / (xb - xa), 0.0), 1.0)
            shares = [(frs[fa]["i"], (1 - r) * (1 - ta)), (frs[fa]["j"], (1 - r) * ta), (frs[fb]["i"], r * (1 - tb)), (frs[fb]["j"], r * tb)]
            on = f"slab (between {frs[fa]['label']} / {frs[fb]['label']})"
        for q_, s in shares:
            jm[q_] = jm.get(q_, 0.0) + 0.5 * W * s
        rows.append({"Wall": w["id"], "thick_cm": w["thick_cm"], "x0": x0, "x1": x1, "y0": y0, "y1": y1, "length": w["length"], "net_length": w["net_length"],
                     "openings": "+".join(f"{o.get('tag')} {o.get('width')}" for o in w["openings"]), "H_m": round(H, 2), "unit_kN/m2": g, "facade_kN/m2": round(fac, 4),
                     "q_kN/m (on net length)": round(q, 3), "W_kN": round(W, 2), "under": on, "half_to_Story1_kN": round(W / 2, 2)})
    return rows, jm


def rebuild_mass_r6(m, factors, pts, frs, ars, wall_items, point_items, part, ground_jm):
    """r5 mass rebuild (joint masses at frame ends by statics + area masses) with walls split half / half."""
    for q in m.PointObj.GetNameList()[1]:
        m.PointObj.DeleteMass(q)
    for a in m.AreaObj.GetNameList()[1]:
        m.AreaObj.DeleteMass(a)
    W_j = {}                 # kN at joints
    tot_by, skipped = {}, 0
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
                skipped += 1; continue
            d1, d2, w1, w2 = r[6][k], r[7][k], abs(r[10][k]), abs(r[11][k])
            W = (w1 + w2) / 2 * (d2 - d1) * L * fac
            if W <= 0:
                continue
            xc = d1 + (d2 - d1) * ((w1 + 2 * w2) / (3 * (w1 + w2)) if (w1 + w2) > 0 else 0.5)
            W_j[i] = W_j.get(i, 0.0) + W * (1 - xc); W_j[j] = W_j.get(j, 0.0) + W * xc
            tot_by[r[2][k]] = tot_by.get(r[2][k], 0.0) + W
        r = m.FrameObj.GetLoadPoint(f)
        for k in range(r[0]):
            fac = factors.get(r[2][k], 0.0)
            if not fac:
                continue
            if r[3][k] != 1 or r[5][k] not in (6, 10):
                skipped += 1; continue
            P, t = abs(r[8][k]) * fac, r[6][k]
            W_j[i] = W_j.get(i, 0.0) + P * (1 - t); W_j[j] = W_j.get(j, 0.0) + P * t
            tot_by[r[2][k] + "(point)"] = tot_by.get(r[2][k] + "(point)", 0.0) + P
    # half / half: walls on beams (line + parallel-wall point loads)
    idx = {(v["story"], round(v["x"], 3), round(v["y"], 3)): q for q, v in pts.items()}
    order = ["Base", "Story1", "Story2", "Story3", "Story4", "Story5"]
    moved, lost = 0.0, []

    def up(q, Wq):
        nonlocal moved
        v = pts[q]
        k = order.index(v["story"])
        qa = idx.get((order[k + 1], round(v["x"], 3), round(v["y"], 3))) if k + 1 < len(order) else None
        if qa is None:
            lost.append((q, v["story"], round(Wq, 2))); return
        W_j[q] -= Wq; W_j[qa] = W_j.get(qa, 0.0) + Wq; moved += Wq
    for r_ in wall_items:
        v = frs[r_["UniqueName"]]
        W = r_["Total_kN/m"] * v["L"]
        up(v["i"], 0.5 * W / 2); up(v["j"], 0.5 * W / 2)
    for r_ in point_items:
        v = frs[r_["UniqueName"]]
        up(v["i"], 0.5 * r_["P_kN"] * (1 - r_["RelDist"])); up(v["j"], 0.5 * r_["P_kN"] * r_["RelDist"])
    g_tot = 0.0
    for q, Wq in ground_jm.items():
        W_j[q] = W_j.get(q, 0.0) + Wq; g_tot += Wq
    tot_by["ground walls upper half"] = g_tot
    for q, Wq in W_j.items():
        if Wq < -1e-6:
            raise RuntimeError(f"negative joint weight {q} {Wq}")
        ms = Wq / G
        m.PointObj.SetMass(q, [ms, ms, 0, 0, 0, 0], 0, False, True)
    # areas: partition q split half / half to the same slab label one level up
    qpart = part["q_partition_kN_m2"]
    labs = ("F1", "F4", "F12", "F13", "F14")
    area_extra = {}
    for a, v in ars.items():
        if v["label"] in labs and v["story"] in ("Story1", "Story2", "Story3"):
            k = order.index(v["story"])
            above = [u for u, w in ars.items() if w["label"] == v["label"] and w["story"] == order[k + 1]]
            assert len(above) == 1, (v, above)
            area_extra[a] = area_extra.get(a, 0.0) - qpart / 2
            area_extra[above[0]] = area_extra.get(above[0], 0.0) + qpart / 2
    nar, A_tot, area_tot = 0, 0.0, 0.0
    for a in m.AreaObj.GetNameList()[1]:
        r = m.AreaObj.GetLoadUniform(a)
        qv = sum(factors.get(r[2][k], 0.0) * abs(r[5][k]) for k in range(r[0]) if r[4][k] in (6, 10)) if r[0] else 0.0
        qv += area_extra.get(a, 0.0)
        if qv > 0:
            m.AreaObj.SetMass(a, qv / G, True)
            v = ars[a]
            area_tot += qv * v["A"]; nar += 1
    tot_by["area"] = area_tot
    tot = sum(W_j.values()) + area_tot
    p(f"  mass rebuilt: {len(W_j)} joints, {nar} areas, added weight {tot:.0f} kN; moved up {moved:.1f} kN; ground half {g_tot:.1f}; skipped {skipped}; no joint above: {lost}")
    by_story = {}
    for q, Wq in W_j.items():
        by_story[pts[q]["story"]] = by_story.get(pts[q]["story"], 0.0) + Wq
    for a, v in ars.items():
        r = m.AreaObj.GetMass(a)
        by_story[v["story"]] = by_story.get(v["story"], 0.0) + (r[0] * G * v["A"] if r[-1] == 0 else 0)
    return {"added_weight_kN": round(tot, 1), "by": {k: round(v, 1) for k, v in tot_by.items()}, "moved_up_kN": round(moved, 1),
            "ground_half_kN": round(g_tot, 1), "no_joint_above": lost, "added_by_story_kN": {k: round(v, 1) for k, v in by_story.items()},
            "partition_half_kN_m2": qpart / 2}


def wcsv(name, rows):
    with open(os.path.join(HERE, name), "w", newline="", encoding="utf-8-sig") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)


if __name__ == "__main__":
    S = {}
    try:
        assert not os.path.exists(os.path.join(HERE, "Merage3_Rev6.EDB.lock"))
        shutil.copy2(SRC, EDB6)
        for ext in (".$et", ".ebk", ".msh", ".ico", ".EDB.tlog"):
            pth = os.path.join(HERE, "Merage3_Rev6" + ext)
            if os.path.exists(pth):
                os.remove(pth)
        p("fresh copy", SRC, "->", EDB6)
        e, m = connect(EDB6)
        m.SetModelIsLocked(False)
        p("1. stories"); S["stories"] = set_stories(m)
        assert S["stories"]["heights_ok"], "storey heights not applied -> STOP (not saved)"
        p("1b. re-add area objects (ETABS 19 SetHeight leaves the deck mesh at the old elevations)")
        from r6_areafix import recreate_areas
        _, alog_ = recreate_areas(m)
        S["areas_readded"] = len(alog_)
        pts, frs, ars = geometry(m)
        zz = sorted({round(v["z"], 3) for v in pts.values()})
        p("  joint z levels:", zz); S["joint_z"] = zz
        p("2. penthouse beams"); S["ph_beams"] = penthouse_beams(m, frs)
        pts, frs, ars = geometry(m)
        json.dump({"points": pts, "frames": frs, "areas": ars}, open(os.path.join(HERE, "geom_Rev6.json"), "w", encoding="utf-8"), indent=0, ensure_ascii=False)
        p("3. loads")
        arch6, alog = arch_rev6()
        for x in alog:
            p("   wall", x)
        rows = roof_rows(wall_rows(arch6, frs), frs)
        pls = slab_parallel_point_loads(arch6, frs)
        part = partition(arch6, ars)
        p("  partition", json.dumps(part, ensure_ascii=False))
        wcsv("wall_loads_Rev6.csv", rows); wcsv("slab_wall_point_loads_Rev6.csv", pls)
        json.dump(part, open(os.path.join(HERE, "partition_Rev6.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        apply_loads(m, frs, ars, rows, pls, part)
        n = 0
        for f, v in frs.items():                         # no Live / Lr frame loads existed in Rev5; clear to be safe
            for pat in ("Live", "Lr"):
                m.FrameObj.DeleteLoadDistributed(f, pat, 0); m.FrameObj.DeleteLoadPoint(f, pat, 0)
            if v["kind"] == "column":
                m.FrameObj.DeleteLoadPoint(f, "SuperDead", 0)
        act, sinfo = stair_actions()
        p("  stair", json.dumps(act), json.dumps(sinfo))
        srows = apply_stair_overrun(m, frs, act)
        wcsv("stair_loads_Rev6.csv", srows)
        S["stair"] = {"actions": act, "info": sinfo}
        sums = {}
        for r in rows:
            sums[r["Story"]] = sums.get(r["Story"], 0.0) + r["Total_kN/m"] * r["L_m"]
        for r in pls:
            sums[r["Story"] + " slab-wall points"] = sums.get(r["Story"] + " slab-wall points", 0.0) + r["P_kN"]
        S["line_load_totals_kN"] = {k: round(v, 1) for k, v in sums.items()}
        S["partition"] = part
        p("  totals", S["line_load_totals_kN"])
        grows, gjm = ground_walls(frs, pts)
        wcsv("ground_walls_SAFE_Rev6.csv", grows)
        S["ground_walls_total_kN"] = round(sum(r["W_kN"] for r in grows), 1)
        p("  ground walls total", S["ground_walls_total_kN"])
        p("4. mass (half / half)")
        elig = [r for r in rows if wall_eligible(r)]
        S["mass"] = rebuild_mass_r6(m, {"Dead": 1.0, "Dead part": 1.0, "SuperDead": 1.0, "Live": 0.2}, pts, frs, ars, elig, pls, part, gjm)
        json.dump(S["mass"], open(os.path.join(HERE, "mass_Rev6.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
        p("5. save", m.File.Save(EDB6)); S["saved"] = True
    except Exception:
        import traceback
        p(traceback.format_exc())
    json.dump(S, open(os.path.join(HERE, "r6_build_summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    finish("r6_build")
    os._exit(0)
