# -*- coding: utf-8 -*-
"""Merage3 - task 34 (2026-10-23): structural DRAFT drawings from the ETABS Rev5 model (after T32-33),
"typical for 3 storeys over parking", layered, thin line weights = architecture Rev.7 standard
(plot style arch/Zagros_ARCH_Rev7.ctb: object/layer line weights, all black, colour 9 grey).

Sheets (A3, 1:100 plans, model units = metres, same orientation as the architecture Rev.7 sheets:
DWG u = -Y + dx, v = X + dy, i.e. axis 1 at the right, axis A at the bottom):
  S-101  grid & column layout plan + column schedule + column sections 1:20
  S-102  typical floor framing plan, floors 1-3 (ETABS Story1-3)
  S-103  roof framing plan (Story4) + stair-house roof (Story5)
  S-104  beam schedule floors 1-3 (ACI 318-19 design, ETABS Rev5)
  S-105  beam schedule roof + stair-house roof, typical beam / cantilever details, general notes

Inputs (read only): ETABS/geom_after_T32-33.json, T34/t34_design.json (from t34_design.py).
The EDB is not opened. Project labels only (Label_project), never ETABS labels.

    python t34_design.py && python make_struct_T34.py && python plot_T34.py
"""
import json
import os
import re
import subprocess

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GEOM = os.path.join(PRJ, "ETABS", "geom_after_T32-33.json")
DES = os.path.join(HERE, "t34_design.json")
OUT_DIR = os.path.abspath(os.path.join(HERE, ".."))           # work/structural
OUT_DWG = os.path.join(OUT_DIR, "Merage3_struct_T34_draft.dwg")
TMP = "C:/ZagrosTemp/t34"
ACCORE = r"C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe"
REV = "T34 Draft A"
DATE = "1405/08/01"
SHEET_W, SHEET_H, PITCH = 42.0, 29.7, 45.0
SHEETS = ["S-101", "S-102", "S-103", "S-104", "S-105"]

# layer: (colour, linetype, lineweight 1/100 mm, description)  - weights per the arch Rev.7 standard
LAYERS = {
    "S-GRID": (5, "CENTER", 9, "Structural grid lines"),
    "S-GRID-IDEN": (2, "CONTINUOUS", 18, "Grid bubbles and labels"),
    "S-COLS": (3, "CONTINUOUS", 25, "Columns, outline (cut)"),
    "S-COLS-PATT": (8, "CONTINUOUS", 9, "Columns, solid fill"),
    "S-BEAM": (4, "CONTINUOUS", 18, "Beam edges (framing plan)"),
    "S-SLAB": (1, "CONTINUOUS", 13, "Slab: joist direction, slab edges"),
    "S-SLAB-OPNG": (1, "CONTINUOUS", 13, "Slab openings (stair, elevator)"),
    "S-DIMS": (1, "CONTINUOUS", 13, "Dimensions"),
    "S-ANNO": (2, "CONTINUOUS", 18, "Text: titles, notes, levels"),
    "S-ANNO-IDEN": (1, "CONTINUOUS", 13, "Member tags (beam / column labels, sections)"),
    "S-TABL": (1, "CONTINUOUS", 13, "Schedule table lines"),
    "S-CONC": (4, "CONTINUOUS", 18, "Concrete outline in details"),
    "S-REBR": (3, "CONTINUOUS", 25, "Reinforcement in details"),
    "S-ANNO-TTLB": (7, "CONTINUOUS", 18, "Title block and sheet trim"),
    "S-ANNO-BRDR": (6, "CONTINUOUS", 35, "Drawing border"),
}
GRID_X = [("A", 0.0), ("B", 2.35), ("B'", 2.50), ("C", 7.15)]
GRID_Y = [("1", 0.0), ("2", 7.50), ("3", 13.50), ("4", 18.81), ("5", 20.01)]
CANT = {"B3", "B5", "B6"}
LEVELS = [("Story1", "FLOOR 1", "طبقه ى اول", 3.50, 3.80), ("Story2", "FLOOR 2", "طبقه ى دوم", 6.40, 6.70),
          ("Story3", "FLOOR 3", "طبقه ى سوم", 9.30, 9.60), ("Story4", "ROOF", "بام", 12.20, 12.50),
          ("Story5", "STAIR-HOUSE ROOF", "بام خرپشته", 15.10, 15.40)]


def fa(text):
    text = text.replace("\u200c", " ")
    return re.sub("ی(?=[ؠ-يپ-ۓ])", "ي", text).replace("ی", "ى")


def phi(s):
    return s.replace("φ", "%%c")


class Sheet:
    def __init__(self, doc, i):
        self.doc, self.msp = doc, doc.modelspace()
        self.fx0, self.fy0 = i * PITCH, 0.0
        self.dx, self.dy = 0.0, 0.0

    # ETABS (X, Y) -> sheet
    def E(self, X, Y):
        return (-Y + self.dx, X + self.dy)

    def L(self, layer, p1, p2, **kw):
        return self.msp.add_line(p1, p2, dxfattribs={"layer": layer, **kw})

    def lineE(self, layer, X1, Y1, X2, Y2):
        return self.L(layer, self.E(X1, Y1), self.E(X2, Y2))

    def poly(self, layer, pts, close=True):
        return self.msp.add_lwpolyline(pts, close=close, dxfattribs={"layer": layer})

    def T(self, s, u, v, h, layer="S-ANNO", farsi=False, rot=0.0, align=TA.MIDDLE_CENTER, width=None):
        st = "FARSI" if farsi else "LATIN"
        t = self.msp.add_text(fa(s) if farsi else phi(s), height=h, rotation=rot,
                              dxfattribs={"layer": layer, "style": st, "width": width or (1.0 if farsi else 0.85)})
        t.set_placement((u, v), align=align)
        return t

    def dim(self, p1, p2, base, ang, txt=None):
        meas = abs(p2[0] - p1[0]) if ang == 0 else abs(p2[1] - p1[1])
        d = self.msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=ang, dimstyle="S100",
                                    text=txt or f"{meas:.2f}", dxfattribs={"layer": "S-DIMS"})
        d.render()

    def hatch_solid(self, layer, pts):
        h = self.msp.add_hatch(dxfattribs={"layer": layer})
        h.paths.add_polyline_path(pts, is_closed=True)


