# -*- coding: utf-8 -*-
"""Merage3 - task 57 (2026-11-07): structural drawings Rev5 = Rev4 with the boss rule for beams: phi16 longitudinal only, phi10
stirrups single or double (no phi12 in beams); 2nd bar layer drawn where needed; cantilevers 8phi16 + 8phi16.
Previous header: task 55 (2026-11-07): structural drawings Rev4 from ETABS Rev6h (C17 Story1 18φ20; bars from the Rev6h design).
Previous header: task 50 (2026-10-31): structural drawings Rev3 FOR APPROVAL, SCALE 1:20 (boss), A0 sheets, real DWG drawings.
Model units = metres; every sheet frame = A0 at 1:20 (23.78 x 16.82 m), plotted with 50 mm per metre.
Sheets (16):
  S3-F01 foundation plan (combined strip footings, axes, elevator pit)       S3-F02 strip sections, column-to-footing, pit section
  S3-B01..B05 beam reinforcement elevations + sections, floors 1-3, roof, stair-house roof
  S3-C01 column reinforcement elevations (CT-1 / CT-2, all storeys) + sections, corbel note
  S3-S01..S05 slab plans (joists, tie beams, openings) floors 1-3, roof, stair-house roof    S3-S06 slab details (joist, tie beam, topping)
  S3-ST01 stair sections all storeys                                           S3-ST02 stair details (corbel seat, sliding top on BS, BS / BT / landing beam)
Inputs (read only): ETABS/geom_Rev6d.json (same geometry as Rev6h), T55/t55_design.json, T55/t55_hand_checks.json.
    python t55_design.py && python t55_hand_checks.py && python make_struct_Rev5.py && python plot_Rev5.py
AutoCAD lock Merage3/work/_autocad.lock around the accoreconsole run."""
import json
import math
import os
import re
import subprocess
import time

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GEOM = os.path.join(PRJ, "ETABS", "geom_Rev6d.json")
DES = os.path.join(HERE, "t55_design.json")
HC = os.path.join(HERE, "t55_hand_checks.json")
OUT_DIR = os.path.join(PRJ, "struct")
OUT_DWG = os.path.join(OUT_DIR, "Merage3_struct_Rev5.dwg")
TMP = "C:/ZagrosTemp/rev3"
LOCK = os.path.join(PRJ, "work", "_autocad.lock")
ACCORE = r"C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe"
DATE = "1405/08/09"
W, H, PITCH = 23.78, 16.82, 25.0                   # A0 at 1:20 in metres
T1, T2, T3, T4 = 0.05, 0.07, 0.10, 0.14            # text heights = 2.5 / 3.5 / 5 / 7 mm on paper
SRC = "ETABS Merage3_Rev6h.EDB (task 55), ACI 318-19, 51 A22 combos (rho 1.0, EV cantilevers), Ax = 1.22; levels arch Rev.12/13"
LAYERS = {
    "S-GRID": (5, "CENTER", 13, "Grid lines"), "S-GRID-IDEN": (2, "CONTINUOUS", 25, "Grid bubbles"),
    "S-CONC": (4, "CONTINUOUS", 35, "Concrete outline (cut)"), "S-CONC-HIDN": (8, "DASHED", 18, "Concrete hidden / beyond"),
    "S-COLS": (3, "CONTINUOUS", 35, "Columns"), "S-COLS-PATT": (8, "CONTINUOUS", 9, "Column fill"),
    "S-FNDN": (4, "CONTINUOUS", 35, "Foundation outline"), "S-FNDN-LEAN": (8, "DASHED", 18, "Lean concrete"),
    "S-REBR": (1, "CONTINUOUS", 50, "Main reinforcement"), "S-REBR-TIES": (3, "CONTINUOUS", 25, "Hoops / ties / stirrups"),
    "S-SLAB": (6, "CONTINUOUS", 18, "Joists, tie beams, slab"), "S-SLAB-OPNG": (6, "CONTINUOUS", 18, "Openings"),
    "S-DIMS": (1, "CONTINUOUS", 18, "Dimensions"), "S-ANNO": (2, "CONTINUOUS", 25, "Titles and notes"),
    "S-ANNO-IDEN": (7, "CONTINUOUS", 18, "Bar marks and labels"), "S-ANNO-TTLB": (7, "CONTINUOUS", 25, "Title block"),
    "S-ANNO-BRDR": (6, "CONTINUOUS", 50, "Border"),
}
LAP = {10: 0.60, 12: 0.75, 14: 0.85, 16: 1.00, 18: 1.10, 20: 1.20, 22: 1.35, 25: 1.50}   # class B lap ~ 60 db (rounded)
STORY = {"Story1": ("FLOOR 1", 4.00, 0.50), "Story2": ("FLOOR 2", 7.40, 0.50), "Story3": ("FLOOR 3", 10.80, 0.50),
         "Story4": ("ROOF", 14.20, 0.50), "Story5": ("STAIR-HOUSE ROOF", 17.50, 0.40)}
FA_TITLE = {"Story1": "طبقه ى اول", "Story2": "طبقه ى دوم", "Story3": "طبقه ى سوم", "Story4": "بام", "Story5": "بام خرپشته"}
GRID_X = [("A", 0.0), ("B", 2.35), ("B'", 2.50), ("C", 7.15)]
GRID_Y = [("1", 0.0), ("2", 7.50), ("3", 13.50), ("4", 18.81), ("5", 20.01)]


def fa(text):
    text = text.replace("\u200c", " ")
    return re.sub("ی(?=[ؠ-يپ-ۓ])", "ي", text).replace("ی", "ى")


def phi(s):
    return s.replace("φ", "%%c")


def bars_of(s):
    """'4φ16+3φ20' -> [(4, 16), (3, 20)]"""
    return [(int(a), int(b)) for a, b in re.findall(r"(\d+)φ(\d+)", s or "")]


class Sheet:
    def __init__(self, doc, i, no, tfa, ten):
        self.doc, self.msp = doc, doc.modelspace()
        self.x0, self.y0 = i * PITCH, 0.0
        self.no, self.tfa, self.ten = no, tfa, ten
        self.frame()

    def L(self, layer, p, q):
        return self.msp.add_line(p, q, dxfattribs={"layer": layer})

    def P(self, layer, pts, close=True):
        return self.msp.add_lwpolyline(pts, close=close, dxfattribs={"layer": layer})

    def R(self, layer, u, v, w, h):
        return self.P(layer, [(u, v), (u + w, v), (u + w, v + h), (u, v + h)])

    def C(self, layer, u, v, r, fill=False):
        self.msp.add_circle((u, v), r, dxfattribs={"layer": layer})
        if fill:
            hh = self.msp.add_hatch(dxfattribs={"layer": layer})
            hh.paths.add_edge_path().add_arc((u, v), r, 0, 360)

    def T(self, s, u, v, h=T1, layer="S-ANNO-IDEN", farsi=False, rot=0.0, align=TA.MIDDLE_LEFT, width=None):
        t = self.msp.add_text(fa(s) if farsi else phi(s), height=h, rotation=rot,
                              dxfattribs={"layer": layer, "style": "FARSI" if farsi else "LATIN", "width": width or (1.0 if farsi else 0.85)})
        t.set_placement((u, v), align=align)
        return t

    def dim(self, p1, p2, base, ang, txt=None):
        meas = abs(p2[0] - p1[0]) if ang == 0 else abs(p2[1] - p1[1])
        d = self.msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=ang, dimstyle="S20", text=txt or f"{meas:.2f}",
                                    dxfattribs={"layer": "S-DIMS"})
        d.render()

    def hatch(self, layer, pts):
        hh = self.msp.add_hatch(dxfattribs={"layer": layer})
        hh.paths.add_polyline_path(pts, is_closed=True)

    def notes(self, u, v, lines, h=T1, step=0.085, head=None):
        if head:
            self.T(head, u, v, T2, layer="S-ANNO"); v -= step * 1.5
        for s in lines:
            self.T(s, u, v, h); v -= step
        return v

    def frame(self):
        x0, y0 = self.x0, self.y0
        self.R("S-ANNO-TTLB", x0, y0, W, H)
        m = 0.5
        self.R("S-ANNO-BRDR", x0 + m, y0 + m, W - 2 * m, H - 2 * m)
        tw, th = 6.0, 2.4
        bx1, by0 = x0 + W - m, y0 + m
        bx0, by1 = bx1 - tw, by0 + th
        self.R("S-ANNO-TTLB", bx0, by0, tw, th)
        rows = [("شرکت آهن بتن زاگرس - سهامی خاص", 0.12, True), ("پروژه: مرآژ ۳ - Merage3 - مسکونی ۳ طبقه روی پارکینگ - مینودشت", 0.09, True),
                ("عنوان: " + self.tfa, 0.09, True), ("مهندس محاسب: رحمت الله شیرزایی", 0.12, True),
                (f"مقیاس: 1:20     کاغذ: A0     تاریخ: {DATE}     شماره نقشه: {self.no}     ویرایش: Rev5", 0.07, True),
                ("وضعیت: برای تأیید - برای اجرا نیست", 0.11, True), ("Source: " + SRC, 0.045, False)]
        rh = th / len(rows)
        for k, (s, hh, f) in enumerate(rows):
            if k:
                self.L("S-ANNO-TTLB", (bx0, by1 - k * rh), (bx1, by1 - k * rh))
            self.T(s, (bx0 + bx1) / 2, by1 - (k + 0.5) * rh, hh, layer="S-ANNO", farsi=f, align=TA.MIDDLE_CENTER)
        self.T(self.tfa + " - برای تأیید", x0 + W / 2, y0 + H - 0.9, T4, layer="S-ANNO", farsi=True, align=TA.MIDDLE_CENTER)
        self.T(f"{self.no}  {self.ten}  -  SCALE 1:20  -  FOR APPROVAL, NOT FOR CONSTRUCTION", x0 + W / 2, y0 + H - 1.15, T2, layer="S-ANNO", align=TA.MIDDLE_CENTER)


