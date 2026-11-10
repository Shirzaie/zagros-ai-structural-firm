# -*- coding: utf-8 -*-
"""Merage3 - task 48 (2026-10-31): structural drawings Rev2 FOR APPROVAL from ETABS Rev6c, SCALE 1:50 (boss 2026-10-31).
Same sheet layout as Rev1 (A3 frames at 1:50 = A1 frames at 1:50: plotted on A1 with 20 mm per metre).
Boss orders: joists of the 7.5 m bay in Y, length 8 m, 3 tie beams per bay; stair-house joists in X (2.3); stair t = 0.20;
elevator pit 2.00; hook 25 kN approved.
Rev1 header:
Re-uses the T34 drawing toolkit (work/structural/T34/make_struct_T34.py: layers, Sheet, grids, columns, beams, tables, details)
and adds the Rev1 sheets. A3 sheets; EVERYTHING at 1:50 (company rule, boss 1405/08/08): plans, sections and details (k = 1);
small details are made readable by dimensions and labels, not by enlarging. Model units = metres at 1:50.

  S-101 grid & column layout + column schedule + column sections
  S-102 typical floor framing plan, floors 1-3 (ETABS Story1-3)
  S-103 roof framing plan (Story4) + stair-house roof (Story5, extended to axis 5, hook beam, sleeves)
  S-104 beam schedule floors 1-3
  S-105 beam schedule roof + stair-house roof + typical details + general notes
  S-106 cantilever details + elevator hook beam BH
  S-107 stair details: waist slab t = 0.25, landing beam, sliding corbel seat, sliding top bearing on B36

Inputs (read only): ETABS/geom_Rev6b.json, T46/t46_design.json, T46/t46_hand_checks.json.
    python t46_design.py && python make_struct_Rev1.py && python plot_Rev1.py
AutoCAD lock: Merage3/work/_autocad.lock is checked / created / removed around the accoreconsole run."""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)   # T34 toolkit copied here as t34_toolkit.py (the original T34 script was deleted with the old drawings)
import t34_toolkit as M                                          # noqa: E402
from t34_toolkit import Sheet, grids, column, beams_plan, joist, opening, level_mark, table, notes, legend, TA  # noqa: E402
import ezdxf                                                         # noqa: E402

GEOM = os.path.join(PRJ, "ETABS", "geom_Rev6c.json")
DES = os.path.join(HERE, "t48_design.json")
HC = os.path.join(HERE, "t48_hand_checks.json")
OUT_DIR = os.path.join(PRJ, "struct")
OUT_DWG = os.path.join(OUT_DIR, "Merage3_struct_Rev2.dwg")
TMP = "C:/ZagrosTemp/rev2"
LOCK = os.path.join(PRJ, "work", "_autocad.lock")
DATE = "1405/08/09"
SHEETS = ["S-101", "S-102", "S-103", "S-104", "S-105", "S-106", "S-107"]
SRC = "Source: ETABS Merage3_Rev6c.EDB (task 48), ACI 318-19, 51 A22 combos, Ax = 1.17 - read only; levels arch Rev.10/11"
M.LEVELS = [("Story1", "FLOOR 1", "طبقه ى اول", 4.00, 4.30), ("Story2", "FLOOR 2", "طبقه ى دوم", 7.40, 7.70),
            ("Story3", "FLOOR 3", "طبقه ى سوم", 10.80, 11.10), ("Story4", "ROOF", "بام", 14.20, 14.50),
            ("Story5", "STAIR-HOUSE ROOF", "بام خرپشته", 17.50, 17.80)]
M.DATE = DATE


def frame(sh, title_fa, title_en, sheet_no, source, tpos=(15.0, 2.0)):
    if "Rev5" in source:
        source = SRC
    fx0, fy0 = sh.fx0, sh.fy0
    fx1, fy1 = fx0 + M.SHEET_W, fy0 + M.SHEET_H
    m = 1.0
    sh.poly("S-ANNO-TTLB", [(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)])
    sh.poly("S-ANNO-BRDR", [(fx0 + m, fy0 + m), (fx1 - m, fy0 + m), (fx1 - m, fy1 - m), (fx0 + m, fy1 - m)])
    tw, th = 17.0, 6.6
    bx1, by0 = fx1 - m, fy0 + m
    bx0, by1 = bx1 - tw, by0 + th
    sh.poly("S-ANNO-TTLB", [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)])
    rows = [("شرکت آهن بتن زاگرس - سهامی خاص", 0.40, True),
            ("پروژه: مرآژ ۳ - Merage3 - مسکونی ۳ طبقه روی پارکینگ - مینودشت", 0.32, True),
            ("عنوان: " + title_fa, 0.30, True),
            ("مهندس محاسب: رحمت الله شیرزایی", 0.40, True),
            (f"مقیاس: 1:50     تاریخ: {DATE}     شماره نقشه: {sheet_no}     ویرایش: Rev2", 0.24, True),
            ("وضعیت: برای تأیید - برای اجرا نیست", 0.34, True),
            (source, 0.15, False)]
    rh = th / len(rows)
    for k, (s, hh, f) in enumerate(rows):
        yy = by1 - (k + 0.5) * rh
        if k:
            sh.L("S-ANNO-TTLB", (bx0, by1 - k * rh), (bx1, by1 - k * rh))
        sh.T(s, (bx0 + bx1) / 2, yy, hh, farsi=f, width=1.0 if f else 0.8)
    sh.T(title_fa + " - برای تأیید", fx0 + tpos[0], fy1 - tpos[1], 0.50, farsi=True)
    sh.T(title_en + "  -  FOR APPROVAL, NOT FOR CONSTRUCTION", fx0 + tpos[0], fy1 - tpos[1] - 0.75, 0.25 if tpos[0] < 20 else 0.17)
    return bx0, by1


M.frame = frame


def _patch_t34_to_1_100():
    """company rule: details at 1:50. Re-define the T34 detail routines with the scale factor 1 and the hook marks scaled."""
    import inspect
    for name, reps in (("col_section", [("S = 5.0", "S = 1.0"), ("0.35, cv + hi - 0.35", "0.07, cv + hi - 0.07"),
                                        ("0.33, cv + hi - 0.02 - 0.31", "0.066, cv + hi - 0.02 - 0.062"), ("SC 1:" + "20", "SC 1:50")]),
                       ("beam_section", [("S = 5.0", "S = 1.0"), ("cu - hi_u + 0.35, cv + hi_v - 0.35", "cu - hi_u + 0.07, cv + hi_v - 0.07"),
                                         ('txt="50"', 'txt=f"{H / S * 100:.0f}"')]),
                       ("beam_elevation", [("S = 2.0", "S = 1.0"), ("(schematic, ~1:" + "50)", "(schematic, 1:50)")])):
        src = inspect.getsource(getattr(M, name))
        for a, b in reps:
            assert a in src, (name, a)
            src = src.replace(a, b)
        exec(compile(src, f"<T34 {name} 1:50>", "exec"), M.__dict__)