# ---------------------------------------------------------------- sheet furniture
def frame(sh, title_fa, title_en, sheet_no, source, tpos=(15.0, 2.0)):
    fx0, fy0 = sh.fx0, sh.fy0
    fx1, fy1 = fx0 + SHEET_W, fy0 + SHEET_H
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
            (f"مقیاس: 1:100     واحد: متر     تاریخ: {DATE}     شماره نقشه: {sheet_no}", 0.26, True),
            ("وضعیت: پیش نویس - برای اجرا نیست", 0.34, True),
            (source, 0.17, False)]
    rh = th / len(rows)
    for k, (s, hh, f) in enumerate(rows):
        yy = by1 - (k + 0.5) * rh
        if k:
            sh.L("S-ANNO-TTLB", (bx0, by1 - k * rh), (bx1, by1 - k * rh))
        sh.T(s, (bx0 + bx1) / 2, yy, hh, farsi=f, width=1.0 if f else 0.8)
    # big draft mark next to the title
    sh.T(title_fa + " - پیش نویس", fx0 + tpos[0], fy1 - tpos[1], 0.50, farsi=True)
    sh.T(title_en + "  -  DRAFT, NOT FOR CONSTRUCTION", fx0 + tpos[0], fy1 - tpos[1] - 0.75, 0.25 if tpos[0] < 20 else 0.17)
    return bx0, by1


def legend(sh, x0, y0, names):
    sh.T("LAYERS / PLOT LINE WEIGHTS (mm) - Zagros_ARCH_Rev7.ctb", x0, y0, 0.16, align=TA.MIDDLE_LEFT, width=0.8)
    y = y0 - 0.32
    for name in names:
        c, lt, lw, desc = LAYERS[name]
        sh.L(name, (x0, y), (x0 + 0.9, y))
        sh.T(name, x0 + 1.1, y, 0.12, align=TA.MIDDLE_LEFT, width=0.8)
        sh.T(f"{lw / 100:.2f}", x0 + 3.0, y, 0.12, align=TA.MIDDLE_LEFT, width=0.8)
        sh.T(desc, x0 + 3.6, y, 0.12, align=TA.MIDDLE_LEFT, width=0.8)
        y -= 0.24
    return y


def notes(sh, x0, y0, lines, h=0.15, step=0.27, head=None, width=0.8):
    y = y0
    if head:
        sh.T(head, x0, y, 0.18, align=TA.MIDDLE_LEFT, width=0.85)
        y -= step * 1.3
    for s in lines:
        sh.T(s, x0, y, h, align=TA.MIDDLE_LEFT, width=width)
        y -= step
    return y


# ---------------------------------------------------------------- plan pieces
def grids(sh, Xr=(0.0, 7.15), Yr=(0.0, 20.01), gx=GRID_X, gy=GRID_Y, dims=True):
    R = 0.40
    ext = 1.3
    for name, X in gx:
        if name == "B'":
            # B' (C19) runs from axis 3 to the rear; bubble at the rear (left) end, B bubble at the front
            u0, _ = sh.E(X, max(Yr[0], 13.5) - 0.8)
            u1, v = sh.E(X, Yr[1] + ext)
            if Yr[1] < 13.5:
                continue
            sh.L("S-GRID", (u0, v), (u1, v))
            sh.msp.add_circle((u1 - R, v), R, dxfattribs={"layer": "S-GRID-IDEN"})
            sh.T("B'", u1 - R, v, 0.30, layer="S-GRID-IDEN")
            continue
        u0, v = sh.E(X, Yr[0] - ext)
        u1, _ = sh.E(X, Yr[1] + ext)
        sh.L("S-GRID", (u0, v), (u1, v))
        sh.msp.add_circle((u0 + R, v), R, dxfattribs={"layer": "S-GRID-IDEN"})
        sh.T(name, u0 + R, v, 0.30, layer="S-GRID-IDEN")
    for name, Y in gy:
        u, v0 = sh.E(Xr[0] - ext, Y)
        _, v1 = sh.E(Xr[1] + 0.8, Y)
        sh.L("S-GRID", (u, v0), (u, v1))
        sh.msp.add_circle((u, v0 - R), R, dxfattribs={"layer": "S-GRID-IDEN"})
        sh.T(name, u, v0 - R, 0.30, layer="S-GRID-IDEN")
    if not dims:
        return
    # dimensions: along Y below the plan, along X at the front (right)
    vb = sh.E(Xr[0] - 0.75, 0)[1]
    ys = [Y for _, Y in gy]
    for a, b in zip(ys, ys[1:]):
        sh.dim(sh.E(Xr[0], a), sh.E(Xr[0], b), (0, vb), 0)
    if len(ys) > 2:
        sh.dim(sh.E(Xr[0], ys[0]), sh.E(Xr[0], ys[-1]), (0, vb - 0.45), 0)
    ub = sh.E(0, Yr[0] - 0.75)[0]
    xs = [X for n, X in gx if n != "B'"]
    for a, b in zip(xs, xs[1:]):
        sh.dim(sh.E(a, Yr[0]), sh.E(b, Yr[0]), (ub, 0), 90)
    if len(xs) > 2:
        sh.dim(sh.E(xs[0], Yr[0]), sh.E(xs[-1], Yr[0]), (ub + 0.45, 0), 90)
    if any(n == "B'" for n, _ in gx) and Yr[1] > 18:
        ul = sh.E(0, Yr[1] + 0.6)[0]
        sh.dim(sh.E(2.35, Yr[1]), sh.E(2.50, Yr[1]), (ul, 0), 90, txt="0.15")
        sh.T("B' = 2.50 (C19)", ul - 0.2, sh.E(2.50, 0)[1] - 0.9, 0.12, layer="S-GRID-IDEN", align=TA.MIDDLE_RIGHT)


def column(sh, X, Y, b, label=None, tag=None):
    r = b / 2
    pts = [sh.E(X - r, Y - r), sh.E(X + r, Y - r), sh.E(X + r, Y + r), sh.E(X - r, Y + r)]
    sh.poly("S-COLS", pts)
    sh.hatch_solid("S-COLS-PATT", pts)
    if label:
        u, v = sh.E(X + r, Y - r)           # upper-right corner on the sheet
        sh.T(label, u + 0.06, v + 0.06, 0.17, layer="S-ANNO-IDEN", align=TA.BOTTOM_LEFT)
        if tag:
            sh.T(tag, u + 0.06, v - 0.06, 0.11, layer="S-ANNO-IDEN", align=TA.TOP_LEFT)