# ------------------------------------------------------------------ data
def load():
    g = json.load(open(GEOM, encoding="utf-8"))
    for u, v in g["new_objects_project_labels"]["frames"].items():
        g["frames"][u]["label_etabs"] = g["frames"][u]["label"]
        g["frames"][u]["label"] = v["label"]
    des = json.load(open(DES, encoding="utf-8"))
    D = {(r["label"], r["story"]): r for r in des["beams"]}
    return g, des, D, json.load(open(HC, encoding="utf-8"))


def beam_lines(g, story):
    """group the beams of a storey into lines: Y lines (A, B/B', C) and X lines (axes, BS, BT, BH)"""
    bms = [f for f in g["frames"].values() if f["kind"] == "beam" and f["story"] == story]
    lines = {}
    for b in bms:
        if abs(b["yi"] - b["yj"]) < 0.02:                      # along X
            key = ("X", round(b["yi"], 3), b["label"] if b["label"] in ("BS", "BT", "BH") else "")
            lines.setdefault(key, []).append(b)
        else:
            xm = (b["xi"] + b["xj"]) / 2
            key = ("Y", "A" if xm < 1.0 else ("B" if xm < 4.0 else "C"), "")
            lines.setdefault(key, []).append(b)
    for k in lines:
        lines[k].sort(key=lambda b: min(b["xi"], b["xj"]) if k[0] == "X" else min(b["yi"], b["yj"]))
    return lines


def col_xy(g, story):
    return {(round(f["xi"], 2), round(f["yi"], 2)): f for f in g["frames"].values() if f["kind"] == "column" and f["story"] == story}


# ------------------------------------------------------------------ beam elevation
def draw_beam_line(sh, u0, v0, key, beams, D, story, cols):
    """elevation of one beam line at 1:20; u0 = left end (start coordinate 0 of the line), v0 = top of the beams"""
    axis = key[0]
    hb = STORY[story][2]
    cov = 0.05
    pos = lambda b, end: (b["xi"] if end == "i" else b["xj"]) if axis == "X" else (b["yi"] if end == "i" else b["yj"])
    s0 = min(min(pos(b, "i"), pos(b, "j")) for b in beams)
    U = lambda s: u0 + (s - s0)
    # supports = column positions on the line
    sup = []
    for b in beams:
        for end in ("i", "j"):
            x, y = (b["xi"], b["yi"]) if end == "i" else (b["xj"], b["yj"])
            c = cols.get((round(x, 2), round(y, 2)))
            s = pos(b, end)
            if c and all(abs(s - q[0]) > 1e-3 for q in sup):
                sup.append((s, int(c["sec"][1:3]) / 100.0, c["label"]))
    sup.sort()
    # columns (stubs) and beam outline
    for s, cw, lab in sup:
        sh.R("S-COLS", U(s) - cw / 2, v0 - hb - 0.6, cw, hb + 1.0)
        sh.T(lab, U(s), v0 + 0.48, T1, layer="S-ANNO-IDEN", align=TA.BOTTOM_CENTER)
    for b in beams:
        a, c = sorted((pos(b, "i"), pos(b, "j")))
        r = D.get((b["label"], story))
        if r is None:
            continue
        fa_ = [q for q in sup if abs(q[0] - a) < 1e-3]; fb_ = [q for q in sup if abs(q[0] - c) < 1e-3]
        ua = U(a) + (fa_[0][1] / 2 if fa_ else 0.0); ub = U(c) - (fb_[0][1] / 2 if fb_ else 0.0)
        hh = int(r["sec"].split("H")[1]) / 100.0
        sh.L("S-CONC", (ua, v0), (ub, v0)); sh.L("S-CONC", (ua, v0 - hh), (ub, v0 - hh))
        for uu, has in ((ua, bool(fa_)), (ub, bool(fb_))):
            if not has:
                sh.L("S-CONC", (uu, v0), (uu, v0 - hh))
        Ln = ub - ua
        cant = r["label"] in ("B3", "B5", "B6") and story != "Story5"
        top, bot = r["topI"], r["bot"]
        # continuous top / bottom (from the design: 4phi16 or the cantilever 3phi25 / BS etc.)
        cont = r["top"]
        sh.L("S-REBR", (ua - (fa_[0][1] - 0.06 if fa_ else 0.0), v0 - cov), (ub + (fb_[0][1] - 0.06 if fb_ else -0.04), v0 - cov))
        sh.L("S-REBR", (ua - (fa_[0][1] - 0.06 if fa_ else 0.0), v0 - hh + cov), (ub + (fb_[0][1] - 0.06 if fb_ else -0.04), v0 - hh + cov))
        # end hooks where the line ends at an exterior column / free end
        for uu, ext, sgn in ((ua - (fa_[0][1] - 0.06 if fa_ else 0.0), a == sup[0][0] if sup else True, 1), (ub + (fb_[0][1] - 0.06 if fb_ else -0.04), c == sup[-1][0] if sup else True, -1)):
            if ext:
                sh.L("S-REBR", (uu, v0 - cov), (uu, v0 - cov - 0.25)); sh.L("S-REBR", (uu, v0 - hh + cov), (uu, v0 - hh + cov + 0.25))
        # extra top bars at the supports (to Ln/3 from the face)
        ext_i = r["topI"].split("+")[1] if "+" in r["topI"] else ""
        ext_j = r["topJ"].split("+")[1] if "+" in r["topJ"] else ""
        if cant:
            sh.T(f"{r['top']} top through the column, ld + Ln/3 into the back span", ua + 0.05, v0 + 0.08, T1)
        for txt, uu, d_ in ((ext_i, ua, 1), (ext_j, ub, -1)):
            if txt:
                e1, e2 = uu - d_ * 0.2, uu + d_ * max(Ln / 3, 0.6)
                sh.L("S-REBR", (e1, v0 - cov - 0.035), (e2, v0 - cov - 0.035))
                sh.T(f"{txt} L={abs(e2 - e1):.2f}", min(e1, e2) + 0.05, v0 + 0.05, T1)
        ext_b = r["bot"].split("+")[1] if "+" in r["bot"] else ""
        if ext_b:
            sh.L("S-REBR", (ua - 0.1, v0 - hh + cov + 0.035), (ub + 0.1, v0 - hh + cov + 0.035))
        # laps (outside 2h zones and joints): top at mid-span, bottom at 0.3 Ln
        dtop = max(d for n_, d in bars_of(cont)) if bars_of(cont) else 16
        lt = LAP.get(dtop, 1.0)
        if Ln > 2 * 2 * hh + lt and not cant:
            um = (ua + ub) / 2
            sh.L("S-REBR", (um - lt / 2, v0 - cov - 0.018), (um + lt / 2, v0 - cov - 0.018))
            sh.T(f"lap {lt:.2f}", um - lt / 2, v0 - cov - 0.08, T1 * 0.8)
            ul = ua + 2 * hh + 0.1
            if ul + lt < ub - 2 * hh:
                sh.L("S-REBR", (ul, v0 - hh + cov + 0.018), (ul + lt, v0 - hh + cov + 0.018))
                sh.T(f"lap {lt:.2f}", ul, v0 - hh + cov + 0.07, T1 * 0.8)
        # hoops
        sp = lambda s: int(re.findall(r"@(\d+)", s)[0]) / 1000.0 if re.findall(r"@(\d+)", s or "") else None
        sh_, sm_ = sp(r["hoop_h"]), sp(r["hoop_m"])
        z = Ln if (cant or r["hoop_m"] is None or "meet" in str(r["hoop_m"]) or r["label"] in ("BS", "BT", "BH")) else min(2 * hh, Ln / 2)
        uu = ua + 0.05
        while uu <= ua + z + 1e-6 and uu < ub - 0.04:
            sh.L("S-REBR-TIES", (uu, v0 - cov + 0.01), (uu, v0 - hh + cov - 0.01)); uu += sh_
        if z < Ln:
            uu = ub - 0.05
            while uu >= ub - z - 1e-6:
                sh.L("S-REBR-TIES", (uu, v0 - cov + 0.01), (uu, v0 - hh + cov - 0.01)); uu -= sh_
            uu = ua + z + (sm_ or sh_)
            while uu < ub - z - 1e-6:
                sh.L("S-REBR-TIES", (uu, v0 - cov + 0.01), (uu, v0 - hh + cov - 0.01)); uu += (sm_ or sh_)
            sh.dim((ua, v0 - hh), (ua + z, v0 - hh), (0, v0 - hh - 0.12), 0, txt=f"2h={z:.2f} {r['hoop_h']}".replace("φ", "%%c"))
            sh.dim((ua + z, v0 - hh), (ub - z, v0 - hh), (0, v0 - hh - 0.12), 0, txt=f"{r['hoop_m']}".replace("φ", "%%c"))
            sh.dim((ub - z, v0 - hh), (ub, v0 - hh), (0, v0 - hh - 0.12), 0, txt=f"2h={z:.2f}")
        else:
            sh.dim((ua, v0 - hh), (ub, v0 - hh), (0, v0 - hh - 0.12), 0, txt=f"{r['hoop_h']} full length".replace("φ", "%%c"))
        # labels
        um = (ua + ub) / 2
        sh.T(f"{r['label']}  {r['sec'].replace('BW', '').replace('xH', 'x')}", um, v0 + 0.30, T2, layer="S-ANNO", align=TA.BOTTOM_CENTER)
        sh.T(f"top cont. {cont}   bottom {bot}" + (f"   web {r['web']}" if r.get("web") else ""), um, v0 + 0.20, T1, align=TA.BOTTOM_CENTER)
        # sections A (support) and B (mid-span) under the beam
        sect(sh, ua + 0.45, v0 - hh - 0.75, r, hh, "support", top, bot)
        if Ln > 1.6:
            sect(sh, um, v0 - hh - 0.75, r, hh, "mid", cont, bot)