_patch_t34_to_1_100()


def load():
    g = json.load(open(GEOM, encoding="utf-8"))
    for u, v in g["new_objects_project_labels"]["frames"].items():
        g["frames"][u]["label_etabs"] = g["frames"][u]["label"]
        g["frames"][u]["label"] = v["label"]
    return g, json.load(open(DES, encoding="utf-8")), json.load(open(HC, encoding="utf-8"))


def col_section(sh, cu, cv, b, nside, db, hoop_lo, hoop_mid, title, legs):
    n0 = len(sh.msp)
    M.col_section(sh, cu, cv, b, nside, hoop_lo, title, legs)
    for ent in list(sh.msp)[n0:]:
        if ent.dxftype() == "TEXT" and "  -  hoops" in ent.dxf.text:      # T34 text says phi16 for every size: replaced below
            sh.msp.delete_entity(ent)
    # overwrite the bar text line of the T34 routine (it says phi16) with an explicit one below
    B = b * 5.0
    sh.T(f"{nside * 4 - 4}φ{db}   lo: {hoop_lo}   mid: {hoop_mid}", cu, cv - B / 2 - 1.20, 0.13, layer="S-ANNO-IDEN")


def sheet_s101(doc, geom, des):
    sh = Sheet(doc, 0)
    sh.dx, sh.dy = sh.fx0 + 28.5, sh.fy0 + 18.6
    grids(sh)
    cols = {}
    for f in geom["frames"].values():
        if f["kind"] == "column":
            cols.setdefault(f["label"], {})[f["story"]] = (f["xi"], f["yi"], f["sec"])
    for lab, st in cols.items():
        X, Y, sec = st["Story1"]
        column(sh, X, Y, 0.50, lab, "CT-1" if "Story5" in st else "CT-2")
    sh.T("CT-1 = continues to the stair-house roof (C2, C6, C16, C17, C18, C19);  CT-2 = up to the roof", sh.fx0 + 18.5, sh.fy0 + 16.0, 0.15)
    sh.T("GRID & COLUMN LAYOUT PLAN 1:50 (columns drawn 50x50 = parking storey size)", sh.fx0 + 18.5, sh.fy0 + 15.6, 0.16)
    frame(sh, "پلان آکس بندی و ستون گذاری و جدول ستون ها", "S-101 GRID & COLUMN LAYOUT + COLUMN SCHEDULE", "S-101", SRC)
    h = des["column_hoops"]
    pm = {}
    for c in des["columns"]:
        if c["pmm"] > pm.get(c["story"], (0, ""))[0]:
            pm[c["story"]] = (c["pmm"], c["label"])
    lo = {c["story"]: c["lo_mm"] for c in des["columns"]}
    spec = [("Story5", "stair house", "+14.20 .. +17.50", "C2 C6 C16 C17 C18 C19", "C40X40/12T16", 40),
            ("Story4", "floor 3 storey", "+10.80 .. +14.20", "all 12", "C45X45/16T16", 45),
            ("Story3", "floor 2 storey", "+7.40 .. +10.80", "all 12", "C45X45/16T16", 45),
            ("Story2", "floor 1 storey", "+4.00 .. +7.40", "all 12", "C50X50/16T18", 50),
            ("Story1", "parking", "+-0.00 .. +4.00", "all 12", "C50X50/16T20", 50)]
    rows = []
    for st, nm, lv, which, sec, b in spec:
        hh = h[sec]
        rows.append([nm, st, lv, which, f"{b}x{b}", f"{hh['bars']} (ρ={hh['rho']}%)", f"{hh['hoop']}, {hh['legs']} legs", f"{lo[st]}",
                     f"{hh['hoop_mid']}", f"{hh['Ash_s_req']:.2f} / {hh['Ash_s_prov']:.2f}", f"{pm[st][0]:.3f} ({pm[st][1]})"])
    cols_t = [("storey", 2.2), ("ETABS\nstory", 1.3), ("TOS range", 2.4), ("columns", 3.4), ("b x h\n(cm)", 1.2), ("longitudinal", 2.9),
              ("hoops lo\n+ joints", 2.4), ("lo\n(mm)", 1.0), ("hoops\nmid height", 1.9), ("Ash/s req/prov\n(mm²/mm)", 2.2), ("max PMM\n(column)", 2.0)]
    sh.T("COLUMN SCHEDULE  /  جدول ستون ها", sh.fx0 + 1.6, sh.fy0 + 14.9, 0.22, align=TA.MIDDLE_LEFT)
    table(sh, sh.fx0 + 1.6, sh.fy0 + 14.5, cols_t, rows, rh=0.42, th=0.14)
    notes(sh, sh.fx0 + 1.6, sh.fy0 + 10.6, [
        "1. Concrete f'c = 25 MPa; longitudinal S400; hoops S340; clear cover 40 mm (ACI 318-19 20.5.1.3).",
        "2. Longitudinal bars as in ETABS Rev6b (check mode): parking 16φ20, floor-1 storey 16φ18 (boss 2026-10-31), above 16φ16 / 12φ16.",
        f"   Max PMM {pm['Story1'][0]:.3f} ({pm['Story1'][1]}, parking); floor-1 storey {pm['Story2'][0]:.3f}. ρ between 1% and 6% (18.7.4.1).",
        "3. lo >= max(h, Ln/6, 450) at both ends of every storey (18.7.5.1); hoops in lo and through the joints per Ash (18.7.5.4, 18.8.3.1);",
        "   mid height s <= min(6db, 150) (18.7.5.5). Column shear demand max 2.27 mm²/mm (C20 roof storey) < mid-height capacity.",
        "4. Lap splices only in the middle half of the clear height, class B (φ20: 100 cm, φ18: 90 cm, φ16: 80 cm), hoops @ <= 100.",
        "5. Bar change 16φ20 -> 16φ18 at +4.00 and 16φ18 -> 16φ16 / 50 -> 45 at +7.40: lap above the floor, cranked bars (slope <= 1 in 6) where the size changes.",
        "6. Strong-column / weak-beam: 4 roof joints > 1.0 exempt by ACI 18.7.3.1 (Pu <= Ag f'c/10).",
        "7. C2 / C6: corbels for the sliding stair-landing seat at +2.09, +5.70, +9.10, +12.50 (S-107).",
        "8. Torsional irregularity (Max/Avg 1.32): Ax = 1.17 applied; slab-to-beam connection force +25% (ASCE 7-22 12.3.3.4).",
        "9. Foundation / starter bars: by SAFE (pending). Elevator pit 2.00 m deep, pit floor -2.00 (arch Rev.12), next to C16 / C18 (boss)."], h=0.13, step=0.26, head="COLUMN NOTES")
    for (cu, b, n, db, legs, sec, tt) in ((sh.fx0 + 27.6, 0.50, 5, 20, 3, "C50X50/16T20", "C50 - parking"),
                                         (sh.fx0 + 31.1, 0.50, 5, 18, 3, "C50X50/16T18", "C50 - floor-1 storey"),
                                         (sh.fx0 + 34.6, 0.45, 5, 16, 3, "C45X45/16T16", "C45 - floors 2, 3"),
                                         (sh.fx0 + 38.0, 0.40, 4, 16, 4, "C40X40/12T16", "C40 - stair house")):
        col_section(sh, cu, sh.fy0 + 12.4, b, n, db, h[sec]["hoop"], h[sec]["hoop_mid"], tt, legs)
    legend(sh, sh.fx0 + 30.5, sh.fy0 + 19.0, ["S-GRID", "S-GRID-IDEN", "S-COLS", "S-COLS-PATT", "S-CONC", "S-REBR", "S-DIMS",
                                              "S-ANNO", "S-ANNO-IDEN", "S-TABL", "S-ANNO-TTLB", "S-ANNO-BRDR"])