def beams_plan(sh, beams, bw_draw, tags, cant_end=20.01, cut=0.25):
    """beam edges between faces; tags = {label: (line1, line2)}"""
    for b in beams:
        x1, y1, x2, y2 = b["xi"], b["yi"], b["xj"], b["yj"]
        Lb = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        ux, uy = (x2 - x1) / Lb, (y2 - y1) / Lb
        nx, ny = -uy, ux
        c1, c2 = cut, cut
        if b["label"] == "B2":
            c1, c2 = -cut, -cut                            # edge beam runs to the outer faces of B3 / B6
        if b["label"] in CANT:
            c2 = cut                                       # stops at the inner face of B2
        h = bw_draw / 2
        for sgn in (-1, 1):
            p = (x1 + ux * c1 + sgn * nx * h, y1 + uy * c1 + sgn * ny * h)
            q = (x2 - ux * c2 + sgn * nx * h, y2 - uy * c2 + sgn * ny * h)
            sh.lineE("S-BEAM", *p, *q)
        if b["label"] == "B2":                             # closing ends
            for xe, ye, s in ((x1 + ux * c1, y1 + uy * c1, 1), (x2 - ux * c2, y2 - uy * c2, 1)):
                sh.lineE("S-BEAM", xe + nx * h, ye + ny * h, xe - nx * h, ye - ny * h)
        # tag at mid-span, beside the beam, inside the bay where possible
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if b["label"] in CANT:
            my += 0.30
        t1, t2 = tags[b["label"]]
        horiz = abs(uy) > 0.5          # beam along Y -> horizontal on the sheet
        if horiz:
            side = 1 if mx < 7.0 else -1
            if b["label"] in CANT:
                side = 1 if mx < 7.0 else -1
            u, v = sh.E(mx + side * (h + 0.12), my)
            al1 = TA.BOTTOM_CENTER if side > 0 else TA.TOP_CENTER
            sh.T(t1, u, v if side > 0 else v, 0.17, layer="S-ANNO-IDEN", align=al1)
            sh.T(t2, u, v + (0.22 if side > 0 else -0.22), 0.12, layer="S-ANNO-IDEN", align=al1)
        else:
            side = -1 if my > 0.1 else 1
            if b["label"] == "B2":
                side = -1
            ub, vb = sh.E(mx, my)
            sg = 1 if b["label"] in ("B38", "B39", "B36") else -1      # -1: label left of the beam on the sheet (larger Y)
            sh.T(t1, ub + sg * (h + 0.15), vb, 0.17, layer="S-ANNO-IDEN", rot=90)
            sh.T(t2, ub + sg * (h + 0.37), vb, 0.12, layer="S-ANNO-IDEN", rot=90)


def joist(sh, X0, X1, Y, tag, h=0.25):
    """joist direction: line along X with ticks + panel tag"""
    sh.lineE("S-SLAB", X0, Y, X1, Y)
    for X in (X0, X1):
        sh.lineE("S-SLAB", X, Y - 0.12, X, Y + 0.12)
    for X, d in ((X0, 1), (X1, -1)):
        a = sh.E(X, Y)
        b = sh.E(X + d * 0.18, Y - 0.07)
        c = sh.E(X + d * 0.18, Y + 0.07)
        sh.poly("S-SLAB", [a, b, c])
    u, v = sh.E((X0 + X1) / 2, Y)
    sh.T(tag, u - 0.08, v, 0.14, layer="S-SLAB", rot=90, align=TA.BOTTOM_CENTER)


def opening(sh, x0, x1, y0, y1, txt):
    pts = [sh.E(x0, y0), sh.E(x1, y0), sh.E(x1, y1), sh.E(x0, y1)]
    sh.poly("S-SLAB-OPNG", pts)
    sh.L("S-SLAB-OPNG", pts[0], pts[2])
    sh.L("S-SLAB-OPNG", pts[1], pts[3])
    u, v = sh.E((x0 + x1) / 2, (y0 + y1) / 2)
    bg = sh.T(txt, u, v + 0.3, 0.14, layer="S-SLAB-OPNG")


def level_mark(sh, u, v, s, h=0.13):
    sh.poly("S-ANNO", [(u, v), (u - 0.09, v + 0.15), (u + 0.09, v + 0.15)])
    sh.L("S-ANNO", (u - 0.25, v), (u + 0.25, v))
    sh.T(s, u + 0.15, v + 0.22, h, align=TA.BOTTOM_LEFT)


# ---------------------------------------------------------------- tables
def table(sh, x0, y0, cols, rows, rh=0.355, th=0.15, head_h=0.75, groups=None):
    """cols = [(header, width)], rows = [[cells]] ; groups = row indices after which a heavier separation"""
    W = sum(w for _, w in cols)
    y = y0
    sh.poly("S-TABL", [(x0, y0), (x0 + W, y0), (x0 + W, y0 - head_h - rh * len(rows)), (x0, y0 - head_h - rh * len(rows))])
    x = x0
    for k, (hd, w) in enumerate(cols):
        lines = hd.split("\n")
        for j, s in enumerate(lines):
            sh.T(s, x + w / 2, y0 - head_h / 2 + (len(lines) - 1) * 0.11 - j * 0.22, 0.14, layer="S-ANNO", width=0.75)
        if k:
            sh.L("S-TABL", (x, y0), (x, y0 - head_h - rh * len(rows)))
        x += w
    y = y0 - head_h
    sh.L("S-TABL", (x0, y), (x0 + W, y))
    for i, r in enumerate(rows):
        x = x0
        for (hd, w), c in zip(cols, r):
            sh.T(str(c), x + w / 2, y - rh / 2, th, layer="S-ANNO-IDEN", width=0.75)
            x += w
        y -= rh
        if i < len(rows) - 1:
            sh.L("S-TABL", (x0 if (groups and i in groups) else x0 + cols[0][1], y), (x0 + W, y))
    return y