def sect(sh, cu, cvtop, r, hh, kind, top, bot):
    b = int(r["sec"][2:4]) / 100.0
    sh.R("S-CONC", cu - b / 2, cvtop - hh, b, hh)
    c = 0.046
    sh.R("S-REBR-TIES", cu - b / 2 + c, cvtop - hh + c, b - 2 * c, hh - 2 * c)
    hs = r["hoop_h"] if kind == "support" else (r["hoop_m"] or r["hoop_h"])
    if "double" in str(hs):   # inner closed hoop around the middle bars
        sh.R("S-REBR-TIES", cu - b / 4, cvtop - hh + c + 0.004, b / 2, hh - 2 * c - 0.008)
    nl = int((b * 1000 - 2 * 40 - 2 * 10 - 16) // 41) + 1          # phi16 bars per layer
    for bars, vv, sg in ((top, cvtop - c - 0.012, -1), (bot, cvtop - hh + c + 0.012, 1)):
        lst = [d for n_, d in bars_of(bars) for _ in range(n_)]
        rows_ = [lst[:nl], lst[nl:]] if len(lst) > nl else [lst]
        for li, row in enumerate(rows_):
            k = len(row)
            for i, d in enumerate(row):
                uu = cu - b / 2 + c + 0.015 + (b - 2 * c - 0.03) * (i / (k - 1) if k > 1 else 0.5)
                sh.C("S-REBR", uu, vv + sg * li * 0.041, d / 2000.0, fill=True)
    sh.T(("A-A support: " if kind == "support" else "B-B mid: ") + f"{top} / {bot}", cu - b / 2, cvtop - hh - 0.07, T1 * 0.8)
    sh.T(r["hoop_h"] if kind == "support" else (r["hoop_m"] or r["hoop_h"]), cu - b / 2, cvtop - hh - 0.15, T1 * 0.8)


def beam_sheets(doc, g, D, i0):
    sheets = []
    for k, story in enumerate(["Story1", "Story2", "Story3", "Story4", "Story5"]):
        sh = Sheet(doc, i0 + k, f"S3-B0{k + 1}", f"آرماتورگذاری تیرهای {FA_TITLE[story]}",
                   f"BEAM REINFORCEMENT - {STORY[story][0]} (TOS {STORY[story][1]:+.2f})")
        lines = beam_lines(g, story)
        cols = col_xy(g, story)
        ylines = [k_ for k_ in lines if k_[0] == "Y"]; xlines = sorted([k_ for k_ in lines if k_[0] == "X"], key=lambda k_: (k_[2] != "", k_[1]))
        v = sh.y0 + H - 2.0
        for key in sorted(ylines, key=lambda k_: k_[1]):
            sh.T(f"BEAM LINE {key[1]} (along Y, axis 1 -> 5)", sh.x0 + 0.8, v + 0.55, T2, layer="S-ANNO")
            draw_beam_line(sh, sh.x0 + 1.5, v, key, lines[key], D, story, cols)
            v -= 2.35
        u = sh.x0 + 1.0
        for key in xlines:
            span = max(max(b["xi"], b["xj"]) for b in lines[key]) - min(min(b["xi"], b["xj"]) for b in lines[key])
            if u + span + 0.8 > sh.x0 + W - 0.6:
                u = sh.x0 + 1.0; v -= 2.35
            if v < sh.y0 + 3.2 and u + span > sh.x0 + W - 6.8:
                u = sh.x0 + 1.0; v -= 2.35
            nm = key[2] or f"axis Y = {key[1]:.2f}"
            sh.T(f"BEAM LINE {nm} (along X)", u - 0.2, v + 0.55, T2, layer="S-ANNO")
            draw_beam_line(sh, u, v, key, lines[key], D, story, cols)
            u += span + 1.2
        sh.notes(sh.x0 + 16.6, sh.y0 + 6.2, [
            "1. Concrete C25, bars S400 (stirrups S340), clear cover 40 mm. Lengths in m, bars in mm. Labels = project labels.",
            "2. Continuous top and bottom bars hooked 90° (12db, 0.25) in exterior columns; extra top bars from the column face to Ln/3 (>= Ln/4 + d).",
            "3. Laps class B (~60db) only in the middle zone (outside 2h and joints, ACI 18.6.3.3); hoops @ <= 100 over the lap.",
            "4. Closed hoops φ10 only (boss), 135° hooks, first hoop 50 mm from the face; 2h zone = special hoop zone (ACI 18.6.4). 2xφ10 (double) = two closed hoops, the inner one around the middle bars.",
            "4a. Longitudinal bars φ16 only (boss); bars beyond one layer in a 2nd layer 25 mm clear below / above the first.",
            "5. Cantilevers B3/B5/B6: 8φ16 top + 8φ16 bottom + 2φ16 EF, φ10@80 full length (Sway Ordinary, J = 0.1).",
        ], head="NOTES")
        sheets.append(sh)
    return sheets


# ------------------------------------------------------------------ foundation
FX = {"A": (-0.25, 1.75), "B/B'": (1.35, 3.35), "C": (5.40, 7.40)}
FY = (-0.25, 20.01)


def foundation_plan(doc, g, hc, i):
    sh = Sheet(doc, i, "S3-F01", "پلان پی نواری مرکب و چاهک آسانسور", "FOUNDATION PLAN - COMBINED STRIP FOOTINGS + ELEVATOR PIT")
    du, dv = sh.x0 + 22.0, sh.y0 + 6.2                        # u = -Y + du, v = X + dv
    E = lambda X, Y: (-Y + du, X + dv)
    for name, X in GRID_X:
        a, b = E(X, -1.2), E(X, 21.2)
        sh.L("S-GRID", a, b); sh.C("S-GRID-IDEN", b[0] - 0.25, b[1], 0.25); sh.T(name, b[0] - 0.25, b[1], T3, layer="S-GRID-IDEN", align=TA.MIDDLE_CENTER)
    for name, Y in GRID_Y:
        a, b = E(-1.2, Y), E(8.4, Y)
        sh.L("S-GRID", a, b); sh.C("S-GRID-IDEN", a[0], a[1] - 0.25, 0.25); sh.T(name, a[0], a[1] - 0.25, T3, layer="S-GRID-IDEN", align=TA.MIDDLE_CENTER)
    for name, (x0, x1) in FX.items():
        pts = [E(x0, FY[0]), E(x1, FY[0]), E(x1, FY[1]), E(x0, FY[1])]
        sh.P("S-FNDN", pts)
        pl = [E(x0 - 0.10, FY[0] - 0.10), E(x1 + 0.10, FY[0] - 0.10), E(x1 + 0.10, FY[1] + 0.10), E(x0 - 0.10, FY[1] + 0.10)]
        sh.P("S-FNDN-LEAN", pl)
        c = E((x0 + x1) / 2, 10.0)
        sh.T(f"STRIP {name}: 2.00 x 0.80 (lean 0.10), 10φ18 top + 10φ18 bottom, transverse φ14@150 (bends 0.20)", c[0], c[1], T1, align=TA.MIDDLE_CENTER)
    ov = [E(1.35, FY[0]), E(1.75, FY[0]), E(1.75, FY[1]), E(1.35, FY[1])]
    hh_ = sh.msp.add_hatch(dxfattribs={"layer": "S-FNDN-LEAN"}); hh_.set_pattern_fill("ANSI31", scale=0.02); hh_.paths.add_polyline_path(ov, is_closed=True)
    c = E(1.55, 5.0); sh.T("OVERLAP A / B 0.40 (strips merge) - QUESTION", c[0], c[1] + 0.05, T1, align=TA.MIDDLE_CENTER)
    for f in g["frames"].values():
        if f["kind"] == "column" and f["story"] == "Story1":
            r = 0.25
            pts = [E(f["xi"] - r, f["yi"] - r), E(f["xi"] + r, f["yi"] - r), E(f["xi"] + r, f["yi"] + r), E(f["xi"] - r, f["yi"] + r)]
            sh.P("S-COLS", pts); sh.hatch("S-COLS-PATT", pts)
            bars = next((c_["bars"] for c_ in json.load(open(DES, encoding="utf-8"))["columns"] if c_["label"] == f["label"] and c_["story"] == "Story1"), "16φ20")
            q = E(f["xi"] + r, f["yi"] - r); sh.T(f["label"] + " 50x50 " + bars, q[0] + 0.03, q[1] + 0.05, T1)
    # pit
    pit = [E(0.20, 13.50), E(2.70, 13.50), E(2.70, 15.80), E(0.20, 15.80)]
    sh.P("S-CONC", pit)
    pin = [E(0.449, 13.754), E(2.449, 13.754), E(2.449, 15.553), E(0.449, 15.553)]
    sh.P("S-CONC", pin)
    c = E(1.45, 14.65)
    sh.T("ELEVATOR PIT -2.00 (inside 2.00 x 1.80, walls 0.25, slab 0.30) - see S3-F02", c[0], c[1], T1, align=TA.MIDDLE_CENTER)
    # dimensions
    for (a, b) in zip([0.0, 7.5, 13.5, 18.81], [7.5, 13.5, 18.81, 20.01]):
        sh.dim(E(-0.25, a), E(-0.25, b), (0, E(-1.6, 0)[1]), 0)
    sh.dim(E(-0.25, FY[0]), E(-0.25, FY[1]), (0, E(-2.0, 0)[1]), 0, txt=f"{FY[1] - FY[0]:.2f}")
    for x0, x1 in FX.values():
        sh.dim(E(x0, -0.25), E(x1, -0.25), (E(0, -1.0)[0], 0), 90, txt="2.00")
    st = hc["strip_footings"]
    lines = ["1. Combined strip footings per the boss: depth 0.80, width 2.00, lean concrete 0.10; 10φ18 top + 10φ18 bottom;",
             "   transverse φ14@150 with 0.20 bends each side; cover bottom 100, top 70, sides 50 mm. Top of footing +-0.00.",
             "2. Strip direction (not given by the boss): longitudinal under axes A, B/B', C from axis 1 to axis 5 (QUESTION).",
             "   Strip A outer edge flush with the column face at the boundary (X -0.25); A and B overlap 0.40 m and merge (QUESTION).",
             "3. Columns cast monolithic into the footing; column bars with 90° bends 0.25 towards the column inside (S3-F02).",
             "4. Elevator pit floor -2.00 between axes 3 and 4 (A-B); the strips step down around the pit (S3-F02, QUESTION).",
             "5. CHECK ONLY (Rev6h reactions, report T55): soil pressure (service) " + ", ".join(f"{k} {v['q_service_kPa (incl. self weight)']}" for k, v in st.items()) + " kPa",
             "   (allowable soil pressure not given - QUESTION); longitudinal flexure Mu up to " + f"{max(v['Mu_max_abs_kNm'] for v in st.values()):.0f}" +
             f" kN.m > phiMn {list(st.values())[0]['phiMn_bottom_10φ18']} kN.m and Vu up to {max(v['Vu_max_kN'] for v in st.values()):.0f} > phiVc {list(st.values())[0]['phiVc_kN']} kN:",
             "   THE STRIPS AS GIVEN DO NOT PASS - dimensions / bars NOT changed (boss order), decision of the boss required."]
    sh.notes(sh.x0 + 0.8, sh.y0 + 3.6, lines, head="FOUNDATION NOTES")
    return sh


def foundation_details(doc, i):
    sh = Sheet(doc, i, "S3-F02", "مقاطع پی نواری، اتصال ستون به پی و چاهک", "STRIP FOOTING SECTIONS, COLUMN-TO-FOOTING, ELEVATOR PIT")
    # transverse section 2.00 x 0.80
    u0, v0 = sh.x0 + 1.5, sh.y0 + 10.5
    sh.R("S-FNDN", u0, v0, 2.0, 0.8); sh.R("S-FNDN-LEAN", u0 - 0.1, v0 - 0.1, 2.2, 0.1)
    sh.R("S-COLS", u0 + 0.75, v0 + 0.8, 0.5, 1.2)
    cb, ct, cs = 0.10, 0.07, 0.05
    # transverse bars (bottom and top) with 0.20 bends
    sh.P("S-REBR-TIES", [(u0 + cs, v0 + cb + 0.2), (u0 + cs, v0 + cb), (u0 + 2.0 - cs, v0 + cb), (u0 + 2.0 - cs, v0 + cb + 0.2)], close=False)
    sh.P("S-REBR-TIES", [(u0 + cs, v0 + 0.8 - ct - 0.2), (u0 + cs, v0 + 0.8 - ct), (u0 + 2.0 - cs, v0 + 0.8 - ct), (u0 + 2.0 - cs, v0 + 0.8 - ct - 0.2)], close=False)
    for k in range(10):
        uu = u0 + cs + 0.014 + (2.0 - 2 * cs - 0.028) * k / 9
        sh.C("S-REBR", uu, v0 + cb + 0.014 + 0.009, 0.009, True); sh.C("S-REBR", uu, v0 + 0.8 - ct - 0.014 - 0.009, 0.009, True)
    # column bars into the footing with 90 deg 0.25 bends inward
    for uu, d_ in ((u0 + 0.75 + 0.07, 1), (u0 + 1.25 - 0.07, -1)):
        sh.P("S-REBR", [(uu, v0 + 2.0), (uu, v0 + cb + 0.05), (uu + d_ * 0.25, v0 + cb + 0.05)], close=False)
    sh.dim((u0, v0), (u0 + 2.0, v0), (0, v0 - 0.35), 0, txt="2.00")
    sh.dim((u0 + 2.0, v0), (u0 + 2.0, v0 + 0.8), (u0 + 2.35, 0), 90, txt="0.80")
    sh.T("TRANSVERSE SECTION 1-1 (1:20)", u0, v0 + 2.25, T3, layer="S-ANNO")
    sh.notes(u0, v0 - 0.6, ["10φ18 top + 10φ18 bottom (longitudinal), transverse φ14@150 top and bottom with 0.20 bends each side,",
                            "cover: bottom 100, top 70, sides 50 mm; lean concrete 0.10. Column bars: 90° bend 0.25 towards the column inside,",
                            "resting on the bottom mat; 3 column hoops inside the footing."])
    # longitudinal section strip A, 20.26 m
    u1, v1 = sh.x0 + 1.5, sh.y0 + 5.2
    Ls = FY[1] - FY[0]
    sh.R("S-FNDN", u1, v1, Ls, 0.8); sh.R("S-FNDN-LEAN", u1 - 0.1, v1 - 0.1, Ls + 0.2, 0.1)
    sh.L("S-REBR", (u1 + 0.05, v1 + 0.8 - ct - 0.03), (u1 + Ls - 0.05, v1 + 0.8 - ct - 0.03))
    sh.L("S-REBR", (u1 + 0.05, v1 + cb + 0.03), (u1 + Ls - 0.05, v1 + cb + 0.03))
    for uu in (u1 + 0.05, u1 + Ls - 0.05):
        sh.L("S-REBR", (uu, v1 + cb + 0.03), (uu, v1 + 0.8 - ct - 0.03))
    for Y, lab in ((0.0, "C1"), (7.5, "C2"), (13.5, "C16"), (18.81, "C17")):
        uc = u1 + (Y - FY[0])
        sh.R("S-COLS", uc - 0.25, v1 + 0.8, 0.5, 1.0)
        sh.T(lab, uc, v1 + 1.9, T2, layer="S-ANNO", align=TA.BOTTOM_CENTER)
        for uu, d_ in ((uc - 0.18, 1), (uc + 0.18, -1)):
            sh.P("S-REBR", [(uu, v1 + 1.8), (uu, v1 + cb + 0.06), (uu + d_ * 0.25, v1 + cb + 0.06)], close=False)
    k = 0
    uu = u1 + 0.10
    while uu < u1 + Ls - 0.05:
        sh.L("S-REBR-TIES", (uu, v1 + cb + 0.01), (uu, v1 + cb + 0.05)); sh.L("S-REBR-TIES", (uu, v1 + 0.8 - ct - 0.05), (uu, v1 + 0.8 - ct - 0.01))
        uu += 0.15
    for um in (u1 + (3.75 - FY[0]), u1 + (10.5 - FY[0]), u1 + (16.15 - FY[0])):
        sh.L("S-REBR", (um - 0.55, v1 + cb + 0.05), (um + 0.55, v1 + cb + 0.05)); sh.T("lap 1.10 (bottom, mid-span)", um - 0.55, v1 + cb + 0.10, T1)
    for Y in (7.5, 13.5):
        um = u1 + (Y - FY[0])
        sh.L("S-REBR", (um - 0.55, v1 + 0.8 - ct - 0.05), (um + 0.55, v1 + 0.8 - ct - 0.05)); sh.T("lap 1.10 (top, over the column)", um - 0.55, v1 + 0.8 - ct - 0.12, T1)
    sh.dim((u1, v1), (u1 + Ls, v1), (0, v1 - 0.35), 0, txt=f"{Ls:.2f} (axis 1 -0.25 to axis 5)")
    sh.T("LONGITUDINAL SECTION 2-2, STRIP A (typical for B/B' and C) (1:20)", u1, v1 + 2.3, T3, layer="S-ANNO")
    # column-to-footing detail
    u2, v2 = sh.x0 + 5.5, sh.y0 + 10.5
    sh.R("S-FNDN", u2, v2, 2.0, 0.8)
    sh.R("S-COLS", u2 + 0.75, v2 + 0.8, 0.5, 2.0)
    for uu, d_ in ((u2 + 0.82, 1), (u2 + 1.18, -1)):
        sh.P("S-REBR", [(uu, v2 + 2.8), (uu, v2 + cb + 0.05), (uu + d_ * 0.25, v2 + cb + 0.05)], close=False)
    for vv in (v2 + 0.25, v2 + 0.45, v2 + 0.65):
        sh.L("S-REBR-TIES", (u2 + 0.80, vv), (u2 + 1.20, vv))
    vv = v2 + 0.85
    while vv < v2 + 0.85 + 0.6:
        sh.L("S-REBR-TIES", (u2 + 0.80, vv), (u2 + 1.20, vv)); vv += 0.085
    sh.L("S-REBR", (u2 + 0.86, v2 + 0.8 + 0.6), (u2 + 0.86, v2 + 0.8 + 0.6 + 1.2))
    sh.T("lap 1.20 (16φ20) above lo, mid-height of the parking storey", u2 + 1.3, v2 + 2.2, T1)
    sh.T("16φ20 column bars, 90° bend 0.25 towards the column inside on the bottom mat", u2 + 1.3, v2 + 0.2, T1)
    sh.T("3 hoops φ12 inside the footing; lo = 0.60 hoops φ12@85 (3 legs) from +-0.00", u2 + 1.3, v2 + 1.0, T1)
    sh.T("COLUMN-TO-FOOTING DETAIL (1:20)", u2, v2 + 3.0, T3, layer="S-ANNO")
    # pit section
    u3, v3 = sh.x0 + 11.0, sh.y0 + 9.0
    sh.R("S-CONC", u3, v3, 2.5, 0.30)                                  # slab -2.00 (top) to -2.30
    sh.R("S-CONC", u3, v3 + 0.30, 0.25, 2.0); sh.R("S-CONC", u3 + 2.25, v3 + 0.30, 0.25, 2.0)
    sh.R("S-FNDN-LEAN", u3 - 0.1, v3 - 0.1, 2.7, 0.1)
    sh.R("S-FNDN", u3 - 1.5, v3 + 1.5, 1.5, 0.8); sh.R("S-FNDN", u3 + 2.5, v3 + 1.5, 1.5, 0.8)
    sh.T("strip footing (A / B) stepped down around the pit 1:2", u3 - 1.5, v3 + 2.45, T1)
    sh.L("S-REBR", (u3 + 0.05, v3 + 0.05), (u3 + 2.45, v3 + 0.05)); sh.L("S-REBR", (u3 + 0.05, v3 + 0.25), (u3 + 2.45, v3 + 0.25))
    for uu in (u3 + 0.05, u3 + 0.20, u3 + 2.30, u3 + 2.45):
        sh.L("S-REBR", (uu, v3 + 0.05), (uu, v3 + 2.25))
    sh.dim((u3 + 2.5, v3 + 0.30), (u3 + 2.5, v3 + 2.30), (u3 + 2.9, 0), 90, txt="2.00 (pit depth)")
    sh.T("ELEVATOR PIT SECTION 3-3 (1:20): floor -2.00, slab 0.30, walls 0.25 RC, φ12@150 both faces both ways (proposal, QUESTION)", u3 - 1.5, v3 + 3.0, T2, layer="S-ANNO")
    return sh


# ------------------------------------------------------------------ columns
def column_sheet(doc, des, i):
    sh = Sheet(doc, i, "S3-C01", "آرماتورگذاری ستون ها - همه ى طبقات", "COLUMN REINFORCEMENT - ALL STOREYS (CT-1 / CT-2)")
    hoops = des["column_hoops"]
    stor = [("found.", -0.80, 0.0, None), ("Story1", 0.0, 4.00, "C50X50/16T20"), ("Story2", 4.00, 7.40, "C50X50/16T18"),
            ("Story3", 7.40, 10.80, "C45X45/16T16"), ("Story4", 10.80, 14.20, "C45X45/16T16"), ("Story5", 14.20, 17.50, "C40X40/12T16")]
    parts = [("CT-1 (C2, C6, C16, C17, C18, C19 - to the stair-house roof) part 1", 1, (-0.80, 7.40)), ("CT-1 part 2", 1, (7.40, 17.50)),
             ("CT-2 (C1, C5, C9, C10, C20, C21 - to the roof) part 1", 2, (-0.80, 7.40)), ("CT-2 part 2", 2, (7.40, 14.20))]
    u = sh.x0 + 1.5
    for title, typ, (za, zb) in parts:
        vbase = sh.y0 + 3.4 - za * 0 + 0.0
        v0 = sh.y0 + 3.4 - (za if za > 0 else -0.8) + 0.0
        Z = lambda z: sh.y0 + 3.4 + (z - za)
        sh.T(title, u, Z(zb) + 0.9, T2, layer="S-ANNO")
        for nm, z0, z1, sec in stor:
            if z1 <= za + 1e-6 or z0 >= zb - 1e-6:
                continue
            if typ == 2 and nm == "Story5":
                continue
            if sec is None:
                sh.R("S-FNDN", u - 0.75, Z(-0.80), 2.0, 0.8)
                for uu, d_ in ((u + 0.07, 1), (u + 0.43, -1)):
                    sh.P("S-REBR", [(uu, Z(0.0)), (uu, Z(-0.80 + 0.15)), (uu + d_ * 0.25, Z(-0.80 + 0.15))], close=False)
                sh.T("footing 0.80, bars bent 90° x 0.25 inward", u + 0.6, Z(-0.4), T1)
                continue
            b = int(sec[1:3]) / 100.0
            hb = 0.40 if nm == "Story5" else 0.50
            hh = hoops[sec]
            sh.R("S-COLS", u + (0.5 - b) / 2, Z(z0), b, (z1 - z0) - hb)
            sh.R("S-CONC", u - 0.3, Z(z1) - hb, b + 0.6 + (0.5 - b), hb)
            db = int(sec.split("T")[1]); lap = LAP[db]
            zl = z0 + ((z1 - z0) - hb) / 2 - lap / 2
            for uu in (u + (0.5 - b) / 2 + 0.06, u + (0.5 + b) / 2 - 0.06):
                sh.L("S-REBR", (uu, Z(z0)), (uu, Z(zl + lap)))
                sh.L("S-REBR", (uu + 0.02, Z(zl)), (uu + 0.02, Z(min(z1 + 0.6, zb if nm != ("Story5" if typ == 1 else "Story4") else z1 - 0.06))))
            top_end = (typ == 1 and nm == "Story5") or (typ == 2 and nm == "Story4")
            if top_end:
                for uu, d_ in ((u + (0.5 - b) / 2 + 0.08, 1), (u + (0.5 + b) / 2 - 0.08, -1)):
                    sh.L("S-REBR", (uu, Z(z1) - 0.06), (uu + d_ * 0.25, Z(z1) - 0.06))
            lo = max(b, ((z1 - z0) - hb) / 6, 0.45); lo = math.ceil(lo / 0.05) * 0.05
            s_lo = int(re.findall(r"@(\d+)", hh["hoop"])[0]) / 1000; s_m = int(re.findall(r"@(\d+)", hh["hoop_mid"])[0]) / 1000
            zz = z0 + 0.05
            while zz < z1:
                inlo = zz <= z0 + lo or zz >= z1 - hb - lo
                sh.L("S-REBR-TIES", (u + (0.5 - b) / 2 + 0.04, Z(zz)), (u + (0.5 + b) / 2 - 0.04, Z(zz)))
                zz += s_lo if (inlo or zz >= z1 - hb) else s_m
            sh.dim((u + (0.5 + b) / 2, Z(z0)), (u + (0.5 + b) / 2, Z(z0 + lo)), (u + 0.95, 0), 90, txt=f"lo {lo:.2f}")
            sh.dim((u + (0.5 + b) / 2, Z(z1 - hb - lo)), (u + (0.5 + b) / 2, Z(z1 - hb)), (u + 0.95, 0), 90, txt=f"lo {lo:.2f}")
            sh.T(f"{nm} {sec.split('/')[0]} {hh['bars']}", u + 1.2, Z((z0 + z1) / 2) + 0.15, T1)
            sh.T(f"lo + joint: {hh['hoop']} ({hh['legs']} legs)  mid: {hh['hoop_mid']}", u + 1.2, Z((z0 + z1) / 2) + 0.05, T1)
            sh.T(f"lap {lap:.2f} at mid-height (class B)", u + 1.2, Z((z0 + z1) / 2) - 0.05, T1)
            sh.T(f"{STORY.get(nm, ('', z1))[1] if nm in STORY else z1:+.2f}", u - 0.7, Z(z1), T1)
            if typ == 1 and nm in ("Story1", "Story2", "Story3", "Story4"):
                zc = {"Story1": 2.09, "Story2": 5.70, "Story3": 9.10, "Story4": 12.50}[nm]
                sh.P("S-CONC", [(u + 0.5, Z(zc)), (u + 0.8, Z(zc)), (u + 0.8, Z(zc) - 0.25), (u + 0.5, Z(zc) - 0.45)], close=False)
                sh.T(f"C2 / C6 only: corbel at {zc:+.2f} (S3-ST02)", u + 0.85, Z(zc) - 0.1, T1)
        u += 5.0
    # sections
    u, v = sh.x0 + 1.5, sh.y0 + 1.6
    for sec in [s_ for s_ in ("C50X50/18T20", "C50X50/16T20", "C50X50/16T18", "C45X45/16T16", "C40X40/12T16") if s_ in hoops]:
        hh = hoops[sec]; b = int(sec[1:3]) / 100.0; db = int(sec.split("T")[1]); nb = int(sec.split("/")[1].split("T")[0])
        sh.R("S-COLS", u, v, b, b)
        c = 0.04 + 0.012
        sh.R("S-REBR-TIES", u + 0.046, v + 0.046, b - 0.092, b - 0.092)
        nx_, ny_ = (6, 5) if nb == 18 else (nb // 4 + 1, nb // 4 + 1)   # 18 bars: 6 on the faces along x, 5 on the faces along y
        a = b - 2 * c - db / 1000
        posx = [c + db / 2000 + a * k / (nx_ - 1) for k in range(nx_)]; posy = [c + db / 2000 + a * k / (ny_ - 1) for k in range(ny_)]
        pos = posx
        pts = {(round(p, 4), round(q, 4)) for p in posx for q in (posy[0], posy[-1])} | {(round(q, 4), round(p, 4)) for p in posy for q in (posx[0], posx[-1])}
        for p, q in pts:
            sh.C("S-REBR", u + p, v + q, db / 2000, True)
        if nb == 18:   # 4 legs across the 6-bar faces (ties on bars 2 and 4 of 6), 3 legs across the 5-bar faces
            for p in (posx[2], posx[3]):
                sh.L("S-REBR-TIES", (u + p, v + 0.046), (u + p, v + b - 0.046))
            sh.L("S-REBR-TIES", (u + 0.046, v + posy[2]), (u + b - 0.046, v + posy[2]))
        else:
            mid = [pos[len(pos) // 2]] if hh["legs"] == 3 else pos[1:-1]
            for p in mid:
                sh.L("S-REBR-TIES", (u + p, v + 0.046), (u + p, v + b - 0.046)); sh.L("S-REBR-TIES", (u + 0.046, v + p), (u + b - 0.046, v + p))
        sh.T(f"{sec.split('/')[0]}  {hh['bars']}  hoops {hh['hoop']} ({hh['legs']} legs), mid {hh['hoop_mid']}" + ("  - C17 STORY1 ONLY (6 x 5)" if nb == 18 else ""), u, v - 0.1, T1)
        u += 4.0
    sh.notes(sh.x0 + 17.5, sh.y0 + 12.0, ["1. Hoops: closed, 135° seismic hooks, cross ties with 135° / 90° alternating hooks.",
                                          "2. lo >= max(h, Ln/6, 450) at both ends of each storey; hoop spacing of lo kept through the joints.",
                                          "3. Laps only in the middle half of the clear height, class B, hoops @ <= 100 over the lap.",
                                          "4. Bar change at +4.00 (16φ20 -> 16φ18) and +7.40 (50 -> 45, cranked 1 in 6).",
                                          "4a. C17 Story1 only (Rev6h): 18φ20 (6 x 5), hoops φ12@85 with 4 legs across the 6-bar faces; 18φ20 lap 1.20 into Story2 16φ18.",
                                          "5. Top of CT-2 at the roof and CT-1 at the stair-house roof: bars hooked 90° x 0.25 inward.",
                                          "6. Column bars into the footing: 90° bend 0.25 towards the column inside (boss)."], head="COLUMN NOTES")
    return sh


# ------------------------------------------------------------------ slabs
def slab_plan(doc, g, story, i, no):
    sh = Sheet(doc, i, no, f"پلان سقف و تیرچه ریزى {FA_TITLE[story]}", f"SLAB PLAN - JOISTS AND TIE BEAMS - {STORY[story][0]} (TOS {STORY[story][1]:+.2f})")
    du, dv = sh.x0 + 22.0, sh.y0 + 6.6
    E = lambda X, Y: (-Y + du, X + dv)
    for name, X in GRID_X:
        a, b = E(X, -1.0), E(X, 21.0); sh.L("S-GRID", a, b); sh.T(name, b[0] - 0.2, b[1], T3, layer="S-GRID-IDEN", align=TA.MIDDLE_CENTER)
    for name, Y in GRID_Y:
        a, b = E(-1.0, Y), E(8.2, Y); sh.L("S-GRID", a, b); sh.T(name, a[0], a[1] - 0.2, T3, layer="S-GRID-IDEN", align=TA.MIDDLE_CENTER)
    for f in g["frames"].values():
        if f["story"] != story:
            continue
        if f["kind"] == "column":
            b = int(f["sec"][1:3]) / 200.0
            pts = [E(f["xi"] - b, f["yi"] - b), E(f["xi"] + b, f["yi"] - b), E(f["xi"] + b, f["yi"] + b), E(f["xi"] - b, f["yi"] + b)]
            sh.P("S-COLS", pts); sh.hatch("S-COLS-PATT", pts)
        else:
            bw = int(f["sec"][2:4]) / 200.0
            dx, dy = f["xj"] - f["xi"], f["yj"] - f["yi"]; Lf = math.hypot(dx, dy); nx, ny = -dy / Lf, dx / Lf
            for sg in (-1, 1):
                sh.L("S-CONC", E(f["xi"] + sg * nx * bw, f["yi"] + sg * ny * bw), E(f["xj"] + sg * nx * bw, f["yj"] + sg * ny * bw))
            m = E((f["xi"] + f["xj"]) / 2, (f["yi"] + f["yj"]) / 2)
            sh.T(f"{f['label']} {f['sec'].replace('BW', '').replace('xH', 'x')}", m[0] + 0.05, m[1] + 0.05, T1)
    if story == "Story5":
        panels = [((0.20, 2.15), (7.70, 13.30), "X", "F17"), ((0.20, 2.30), (13.70, 18.61), "X", "F14'"), ((0.20, 2.30), (19.01, 19.81), "X", "F2'")]
        tbs = []
    else:
        panels = [((0.25, 2.10), (0.25, 7.25), "Y", "F1"), ((2.60, 6.90), (0.25, 7.25), "Y", "F4"), ((2.60, 6.90), (7.75, 13.25), "Y", "F12"),
                  ((2.75, 6.90), (13.75, 18.56), "Y", "F13"), ((0.25, 2.25), (15.45, 18.56), "Y", "F14"), ((0.25, 2.25), (19.06, 19.76), "X", "F2"),
                  ((2.75, 6.90), (19.06, 19.76), "X", "F3")]
        tbs = [(Y, 0.0, 7.15) for Y in (1.875, 3.75, 5.625)] + [(Y, 2.35, 7.15) for Y in (9.0, 10.5, 12.0)] + \
              [(14.8275, 2.35, 7.15), (16.155, 0.0, 7.15), (17.4825, 0.0, 7.15)]
    for (x0, x1), (y0, y1), d, tag in panels:
        if d == "Y":
            x = x0 + 0.25
            while x < x1:
                sh.L("S-SLAB", E(x, y0), E(x, y1)); x += 0.50
            c = E((x0 + x1) / 2, (y0 + y1) / 2)
            sh.T(f"{tag}: joists in Y @0.50, back to back over the beams", c[0], c[1] + 0.1, T1, align=TA.MIDDLE_CENTER)
        else:
            y = y0 + 0.2
            while y < y1:
                sh.L("S-SLAB", E(x0, y), E(x1, y)); y += 0.50
            c = E((x0 + x1) / 2, (y0 + y1) / 2)
            sh.T(f"{tag}: joists in X @0.50", c[0], c[1] + 0.1, T1, align=TA.MIDDLE_CENTER)
    for Y, xa, xb in tbs:
        for sg in (-1, 1):
            sh.L("S-SLAB", E(xa, Y + sg * 0.15), E(xb, Y + sg * 0.15))
        c = E(xb + 0.1, Y); sh.T("TB 30x30", c[0], c[1], T1, rot=90)
    if story != "Story5":
        for x0, x1, y0, y1, t in ((0.0, 2.35, 7.5, 13.5, "STAIR"), (0.0, 2.35, 13.5, 15.30, "ELEV. SHAFT")):
            pts = [E(x0, y0), E(x1, y0), E(x1, y1), E(x0, y1)]
            sh.P("S-SLAB-OPNG", pts); sh.L("S-SLAB-OPNG", pts[0], pts[2]); sh.L("S-SLAB-OPNG", pts[1], pts[3])
            c = E((x0 + x1) / 2, (y0 + y1) / 2); sh.T(t, c[0], c[1] + 0.3, T2, align=TA.MIDDLE_CENTER)
    else:
        for X, Y in ((0.30, 14.10), (0.30, 15.20)):
            c = E(X, Y); sh.C("S-SLAB-OPNG", c[0], c[1], 0.0625)
        c = E(0.30, 14.65); sh.T("2 sleeves φ125 (move to X 0.32, QUESTION)", c[0], c[1] + 0.3, T1)
    lines = ["1. Joist (tirche) slab h = 0.31: block 0.25 + topping 0.06; joists 0.10 wide @ 0.50 (ASSUMPTION as the model).",
             ("2. Joists in Y (the 7.5 m direction) in all bays, back to back over the beams on axes 1-4 (boss); cantilever panels F2 / F3 in X." if story != "Story5"
              else "2. Stair-house roof: all joists in X, span 2.3 (boss); no tie beams."),
             "3. Tie beams TB 30x30 hidden in the slab, continuous in X over the whole width, end hooks; 2φ14 top + 2φ14 bottom;" if story != "Story5" else "",
             "   3 closed hoops 20x20 φ10 (135°) in each 50 cm between two joists (boss). 3 per bay at L/4." if story != "Story5" else "",
             "4. Joist bars (per joist): bay 7.50 2φ16, bay 6.00 2φ14, bay 5.31 2φ12, cantilever / X panels 2φ10; top 1φ12 over the supports L/4.",
             "5. Topping: temperature mesh φ8@250 both ways (ASSUMPTION, QUESTION); slab-to-beam dowels φ10@200 (+25% connection force).",
             "6. Trimmer BT 30x50 at Y 15.30 (elevator opening, unavoidable for the Y joists); stair beam BS 30x50 at Y 11.66 (S3-ST)." if story != "Story5" else "6. Hook beam BH 25x40 (S3-B05)."]
    sh.notes(sh.x0 + 0.8, sh.y0 + 3.8, [s for s in lines if s], head="SLAB NOTES")
    return sh


def slab_details(doc, hc, i):
    sh = Sheet(doc, i, "S3-S06", "جزئیات سقف تیرچه بلوک و تای بیم", "SLAB DETAILS - JOIST, TIE BEAM 30x30, TOPPING")
    u, v = sh.x0 + 1.5, sh.y0 + 11.0
    # joist slab section across the joists (3 joists)
    sh.R("S-CONC", u, v + 0.25, 1.6, 0.06)
    for k in range(4):
        x = u + 0.05 + k * 0.50
        sh.R("S-CONC", x, v, 0.10, 0.25)
        sh.C("S-REBR", x + 0.03, v + 0.03, 0.008, True); sh.C("S-REBR", x + 0.07, v + 0.03, 0.008, True)
        if k < 3:
            sh.R("S-CONC-HIDN", x + 0.10, v, 0.40, 0.25)
    sh.L("S-REBR", (u + 0.02, v + 0.28), (u + 1.58, v + 0.28))
    sh.T("JOIST SLAB SECTION (across the joists) 1:20", u, v + 0.6, T3, layer="S-ANNO")
    sh.T("topping 0.06 with φ8@250 both ways; blocks 0.40 x 0.25; joists 0.10 @ 0.50; bottom bars per bay (S3-S01..S05)", u, v - 0.15, T1)
    sh.dim((u + 0.05, v), (u + 0.55, v), (0, v - 0.3), 0, txt="0.50")
    sh.dim((u + 1.6, v), (u + 1.6, v + 0.31), (u + 1.9, 0), 90, txt="0.31")
    # tie beam section
    u2 = sh.x0 + 6.0
    sh.R("S-CONC", u2, v, 0.30, 0.31); sh.R("S-REBR-TIES", u2 + 0.05, v + 0.055, 0.20, 0.20)
    for p in (u2 + 0.07, u2 + 0.23):
        sh.C("S-REBR", p, v + 0.075, 0.007, True); sh.C("S-REBR", p, v + 0.235, 0.007, True)
    sh.T("TIE BEAM TB 30x30 SECTION 1:20 (boss): 2φ14 top + 2φ14 bottom, closed hoops 20x20 φ10, 135° hooks", u2, v + 0.6, T3, layer="S-ANNO")
    # tie beam elevation over 2 joist spaces with 3 hoops each
    u3, v3 = sh.x0 + 1.5, sh.y0 + 8.0
    sh.R("S-CONC", u3, v3, 2.5, 0.31)
    for k in range(6):
        sh.R("S-CONC-HIDN", u3 + 0.05 + k * 0.5 - 0.05, v3, 0.10, 0.25) if k else None
    sh.L("S-REBR", (u3 - 0.4, v3 + 0.07), (u3 + 2.5, v3 + 0.07)); sh.L("S-REBR", (u3 - 0.4, v3 + 0.24), (u3 + 2.5, v3 + 0.24))
    sh.L("S-REBR", (u3 - 0.4, v3 + 0.07), (u3 - 0.4, v3 + 0.24))
    for k in range(5):
        x0 = u3 + k * 0.5 + 0.05
        for j in range(3):
            xx = x0 + 0.10 + j * 0.13
            sh.L("S-REBR-TIES", (xx, v3 + 0.055), (xx, v3 + 0.255))
    sh.R("S-CONC", u3 - 0.5, v3 - 0.19, 0.5, 0.5)
    sh.T("edge beam (end hook of the TB bars into the beam)", u3 - 0.5, v3 - 0.30, T1)
    sh.T("TIE BEAM ELEVATION 1:20: continuous in X over the whole width, end hooks; 3 hoops φ10 between each two joists (50 cm)", u3, v3 + 0.6, T3, layer="S-ANNO")
    jo = hc["joists"]
    rows = [f"bay {k} m: bottom {v_['bottom']} (As req {v_['As_req']}), top {v_['top_at_supports']}; deflection live {v_['delta_L_mm']} / L/360 {v_['L/360']}, "
            f"long-term {v_['delta_long_plus_L_mm']} / L/240 {v_['L/240']} mm" for k, v_ in jo.items()]
    sh.notes(sh.x0 + 1.5, sh.y0 + 6.5, rows + ["Joist deflection: simply supported, cracked T section (ACI 24.2), long-term factor 2.0 - the 7.5 m joist exceeds L/240 (QUESTION)."], head="JOIST SCHEDULE / CHECK")
    return sh


# ------------------------------------------------------------------ stairs
def stair_section(sh, u0, v0, Hs, ylanding, title, st):
    k = 1.0
    sh.R("S-COLS", u0 - 0.25, v0 - 0.5, 0.5, Hs + 0.5)                       # C2 / C6 (axis 2)
    sh.R("S-CONC", u0 + 6.0 - 0.25, v0 - 0.5, 0.5, 0.5); sh.R("S-CONC", u0 + 6.0 - 0.25, v0 + Hs - 0.5, 0.5, 0.5)     # B36 lower / upper
    ybs = 11.658 - 7.5
    sh.R("S-CONC", u0 + ybs - 0.15, v0 - 0.5, 0.30, 0.5); sh.R("S-CONC", u0 + ybs - 0.15, v0 + Hs - 0.5, 0.30, 0.5)        # BS lower / upper
    zl = ylanding
    sh.R("S-CONC", u0 + 0.29, v0 + zl - 0.40, 0.30, 0.40)                    # landing beam 30x40, gap 40
    sh.P("S-CONC", [(u0 + 0.25, v0 + zl - 0.45), (u0 + 0.55, v0 + zl - 0.45), (u0 + 0.55, v0 + zl - 0.70), (u0 + 0.25, v0 + zl - 0.90)], close=False)
    t = 0.20; yhl = 8.958 - 7.5
    # upper flight: landing (zl) -> upper floor at BS (Hs)
    sh.P("S-CONC", [(u0 + 0.59, v0 + zl), (u0 + yhl, v0 + zl), (u0 + ybs, v0 + Hs), (u0 + 6.0 - 0.25, v0 + Hs)], close=False)
    sh.P("S-CONC", [(u0 + 0.59, v0 + zl - t), (u0 + yhl, v0 + zl - t), (u0 + ybs, v0 + Hs - t)], close=False)
    sh.P("S-REBR", [(u0 + 0.62, v0 + zl - t + 0.03), (u0 + yhl, v0 + zl - t + 0.03), (u0 + ybs - 0.02, v0 + Hs - t + 0.03)], close=False)
    sh.L("S-REBR", (u0 + ybs + 0.18, v0 + Hs - t + 0.03), (u0 + 6.0 - 0.27, v0 + Hs - t + 0.03))
    # lower flight: lower floor at BS (0) -> landing
    sh.P("S-CONC-HIDN", [(u0 + yhl, v0 + zl), (u0 + ybs, v0), (u0 + 6.0 - 0.25, v0)], close=False)
    sh.R("S-REBR-TIES", u0 + 0.32, v0 + zl - 0.45, 0.15, 0.02)
    sh.R("S-REBR-TIES", u0 + ybs - 0.10, v0 + Hs - 0.5 + 0.5, 0.20, 0.02)
    sh.T("sliding seat PTFE + 70 mm gap", u0 + ybs - 0.6, v0 + Hs + 0.12, T1)
    sh.T("corbel 400x300x450 4φ14, PTFE 150x250, gap 40", u0 + 0.6, v0 + zl - 0.95, T1)
    sh.T(f"BS 30x50 (Y {11.658 if 'parking' not in title else 11.758}) 3φ16+3φ16", u0 + ybs - 0.6, v0 - 0.62, T1)
    sh.T("B36", u0 + 6.0 - 0.2, v0 - 0.62, T1)
    sh.T(f"waist / landing t = 0.20: bottom {st['bottom']}, dist. {st['distribution']}, top {st['top']}", u0, v0 + Hs + 0.55, T1)
    sh.dim((u0, v0 + Hs + 0.3), (u0 + ybs, v0 + Hs + 0.3), (0, v0 + Hs + 0.38), 0, txt=f"{ybs:.2f} (flight span)")
    sh.dim((u0 + ybs, v0 + Hs + 0.3), (u0 + 6.0, v0 + Hs + 0.3), (0, v0 + Hs + 0.38), 0, txt=f"{6.0 - ybs:.2f}")
    sh.dim((u0 - 0.6, v0), (u0 - 0.6, v0 + Hs), (u0 - 0.9, 0), 90, txt=f"{Hs:.2f}")
    sh.T(title, u0, v0 + Hs + 0.85, T3, layer="S-ANNO")


def stair_sheets(doc, hc, i):
    st = hc["stair_t200_with_BS"]
    sh = Sheet(doc, i, "S3-ST01", "جزئیات پله - همه ى طبقات", "STAIR SECTIONS - ALL STOREYS (t = 0.20, INTERMEDIATE SUPPORT BS)")
    specs = [("STAIR SECTION, PARKING -> FLOOR 1 (+0.00 -> +4.00, landing +2.09) 1:20", 4.00, 2.09), ("STAIR SECTION, FLOOR 1 -> 2 (+4.00 -> +7.40, landing +5.70) 1:20", 3.40, 1.70),
             ("STAIR SECTION, FLOOR 2 -> 3 (+7.40 -> +10.80, landing +9.10) 1:20", 3.40, 1.70), ("STAIR SECTION, FLOOR 3 -> ROOF (+10.80 -> +14.20, landing +12.50) 1:20", 3.40, 1.70)]
    for k, (t, Hs, zl) in enumerate(specs):
        u0 = sh.x0 + 1.5 + (k % 2) * 8.5; v0 = sh.y0 + (9.3 if k < 2 else 3.6)
        stair_section(sh, u0, v0, Hs, zl, t, st)
    sh.notes(sh.x0 + 17.5, sh.y0 + 13.5, [
        f"1. Waist / landing slab t = 0.20 (boss) with the intermediate support BS (boss).",
        f"2. Flight span {st['span1_m']} m: Mu {st['Mu1_kNm_m']} kN.m/m, As req {st['As_req']} -> bottom {st['bottom']}.",
        f"3. Deflection: live {st['delta_L_mm']} <= L/360 {st['L/360']}; long-term + live {st['delta_long_plus_L_mm']} mm > L/240 {st['L/240']} (report T55).",
        "4. Lower flight fixed on BS of the lower floor; upper flight SLIDING on BS of the upper floor (70 mm).",
        "5. Landing beam 30x40 on corbels of C2 / C6, sliding seat, 40 mm joint around the columns.",
        "6. The stair does not brace the frame (vertical load + corbel moment only in ETABS)."], head="STAIR NOTES")
    sh2 = Sheet(doc, i + 1, "S3-ST02", "جزئیات نشیمن لغزشی، تیر پاگرد و تیرهای BS و BT", "STAIR DETAILS - CORBEL SEAT, LANDING BEAM, BS, BT")
    cu, cv = sh2.x0 + 2.0, sh2.y0 + 9.0
    sh2.R("S-COLS", cu - 0.5, cv - 1.0, 0.5, 2.5)
    sh2.P("S-CONC", [(cu, cv + 0.45), (cu + 0.30, cv + 0.45), (cu + 0.30, cv + 0.20), (cu, cv)], close=False)
    sh2.R("S-CONC", cu + 0.04, cv + 0.47, 0.30, 0.40)
    sh2.R("S-REBR-TIES", cu + 0.05, cv + 0.45, 0.15, 0.02)
    sh2.P("S-REBR", [(cu - 0.40, cv + 0.10), (cu - 0.40, cv + 0.40), (cu + 0.26, cv + 0.40)], close=False)
    sh2.C("S-REBR", cu + 0.26, cv + 0.38, 0.007, True)
    for j in range(3):
        sh2.L("S-REBR-TIES", (cu - 0.40, cv + 0.33 - j * 0.07), (cu + 0.24, cv + 0.33 - j * 0.07))
    sh2.dim((cu, cv + 0.45), (cu + 0.30, cv + 0.45), (0, cv + 1.1), 0, txt="0.30")
    sh2.dim((cu + 0.30, cv), (cu + 0.30, cv + 0.45), (cu + 0.6, 0), 90, txt="0.45")
    sh2.dim((cu, cv + 0.67), (cu + 0.04, cv + 0.67), (0, cv + 0.95), 0, txt="0.04")
    sh2.T("CORBEL SEAT ON C2 / C6 1:20: 400 x 300 x 450, Asc 4φ14 with welded cross bar, 3 closed φ10 (Ah), PTFE pad 150x250x20, gap 40, guide pin φ16 in a slotted sleeve",
          cu - 0.5, cv + 1.6, T2, layer="S-ANNO")
    for k, (lab, b, h, top, bot, hp) in enumerate((("LANDING BEAM 30x40", 0.30, 0.40, 3, 3, "φ10@100"), ("STAIR BEAM BS 30x50", 0.30, 0.50, 3, 3, "φ10@200"),
                                                  ("TRIMMER BT 30x50 (elevator)", 0.30, 0.50, 3, 3, "φ10@200"))):
        u = sh2.x0 + 8.0 + k * 3.5; v = sh2.y0 + 9.0
        sh2.R("S-CONC", u, v, b, h); sh2.R("S-REBR-TIES", u + 0.046, v + 0.046, b - 0.092, h - 0.092)
        for j in range(top):
            sh2.C("S-REBR", u + 0.065 + (b - 0.13) * j / (top - 1), v + h - 0.065, 0.007 if k else 0.008, True)
            sh2.C("S-REBR", u + 0.065 + (b - 0.13) * j / (top - 1), v + 0.065, 0.007 if k else 0.008, True)
        sh2.T(f"{lab} 1:20: {top}φ{16 if k == 0 else 14} top + {bot}φ{16 if k == 0 else 14} bottom, closed {hp}; pinned ends (BS / BT)", u, v - 0.15, T1)
    u, v = sh2.x0 + 1.5, sh2.y0 + 4.5
    sh2.R("S-CONC", u, v, 0.30, 0.50); sh2.P("S-CONC", [(u + 0.30, v + 0.50), (u + 1.6, v + 0.50 + 0.0), (u + 1.6, v + 0.30)], close=False)
    sh2.R("S-REBR-TIES", u + 0.08, v + 0.50, 0.20, 0.02)
    sh2.T("SLIDING TOP OF THE UPPER FLIGHT ON BS 1:20: seat >= 220, PTFE on stainless, 70 mm movement joint, no bars across the joint", u, v + 1.0, T2, layer="S-ANNO")
    return [sh, sh2]


# ------------------------------------------------------------------ main
def acquire():
    for _ in range(120):
        if not os.path.exists(LOCK):
            with open(LOCK, "w", encoding="utf-8") as f:
                f.write(f"structural-engineer (task 50) {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            return
        print("AutoCAD lock present, waiting:", open(LOCK, encoding="utf-8").read().strip())
        time.sleep(10)
    raise SystemExit("AutoCAD lock not released")


def release():
    if os.path.exists(LOCK) and "structural-engineer" in open(LOCK, encoding="utf-8").read():
        os.remove(LOCK)


def main():
    g, des, D, hc = load()
    os.makedirs(TMP, exist_ok=True); os.makedirs(OUT_DIR, exist_ok=True)
    doc = ezdxf.new("R2018", setup=False)
    doc.units = ezdxf.units.M
    doc.header["$INSUNITS"] = 6; doc.header["$MEASUREMENT"] = 1; doc.header["$LTSCALE"] = 0.2; doc.header["$LWDISPLAY"] = 1
    doc.linetypes.add("CENTER", pattern=[0.56, 0.35, -0.08, 0.05, -0.08], description="Center")
    doc.linetypes.add("DASHED", pattern=[0.3, 0.2, -0.1], description="Dashed")
    for name, (c, lt, lw, desc) in LAYERS.items():
        lay = doc.layers.add(name, color=c, linetype=lt, lineweight=lw); lay.description = desc
    doc.styles.add("LATIN", font="arial.ttf"); doc.styles.add("FARSI", font="tahoma.ttf")
    ds = doc.dimstyles.add("S20"); ds.dxf.dimtxsty = "LATIN"
    for k, v in dict(dimtxt=0.05, dimasz=0.03, dimtsz=0.02, dimexo=0.015, dimexe=0.03, dimgap=0.015, dimdec=2, dimdsep=46, dimtad=1, dimtih=0, dimtoh=0,
                     dimzin=0, dimlunit=2, dimscale=1.0, dimtix=0, dimatfit=3, dimtmove=0).items():
        ds.set_dxf_attrib(k, v)
    sheets = []
    sheets.append(foundation_plan(doc, g, hc, 0)); sheets.append(foundation_details(doc, 1))
    sheets += beam_sheets(doc, g, D, 2)
    sheets.append(column_sheet(doc, des, 7))
    for k, story in enumerate(["Story1", "Story2", "Story3", "Story4", "Story5"]):
        sheets.append(slab_plan(doc, g, story, 8 + k, f"S3-S0{k + 1}"))
    sheets.append(slab_details(doc, hc, 13))
    sheets += stair_sheets(doc, hc, 14)
    dxf = os.path.join(TMP, "Merage3_struct_Rev5.dxf")
    doc.saveas(dxf)
    scr = os.path.join(TMP, "save_rev3.scr")
    with open(scr, "w", encoding="utf-8") as f:
        f.write(f'_.FILEDIA 0\n_.ZOOM _E\n_.SAVEAS 2018 "{OUT_DWG}"\n')
    if os.path.exists(OUT_DWG):
        os.makedirs(os.path.join(HERE, "_prev"), exist_ok=True)
        os.replace(OUT_DWG, os.path.join(HERE, "_prev", "Merage3_struct_Rev5_prev.dwg"))
    acquire()
    try:
        r = subprocess.run([ACCORE, "/i", dxf, "/s", scr, "/l", "en-US"], capture_output=True, timeout=600)
    finally:
        release()
    if not os.path.exists(OUT_DWG):
        print(r.stdout.decode("utf-16-le", errors="ignore")[-2000:]); raise SystemExit("DWG not written")
    print("DWG:", OUT_DWG, os.path.getsize(OUT_DWG))
    json.dump({s.no: [s.x0, s.y0, s.x0 + W, s.y0 + H] for s in sheets}, open(os.path.join(HERE, "rev3_sheets.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