_joist_x = M.joist


def _joist_skip_y(sh, X0, X1, Y, tag, h=0.25):
    """T34 draws every panel with X joists; the 7.5 m bay panels F1 / F4 are drawn in Y by bay_75() instead"""
    if tag in ("F1", "F4"):
        return
    _joist_x(sh, X0, X1, Y, tag, h)


M.joist = _joist_skip_y


def joist_y(sh, X, Y0, Y1, tag):
    sh.lineE("S-SLAB", X, Y0, X, Y1)
    for Y in (Y0, Y1):
        sh.lineE("S-SLAB", X - 0.12, Y, X + 0.12, Y)
    for Y, d in ((Y0, 1), (Y1, -1)):
        sh.poly("S-SLAB", [sh.E(X, Y), sh.E(X - 0.07, Y + d * 0.18), sh.E(X + 0.07, Y + d * 0.18)])
    u, v = sh.E(X, (Y0 + Y1) / 2)
    sh.T(tag, u, v + 0.10, 0.13, layer="S-SLAB", align=TA.BOTTOM_CENTER)


def bay_75(sh):
    """joists in Y over the 7.5 m bay (axis 1-2), length 8.00 back to back over the beams, 3 tie beams at L/4"""
    joist_y(sh, 1.10, 0.30, 7.20, "F1  joists Y, L = 8.00")
    joist_y(sh, 4.75, 0.30, 7.20, "F4  joists Y, L = 8.00")
    for Y in (1.875, 3.75, 5.625):
        for sgn in (-1, 1):
            sh.lineE("S-BEAM", 0.25, Y + sgn * 0.075, 6.90, Y + sgn * 0.075)
        u, v = sh.E(6.0, Y)
        sh.T("TB 15x31", u - 0.12, v, 0.11, layer="S-ANNO-IDEN", rot=90)
    # tie beam section / bars: framing notes and S-105


def framing(doc, geom, des, i, stories, no, tfa, ten, nl, roof=False):
    sh = M.framing_sheet(doc, geom, des, i, stories, no, tfa, ten, nl, roof)
    bay_75(sh)
    return sh


def stairhouse(sh, geom, des):
    """Story5 plan, A-B' / 2-5, lower part of S-103"""
    sh.dx, sh.dy = sh.fx0 + 22.6, sh.fy0 + 3.4
    grids(sh, Xr=(0.0, 2.50), Yr=(7.5, 20.01), gx=[("A", 0.0), ("B", 2.35), ("B'", 2.50)],
          gy=[("2", 7.5), ("3", 13.5), ("4", 18.81), ("5", 20.01)], dims=True)
    bms = [f for f in geom["frames"].values() if f["kind"] == "beam" and f["story"] == "Story5" and f["label"] != "BH"]
    tags = {b["label"]: (b["label"], "cant. 40x40" if b["label"] in ("B3", "B5") else "40x40") for b in bms}
    beams_plan(sh, bms, 0.40, tags, cut=0.20)
    bh = next(f for f in geom["frames"].values() if f["label"] == "BH")
    for sgn in (-1, 1):
        sh.lineE("S-BEAM", bh["xi"] + 0.20, bh["yi"] + sgn * 0.125, bh["xj"] - 0.20, bh["yj"] + sgn * 0.125)
    u, v = sh.E(1.2, bh["yi"])
    sh.T("BH 25x40 (hook beam, S-106)", u - 0.25, v, 0.12, layer="S-ANNO-IDEN", rot=90)
    for f in geom["frames"].values():
        if f["kind"] == "column" and f["story"] == "Story5":
            column(sh, f["xi"], f["yi"], 0.40, f["label"])
    joist(sh, 0.20, 2.15, 9.2, "F17")
    joist(sh, 0.20, 2.20, 16.9, "F14'")
    joist(sh, 0.20, 2.30, 19.4, "F2'")
    for (X, Y) in ((0.30, 14.10), (0.30, 15.20)):
        u, v = sh.E(X, Y)
        sh.msp.add_circle((u, v), 0.0625, dxfattribs={"layer": "S-SLAB-OPNG"})
    u, v = sh.E(0.30, 14.65)
    sh.T("2 sleeves φ125 (duct D-1) between joists, 1φ10 trim each side", u, v + 0.35, 0.10, layer="S-SLAB-OPNG", rot=90)
    sh.T("STAIR-HOUSE ROOF (Story5, TOS +17.50; ETABS 17.80) - extended to axis 5 - 1:50", sh.E(0, 13.7)[0], sh.E(4.5, 0)[1], 0.17)
    sh.T("پلان تیر ریزى بام خرپشته", sh.E(0, 13.7)[0], sh.E(5.1, 0)[1], 0.26, farsi=True)


ORDER = ["B1", "B30", "B31", "B3", "B4", "B32", "B33", "B5", "B7", "B34", "B35", "B6", "B10", "B11", "B12", "B13", "B36", "B37", "B38", "B39", "B2", "BH"]