# ---------------------------------------------------------------- details
def col_section(sh, cu, cv, b, nside, hoop_txt, title, legs):
    S = 5.0                                     # 1:20 on a 1:100 sheet
    B = b * S
    c = (0.040 + 0.012) * S                     # cover + hoop
    sh.poly("S-CONC", [(cu - B / 2, cv - B / 2), (cu + B / 2, cv - B / 2), (cu + B / 2, cv + B / 2), (cu - B / 2, cv + B / 2)])
    hi = B / 2 - 0.040 * S - 0.006 * S
    sh.poly("S-REBR", [(cu - hi, cv - hi), (cu + hi, cv - hi), (cu + hi, cv + hi), (cu - hi, cv + hi)])
    # 135 deg hook marks at one corner
    sh.L("S-REBR", (cu - hi, cv + hi), (cu - hi + 0.35, cv + hi - 0.35))
    sh.L("S-REBR", (cu - hi + 0.02, cv + hi - 0.02 + 0.0), (cu - hi + 0.33, cv + hi - 0.02 - 0.31 + 0.0))
    r = 0.008 * S
    a = B / 2 - c - r
    pos = [-a + 2 * a * k / (nside - 1) for k in range(nside)]
    bars = set()
    for p in pos:
        for q in (-a, a):
            bars.add((round(p, 4), round(q, 4)))
            bars.add((round(q, 4), round(p, 4)))
    for p, q in bars:
        sh.msp.add_circle((cu + p, cv + q), r, dxfattribs={"layer": "S-REBR"})
        h = sh.msp.add_hatch(dxfattribs={"layer": "S-REBR"})
        h.paths.add_edge_path().add_arc((cu + p, cv + q), r, 0, 360)
    # cross ties through the middle bars (legs - 2 per direction)
    inner = [p for p in pos[1:-1]]
    if legs == 3:
        inner = [pos[len(pos) // 2]]
    for p in inner:
        sh.L("S-REBR", (cu + p, cv - hi), (cu + p, cv + hi))
        sh.L("S-REBR", (cu - hi, cv + p), (cu + hi, cv + p))
    sh.dim((cu - B / 2, cv + B / 2), (cu + B / 2, cv + B / 2), (cu, cv + B / 2 + 0.35), 0, txt=f"{b * 100:.0f}")
    sh.dim((cu + B / 2, cv - B / 2), (cu + B / 2, cv + B / 2), (cu + B / 2 + 0.35, cv), 90, txt=f"{b * 100:.0f}")
    sh.T(title, cu, cv - B / 2 - 0.35, 0.16, layer="S-ANNO")
    sh.T(f"{nside * 4 - 4}φ16  -  hoops {hoop_txt}", cu, cv - B / 2 - 0.70, 0.14, layer="S-ANNO-IDEN")
    sh.T(f"{legs} legs each way, 135° hooks  -  SC 1:20", cu, cv - B / 2 - 0.95, 0.12, layer="S-ANNO-IDEN")


def beam_section(sh, cu, cv, bw, top, bot, side, hoop_txt, title, sub):
    S = 5.0
    B, H = bw * S, 0.50 * S
    sh.poly("S-CONC", [(cu - B / 2, cv - H / 2), (cu + B / 2, cv - H / 2), (cu + B / 2, cv + H / 2), (cu - B / 2, cv + H / 2)])
    # slab line (joist slab top) on both sides, indicative
    sh.L("S-CONC", (cu - B / 2 - 0.8, cv + H / 2), (cu - B / 2, cv + H / 2))
    sh.L("S-CONC", (cu + B / 2, cv + H / 2), (cu + B / 2 + 0.8, cv + H / 2))
    hi_u, hi_v = B / 2 - 0.046 * S, H / 2 - 0.046 * S
    sh.poly("S-REBR", [(cu - hi_u, cv - hi_v), (cu + hi_u, cv - hi_v), (cu + hi_u, cv + hi_v), (cu - hi_u, cv + hi_v)])
    sh.L("S-REBR", (cu - hi_u, cv + hi_v), (cu - hi_u + 0.35, cv + hi_v - 0.35))

    def row(n, d, vv):
        r = d / 2000 * S
        a = hi_u - 0.006 * S - r
        for k in range(n):
            p = -a + 2 * a * k / (n - 1)
            sh.msp.add_circle((cu + p, vv), r, dxfattribs={"layer": "S-REBR"})
            h = sh.msp.add_hatch(dxfattribs={"layer": "S-REBR"})
            h.paths.add_edge_path().add_arc((cu + p, vv), r, 0, 360)
    nt, dt = top
    nb, db = bot
    row(nt, dt, cv + hi_v - 0.006 * S - dt / 2000 * S)
    row(nb, db, cv - hi_v + 0.006 * S + db / 2000 * S)
    if side:
        ns, ds = side
        r = ds / 2000 * S
        a = hi_u - 0.006 * S - r
        for k in range(ns):
            vv = cv - hi_v + 2 * hi_v * (k + 1) / (ns + 1)
            for p in (-a, a):
                sh.msp.add_circle((cu + p, vv), r, dxfattribs={"layer": "S-REBR"})
    sh.dim((cu - B / 2, cv - H / 2), (cu + B / 2, cv - H / 2), (cu, cv - H / 2 - 0.35), 0, txt=f"{bw * 100:.0f}")
    sh.dim((cu + B / 2, cv - H / 2), (cu + B / 2, cv + H / 2), (cu + B / 2 + 0.35, cv), 90, txt="50")
    sh.T(title, cu, cv - H / 2 - 0.80, 0.20)
    for k, s in enumerate(sub):
        sh.T(s, cu, cv - H / 2 - 1.10 - k * 0.24, 0.12, layer="S-ANNO-IDEN")


def beam_elevation(sh, u0, v0):
    """typical SMF beam elevation, schematic, ~1:50 (factor 2)."""
    S = 2.0
    Ln = 5.0
    cw = 0.5
    H = 0.5
    # columns
    for uc in (u0, u0 + (cw + Ln) * S):
        sh.poly("S-CONC", [(uc, v0 - 0.6), (uc + cw * S, v0 - 0.6), (uc + cw * S, v0 + H * S + 0.6), (uc, v0 + H * S + 0.6)])
    ua, ub = u0 + cw * S, u0 + (cw + Ln) * S
    sh.L("S-CONC", (ua, v0), (ub, v0))
    sh.L("S-CONC", (ua, v0 + H * S), (ub, v0 + H * S))
    c = 0.05 * S
    # continuous bars (hooked into the exterior columns)
    for vv in (v0 + H * S - c, v0 + c):
        sh.L("S-REBR", (u0 + 0.08 * S, vv), (ub + (cw - 0.08) * S, vv))
        for ue, d in ((u0 + 0.08 * S, 1), (ub + (cw - 0.08) * S, -1)):
            sh.L("S-REBR", (ue, vv), (ue, vv + (-0.3 if vv > v0 + 0.3 else 0.3)))
    # extra top bars Ln/3
    vt = v0 + H * S - c - 0.07
    sh.L("S-REBR", (u0 + 0.12 * S, vt), (ua + Ln / 3 * S, vt))
    sh.L("S-REBR", (ub - Ln / 3 * S, vt), (ub + (cw - 0.12) * S, vt))
    # hoops: 2h zones dense, middle wider
    z = 2 * H * S
    u = ua + 0.05 * S
    while u <= ua + z + 1e-6:
        sh.L("S-REBR", (u, v0 + c), (u, v0 + H * S - c))
        u += 0.09 * S * 1.6
    u = ub - 0.05 * S
    while u >= ub - z - 1e-6:
        sh.L("S-REBR", (u, v0 + c), (u, v0 + H * S - c))
        u -= 0.09 * S * 1.6
    u = ua + z + 0.2 * S
    while u < ub - z - 0.1:
        sh.L("S-REBR", (u, v0 + c), (u, v0 + H * S - c))
        u += 0.20 * S
    # dims / labels
    yb = v0 - 0.9
    sh.dim((ua, v0), (ua + z, v0), (0, yb), 0, txt="2h = 100")
    sh.dim((ub - z, v0), (ub, v0), (0, yb), 0, txt="2h = 100")
    sh.dim((ua + z, v0), (ub - z, v0), (0, yb), 0, txt="middle zone")
    sh.dim((ua, v0 + H * S), (ua + Ln / 3 * S, v0 + H * S), (0, v0 + H * S + 0.9), 0, txt="Ln/3 (min)")
    sh.dim((ub - Ln / 3 * S, v0 + H * S), (ub, v0 + H * S), (0, v0 + H * S + 0.9), 0, txt="Ln/3 (min)")
    sh.T("hoops 'Hoops 2h' of the schedule, first hoop <= 50 mm from the column face", (ua + ua + z) / 2 + 0.4, yb - 0.45, 0.12, layer="S-ANNO-IDEN")
    sh.T("hoops 'Hoops mid' (s <= d/2); lap splices only here, hoops at <= 100 over the lap", (ub + ua) / 2, yb - 0.75, 0.12, layer="S-ANNO-IDEN")
    sh.T("continuous 4φ16 top + 4φ16 bottom (+ extra bottom of the schedule, full length), 90° hooks in exterior columns (ldh)",
         (ua + ub) / 2, v0 + H * S + 1.45, 0.12, layer="S-ANNO-IDEN")
    sh.T("TYPICAL SMF BEAM - ELEVATION (schematic, ~1:50)", (ua + ub) / 2, v0 + H * S + 1.85, 0.20)
    sh.T("ستون", u0 + cw * S / 2, v0 - 0.85, 0.14, farsi=True)


# ---------------------------------------------------------------- sheets
def plan_frame_common(sh, geom, story, beams, bw_draw, col_b, des):
    for b in beams:
        pass
    cols = {}
    for f in geom["frames"].values():
        if f["kind"] == "column" and f["story"] == story:
            cols[f["label"]] = (f["xi"], f["yi"], f["sec"])
    return cols


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
        tag = "CT-1" if "Story5" in st else "CT-2"
        column(sh, X, Y, 0.50, lab, tag)
    # stair-house columns marker
    sh.T("CT-1 = continues to the stair-house roof (C2, C6, C16, C18);  CT-2 = up to the roof", sh.fx0 + 18.5, sh.fy0 + 16.0, 0.15)
    sh.T("GRID & COLUMN LAYOUT PLAN 1:100 (columns drawn 50x50 = ground storey size)", sh.fx0 + 18.5, sh.fy0 + 15.6, 0.16)
    bx0, by1 = frame(sh, "پلان آکس بندی و ستون گذاری و جدول ستون ها", "S-101 GRID & COLUMN LAYOUT + COLUMN SCHEDULE", "S-101",
                     "Source: ETABS Merage3_Rev5.EDB (T32-33), ACI 318-19, 51 A22 combos - read only")
    # column schedule
    h = des["column_hoops"]
    pm = {}
    for c in des["columns"]:
        k = c["story"]
        if c["pmm"] > pm.get(k, (0, ""))[0]:
            pm[k] = (c["pmm"], c["label"])
    rows = []
    spec = [("Story5", "stair house", "+12.20 .. +15.10", "C2 C6 C16 C18", 400),
            ("Story4", "floor 3 storey", "+9.30 .. +12.20", "all 12", 450),
            ("Story3", "floor 2 storey", "+6.40 .. +9.30", "all 12", 450),
            ("Story2", "floor 1 storey", "+3.50 .. +6.40", "all 12", 500),
            ("Story1", "ground / parking", "+-0.00 .. +3.50", "all 12", 500)]
    for st, nm, lv, which, b in spec:
        hh = h[str(b)]
        rows.append([nm, st, lv, which, f"{b // 10}x{b // 10}", f"{hh['bars']} (ρ={hh['rho']}%)",
                     f"{hh['hoop']}, {hh['legs']} legs", f"{hh['Ash_s_req']:.2f} / {hh['Ash_s_prov']:.2f}", f"{pm[st][0]:.3f} ({pm[st][1]})"])
    cols_t = [("storey", 2.4), ("ETABS\nstory", 1.5), ("FFL range", 2.6), ("columns", 2.3), ("b x h\n(cm)", 1.4),
              ("longitudinal", 3.2), ("hoops: lo, joint\nand full height", 3.2), ("Ash/s req/prov\n(mm²/mm)", 2.4), ("max PMM\n(column)", 2.2)]
    sh.T("COLUMN SCHEDULE  /  جدول ستون ها", sh.fx0 + 1.6, sh.fy0 + 14.9, 0.22, align=TA.MIDDLE_LEFT)
    table(sh, sh.fx0 + 1.6, sh.fy0 + 14.5, cols_t, rows, rh=0.42, th=0.15)
    notes(sh, sh.fx0 + 1.6, sh.fy0 + 10.6, [
        "1. Concrete f'c = 25 MPa; longitudinal S400 (fy 400); hoops S340 (fyt 340); clear cover 40 mm (ACI 318-19 20.5.1.3).",
        "2. Longitudinal bars as in the ETABS model (check mode, max PMM 0.926 C1 ground storey). ρ between 1% and 6% (18.7.4.1).",
        "3. Hoops: Ash/s per 18.7.5.4 (fyt 340); s <= min(b/4, 6db = 96, so) (18.7.5.3); the same spacing is kept over the full height",
        "   (outside lo, 18.7.5.5 also limits s to 6db = 96 mm) and through the beam-column joints (18.8.3.1).",
        "4. lo = 500 mm >= max(h, Ln/6, 450) at both ends of every storey (18.7.5.1). Column shear demand max 2.51 mm²/mm (C20 roof storey) < 3.99.",
        "5. Lap splices of column bars only in the middle half of the clear height, class B, 80 cm for φ16 (18.7.4.3, 25.5.2), hoops @ <= 100.",
        "6. Beam-column strong-column check: 5 roof joints exceed 1.0 but are exempt (ACI 18.7.3.1, Pu <= Ag f'c/10; boss 2026-10-19).",
        "7. Grid B' = 2.50 and C19 on it: approved by the boss 2026-10-23. Columns centred on the grid points (no eccentricity).",
        "8. Column sizes change at Story2 -> Story3 (50 -> 45, concentric) and Story4 -> Story5 (45 -> 40): bend bars 1:6 or add dowels.",
        "9. Foundation / pedestal / starter bars: by SAFE (pending, coordination 56)."], h=0.14, step=0.27, head="COLUMN NOTES")
    # sections 1:20
    for (cu, b, n, legs, hp, tt) in ((sh.fx0 + 32.0, 0.50, 5, 3, h["500"]["hoop"], "C50 - ground & floor-1 storeys"),
                                    (sh.fx0 + 35.6, 0.45, 5, 3, h["450"]["hoop"], "C45 - floor-2 & floor-3 storeys"),
                                    (sh.fx0 + 39.0, 0.40, 4, 4, h["400"]["hoop"], "C40 - stair house")):
        col_section(sh, cu, sh.fy0 + 23.8, b, n, hp, tt, legs)
    legend(sh, sh.fx0 + 30.5, sh.fy0 + 19.2, ["S-GRID", "S-GRID-IDEN", "S-COLS", "S-COLS-PATT", "S-CONC", "S-REBR", "S-DIMS",
                                              "S-ANNO", "S-ANNO-IDEN", "S-TABL", "S-ANNO-TTLB", "S-ANNO-BRDR"])


def framing_sheet(doc, geom, des, i, stories, sheet_no, title_fa, title_en, note_lines, roof=False):
    sh = Sheet(doc, i)
    sh.dx, sh.dy = sh.fx0 + 28.5, sh.fy0 + 18.6
    st0 = stories[0]
    grids(sh)
    bms = [f for f in geom["frames"].values() if f["kind"] == "beam" and f["story"] == st0]
    D = {(r["label"], r["story"]): r for r in des["beams"]}
    tags = {}
    for b in bms:
        secs = sorted({D[(b["label"], s)]["sec"] for s in stories}, key=lambda s: stories.index(next(st for st in stories if D[(b["label"], st)]["sec"] == s)))
        t2 = " / ".join(s.replace("BW", "").replace("xH", "x") for s in secs)
        tags[b["label"]] = (b["label"], "cant." if b["label"] in CANT else t2)
    beams_plan(sh, bms, 0.50, tags)
    for f in geom["frames"].values():
        if f["kind"] == "column" and f["story"] == st0:
            column(sh, f["xi"], f["yi"], 0.50, f["label"])
    # slabs
    for X0, X1, Y, tg in ((0.25, 2.10, 3.0, "F1"), (2.60, 6.90, 4.4, "F4"), (2.60, 6.90, 11.6, "F12"), (2.75, 6.90, 16.9, "F13"),
                          (0.25, 2.20, 17.0, "F14"), (0.25, 2.25, 19.08, "F2"), (2.75, 6.90, 19.08, "F3")):
        joist(sh, X0, X1, Y, tg)
    opening(sh, 0.25, 2.10, 7.75, 13.25, "STAIR (opening)" if not roof else "STAIR -> stair house")
    opening(sh, 0.25, 2.10, 13.75, 15.30, "ELEV.")
    u, v = sh.E(7.65, 21.3)
    for k, s in enumerate(stories):
        lv = next(l for l in LEVELS if l[0] == s)
        level_mark(sh, sh.fx0 + 2.4, sh.fy0 + 27.4 - 0.45 * k, f"{lv[1]}: FFL {lv[3]:+.2f}  (ETABS {s} = {lv[4]:.2f})")
    bx0, by1 = frame(sh, title_fa, title_en, sheet_no, "Source: ETABS Merage3_Rev5.EDB (T32-33), ACI 318-19, 51 A22 combos - read only")
    notes(sh, sh.fx0 + 1.6, sh.fy0 + 14.9, note_lines, h=0.14, step=0.27, head="NOTES")
    legend(sh, sh.fx0 + 30.5, sh.fy0 + 15.6, ["S-GRID", "S-GRID-IDEN", "S-COLS", "S-COLS-PATT", "S-BEAM", "S-SLAB", "S-SLAB-OPNG",
                                              "S-DIMS", "S-ANNO", "S-ANNO-IDEN", "S-ANNO-TTLB", "S-ANNO-BRDR"])
    return sh


def stairhouse(sh, geom, des):
    """Story5 plan, A-B / 2-3, placed lower-left of S-103"""
    sh.dx, sh.dy = sh.fx0 + 17.6, sh.fy0 + 3.2
    grids(sh, Xr=(0.0, 2.35), Yr=(7.5, 13.5), gx=[("A", 0.0), ("B", 2.35)], gy=[("2", 7.5), ("3", 13.5)])
    bms = [f for f in geom["frames"].values() if f["kind"] == "beam" and f["story"] == "Story5"]
    tags = {b["label"]: (b["label"], "40x50") for b in bms}
    beams_plan(sh, bms, 0.40, tags, cut=0.20)
    for f in geom["frames"].values():
        if f["kind"] == "column" and f["story"] == "Story5":
            column(sh, f["xi"], f["yi"], 0.40, f["label"])
    joist(sh, 0.20, 2.15, 9.2, "F17")
    u, v = sh.E(1.2, 10.5)
    sh.T("STAIR-HOUSE ROOF (Story5, FFL +15.10)  -  1:100", sh.E(0, 10.5)[0], sh.E(3.9, 0)[1], 0.18)
    sh.T("پلان تیر ریزى بام خرپشته", sh.E(0, 10.5)[0], sh.E(4.4, 0)[1], 0.26, farsi=True)


def schedule_sheet(doc, des, i, stories, sheet_no, title_fa, title_en, extra=None):
    sh = Sheet(doc, i)
    D = [r for r in des["beams"] if r["story"] in stories]
    order = {lab: k for k, lab in enumerate(["B1", "B30", "B31", "B3", "B4", "B32", "B33", "B5", "B7", "B34", "B35", "B6",
                                             "B10", "B11", "B12", "B13", "B36", "B37", "B38", "B39", "B2"])}
    D.sort(key=lambda r: (order[r["label"]], stories.index(r["story"])))
    floor = {"Story1": "F1 (Story1)", "Story2": "F2 (Story2)", "Story3": "F3 (Story3)", "Story4": "Roof (Story4)", "Story5": "St.house (Story5)"}
    rows, groups = [], []
    for k, r in enumerate(D):
        sec = r["sec"].replace("BW", "").replace("xH", "x")
        if r["label"] in CANT:
            dem = f"As {r['AsTop_req']}/{r['AsBot_req']}, Al {r['Al_req']}; q {r['q_h']:.2f}"
        else:
            dem = f"{r['AsTopI_gov']} / {r['AsTopJ_gov']} / {r['AsBot_req']}" + (f"; Al {r['Al_req']}" if r["Al_req"] else "") + \
                  f"; q {r['q_h']:.2f}" + (f"/{r['q_m']:.2f}" if r["q_m"] is not None else "")
        rows.append([r["label"] if (k == 0 or D[k - 1]["label"] != r["label"]) else "", floor[r["story"]], sec, f"{r['L']:.2f}",
                     r["topI"], r["topJ"], r["bot"], r["web"] or "-", r["hoop_h"], r["hoop_m"], dem])
        if k < len(D) - 1 and D[k + 1]["label"] != r["label"]:
            groups.append(k)
    cols_t = [("beam", 1.1), ("floor", 2.0), ("b x h\n(cm)", 1.2), ("L c/c\n(m)", 1.0), ("TOP end I\n(face, Ln/3)", 2.3),
              ("TOP end J\n(face, Ln/3)", 2.3), ("BOTTOM\n(full length)", 2.3), ("web\n(torsion)", 1.4),
              ("hoops 2h\n(2-leg closed)", 1.8), ("hoops mid", 1.9), ("ETABS demand: As top I/J/bot (mm²);\nAl (mm²); q=Av/s+2At/s 2h/mid", 5.2)]
    title_y = sh.fy0 + 28.3
    sh.T(f"BEAM SCHEDULE  -  {title_en.split(' - ', 1)[-1]}", sh.fx0 + 1.6, title_y, 0.22, align=TA.MIDDLE_LEFT)
    yend = table(sh, sh.fx0 + 1.6, title_y - 0.35, cols_t, rows, rh=0.31 if len(rows) > 40 else 0.36, th=0.13, head_h=0.72, groups=groups)
    bx0, by1 = frame(sh, title_fa, title_en, sheet_no, "Source: ETABS Rev5 Concrete Frame Design (ACI 318-19), Merage3_Rev5_results.xlsx",
                     tpos=(33.3, 1.8))
    if extra:
        extra(sh, yend)
    return sh


SCHED_NOTES = [
    "1. Labels = project labels (Label_project), as on S-102 / S-103. End I = end toward axis A or axis 1 (cantilevers: end I at axis 4).",
    "2. Continuous 4φ16 top and 4φ16 bottom in every beam (>= As,min = 1.4/fy bw d, 9.6.1.2; 2 bars continuous, 18.6.3.1).",
    "3. TOP end I / J = continuous + extra bars; extra bars from the column face to Ln/3 (and >= Ln/4 + d), anchored through the joint.",
    "   At a column the larger requirement of the two collinear beams governs and the bars pass through (already unified in the table).",
    "4. BOTTOM = continuous + extra, full length, anchored in the columns; checks bottom >= 1/2 top at the face and >= 1/4 max (18.6.3.2).",
    "5. web (torsion) = longitudinal torsion bars Al/3 at mid-depth on each face (EF), anchored at the supports (9.5.4.3, 9.7.5).",
    "6. Hoops: closed, 135° seismic hooks, first hoop <= 50 mm from the face; 2h = 1.00 m zone: s <= min(d/4, 6db, 150) = 90 (18.6.4.4);",
    "   middle zone s <= d/2 (18.6.4.6). q = Av/s + 2At/s from ETABS (mm²/mm); capacity 2-leg φ10@90 = 1.75, φ12@90 = 2.51.",
    "7. B12 floor 1 (Story1): hoops φ12@65 (q 3.28, T32 / boss), Al 743 -> 1φ14 EF. Cantilevers B3/B5/B6: 3φ25 top + 3φ25 bottom,",
    "   2φ16 EF, closed φ12@80 full length (boss decision, task 13); cantilever top bars continue into the back span >= ld beyond Ln/3.",
    "8. No lap splice within joints, within 2h of the faces, or where yielding is expected (18.6.3.3). Lap = class B, hoops @ <= 100.",
    "9. Status: all beams OK in ETABS (no D/C > 1.0, no warnings). Bar choice = engineer's draft; to be confirmed by the boss.",
]


def s104_extra(sh, yend):
    notes(sh, sh.fx0 + 25.2, sh.fy0 + 25.6, [s for s in SCHED_NOTES], h=0.115, step=0.235, head="SCHEDULE NOTES", width=0.68)


def s105_extra(sh, yend):
    beam_elevation(sh, sh.fx0 + 1.8, sh.fy0 + 12.4)
    beam_section(sh, sh.fx0 + 17.0, sh.fy0 + 13.6, 0.50, (6, 18), (4, 16), (1, 14), "",
                 "TYPICAL SECTION AT SUPPORT 1:20", ["e.g. B12 floor 1: 4φ16+2φ18 top, 4φ16+2φ16 bottom,", "1φ14 EF, closed φ12@65 (2h zones meet)"])
    beam_section(sh, sh.fx0 + 23.5, sh.fy0 + 13.6, 0.50, (3, 25), (3, 25), (2, 16), "",
                 "CANTILEVER B3 / B5 / B6 1:20", ["3φ25 top + 3φ25 bottom + 2φ16 EF", "closed φ12@80 full length (boss)"])
    notes(sh, sh.fx0 + 1.6, sh.fy0 + 8.4, SCHED_NOTES, h=0.115, step=0.225, head="SCHEDULE / DETAIL NOTES (same as S-104)", width=0.72)
    notes(sh, sh.fx0 + 27.4, sh.fy0 + 18.2, [
        "G1. Codes: ACI 318-19 (ch. 18, special moment frame), loads ASCE 7-22,",
        "    seismic Standard 2800 4th ed.; design by ETABS 19, 51 A22 combos.",
        "G2. Concrete C25 (f'c 25 MPa); bars S400 long., S340 hoops/ties.",
        "G3. Clear cover: beams and columns 40 mm; joist slab per slab detail.",
        "G4. Hooks 90° for longitudinal bars in exterior joints: ldh per 18.8.5",
        "    (φ16: 240, φ18: 270, φ20: 300 mm min, inside the confined core).",
        "G5. Infill walls separated from columns (gap 40 mm, T32: 45 proposed).",
        "G6. Joist (tirche) slabs: joists span in X (A-B, B-C), see S-102.",
        "G7. Drawing units: metres (dimensions), centimetres (sections),",
        "    bars in mm. All sheets DRAFT - not for construction.",
    ], h=0.13, step=0.25, head="GENERAL NOTES")


def main():
    os.makedirs(TMP, exist_ok=True)
    geom = json.load(open(GEOM, encoding="utf-8"))
    des = json.load(open(DES, encoding="utf-8"))
    doc = ezdxf.new("R2018", setup=False)
    doc.units = ezdxf.units.M
    doc.header["$INSUNITS"] = 6
    doc.header["$MEASUREMENT"] = 1
    doc.header["$LTSCALE"] = 1.0
    doc.header["$LWDISPLAY"] = 1
    doc.linetypes.add("CENTER", pattern=[0.56, 0.35, -0.08, 0.05, -0.08], description="Center ____ _ ____")
    for name, (c, lt, lw, desc) in LAYERS.items():
        lay = doc.layers.add(name, color=c, linetype=lt, lineweight=lw)
        lay.description = desc
    doc.layers.get("0").dxf.lineweight = 13
    doc.styles.add("LATIN", font="arial.ttf")
    doc.styles.add("FARSI", font="tahoma.ttf")
    ds = doc.dimstyles.add("S100")
    ds.dxf.dimtxsty = "LATIN"
    for k, v in dict(dimtxt=0.16, dimasz=0.09, dimtsz=0.06, dimexo=0.04, dimexe=0.08, dimgap=0.04, dimdec=2, dimdsep=46,
                     dimtad=1, dimtih=0, dimtoh=0, dimzin=0, dimclrd=1, dimclre=1, dimclrt=1, dimlunit=2, dimscale=1.0,
                     dimtix=0, dimatfit=3, dimtmove=0).items():
        ds.set_dxf_attrib(k, v)

    sheet_s101(doc, geom, des)
    b12 = next(r for r in des["beams"] if r["label"] == "B12" and r["story"] == "Story1")
    framing_sheet(doc, geom, des, 1, ["Story1", "Story2", "Story3"], "S-102", "پلان تیر ریزى تیپ طبقات اول تا سوم",
                  "S-102 TYPICAL FLOOR FRAMING PLAN - FLOORS 1, 2, 3", [
                      "1. ONE PLAN FOR FLOORS 1, 2 AND 3 (ETABS Story1-3): same grid, beams, cantilevers, slab panels and openings on all three floors.",
                      "2. STOREY DIFFERENCES: beams 50x50 on floors 1-2, 45x50 on floor 3 (tag '50x50 / 45x50' = F1-F2 / F3);",
                      "   columns below the floor: 50x50 under floors 1-2, 45x45 under floor 3 (S-101); reinforcement per floor in S-104.",
                      f"3. B12 floor 1: hoops {b12['hoop_h']} (torsion, T32); B32 carries wall W24 (4.495 kN/m) on floors 1-3.",
                      "4. Cantilevers B3, B5 (on grid B' at C19), B6: 1.20 m, tied by edge beam B2; 'Sway Ordinary' (boss, task 13/14).",
                      "5. Joist-block slabs (tirche): joists span in X between beams on axes A, B (B' at the balcony) and C; arrows = joist direction.",
                      "6. Stair (A-B, 2-3) and elevator shaft (A-B, 3 to +1.80) are slab openings; stair slabs and landings: separate detail",
                      "   (half landings must not frame into the columns - see report T34, coordination 56). Beams drawn 50 wide.",
                      "7. Ground floor (parking, 3 tandem stalls; rear yard at +-0.00) has no suspended framing in ETABS: slab on grade, walls on grade",
                      "   beams (SAFE). Ground stair: 20 risers x 17.5 cm, mid landing +1.75 (boss 2026-10-23) - landing kept free of C2 / C6 / C16.",
                      "8. Beam tags: label (project) / b x h (cm). Levels: FFL; ETABS level = FFL + 0.30 (ETABS datum, Base +0.30).",
                  ])
    sh3 = framing_sheet(doc, geom, des, 2, ["Story4"], "S-103", "پلان تیر ریزى بام و بام خرپشته",
                        "S-103 ROOF FRAMING PLAN (Story4) + STAIR-HOUSE ROOF (Story5)", [
                            "1. Roof (Story4): same beam layout as the typical floors, all beams 45x50; columns below 45x45.",
                            "2. B12, B30, B32, B36 carry the stair-house walls (6.96 kN/m); edge beams carry the 1.10 parapet (3.42 kN/m, + facade on B10/B11).",
                            "3. Roof joints of C5, C10, C19, C20, C21: strong-column ratio > 1.0, exempt by ACI 18.7.3.1 (boss 2026-10-19).",
                            "4. Elevator shaft opening continues to the roof; overrun / machine to be coordinated with the elevator supplier.",
                            "5. Stair-house roof (Story5, lower left): C2, C6, C16, C18 40x40; beams 40x50; joist slab F17.",
                            "6. Reinforcement: S-105.",
                        ], roof=True)
    stairhouse(sh3, geom, des)
    schedule_sheet(doc, des, 3, ["Story1", "Story2", "Story3"], "S-104", "جدول آرماتور تیرهای طبقات اول تا سوم",
                   "S-104 BEAM SCHEDULE - FLOORS 1, 2, 3 (ACI 318-19)", s104_extra)
    schedule_sheet(doc, des, 4, ["Story4", "Story5"], "S-105", "جدول آرماتور تیرهای بام و جزئیات تیپ",
                   "S-105 BEAM SCHEDULE - ROOF & STAIR HOUSE + TYPICAL DETAILS", s105_extra)
    doc.set_modelspace_vport(height=32, center=(2 * PITCH + 21, 15))
    dxf = os.path.join(TMP, "Merage3_struct_T34_draft.dxf")
    doc.saveas(dxf)
    scr = os.path.join(TMP, "save_t34.scr")
    with open(scr, "w", encoding="utf-8") as f:
        f.write(f'_.FILEDIA 0\n_.ZOOM _E\n_.SAVEAS 2018 "{OUT_DWG}"\n')
    if os.path.exists(OUT_DWG):
        os.makedirs(os.path.join(HERE, "_prev"), exist_ok=True)
        os.replace(OUT_DWG, os.path.join(HERE, "_prev", "Merage3_struct_T34_draft_prev.dwg"))
    r = subprocess.run([ACCORE, "/i", dxf, "/s", scr, "/l", "en-US"], capture_output=True, timeout=300)
    if not os.path.exists(OUT_DWG):
        print(r.stdout.decode("utf-16-le", errors="ignore")[-2000:])
        raise SystemExit("DWG not written")
    print("DWG:", OUT_DWG, os.path.getsize(OUT_DWG))
    json.dump({n: [k * PITCH, 0.0, k * PITCH + SHEET_W, SHEET_H] for k, n in enumerate(SHEETS)},
              open(os.path.join(HERE, "t34_sheets.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