def schedule_sheet(doc, des, i, stories, no, tfa, ten, extra=None):
    sh = Sheet(doc, i)
    D = [r for r in des["beams"] if r["story"] in stories]
    D.sort(key=lambda r: (ORDER.index(r["label"]), stories.index(r["story"])))
    floor = {"Story1": "F1 +4.00", "Story2": "F2 +7.40", "Story3": "F3 +10.80", "Story4": "Roof +14.20", "Story5": "St.house +17.50"}
    rows, groups = [], []
    for k, r in enumerate(D):
        sec = r["sec"].replace("BW", "").replace("xH", "x")
        cant = r["label"] in M.CANT and r["story"] != "Story5"
        if cant:
            dem = f"As {r['AsTop_req']}/{r['AsBot_req']}, Al {r['Al_req']}; q {r['q_h']:.2f}"
        elif r["label"] == "BH":
            dem = f"As bot {r['AsBot_req']}; q {r['q_h']:.2f}"
        else:
            dem = f"{r['AsTopI_gov']} / {r['AsTopJ_gov']} / {r['AsBot_req']}" + (f"; Al {r['Al_req']}" if r["Al_req"] else "") + \
                  f"; q {r['q_h']:.2f}" + (f"/{r['q_m']:.2f}" if r["q_m"] is not None else "")
        rows.append([r["label"] if (k == 0 or D[k - 1]["label"] != r["label"]) else "", floor[r["story"]], sec, f"{r['L']:.2f}",
                     r["topI"], r["topJ"], r["top"] if not cant else "3φ25", r["bot"], r["web"] or "-", r["hoop_h"], r["hoop_m"], dem])
        if k < len(D) - 1 and D[k + 1]["label"] != r["label"]:
            groups.append(k)
    cols_t = [("beam", 1.0), ("floor", 1.9), ("b x h\n(cm)", 1.1), ("L c/c\n(m)", 0.9), ("TOP end I\n(face-Ln/3)", 2.2),
              ("TOP end J\n(face-Ln/3)", 2.2), ("TOP mid\n(cont.)", 1.3), ("BOTTOM\n(supp.+mid)", 2.2), ("web\n(torsion)", 1.3),
              ("hoops 2h\n(closed)", 2.1), ("hoops mid", 2.0), ("ETABS: As top I/J/bot (mm²);\nAl; q=Av/s+2At/s 2h/mid", 4.6)]
    title_y = sh.fy0 + 28.3
    sh.T(f"BEAM SCHEDULE  -  {ten.split(' - ', 1)[-1]}", sh.fx0 + 1.6, title_y, 0.22, align=TA.MIDDLE_LEFT)
    yend = table(sh, sh.fx0 + 1.6, title_y - 0.35, cols_t, rows, rh=0.30 if len(rows) > 40 else 0.35, th=0.12, head_h=0.72, groups=groups)
    frame(sh, tfa, ten, no, SRC.replace(" - read only", ""), tpos=(32.4, 1.8))
    if extra:
        extra(sh, yend)
    return sh


SCHED_NOTES = [
    "1. Labels = project labels (Label_project). End I = end toward axis A or axis 1 (cantilevers: end I at axis 4).",
    "2. Continuous 4φ16 top and 4φ16 bottom in every frame beam (>= As,min, 9.6.1.2; 2 bars continuous, 18.6.3.1).",
    "3. TOP end I / J = continuous + extra bars from the face to Ln/3 (>= Ln/4 + d), through the joint; collinear beams unified.",
    "4. BOTTOM = continuous + extra, full length (= support and mid-span), anchored in the columns (18.6.3.2 checked).",
    "5. web = torsion bars Al/3 per face (EF) at mid-depth, anchored at the supports (9.5.4.3, 9.7.5).",
    "6. Hoops: closed, 135° hooks, first <= 50 mm from the face; 2h zone s <= min(d/4, 6db, 150) (18.6.4.4); mid s <= d/2 (18.6.4.6).",
    "   3-leg hoops (2 hoops overlapped or hoop + crosstie) in B10, B12, B38 all levels (boss) and where 2 legs would need s < 50.",
    "7. Cantilevers B3/B5/B6 (floors, roof): 3φ25 top + 3φ25 bottom, 2φ16 EF, closed φ12@80 full length; Sway Ordinary, J = 0.1 (22.7.3.2).",
    "   Stair-house cantilevers B3/B5 40x40: 4φ16 + 4φ16, φ10@85 full length (Sway Ordinary, J = 0.1, boss 2026-10-31).",
    "8. No lap splice within joints or within 2h of the faces (18.6.3.3); laps class B with hoops @ <= 100.",
    "9. All beams OK in ETABS Rev6b (no D/C > 1.0, no messages). FOR APPROVAL by the boss.",
]


def s104_extra(sh, yend):
    notes(sh, sh.fx0 + 25.2, sh.fy0 + 25.6, SCHED_NOTES, h=0.11, step=0.23, head="SCHEDULE NOTES", width=0.66)


def s105_extra(sh, yend):
    M.beam_elevation(sh, sh.fx0 + 1.8, sh.fy0 + 11.4)
    M.beam_section(sh, sh.fx0 + 17.0, sh.fy0 + 12.6, 0.50, (7, 20), (7, 20), (1, 14), "",
                   "TYPICAL SECTION AT SUPPORT 1:50", ["e.g. B12 floor 1: 4φ16+3φ20 top, 4φ16+3φ20 bottom,", "1φ14 EF, φ12@80 3-leg (2h)"])
    M.beam_section(sh, sh.fx0 + 23.5, sh.fy0 + 12.6, 0.50, (3, 25), (3, 25), (2, 16), "",
                   "CANTILEVER B3 / B5 / B6 SECTION 1:50", ["3φ25 top + 3φ25 bottom + 2φ16 EF", "closed φ12@80 full length"])
    notes(sh, sh.fx0 + 1.6, sh.fy0 + 7.6, SCHED_NOTES, h=0.11, step=0.215, head="SCHEDULE / DETAIL NOTES", width=0.70)
    notes(sh, sh.fx0 + 27.4, sh.fy0 + 18.2, [
        "G1. Codes: ACI 318-19 (ch. 18, special moment frame), loads ASCE 7-22,",
        "    seismic Standard 2800 4th ed. (C = 0.10); ETABS 19 Rev6b, 51 A22 combos.",
        "G2. Concrete C25 (f'c 25 MPa); bars S400 long., S340 hoops / ties.",
        "G3. Clear cover: beams and columns 40 mm; slabs 20 mm.",
        "G4. Longitudinal bars in exterior joints: 90° hooks, ldh per 18.8.5.",
        "G5. INFILL GAP 80 mm to columns and beams, all storeys (boss 2026-10-31),",
        "    flexible filler + ties; design story drift 70.3 mm.",
        "G6. Joists: 7.5 m bay in Y (8.00, 3 TB), stair house in X; dowels φ10@200",
        "    (+25% connection force, torsional irregularity, ASCE 7-22 12.3.3.4).",
        "G7. Stair: sliding seats, the stair does not brace the frame (S-107).",
        "G8. Units: m (plans), cm (sections), bars mm. FOR APPROVAL - NOT FOR",
        "    CONSTRUCTION.",
    ], h=0.13, step=0.25, head="GENERAL NOTES")


# ---------------------------------------------------------------- detail helpers (sheet units; k = scale factor vs 1:50)
def rect(sh, layer, u0, v0, w, h):
    sh.poly(layer, [(u0, v0), (u0 + w, v0), (u0 + w, v0 + h), (u0, v0 + h)])


def bars_row(sh, u0, u1, v, n, r):
    for k in range(n):
        u = u0 + (u1 - u0) * k / max(n - 1, 1)
        sh.msp.add_circle((u, v), r, dxfattribs={"layer": "S-REBR"})
        hh = sh.msp.add_hatch(dxfattribs={"layer": "S-REBR"})
        hh.paths.add_edge_path().add_arc((u, v), r, 0, 360)


def section_box(sh, cu, cv, b, h, top, bot, side, title, sub, k=1.0):
    """beam cross section at 1:50 (k = 1): b, h in m; top/bot = (n, d mm); side = (n per face, d) or None"""
    B, H = b * k, h * k
    rect(sh, "S-CONC", cu - B / 2, cv - H / 2, B, H)
    c = 0.046 * k
    rect(sh, "S-REBR", cu - B / 2 + c, cv - H / 2 + c, B - 2 * c, H - 2 * c)
    for (n, d), vv in ((top, cv + H / 2 - c - 0.01 * k), (bot, cv - H / 2 + c + 0.01 * k)):
        bars_row(sh, cu - B / 2 + c + 0.012 * k, cu + B / 2 - c - 0.012 * k, vv, n, d / 2000 * k)
    if side:
        n, d = side
        for j in range(n):
            vv = cv - H / 2 + H * (j + 1) / (n + 1)
            for uu in (cu - B / 2 + c + 0.012 * k, cu + B / 2 - c - 0.012 * k):
                sh.msp.add_circle((uu, vv), d / 2000 * k, dxfattribs={"layer": "S-REBR"})
    sh.dim((cu - B / 2, cv - H / 2), (cu + B / 2, cv - H / 2), (cu, cv - H / 2 - 0.35), 0, txt=f"{b * 100:.0f}")
    sh.dim((cu + B / 2, cv - H / 2), (cu + B / 2, cv + H / 2), (cu + B / 2 + 0.35, cv), 90, txt=f"{h * 100:.0f}")
    sh.T(title, cu, cv - H / 2 - 0.80, 0.18)
    for j, s in enumerate(sub):
        sh.T(s, cu, cv - H / 2 - 1.08 - j * 0.24, 0.12, layer="S-ANNO-IDEN")


def sheet_s106(doc, des):
    sh = Sheet(doc, 5)
    frame(sh, "جزئیات کنسول ها و تیر قلاب آسانسور", "S-106 CANTILEVER DETAILS + ELEVATOR HOOK BEAM", "S-106", SRC)
    D = {(r["label"], r["story"]): r for r in des["beams"]}
    # cantilever elevation 1:50 (k=1): back span stub + column + cantilever 1.20 + edge beam B2
    k = 1.0
    u0, v0 = sh.fx0 + 11.0, sh.fy0 + 20.0
    H = 0.50 * k
    rect(sh, "S-CONC", u0, v0 - 0.6 * k, 0.50 * k, H + 1.2 * k)                         # column C17/C19 (axis 4)
    rect(sh, "S-CONC", u0 - 1.6 * k, v0, 1.6 * k, H)                                    # back span stub (B31/B33 typ.)
    rect(sh, "S-CONC", u0 + 0.50 * k, v0, 0.95 * k, H)                                  # cantilever clear 0.95 to the B2 face
    rect(sh, "S-CONC", u0 + 1.45 * k, v0, 0.50 * k, H)                                  # edge beam B2 (cut)
    c = 0.05 * k
    sh.L("S-REBR", (u0 - 1.6 * k, v0 + H - c), (u0 + 1.90 * k, v0 + H - c))            # top 3phi25
    sh.L("S-REBR", (u0 + 1.90 * k, v0 + H - c), (u0 + 1.90 * k, v0 + c + 0.3))
    sh.L("S-REBR", (u0 - 0.05 * k, v0 + c), (u0 + 1.90 * k, v0 + c))                     # bottom 3phi25
    sh.L("S-REBR", (u0 - 0.05 * k, v0 + c), (u0 - 0.05 * k, v0 + c + 0.6 * k))
    for j in range(13):
        uu = u0 + 0.55 * k + j * 0.08 * k
        if uu < u0 + 1.45 * k:
            sh.L("S-REBR", (uu, v0 + c), (uu, v0 + H - c))
    sh.dim((u0 + 0.25 * k, v0 + H), (u0 + 1.70 * k, v0 + H), (0, v0 + H + 0.6), 0, txt="1.20 (axis 4 - axis 5)")
    sh.dim((u0 - 1.6 * k, v0 + H), (u0 + 0.25 * k, v0 + H), (0, v0 + H + 0.6), 0, txt="ld + Ln/3 into back span")
    sh.T("CANTILEVER B3 / B5 / B6 - FLOORS 1-3 AND ROOF - ELEVATION 1:50", u0 + 0.5 * k, v0 + H + 1.4, 0.20)
    notes(sh, u0 - 1.6 * k, v0 - 1.0, [
        "3φ25 top: through the column, >= ld + Ln/3 into the back span; 90° down-bend at the free end into B2.",
        "3φ25 bottom: hooked into the column (ldh) and lapped with B2 bottom bars.",
        "2φ16 each face (torsion, EF) full length; closed φ12@80 full length, first 50 mm from the face.",
        "Torsion reduced to compatibility value (J = 0.1, ACI 22.7.3.2): B2 and the back spans designed for the redistributed moments.",
        "Stair-house cantilevers B3 / B5 (Story5, 40x40): 4φ16 top + 4φ16 bottom, closed φ10@85 full length.",
    ], h=0.13, step=0.26)
    rows = []
    for st in ("Story1", "Story2", "Story3", "Story4", "Story5"):
        for lab in ("B3", "B5", "B6"):
            r = D.get((lab, st))
            if r:
                rows.append([lab, st, r["sec"].replace("BW", "").replace("xH", "x"), r["topI"], r["bot"], r["web"] or "-", r["hoop_h"],
                             f"{r['AsTop_req']} / {r['AsBot_req']}", f"{r['q_h']:.2f}"])
    table(sh, sh.fx0 + 1.6, sh.fy0 + 12.6, [("cant.", 1.0), ("storey", 1.4), ("b x h", 1.2), ("top", 1.6), ("bottom", 1.6), ("web", 1.4),
                                           ("hoops", 2.2), ("As req\ntop/bot", 1.8), ("q", 1.0)], rows, rh=0.30, th=0.12, head_h=0.6)
    sh.T("CANTILEVER SCHEDULE (ETABS Rev6b)", sh.fx0 + 1.6, sh.fy0 + 12.9, 0.18, align=TA.MIDDLE_LEFT)
    # hook beam
    bh = D[("BH", "Story5")]
    u1, v1 = sh.fx0 + 22.0, sh.fy0 + 21.0
    k2 = 1.0                                                                          # 1:50
    L = 2.3825
    rect(sh, "S-CONC", u1 - 0.20 * k2, v1 - 0.6, 0.40 * k2, 0.40 * k2 + 1.2)
    rect(sh, "S-CONC", u1 + (L - 0.20) * k2, v1 - 0.6, 0.40 * k2, 0.40 * k2 + 1.2)
    rect(sh, "S-CONC", u1 + 0.20 * k2, v1, (L - 0.40) * k2, 0.40 * k2)
    sh.L("S-REBR", (u1, v1 + 0.08), (u1 + L * k2, v1 + 0.08))
    sh.L("S-REBR", (u1, v1 + 0.40 * k2 - 0.08), (u1 + L * k2, v1 + 0.40 * k2 - 0.08))
    for j in range(16):
        uu = u1 + 0.25 * k2 + j * 0.15 * k2
        if uu < u1 + (L - 0.2) * k2:
            sh.L("S-REBR", (uu, v1 + 0.08), (uu, v1 + 0.40 * k2 - 0.08))
    uh = u1 + 1.45 * k2
    sh.poly("S-REBR", [(uh - 0.05, v1 - 0.01), (uh + 0.05, v1 - 0.01), (uh + 0.05, v1 - 0.03), (uh - 0.05, v1 - 0.03)])
    sh.msp.add_circle((uh, v1 - 0.10), 0.05, dxfattribs={"layer": "S-REBR"})
    sh.T("hook 25 kN (approved)", uh, v1 - 0.75, 0.12, layer="S-ANNO-IDEN")
    sh.dim((u1, v1 + 0.40 * k2), (u1 + L * k2, v1 + 0.40 * k2), (0, v1 + 0.40 * k2 + 0.5), 0, txt="2.38 (B31 - B33, Y 14.65)")
    sh.dim((u1, v1 - 0.6), (uh, v1 - 0.6), (0, v1 - 1.2), 0, txt="1.45")
    sh.T("ELEVATOR HOOK BEAM BH 25x40 - ELEVATION 1:50 (under the stair-house roof slab, over the shaft centre)", u1 + L, v1 + 2.0, 0.18)
    section_box(sh, sh.fx0 + 34.5, sh.fy0 + 22.4, 0.25, 0.40, (2, 14), (2, 16), None, "BH SECTION 1:50",
                [f"top {bh['topI']}, bottom {bh['bot']}", f"closed {bh['hoop_h']} + 2φ10 hanger hoops each side of the hook"])
    notes(sh, sh.fx0 + 21.0, sh.fy0 + 17.0, [
        "BH: pinned ends (M3 released in ETABS), bars anchored into B31 / B33 (top 2φ14 hooked, bottom 2φ16 ld past the support face).",
        "ETABS Rev6b: As bot req 247 mm², Vu 25.4 kN, no shear reinforcement required; hand: Mu 19.2 kN.m (1.2D), x2 impact OK.",
        "Hook 25 kN APPROVED by the boss; cast-in eye bolt / embedded plate per the supplier; hanger hoops 2φ10 each side.",
        "Elevator pit depth 2.00 m, pit floor -2.00 below the foundation top +-0.00 (arch Rev.12): part of the foundation (SAFE, pending).",
        "BH bottom TOS +17.10; shaft top clear height to be checked with the supplier (overrun >= 3.87 m, boss).",
    ], h=0.13, step=0.26, head="HOOK BEAM NOTES")


def sheet_s107(doc, hc):
    sh = Sheet(doc, 6)
    frame(sh, "جزئیات پله، تیر پاگرد و نشیمن لغزشی", "S-107 STAIR DETAILS - WAIST SLAB, LANDING BEAM, SLIDING SEATS", "S-107", SRC)
    k = 1.0                                                                              # 1:50
    u0, v0 = sh.fx0 + 2.5, sh.fy0 + 13.5                                                 # Y 7.50 (axis 2) at u0, floor level at v0
    Hs = 3.40
    yl, zl = 8.958 - 7.5, 1.70                                                           # landing edge, landing TOS rel. floor
    # floor slabs / beams B36 at axis 3 (lower and upper) and landing beam at axis 2
    for z in (0.0, Hs):
        rect(sh, "S-CONC", u0 + (6.0 - 0.25) * k, v0 + (z - 0.50) * k, 0.50 * k, 0.50 * k)          # B36
        sh.T("B36" + (" (upper, sliding seat)" if z else " (lower, fixed)"), u0 + 6.0 * k, v0 + (z - 0.50) * k - 0.3, 0.13, layer="S-ANNO-IDEN")
    rect(sh, "S-CONC", u0 - 0.25 * k, v0 - 0.6 * k, 0.50 * k, (Hs + 0.6) * k)                    # column C2 / C6 (axis 2)
    rect(sh, "S-CONC", u0 + 0.25 * k + 0.04 * k, v0 + (zl - 0.40) * k, 0.30 * k, 0.40 * k)      # landing beam 30x40 (gap 40)
    sh.poly("S-CONC", [(u0 + 0.25 * k, v0 + (zl - 0.45) * k - 0.0), (u0 + 0.55 * k, v0 + (zl - 0.45) * k),
                       (u0 + 0.55 * k, v0 + (zl - 0.45 - 0.25) * k), (u0 + 0.25 * k, v0 + (zl - 0.45 - 0.45) * k)], close=True)  # corbel
    t = 0.20
    # landing slab Y 7.50..8.96 at zl, flight A down to the lower floor at Y 13.5 - 1.84 (arrive), flight B up
    sh.poly("S-CONC", [(u0 + 0.59 * k, v0 + zl * k), (u0 + yl * k, v0 + zl * k), (u0 + 4.16 * k, v0 + Hs * k), (u0 + 5.75 * k, v0 + Hs * k)], close=False)
    sh.poly("S-CONC", [(u0 + 0.59 * k, v0 + (zl - t) * k), (u0 + yl * k, v0 + (zl - t) * k), (u0 + 4.16 * k, v0 + (Hs - t) * k), (u0 + 5.70 * k, v0 + (Hs - t) * k)], close=False)
    sh.poly("S-REBR", [(u0 + 0.62 * k, v0 + (zl - t + 0.03) * k), (u0 + yl * k, v0 + (zl - t + 0.03) * k), (u0 + 4.16 * k, v0 + (Hs - t + 0.03) * k), (u0 + 5.70 * k, v0 + (Hs - t + 0.03) * k)], close=False)
    # lower flight (dashed idea: drawn as thin)
    sh.poly("S-SLAB", [(u0 + yl * k, v0 + zl * k), (u0 + 4.16 * k, v0), (u0 + 5.75 * k, v0)], close=False)
    # sliding pads
    for uu, vv in ((u0 + 0.40 * k, v0 + (zl - 0.45) * k), (u0 + 5.85 * k, v0 + (Hs - t) * k)):
        rect(sh, "S-REBR", uu - 0.075, vv, 0.15, 0.02)
    sh.T("PTFE pad 150x250", u0 + 0.40 * k, v0 + (zl - 0.45) * k - 0.25, 0.11, layer="S-ANNO-IDEN")
    sh.T("sliding bearing + 70 mm gap", u0 + 5.85 * k, v0 + Hs * k + 0.35, 0.11, layer="S-ANNO-IDEN")
    sh.dim((u0, v0 + Hs * k + 0.9), (u0 + 6.0 * k, v0 + Hs * k + 0.9), (0, v0 + Hs * k + 1.3), 0, txt="6.00 (axis 2 - axis 3)")
    sh.dim((u0 - 0.5 * k, v0), (u0 - 0.5 * k, v0 + Hs * k), (u0 - 0.5 * k - 0.4, 0), 90, txt="3.40")
    sh.T("STAIR - LONGITUDINAL SECTION 1:50 (typical storey; parking storey 4.00 / landing +2.09)", u0 + 6.0, v0 + Hs * k + 2.0, 0.20)
    st = hc["stair_waist_t200"]
    notes(sh, sh.fx0 + 1.6, sh.fy0 + 11.0, [
        f"S1. Waist + landing slab t = 0.20 (boss 2026-10-31); main bottom {st['As_prov']} (As req {st['As_req_mm2_m']} mm²/m, Mu {st['Mu_kNm_m']} kN.m/m),",
        f"    distribution {st['distribution']}; top φ10@200 over L/4 at both ends. Cover 20 mm. Concrete C25, S400.",
        "S2. Lower flight: fixed (monolithic) on the lower B36. Upper flight: SLIDING seat on the nib of the upper B36 (PTFE on stainless,",
        "    seat >= 220 mm), 70 mm movement gap along the flight, 40 mm to the walls; no bars continue across the sliding joint.",
        "S3. Landing beam 30x40 between C2 and C6: 3φ16 top + 3φ16 bottom, closed φ10@100 (Mu 36 kN.m with t = 0.20); rests on corbels only.",
        "S4. Result: the stair carries gravity only and does not brace the frame; C2 / C6 are full-height columns (no short column).",
        f"S5. Deflection (hand check): live {st['delta_L_mm']} mm <= L/360 = {st['L/360_mm']} OK; long-term + live {st['delta_long_term_plus_L_mm']} mm > L/240 = {st['L/240_mm']}:",
        "    WARNING - t = 0.20 < l/20 = 0.30 (ACI table 7.3.1.1, simply supported): reported to the boss, no change made.",
    ], h=0.13, step=0.26, head="STAIR NOTES")
    # corbel detail 1:50 (kc = 1)
    kc = 1.0
    cu, cv = sh.fx0 + 31.5, sh.fy0 + 18.2
    rect(sh, "S-CONC", cu - 0.25 * kc, cv - 0.35 * kc, 0.25 * kc, 1.30 * kc)                   # column half (face at cu)
    sh.poly("S-CONC", [(cu, cv + 0.45 * kc), (cu + 0.30 * kc, cv + 0.45 * kc), (cu + 0.30 * kc, cv + 0.20 * kc), (cu, cv)], close=False)
    rect(sh, "S-CONC", cu + 0.04 * kc, cv + 0.47 * kc, 0.30 * kc, 0.40 * kc)                   # landing beam end (gap 40 to the column)
    rect(sh, "S-REBR", cu + 0.05 * kc, cv + 0.45 * kc, 0.15 * kc, 0.02 * kc)                   # pad
    sh.L("S-REBR", (cu - 0.20 * kc, cv + 0.40 * kc), (cu + 0.26 * kc, cv + 0.40 * kc))          # Asc 4phi14
    sh.L("S-REBR", (cu - 0.20 * kc, cv + 0.40 * kc), (cu - 0.20 * kc, cv + 0.10 * kc))
    sh.msp.add_circle((cu + 0.26 * kc, cv + 0.38 * kc), 0.01, dxfattribs={"layer": "S-REBR"})
    for j in range(3):
        vv = cv + 0.32 * kc - j * 0.07 * kc
        sh.L("S-REBR", (cu - 0.20 * kc, vv), (cu + 0.24 * kc, vv))
    sh.dim((cu, cv + 0.45 * kc), (cu + 0.30 * kc, cv + 0.45 * kc), (0, cv + 1.10 * kc), 0, txt="300")
    sh.dim((cu + 0.30 * kc, cv), (cu + 0.30 * kc, cv + 0.45 * kc), (cu + 0.30 * kc + 0.8, 0), 90, txt="450")
    sh.dim((cu, cv + 0.67 * kc), (cu + 0.04 * kc, cv + 0.67 * kc), (0, cv + 0.95 * kc), 0, txt="40")
    sh.T("CORBEL SEAT ON C2 / C6 - 1:50", cu + 0.05 * kc, cv + 1.35 * kc, 0.20)
    notes(sh, sh.fx0 + 26.0, sh.fy0 + 13.8, [
        "Corbel 400 wide x 300 projection x 450 deep at the face (>= 250 at the edge); av = 125, av/d = 0.32 (ACI 16.5).",
        "Vu = 69.8 kN, Nuc = 0.2 Vu = 14 kN: Asc 4φ14 (616 >= 394 mm²), welded cross bar φ14 at the outer end, 90° hook into the column.",
        "Ah: 3 closed φ10 within 2d/3 (471 >= 174 mm²). Bearing: elastomeric pad 150x250x20 + PTFE / stainless (1.86 MPa).",
        "40 mm soft joint around the column at the landing (PE foam + sealant); guide pin φ16 in a slotted sleeve ±40 (no restraint).",
        "Levels (TOS landing): +2.09, +5.70, +9.10, +12.50. Corbel on the +X face of C2, -X face of C6. Model: vertical load + P.e moment only.",
    ], h=0.12, step=0.25, head="CORBEL / SLIDING SEAT")
    section_box(sh, sh.fx0 + 22.0, sh.fy0 + 22.6, 0.30, 0.40, (3, 16), (3, 16), None, "LANDING BEAM 30x40 SECTION 1:50",
                ["3φ16 top + 3φ16 bottom", "closed φ10@100; Mu 40.8 kN.m, Vu 69 kN"])


def main():
    geom, des, hc = load()
    os.makedirs(TMP, exist_ok=True); os.makedirs(OUT_DIR, exist_ok=True)
    doc = ezdxf.new("R2018", setup=False)
    doc.units = ezdxf.units.M
    doc.header["$INSUNITS"] = 6; doc.header["$MEASUREMENT"] = 1; doc.header["$LTSCALE"] = 1.0; doc.header["$LWDISPLAY"] = 1
    doc.linetypes.add("CENTER", pattern=[0.56, 0.35, -0.08, 0.05, -0.08], description="Center ____ _ ____")
    for name, (c, lt, lw, desc) in M.LAYERS.items():
        lay = doc.layers.add(name, color=c, linetype=lt, lineweight=lw); lay.description = desc
    doc.layers.get("0").dxf.lineweight = 13
    doc.styles.add("LATIN", font="arial.ttf"); doc.styles.add("FARSI", font="tahoma.ttf")
    ds = doc.dimstyles.add("S100"); ds.dxf.dimtxsty = "LATIN"
    for kk, vv in dict(dimtxt=0.16, dimasz=0.09, dimtsz=0.06, dimexo=0.04, dimexe=0.08, dimgap=0.04, dimdec=2, dimdsep=46,
                       dimtad=1, dimtih=0, dimtoh=0, dimzin=0, dimclrd=1, dimclre=1, dimclrt=1, dimlunit=2, dimscale=1.0,
                       dimtix=0, dimatfit=3, dimtmove=0).items():
        ds.set_dxf_attrib(kk, vv)
    g_plan = dict(geom); g_plan["frames"] = {u: f for u, f in geom["frames"].items() if f["label"] != "BH"}
    sheet_s101(doc, g_plan, des)
    framing(doc, g_plan, des, 1, ["Story1", "Story2", "Story3"], "S-102", "پلان تیر ریزى تیپ طبقات اول تا سوم",
            "S-102 TYPICAL FLOOR FRAMING PLAN - FLOORS 1, 2, 3", [
                "1. ONE PLAN FOR FLOORS 1, 2, 3 (ETABS Story1-3; TOS +4.00, +7.40, +10.80): same grid, beams, cantilevers, slabs and openings.",
                "2. Beams 50x50 on floors 1-2, 45x50 on floor 3; columns below: 50x50 (16φ20 parking, 16φ18 floor-1 storey), 45x45 (S-101).",
                "3. Cantilevers B3, B5 (grid B' at C19), B6: 1.20 m, edge beam B2; Sway Ordinary, torsion J = 0.1 (boss); details S-106.",
                "4. 3-leg hoops in B10, B12, B38 (boss) and B36 floor 1 (S-104).",
                "5. Joists: 7.5 m bay (axis 1-2) in Y, 8.00 long back to back over B10/B11 and B12/B13, 3 tie beams TB per bay (boss);",
                "   bays 2-3 / 3-4 / cantilevers unchanged in X (question to the boss). Slab-to-beam dowels φ10@200 (+25%).",
                "6. Stair (A-B, 2-3): landing beam on corbels of C2 / C6 with sliding seats, upper flight sliding on B36 (S-107).",
                "7. Elevator shaft (A-B, 3 to +1.80) opening; infill walls with 80 mm gap to the frame (boss 2026-10-31).",
                "8. Beam tags: label / b x h (cm). ETABS level = TOS + 0.30 (ETABS Base +0.30).",
            ])
    sh3 = framing(doc, g_plan, des, 2, ["Story4"], "S-103", "پلان تیر ریزى بام و بام خرپشته",
                  "S-103 ROOF FRAMING PLAN (Story4, +14.20) + STAIR-HOUSE ROOF (Story5, +17.50)", [
                      "1. Roof (Story4, TOS +14.20): beams 45x50; columns below 45x45.",
                      "2. Stair-house walls 20 cm h 2.90 on B30, B32, B12, B36 and, extended, on B31, B33 (part), B38 (8.41 kN/m);",
                      "   shaft walls 15 / 10 cm on B33 and on the slab; parapet 0.20x1.20 (4.20 kN/m) on the other edges.",
                      "3. Roof joints of C5, C10, C20, C21: strong-column ratio > 1.0, exempt (ACI 18.7.3.1).",
                      "4. Stair-house roof (lower part): ALL joists in X, span 2.3 (boss); extended to axis 5; columns C2, C6, C16, C17, C18, C19 40x40;",
                      "   beams 40x40; cantilevers B3/B5 1.20; hook beam BH 25x40 over the shaft (S-106); 2 sleeves φ125.",
                      "5. Roof bay 1-2: joists in Y, 8.00, 3 tie beams TB (as floors). Reinforcement: S-105.",
                  ], roof=True)
    stairhouse(sh3, geom, des)
    schedule_sheet(doc, des, 3, ["Story1", "Story2", "Story3"], "S-104", "جدول آرماتور تیرهای طبقات اول تا سوم",
                   "S-104 BEAM SCHEDULE - FLOORS 1, 2, 3 (ACI 318-19)", s104_extra)
    schedule_sheet(doc, des, 4, ["Story4", "Story5"], "S-105", "جدول آرماتور تیرهای بام و خرپشته و جزئیات تیپ",
                   "S-105 BEAM SCHEDULE - ROOF & STAIR HOUSE + TYPICAL DETAILS", s105_extra)
    sheet_s106(doc, des)
    sheet_s107(doc, hc)
    doc.set_modelspace_vport(height=32, center=(3 * M.PITCH + 21, 15))
    dxf = os.path.join(TMP, "Merage3_struct_Rev2.dxf")
    doc.saveas(dxf)
    scr = os.path.join(TMP, "save_rev2.scr")
    with open(scr, "w", encoding="utf-8") as f:
        f.write(f'_.FILEDIA 0\n_.ZOOM _E\n_.SAVEAS 2018 "{OUT_DWG}"\n')
    if os.path.exists(OUT_DWG):
        os.makedirs(os.path.join(HERE, "_prev"), exist_ok=True)
        os.replace(OUT_DWG, os.path.join(HERE, "_prev", "Merage3_struct_Rev2_prev.dwg"))
    acquire()
    try:
        r = subprocess.run([M.ACCORE, "/i", dxf, "/s", scr, "/l", "en-US"], capture_output=True, timeout=300)
    finally:
        release()
    if not os.path.exists(OUT_DWG):
        print(r.stdout.decode("utf-16-le", errors="ignore")[-2000:])
        raise SystemExit("DWG not written")
    print("DWG:", OUT_DWG, os.path.getsize(OUT_DWG))
    json.dump({n: [k * M.PITCH, 0.0, k * M.PITCH + M.SHEET_W, M.SHEET_H] for k, n in enumerate(SHEETS)},
              open(os.path.join(HERE, "rev2_sheets.json"), "w"), indent=1)


def acquire():
    for _ in range(120):
        if not os.path.exists(LOCK):
            with open(LOCK, "w", encoding="utf-8") as f:
                f.write(f"structural-engineer (task 48) {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            return
        print("AutoCAD lock present, waiting:", open(LOCK, encoding="utf-8").read().strip())
        time.sleep(10)
    raise SystemExit("AutoCAD lock not released in 20 min")


def release():
    if os.path.exists(LOCK) and "structural-engineer" in open(LOCK, encoding="utf-8").read():
        os.remove(LOCK)


if __name__ == "__main__":
    main()
