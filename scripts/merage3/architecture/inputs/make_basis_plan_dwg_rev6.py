# -*- coding: utf-8 -*-
"""Merage3 task 8c Rev.1: typical-floor architectural plan from the BASIS PDF + boss decisions 2026-10-22.

Source: arch/memary500_Model_600_BASIS.pdf (vector). Every black line of the PDF is copied, scaled with
K pt/m found from the dimension texts, and sorted into layers. Rev.1 changes (boss, 2026-10-22):
  1. corridor 1.36: walls W9 and W15 moved onto the line of W7 (+1.2 pt = 4.3 cm);
  2. axis 4 at 18.81 and C19 at X=2.507 stay (architecture governs; ETABS to be coordinated);
  3. front terrace 1.90 x 1.00 restored as in the previous plan (memary 500.dwg): no wall on B10,
     recessed wall on slab F1 with a steel door, return wall on B4, railing on the open edge;
  5. window / door sizes and heights, schedule on the sheet, wall table with opening areas.
Model units: metre. Plot 1:100 on A3. DWG coordinates: u = -Y(ETABS), v = X(ETABS), origin column A/1.

    python make_basis_plan_dwg.py      -> arch/Merage3_arch_plan_BASIS.dwg + task08c_basis_geometry.json
"""
import json
import os
import re
import subprocess
import sys
import tempfile

import ezdxf
import pymupdf as fitz
from ezdxf.enums import TextEntityAlignment as TA

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.abspath(os.path.join(HERE, "..", ".."))
PDF = os.path.join(PRJ, "arch", "memary500_Model_600_BASIS.pdf")
OUT_DWG = os.path.join(PRJ, "arch", "Merage3_arch_plan_BASIS.dwg")
OUT_JSON = os.path.join(HERE, "task08c_basis_geometry.json")
OUT_JSON_ARCH = os.path.join(PRJ, "arch", "Merage3_arch_plan_BASIS_geometry.json")
GEOM = os.path.join(PRJ, "work", "etabs", "Merage3_geometry.json")
ACCORE = r"C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe"
REV = "Rev.6"

# ---------------------------------------------------------------- heights (m)
SLAB = 0.31      # joist slab 60 + 250 (ETABS deck TIRCHEH)
BEAM = 0.50      # beam depth (ETABS BWxxH50)
FIN = 0.08       # floor finish above structural slab: CONFIRMED by boss 2026-10-23
SILL = 0.70      # window sill above finished floor (boss)
SILL_BAL = 0.20  # door-window to the rear balcony (boss)
DOOR_HEAD = 2.10  # interior door head above finished floor: CONFIRMED by boss 2026-10-23
PARAPET = 1.10   # W4 rear balcony parapet and terrace railing, above FFL: CONFIRMED 2026-10-23
GUARD = 1.10     # steel guard of windows with sill 0.70, upper floors, above FFL: CONFIRMED 2026-10-23 (printed Mobhas 4 text still to be checked)
LIFT_DOOR = (1.20, 2.00)   # elevator door width x height (Rev.5 final)
PARAPET_WALLS = ("W4", "W6")   # Rev.4: only rear edge W4 and divider W6 are parapets; side walls W1a/W2a full (boundary)
LIFT_DOOR_X = (0.60, 1.80)   # ETABS X of the lift door in W19: shaft face clear 0.45..2.10, 0.30 to column B/3

# ---------------------------------------------------------------- PDF dimensions
# (text, orientation, fixed coord, p1, p2) in PDF pt. Rev.1: 3.03 and 1.15 follow wall W15 (+1.2 pt).
SHIFT = 1.2
PDF_DIMS = [
    ("4.80", "H", 599.96, 52.64, 185.36), ("3.10", "H", 599.96, 189.56, 275.24),
    ("1.30", "H", 608.72, 280.76, 316.76), ("1.75", "H", 628.88, 320.84, 369.32),
    ("1.80", "H", 757.76, 143.96, 193.64), ("3.15", "H", 710.48, 52.64, 139.76),
    ("2.85", "V", 382.40, 715.28, 794.00), ("1.80", "V", 345.80, 588.08, 637.76),
    ("0.10", "V", 192.08, 777.44, 780.20), ("3.09", "V", 254.84, 588.08, 673.52),
    ("3.03", "V", 379.52, 588.74, 672.38), ("3.04", "V", 65.96, 589.40, 673.52),
    ("1.68", "V", 41.12, 626.72, 673.10), ("1.20", "V", 29.12, 588.08, 621.20),
    ("3.24", "V", 28.88, 621.20, 710.84), ("4.06", "V", 73.16, 677.72, 789.92),
    ("1.20", "V", 294.56, 604.64, 637.76), ("1.15", "V", 324.56, 640.52, 672.32),
    ("1.36", "V", 225.32, 677.72, 715.28),
]
REV1_DIM_SHIFT = {"3.03": SHIFT, "1.15": SHIFT}     # second point moves with W15

# ---------------------------------------------------------------- walls (PDF pt), Rev.1
# (id, dir, face1, face2, from, to, note); door gaps are INCLUDED in from-to, openings listed below.
WALLS = [
    ("W1a", "H", 582.56, 588.08, 19.52, 47.12, "axis C, rear balcony side: FULL wall (boundary, Rev.4)"),
    ("W1b", "H", 582.56, 588.08, 60.92, 193.64, "axis C, 3-4"),
    ("W1c", "H", 582.56, 588.08, 207.56, 359.60, "axis C, 2-3"),
    ("W1d", "H", 582.56, 588.08, 373.40, 566.96, "axis C, 1-2"),
    ("W2a", "H", 788.48, 794.00, 19.52, 47.12, "axis A, rear balcony side: FULL wall (boundary, Rev.4)"),
    ("W2b", "H", 788.48, 794.00, 60.92, 193.64, "axis A, 3-4 (elevator, duct)"),
    ("W2c", "H", 788.48, 794.00, 207.56, 359.60, "axis A, 2-3 (stair)"),
    ("W2d", "H", 788.48, 794.00, 373.40, 566.96, "axis A, 1-2 (incl. terrace side)"),
    ("W3a", "V", 575.24, 580.76, 596.36, 715.28, "front facade axis 1, B-C"),
    ("W4", "V", 14.00, 19.52, 582.56, 794.00, "rear balcony edge (axis 5): PARAPET h=1.10 above FFL (Rev.2)"),
    ("W5a", "V", 47.12, 52.64, 596.36, 710.84, "axis 4, B-C (door 0.70 + door-window 1.69)"),
    ("W5c", "V", 47.12, 52.64, 724.76, 780.20, "axis 4, A-B (window behind elevator)"),
    ("W6", "H", 621.20, 626.72, 19.52, 47.12, "rear balcony divider (cantilever slab): PARAPET h=1.10 (Rev.3)"),
    ("W7", "H", 673.52, 677.72, 52.64, 185.36, "room 4.80 / corridor"),
    ("W8", "V", 185.36, 189.56, 588.08, 677.72, "room 4.80 / room 3.10"),
    ("W9", "H", 673.52, 677.72, 189.56, 275.24, "room 3.10 / corridor (Rev.1: on W7 line)"),
    ("W10", "V", 275.24, 280.76, 588.08, 677.72, "room 3.10 / WC + shaft"),
    ("W11", "H", 600.44, 604.64, 280.76, 316.76, "shaft / WC-1"),
    ("W12", "H", 637.76, 640.52, 280.76, 316.76, "WC-1 front"),
    ("W13", "V", 316.76, 320.84, 588.08, 654.20, "WC-1 / WC-2"),
    ("W14", "H", 637.76, 640.52, 320.84, 369.32, "WC-2 front"),
    ("W15", "H", 673.52, 677.72, 280.76, 369.32, "service lobby / corridor (Rev.1: on W7 line)"),
    ("W16", "V", 369.32, 373.40, 596.36, 677.72, "axis 2, B-C"),
    ("W17", "V", 139.76, 143.96, 677.72, 788.48, "elevator + duct side / room 3.15"),
    ("W18", "H", 715.28, 719.36, 143.96, 193.64, "elevator front, corridor side: FULL wall (Rev.4, door moved to W19)"),
    ("W19", "V", 193.64, 197.84, 729.08, 780.20, "elevator / stair landing"),
    ("W20", "H", 774.68, 777.44, 143.96, 193.64, "elevator / duct"),
]
# terrace walls from the previous plan (ETABS metres): (id, dir, line, from, to, thick, note)
WALLS_M = [
    ("W22", "X", 0.85, -0.05, 2.10, 0.20, "front terrace recessed wall (slab F1), steel door"),
    ("W23", "Y", 2.20, 0.25, 0.95, 0.20, "front terrace return wall next to column B/1"),
    ("W24", "Y", 2.325, 7.75, 13.25, 0.15, "corridor / stair wall 15 cm (Rev.6), on B32, entry door DE1"),
    ("W21", "X", 7.70, 0.25, 2.10, 0.10, "axis 2, A-B, stair / living 10 cm (Rev.6): stair face flush with columns (Y=7.75)"),
]
# openings: (tag, wall, kind, a, b) -- a/b in PDF pt along the wall, or ETABS m for W22
OPENINGS = [
    ("WN1", "W3a", "window_full", None, None),      # 3.50 centred in bay B-C (boss)
    ("WN2", "W5c", "window_full", 738.80, 771.92),   # behind elevator, 1.20 (boss)
    ("DW1", "W5a", "door_window", 626.72, 673.52),   # to rear balcony, 0.20 -> ceiling (boss)
    ("D3", "W5a", "door", 601.88, 621.20),           # to small balcony 0.70
    ("DS1", "W22", "steel_door", 0.65, 2.10),        # terrace steel door, slab -> ceiling (boss)
    ("D1", "W7", "door", 160.52, 185.36), ("D1", "W9", "door", 189.56, 214.40),
    ("D1", "W17", "door", 677.72, 702.56),
    ("D3", "W12", "door", 297.44, 316.76), ("D2", "W14", "door", 345.80, 369.32),
    ("D4", "W15", "door", 280.76, 297.44),
    ("DL1", "W19", "lift_door", None, None),
    ("DE1", "W24", "door", 12.155, 13.055),
]
FRONT_WIN = (3.00, 6.50)
# Rev.6 door symbols: (tag, hinge X, hinge Y, closing dir, opening dir, width, opens into)
DOORS = [
    ("D1", 4.109, 14.061, (0, 1), (1, 0), 0.899, "room 4.80 (inward, leaf against W8)"),
    ("D1", 4.109, 13.905, (0, -1), (1, 0), 0.900, "room 3.10 (inward, leaf against W8)"),
    ("D1", 3.957, 15.704, (-1, 0), (0, 1), 0.899, "room 3.15 (inward, leaf against W7)"),
    ("D2", 5.303, 7.400, (0, 1), (-1, 0), 0.851, "WC-2: outward into the service lobby"),
    ("D3", 5.303, 9.301, (0, 1), (-1, 0), 0.699, "WC-1: outward into the service lobby"),
    ("D4", 4.109, 10.603, (0, -1), (1, 0), 0.603, "service lobby (inward, leaf against W10)"),
    ("D3", 6.701, 18.856, (-1, 0), (0, -1), 0.699, "small rear balcony: inward into room 4.80"),
    ("DW1", 4.109, 18.856, (1, 0), (0, -1), 0.8465, "rear balcony, double leaf, inward"),
    ("DW1", 5.802, 18.856, (-1, 0), (0, -1), 0.8465, "rear balcony, double leaf, inward"),
    ("DE1", 2.40, 13.055, (0, -1), (1, 0), 0.90, "unit entry from the stair floor landing: inward into the unit corridor"),
]        # ETABS X of window WN1 (3.50, centred on 2.60..6.90)

LAYERS = {
    "A-WALL": (7, "CONTINUOUS", 50), "A-COLUMN": (2, "CONTINUOUS", 50),
    "A-STAIR": (3, "CONTINUOUS", 25), "A-ELEV": (4, "CONTINUOUS", 25),
    "A-SHAFT": (6, "CONTINUOUS", 25), "A-OPENING": (5, "CONTINUOUS", 25),
    "A-RAIL": (3, "CONTINUOUS", 25), "A-DOOR": (4, "CONTINUOUS", 18), "A-DIM": (1, "CONTINUOUS", 18), "A-AXIS": (8, "CENTER", 18),
    "A-TEXT": (7, "CONTINUOUS", 25), "A-SHEET": (7, "CONTINUOUS", 50),
}


def fa(text):
    text = text.replace("\u200c", " ")
    return re.sub("ی(?=[ؠ-يپ-ۓ])", "ي", text).replace("ی", "ى")


def read_pdf():
    page = fitz.open(PDF)[0]
    segs, quads = [], []
    for d in page.get_drawings():
        black = d["color"] == (0, 0, 0)
        for it in d["items"]:
            if it[0] == "l":
                segs.append((black, it[1].x, it[1].y, it[2].x, it[2].y))
            elif it[0] == "qu":
                r = it[1].rect
                quads.append((r.x0, r.y0, r.x1, r.y1))
    return segs, quads


def fit_scale():
    num = den = 0.0
    lo, hi = 0.0, 1e9
    for t, _, _, a, b in PDF_DIMS:
        v, L = float(t), abs(b - a)
        if v < 0.5:
            continue
        num += L * v
        den += v * v
        lo, hi = max(lo, L / (v + 0.005)), min(hi, L / (v - 0.005))
    return num / den, lo, hi


def rev1_point(x, y):
    """Rev.1: W9 / W15 (and the ends of the walls meeting them) move down onto the W7 line."""
    if 214.0 <= x <= 373.5 and (abs(y - 672.32) < 0.05 or abs(y - 676.52) < 0.05):
        return x, y + SHIFT
    return x, y


def main():
    segs, quads = read_pdf()
    K, klo, khi = fit_scale()
    cols = quads
    c1 = max(cols, key=lambda q: (q[2], q[3]))
    X0, Y0 = (c1[0] + c1[2]) / 2, (c1[1] + c1[3]) / 2

    def P(x, y):
        return ((x - X0) / K, (Y0 - y) / K)

    def etabs(x, y):
        u, v = P(x, y)
        return (v, -u)

    def pt_y(Xm):   # ETABS X -> PDF y
        return Y0 - Xm * K

    col_e = sorted([etabs((q[0] + q[2]) / 2, (q[1] + q[3]) / 2) for q in cols], key=lambda p: (round(p[1], 1), p[0]))

    def cluster(vals, tol=0.3):
        out = []
        for v in sorted(vals):
            if out and abs(v - out[-1][-1]) < tol:
                out[-1].append(v)
            else:
                out.append([v])
        return [sum(g) / len(g) for g in out]
    ys = cluster([p[1] for p in col_e])
    xs_all = cluster([p[0] for p in col_e], tol=0.05)
    AX_Y = {"1": ys[0], "2": ys[1], "3": ys[2], "4": ys[3]}
    AX_Y["5"] = AX_Y["4"] + 1.20
    AX_X = {"A": 0.0, "B": min(xs_all, key=lambda v: abs(v - 2.35)), "C": max(xs_all)}

    # ---------------- classify PDF lines
    def in_rect(x, y, r, tol=0.3):
        return r[0] - tol <= x <= r[2] + tol and r[1] - tol <= y <= r[3] + tol

    ELEV = (143.96, 719.36, 193.64, 774.68)
    DUCT = (143.96, 777.44, 193.64, 788.48)
    SHAFT = (280.76, 588.08, 316.76, 600.44)
    STAIR = (243.44, 715.28, 326.36, 781.64)
    y_b1, y_a1 = 729.08, 780.20            # faces of columns B/1 and A/1 along the facade
    out, seen = [], set()
    for black, x1, y1, x2, y2 in segs:
        if not black:
            continue
        key = tuple(sorted([(round(x1, 1), round(y1, 1)), (round(x2, 1), round(y2, 1))]))
        if key in seen or key[0] == key[1]:
            continue
        seen.add(key)
        # Rev.1 terrace: no facade wall / window between columns A/1 and B/1
        if min(x1, x2) >= 575.0:
            if abs(x1 - x2) < 0.1:          # vertical facade lines: cut y_b1..y_a1
                a, b = sorted([y1, y2])
                if a < y_b1 - 0.05 or b > y_a1 + 0.05:
                    pieces = [(a, min(b, y_b1)), (max(a, y_a1), b)]
                    pieces = [p for p in pieces if p[1] - p[0] > 0.05]
                    if abs(x1 - 578.0) < 0.1:
                        continue            # glazing lines are redrawn below
                    for p in pieces:
                        out.append(("A-WALL" if not any(in_rect(x1, p[0], q) and in_rect(x1, p[1], q) for q in cols)
                                    else "A-COLUMN", x1, p[0], x1, p[1]))
                    continue
                continue                    # fully inside the terrace opening
            if abs(y1 - y2) < 0.1 and any(abs(y1 - v) < 0.1 for v in (615.68, 695.84, 736.04, 773.36)):
                continue                    # old window jambs (redrawn below)
        x1, y1 = rev1_point(x1, y1)
        x2, y2 = rev1_point(x2, y2)
        diag = abs(x1 - x2) > 0.1 and abs(y1 - y2) > 0.1
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        layer = "A-WALL"
        if any(in_rect(x1, y1, q) and in_rect(x2, y2, q) for q in cols):
            layer = "A-COLUMN"
        elif diag and in_rect(mx, my, ELEV):
            layer = "A-ELEV"
        elif diag and (in_rect(mx, my, DUCT) or in_rect(mx, my, SHAFT)):
            layer = "A-SHAFT"
        elif in_rect(x1, y1, STAIR, 0.05) and in_rect(x2, y2, STAIR, 0.05) and not (
                abs(y1 - y2) < 0.1 and abs(y1 - 715.28) < 0.1):
            layer = "A-STAIR"
        elif abs(y1 - y2) < 0.1 and abs(y1 - 781.64) < 0.1:
            layer = "A-STAIR"
        elif abs(x1 - x2) < 0.1 and abs(x1 - 49.88) < 0.1:
            layer = "A-OPENING"
        elif abs(y1 - y2) < 0.1 and max(x1, x2) <= 52.7 and any(abs(y1 - v) < 0.1 for v in (738.8, 771.92)):
            layer = "A-OPENING"
        if layer == "A-WALL" and abs(y1 - y2) < 0.1 and abs(y1 - 715.28) < 0.1:
            a, b = sorted([x1, x2])
            if a < 193.7:
                out.append(("A-WALL", a, y1, min(b, 193.64), y1))
            continue                         # Rev.6: stair edge on line B replaced by wall W24
        if layer == "A-STAIR":
            continue                         # Rev.6: stair regenerated (flights shifted, widths kept)
        # Rev.6: old W21 (Y 7.25-7.35) removed between columns A/2 and B/2; redrawn at Y 7.65-7.75
        if abs(x1 - x2) < 0.1 and (abs(x1 - 370.64) < 0.1 or abs(x1 - 373.40) < 0.1) and max(y1, y2) > 729.1:
            a, b = sorted([y1, y2])
            for pa, pb in ((a, min(b, 729.08)), (max(a, 780.20), b)):
                if pb - pa > 0.05 and abs(x1 - 373.40) < 0.1:
                    lay = "A-COLUMN" if any(in_rect(x1, pa, q) and in_rect(x1, pb, q) for q in cols) else "A-WALL"
                    out.append((lay, x1, pa, x1, pb))
            continue
        out.append((layer, x1, y1, x2, y2))
    # front window WN1 3.50 (glazing + jambs)
    wa, wb = pt_y(FRONT_WIN[1]), pt_y(FRONT_WIN[0])
    out.append(("A-OPENING", 578.0, wa, 578.0, wb))
    out.append(("A-OPENING", 575.24, wa, 580.76, wa))
    out.append(("A-OPENING", 575.24, wb, 580.76, wb))
    # Rev.4: lift door DL1 (1.80, boss order) in W19 = shaft wall facing the stair landing; W18 stays full.
    # centred between the faces of columns A/3 (X 0.25) and B/3 (X 2.10): X 0.275..2.075
    la, lb = Y0 - LIFT_DOOR_X[1] * K, Y0 - LIFT_DOOR_X[0] * K      # PDF y of the two jambs
    cut = []
    for seg in out:
        layer, x1, y1, x2, y2 = seg
        if layer == "A-WALL" and abs(x1 - x2) < 0.1 and any(abs(x1 - xx) < 0.1 for xx in (193.64, 197.84))                 and min(y1, y2) < la and max(y1, y2) > lb:
            a, b = sorted([y1, y2])
            cut += [(layer, x1, a, x1, la), (layer, x1, lb, x1, b)]
        else:
            cut.append(seg)
    out = cut
    out += [("A-WALL", 193.64, la, 197.84, la), ("A-WALL", 193.64, lb, 197.84, lb)]

    # ---------------- DXF
    doc = ezdxf.new("R2018", setup=False)
    doc.units = ezdxf.units.M
    doc.header["$INSUNITS"] = 6
    doc.header["$MEASUREMENT"] = 1
    doc.header["$LTSCALE"] = 1.0
    doc.header["$LWDISPLAY"] = 1
    doc.linetypes.add("CENTER", pattern=[0.56, 0.35, -0.08, 0.05, -0.08], description="Center ____ _ ____")
    for name, (c, lt, lw) in LAYERS.items():
        doc.layers.add(name, color=c, linetype=lt, lineweight=lw)
    doc.styles.add("LATIN", font="arial.ttf")
    doc.styles.add("FARSI", font="tahoma.ttf")
    ds = doc.dimstyles.add("A100")
    ds.dxf.dimtxsty = "LATIN"
    for k, v in dict(dimtxt=0.18, dimasz=0.10, dimtsz=0.07, dimexo=0.04, dimexe=0.08, dimgap=0.04,
                     dimdec=2, dimdsep=46, dimtad=1, dimtih=0, dimtoh=0, dimzin=0, dimclrd=1, dimclre=1,
                     dimclrt=5, dimlunit=2, dimscale=1.0, dimtix=0, dimatfit=3, dimtmove=0).items():
        ds.set_dxf_attrib(k, v)
    msp = doc.modelspace()

    def text(s, x, y, h, layer="A-TEXT", style="LATIN", align=TA.MIDDLE_CENTER, rot=0.0, width=0.9):
        t = msp.add_text(s, height=h, rotation=rot, dxfattribs={"layer": layer, "style": style, "width": width})
        t.set_placement((x, y), align=align)
        return t

    def E(X, Y):    # ETABS -> DWG
        return (-Y, X)

    def line_e(layer, X1, Y1, X2, Y2):
        msp.add_line(E(X1, Y1), E(X2, Y2), dxfattribs={"layer": layer})

    for layer, x1, y1, x2, y2 in out:
        msp.add_line(P(x1, y1), P(x2, y2), dxfattribs={"layer": layer})
    for q in cols:
        pts = [P(q[0], q[1]), P(q[2], q[1]), P(q[2], q[3]), P(q[0], q[3])]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "A-COLUMN"})
        h = msp.add_hatch(color=8, dxfattribs={"layer": "A-COLUMN"})
        h.paths.add_polyline_path(pts, is_closed=True)

    # ---------------- Rev.6: corridor / stair wall W24 (stair face X=2.25, 15 cm to the corridor), entry door DE1
    for X1, Y1, X2, Y2 in [(2.25, 7.75, 2.25, 12.155), (2.40, 7.75, 2.40, 12.155),
                           (2.25, 13.055, 2.25, 13.25), (2.40, 13.055, 2.40, 13.25),
                           (2.25, 12.155, 2.40, 12.155), (2.25, 13.055, 2.40, 13.055)]:
        line_e("A-WALL", X1, Y1, X2, Y2)
    # W21 (10 cm) with its stair face on the column faces Y=7.75
    for X1, Y1, X2, Y2 in [(0.25, 7.65, 2.10, 7.65), (0.25, 7.75, 2.10, 7.75)]:
        line_e("A-WALL", X1, Y1, X2, Y2)
    # stair regenerated: two flights 1.10 (X -0.05..1.05 DN, X 1.15..2.25 UP), well 0.10, 10 treads 0.30
    FL = [(-0.05, 1.05), (1.15, 2.25)]
    for k in range(11):
        Yt = 8.958 + 0.30 * k
        for xa, xb in FL:
            line_e("A-STAIR", xa, Yt, xb, Yt)
    for Xw in (1.05, 1.15):
        line_e("A-STAIR", Xw, 8.958, Xw, 11.958)
    for Xc, lab in ((1.70, "UP"), (0.50, "DN")):
        line_e("A-STAIR", Xc, 11.80, Xc, 9.30)
        line_e("A-STAIR", Xc, 9.30, Xc - 0.10, 9.50)
        line_e("A-STAIR", Xc, 9.30, Xc + 0.10, 9.50)
        msp.add_circle(E(Xc, 11.80), 0.04, dxfattribs={"layer": "A-STAIR"})
        u, v = E(Xc, 12.05)
        text(lab, u, v, 0.15, layer="A-STAIR")
    u, v = E(1.45, 12.40)
    text("FLOOR LANDING", u, v, 0.12, rot=90)
    u, v = E(1.10, 8.35)
    text("HALF LANDING", u, v, 0.12, rot=90)

    # ---------------- Rev.6: door symbols (leaf + 90 deg swing arc), layer A-DOOR; none for the lift door
    import math as _m

    def door(hx, hy, c, o, w):
        lu = (-o[1], o[0])
        cv = (-c[1], c[0])
        H = E(hx, hy)
        msp.add_line(H, (H[0] + lu[0] * w, H[1] + lu[1] * w), dxfattribs={"layer": "A-DOOR"})
        ao = round(_m.degrees(_m.atan2(lu[1], lu[0]))) % 360
        ac = round(_m.degrees(_m.atan2(cv[1], cv[0]))) % 360
        if (ac - ao) % 360 == 90:
            msp.add_arc(H, w, ao, ac, dxfattribs={"layer": "A-DOOR"})
        else:
            msp.add_arc(H, w, ac, ao, dxfattribs={"layer": "A-DOOR"})

    for _t, hx, hy, c, o, w, _n in DOORS:
        door(hx, hy, c, o, w)

    # ---------------- front terrace (previous plan geometry, ETABS m)
    for X1, Y1, X2, Y2 in [(-0.05, 0.75, 0.65, 0.75), (-0.05, 0.95, 0.65, 0.95), (0.65, 0.75, 0.65, 0.95),
                           (2.10, 0.25, 2.10, 0.95), (2.30, 0.25, 2.30, 0.95), (2.10, 0.95, 2.30, 0.95)]:
        line_e("A-WALL", X1, Y1, X2, Y2)
    # steel door DS1: frame line + two leaves (90 deg arcs) opening to the terrace
    line_e("A-OPENING", 0.65, 0.85, 2.10, 0.85)
    mid = (0.65 + 2.10) / 2
    for hx, sgn in ((0.65, 1), (2.10, -1)):
        lw = mid - 0.65
        line_e("A-DOOR", hx, 0.75, hx, 0.75 - lw)
        c = E(hx, 0.75)
        # arc from leaf tip (hx, 0.75-lw) to the closed position (hx+sgn*lw, 0.75)
        a_open, a_closed = (0.0 if True else 0), 0
        if sgn > 0:
            msp.add_arc(c, lw, 0, 90, dxfattribs={"layer": "A-DOOR"})
        else:
            msp.add_arc(c, lw, 270, 360, dxfattribs={"layer": "A-DOOR"})
    # railing on the open edge (B10), X 0.25..2.10, 5 cm wide, at Y=-0.20
    line_e("A-RAIL", 0.25, -0.225, 2.10, -0.225)
    line_e("A-RAIL", 0.25, -0.175, 2.10, -0.175)
    u, v = E(1.175, -0.55)
    text("STEEL RAILING h=1.10", u, v, 0.12, rot=90)
    u, v = E(3.70, 20.55)
    text("PARAPET h=1.10 above FFL", u, v, 0.13, rot=90)
    u, v = E(3.20, 19.93)
    text("BALCONY OPEN TO THE REAR ONLY: PARAPET W4 h=1.10; SIDE WALLS W1a/W2a FULL (Rev.4)", u, v, 0.08, rot=90)
    for Xp, Yp in ((7.65, 19.55), (-0.45, 19.55)):
        u, v = E(Xp, Yp)
        text("FULL WALL (BOUNDARY)", u, v, 0.11)
    u, v = E(6.55, 19.30)
    text("W6 PARAPET h=1.10", u, v, 0.08, rot=90)
    u, v = E(0.30, 0.30)
    text(fa("تراس"), u, v, 0.16, style="FARSI", width=1.0, rot=90)

    # ---------------- dimensions
    dim_check = []

    def ldim(p1, p2, base, ang):
        d = msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=ang, dimstyle="A100", dxfattribs={"layer": "A-DIM"})
        d.render()

    for t, o, c, a, b in PDF_DIMS:
        if t == "1.36":
            continue                     # Rev.6: stair edge replaced by W24; corridor dims redrawn below
        b2 = b + REV1_DIM_SHIFT.get(t, 0.0) if (t != "1.15" or True) else b
        if t not in REV1_DIM_SHIFT:
            b2 = b
        if o == "H":
            ldim(P(a, c), P(b2, c), P(a, c), 0)
        else:
            ldim(P(c, a), P(c, b2), P(c, a), 90)
        meas = abs(b2 - a) / K
        dim_check.append(dict(pdf=t, rev1=f"{meas:.2f}", measured=round(meas, 4), same=f"{meas:.2f}" == t))
    # terrace dims (ETABS m)
    ldim(E(-0.05, 1.60), E(2.10, 1.60), E(-0.05, 1.60), 90)          # terrace width 2.15 (inner)
    ldim(E(2.90, -0.25), E(2.90, 0.75), E(2.90, -0.25), 0)          # terrace depth 1.00
    ldim(E(0.65, 1.15), E(2.10, 1.15), E(0.65, 1.15), 90)           # steel door 1.45
    ldim(E(FRONT_WIN[0], -0.55), E(FRONT_WIN[1], -0.55), E(FRONT_WIN[0], -0.55), 90)  # window 3.50
    ldim(E(2.40, 9.00), E(3.957, 9.00), E(2.40, 9.00), 90)                     # corridor 1.56 at W24
    ldim(E(2.60, 7.55), E(3.957, 7.55), E(2.60, 7.55), 90)                     # corridor 1.36 at column B/2
    for xa, xb in ((-0.05, 1.05), (1.05, 1.15), (1.15, 2.25)):                 # flights 1.10 / well / 1.10
        ldim(E(xa, 10.45), E(xb, 10.45), E(xa, 10.45), 90)
    ldim(E(LIFT_DOOR_X[0], 13.42), E(LIFT_DOOR_X[1], 13.42), E(LIFT_DOOR_X[0], 13.42), 90)  # lift door 1.20

    # ---------------- axes and overall dims
    u_min, u_max = P(14.0, 0)[0], P(580.76, 0)[0]
    v_min, v_max = P(0, 794.0)[1], P(0, 582.56)[1]
    R = 0.40
    for lab, Y in AX_Y.items():
        u = -Y
        msp.add_line((u, v_min - 3.0), (u, v_max + 1.0), dxfattribs={"layer": "A-AXIS"})
        msp.add_circle((u, v_min - 3.0 - R), R, dxfattribs={"layer": "A-AXIS", "linetype": "CONTINUOUS"})
        text(lab, u, v_min - 3.0 - R, 0.35, layer="A-AXIS")
    for lab, X in AX_X.items():
        msp.add_line((u_min - 1.0, X), (u_max + 3.0, X), dxfattribs={"layer": "A-AXIS"})
        msp.add_circle((u_max + 3.0 + R, X), R, dxfattribs={"layer": "A-AXIS", "linetype": "CONTINUOUS"})
        text(lab, u_max + 3.0 + R, X, 0.35, layer="A-AXIS")
    us = [u_max] + [-AX_Y[k] for k in "12345"] + [u_min]
    for a, b in zip(us, us[1:]):
        if abs(a - b) > 1e-6:
            ldim((a, v_min), (b, v_min), (a, v_min - 1.0), 0)
    ldim((u_max, v_min), (u_min, v_min), (u_max, v_min - 1.8), 0)
    vs = [v_min] + [AX_X[k] for k in "ABC"] + [v_max]
    for a, b in zip(vs, vs[1:]):
        ldim((u_max, a), (u_max, b), (u_max + 1.0, a), 90)
    ldim((u_max, v_min), (u_max, v_max), (u_max + 1.8, v_min), 90)

    # ---------------- labels
    for s, x, y in [("پله", 343.05, 773.3), ("آسانسور", 168.8, 733.0), ("بالکن", 33.0, 690.0)]:
        u, v = P(x, y)
        text(fa(s), u, v, 0.18, style="FARSI", width=1.0, rot=90 if s == "بالکن" else 0)
    # opening tags (ETABS position of the tag)
    tags = [("WN1", 4.75, -0.75), ("WN2", 1.15, 18.35), ("DW1", 4.38, 18.35), ("D3", 6.35, 18.35),
            ("DS1", 1.375, 2.00), ("DL1", 0.95, 12.95), ("D1", 3.60, 14.51), ("D1", 3.60, 13.46), ("D1", 3.40, 15.85),
            ("D3", 5.05, 9.65), ("D2", 5.05, 7.83), ("D4", 3.65, 10.30), ("DE1", 3.05, 12.60)]
    for tg, X, Y in tags:
        u, v = E(X, Y)
        msp.add_lwpolyline([(u - 0.22, v - 0.1), (u + 0.22, v - 0.1), (u + 0.22, v + 0.1), (u - 0.22, v + 0.1)],
                           close=True, dxfattribs={"layer": "A-TEXT"})
        text(tg, u, v, 0.11)

    # ---------------- sheet
    cu = (u_min + u_max + 3.0) / 2
    fx0, fy0 = cu - 21.0, -15.2
    fx1, fy1 = fx0 + 42.0, fy0 + 29.7
    msp.add_lwpolyline([(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)], close=True, dxfattribs={"layer": "A-SHEET"})
    m = 1.0
    msp.add_lwpolyline([(fx0 + m, fy0 + m), (fx1 - m, fy0 + m), (fx1 - m, fy1 - m), (fx0 + m, fy1 - m)],
                       close=True, dxfattribs={"layer": "A-SHEET"})
    tcx = (u_min + u_max) / 2
    text(fa("پلان معماری طبقه ی تیپ - ملاک نهایی - ") + REV, tcx, v_max + 2.6, 0.50, style="FARSI", width=1.0)
    text(f"TYPICAL FLOOR ARCHITECTURAL PLAN (BASIS) {REV} FINAL  -  1:100  -  DIMENSIONS IN METRES", tcx, v_max + 1.9, 0.25)
    tw, th = 17.0, 6.0
    bx1, by0 = fx1 - m, fy0 + m
    bx0, by1 = bx1 - tw, by0 + th
    msp.add_lwpolyline([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], close=True, dxfattribs={"layer": "A-SHEET"})
    rows = [
        (fa("شرکت آهن بتن زاگرس - سهامی خاص"), 0.40, "FARSI"),
        (fa("پروژه: مرآژ ۳ - Merage3"), 0.40, "FARSI"),
        (fa("عنوان: پلان معماری طبقه ی تیپ - ملاک نهایی - ") + REV, 0.40, "FARSI"),
        (fa("مهندس محاسب: رحمت الله شیرزایی"), 0.40, "FARSI"),
        (fa("مقیاس: 1:100      واحد: متر      تاریخ: 1405/07/30"), 0.30, "FARSI"),
        (f"SOURCE: arch/memary500_Model_600_BASIS.pdf  |  K = {K:.2f} pt/m  |  {REV}: BOSS DECISIONS 2026-10-22/23", 0.20, "LATIN"),
    ]
    rh = th / len(rows)
    for k, (s, hh, st) in enumerate(rows):
        yy = by1 - (k + 0.5) * rh
        if k:
            msp.add_line((bx0, by1 - k * rh), (bx1, by1 - k * rh), dxfattribs={"layer": "A-SHEET"})
        text(s, (bx0 + bx1) / 2, yy, hh, style=st, width=1.0 if st == "FARSI" else 0.85)

    # door / window schedule (heights above finished floor, typical storey h=2.90; ground h=3.50)
    h_typ = 2.90
    head_beam = h_typ - BEAM - FIN        # 2.32 under edge beam
    head_slab = h_typ - SLAB - FIN        # 2.51 under slab
    sched = [
        ("TAG", "TYPE", "W", "SILL", "HEAD", "WHERE / NOTE"),
        ("WN1", "WINDOW", "3.50", f"{SILL:.2f}", f"{head_beam:.2f}", "front facade B-C, to u/s of beam B11; GUARD G1"),
        ("WN2", "WINDOW", "1.20", f"{SILL:.2f}", f"{head_beam:.2f}", "axis 4 A-B (behind elevator), to u/s of B38; NO guard (opens to balcony)"),
        ("G1", "STEEL GUARD", "=win", f"{SILL:.2f}", f"{GUARD:.2f}**", "on WN1 only, upper floors (Story1-3); not at ground floor; not on WN2"),
        ("DW1", "DOOR-WINDOW", "1.69", f"{SILL_BAL:.2f}", f"{head_beam:.2f}", "axis 4 B-C to rear balcony, to u/s of beam B39"),
        ("DS1", "STEEL DOOR", "1.45", f"{-FIN:.2f}", f"{head_slab:.2f}", "front terrace, from concrete slab to u/s of slab"),
        ("D1", "DOOR", "0.90", "0.00", f"{DOOR_HEAD:.2f}*", "rooms 4.80, 3.10, 3.15 (x3)"),
        ("D2", "DOOR", "0.85", "0.00", f"{DOOR_HEAD:.2f}*", "WC-2"),
        ("D3", "DOOR", "0.70", "0.00", f"{DOOR_HEAD:.2f}*", "WC-1; small rear balcony"),
        ("D4", "DOOR", "0.60", "0.00", f"{DOOR_HEAD:.2f}*", "service lobby"),
        ("DE1", "ENTRY DOOR", "0.90", "0.00", f"{DOOR_HEAD:.2f}*", "unit entry from the stair floor landing, wall W24, opens into the unit"),
        ("DL1", "LIFT DOOR", f"{LIFT_DOOR[0]:.2f}", "0.00", f"{LIFT_DOOR[1]:.2f}", "elevator, to the stair floor landing, wall W19, telescopic"),
    ]
    sx0, sy0 = fx0 + m + 0.6, -4.6
    colx = [0.0, 1.2, 3.4, 4.3, 5.2, 6.3]
    text(fa("جدول در و پنجره - ") + REV, sx0 + 4.0, sy0 + 0.45, 0.30, style="FARSI", width=1.0)
    for k, row in enumerate(sched):
        yy = sy0 - k * 0.36
        for cx, s in zip(colx, row):
            text(s, sx0 + cx, yy, 0.17 if k else 0.18, align=TA.MIDDLE_LEFT, width=0.85)
        msp.add_line((sx0 - 0.1, yy - 0.18), (sx0 + 13.0, yy - 0.18), dxfattribs={"layer": "A-TEXT"})
    yy = sy0 - len(sched) * 0.36
    for s in ["Heights in m above finished floor (FFL), typical storey h=2.90: u/s beam = FFL+2.32, u/s slab = FFL+2.51;",
              "ground storey h=3.50: u/s beam = FFL+2.92, u/s slab = FFL+3.11.  Slab 0.31, beams 0.50 (ETABS); floor finish 0.08.",
              "* door heads 2.10.  ** guard height 1.10 (check with the printed text of Mobhas 4)."]:
        text(s, sx0, yy, 0.15, align=TA.MIDDLE_LEFT, width=0.85)
        yy -= 0.30
    notes = [
        "NOTES:",
        "1. Redrawn from the vector PDF (all lines), scale from its dimension texts. Rev.1 to Rev.6 = boss decisions 2026-10-22/23.",
        "FA2",
        "3. Axis 5 (cantilever edge beam) = axis 4 + 1.20; no column in the PDF.",
        "4. Corridor / stair wall W24 15 cm: stair face X=2.25 (flights kept 1.10), on beam B32; corridor 1.56, 1.36 at columns B/2, B/3.",
        "5. Front terrace: no wall on B10, steel railing h=1.10 above FFL, recessed wall W22 on slab F1 with steel door DS1.",
        "6. Rear balcony open to the rear only: W4 (edge) and W6 (divider) = parapets h=1.10; W1a, W2a = full walls (boundary).",
        "7. Axis-4 wall W5 = rear external wall (DW1, D3, WN2 external openings, insulation per Mobhas 19).",
        "8. Steel guard G1 to FFL+1.10 on WN1 only (upper floors); WN2 has no guard.",
        "9. Lift door DL1 1.20 x 2.00 to the stair floor landing (no door symbol). Unit entry DE1 0.90 in W24 from the floor landing.",
        "10. Stair: flights 1.10 + well 0.10 + 1.10 against the A wall; floor landing axis-3 side (UP B side, DN A side); W21 flush with columns.",
        f"11. {REV} FINAL - architectural basis plan.",
    ]
    ny = yy - 0.10
    for k, s in enumerate(notes):
        if s == "FA2":
            t2 = "2. Axis 4 at 18.81 and column C19 at X=2.507 as in the architectural basis plan:"
            text(t2, sx0, ny - k * 0.30, 0.17, align=TA.MIDDLE_LEFT, width=0.85)
            text(fa("مدل ETABS باید با این هماهنگ شود"), sx0 + 8.6, ny - k * 0.30, 0.20, style="FARSI",
                 align=TA.MIDDLE_LEFT, width=1.0)
        else:
            text(s, sx0, ny - k * 0.30, 0.17, align=TA.MIDDLE_LEFT, width=0.85)
    # shift notes 3.. down by half a row so the Persian note 2 has its own line
    doc.set_modelspace_vport(height=31, center=((fx0 + fx1) / 2, (fy0 + fy1) / 2))

    # ---------------- wall table
    beams = []
    g = json.load(open(GEOM, encoding="utf-8"))
    for f in g["frames"]:
        if f["kind"] != "Column" and f["story"] == "Story1":
            beams.append((f["label"], f["i"][0] / 1000, f["i"][1] / 1000, f["j"][0] / 1000, f["j"][1] / 1000))
    slabs = {a["label"]: (a["pts"], a.get("angle", 0)) for a in g["areas"] if a["story"] == "Story1"}
    stories = dict(g["stories"])
    storeys = {"ground (Base->Story1)": (stories["Story1"] - stories["Base"]) / 1000,
               "typical (Story1..3 -> next)": (stories["Story2"] - stories["Story1"]) / 1000}

    walls = []
    defs = []
    for wid, o, f1, f2, a, b, note in WALLS:
        t = abs(f2 - f1) / K
        if o == "H":
            line = ("Y", etabs(0, (f1 + f2) / 2)[0], *sorted([etabs(a, 0)[1], etabs(b, 0)[1]]))
        else:
            line = ("X", etabs((f1 + f2) / 2, 0)[1], *sorted([etabs(0, a)[0], etabs(0, b)[0]]))
        defs.append((wid, line, t, note))
    for wid, d_, ln, a, b, t, note in WALLS_M:
        defs.append((wid, (d_, ln, a, b), t, note))

    def opening_width(wid, kind, a, b):
        if kind == "lift_door":
            return LIFT_DOOR[0]
        if wid == "W3a":
            return FRONT_WIN[1] - FRONT_WIN[0]
        if wid in ("W22", "W24"):
            return b - a
        return abs(b - a) / K

    for wid, line, t, note in defs:
        tcm = int(round(t * 20)) * 5
        L = line[3] - line[2]
        sup, off = [], None
        for lab, x1, y1, x2, y2 in beams:
            if line[0] == "Y" and abs(x1 - x2) < 1e-6 and abs(x1 - line[1]) <= 0.30:
                lo, hi = sorted([y1, y2])
                if hi > line[2] + 0.05 and lo < line[3] - 0.05:
                    sup.append(lab); off = line[1] - x1
            if line[0] == "X" and abs(y1 - y2) < 1e-6 and abs(y1 - line[1]) <= 0.30:
                lo, hi = sorted([x1, x2])
                if hi > line[2] + 0.05 and lo < line[3] - 0.05:
                    sup.append(lab); off = line[1] - y1
        on_beam = bool(sup)
        # slab panel + joist direction (angle 90 -> joists along Y, else along X)
        panel, joist = None, None
        if not on_beam:
            mxp = (line[2] + line[3]) / 2
            px, py = (line[1], mxp) if line[0] == "Y" else (mxp, line[1])
            for lab, (pts, ang) in slabs.items():
                xs_ = [p[0] / 1000 for p in pts]; ys_ = [p[1] / 1000 for p in pts]
                if min(xs_) - 0.3 <= px <= max(xs_) + 0.3 and min(ys_) - 0.05 <= py <= max(ys_) + 0.05:
                    panel = lab
                    jdir = "Y" if abs(ang - 90) < 1 else "X"
                    joist = "PARALLEL" if jdir == line[0] else "perpendicular"
                    break
        ops = [o_ for o_ in OPENINGS if o_[1] == wid]
        per = {}
        for sname, h in storeys.items():
            H = h - (BEAM if on_beam else SLAB)
            if wid in PARAPET_WALLS:
                H = FIN + PARAPET          # Rev.2: parapet 1.10 above FFL
            olist, Aop = [], 0.0
            for tg, _, kind, a, b in ops:
                w = opening_width(wid, kind, a, b)
                if kind == "window_full":
                    bot, top = FIN + SILL, H
                elif kind == "door_window":
                    bot, top = FIN + SILL_BAL, H
                elif kind == "lift_door":
                    w = LIFT_DOOR[0]
                    bot, top = 0.0, min(H, FIN + LIFT_DOOR[1])
                elif kind == "steel_door":
                    bot, top = 0.0, H
                else:
                    bot, top = 0.0, min(H, FIN + DOOR_HEAD)
                hh = top - bot
                olist.append(dict(tag=tg, kind=kind, width=round(w, 3), bottom=round(bot, 3), top=round(top, 3),
                                  height=round(hh, 3), area=round(w * hh, 3)))
                Aop += w * hh
            gross = L * H
            per[sname] = dict(H_wall=round(H, 3), gross_area=round(gross, 3), openings=olist,
                              opening_area=round(Aop, 3), net_area=round(gross - Aop, 3),
                              H_equiv=round((gross - Aop) / L, 3) if L > 0 else 0)
        walls.append(dict(id=wid, dir=line[0], line=round(line[1], 3), frm=round(line[2], 3), to=round(line[3], 3),
                          length=round(L, 3), thick_cm=tcm, on=("beam " + "+".join(sup)) if on_beam else f"slab {panel}",
                          joists=joist, offset=None if off is None else round(off, 3), note=note, storeys=per))
    # railing on B10 (proposed)
    walls.append(dict(id="R1", dir="X", line=-0.20, frm=0.25, to=2.10, length=1.85, thick_cm=0, on="beam B10",
                      joists=None, offset=-0.20, note="terrace steel railing h=1.10 above FFL (~0.3-0.5 kN/m)",
                      storeys={}))

    # totals per storey type: by support (beam/slab) and thickness
    totals = {}
    for sname in storeys:
        tt = {}
        for w in walls:
            if not w["storeys"]:
                continue
            k = ("beam" if w["on"].startswith("beam") else "slab", w["thick_cm"])
            s = w["storeys"][sname]
            e = tt.setdefault(f"{k[0]}_{k[1]}", dict(length=0.0, gross_area=0.0, opening_area=0.0, net_area=0.0))
            e["length"] += w["length"]; e["gross_area"] += s["gross_area"]
            e["opening_area"] += s["opening_area"]; e["net_area"] += s["net_area"]
        totals[sname] = {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in sorted(tt.items())}

    tmp = tempfile.mkdtemp(prefix="m3_basis_")
    dxf = os.path.join(tmp, "Merage3_arch_plan_BASIS.dxf")
    doc.saveas(dxf)
    counts = {ln: len(msp.query(f'*[layer=="{ln}"]')) for ln in LAYERS}
    res = dict(rev=REV, K_pt_per_m=K, K_interval=[klo, khi], paper_scale_of_pdf=f"1:{1000 / (K * 25.4 / 72):.2f}",
               origin_pt=[X0, Y0], axes_Y=AX_Y, axes_X=AX_X, columns_etabs=col_e,
               outline=dict(length=u_max - u_min, width=v_max - v_min),
               heights=dict(slab=SLAB, beam=BEAM, floor_finish=FIN, parapet=PARAPET, window_guard_check_Mobhas4=GUARD, lift_door=LIFT_DOOR, lift_door_X=LIFT_DOOR_X, parapet_walls=PARAPET_WALLS, sill=SILL, sill_balcony=SILL_BAL,
                            door_head=DOOR_HEAD, storeys=storeys),
               dims=dim_check, walls=walls, totals=totals, layer_counts=counts, dxf=dxf)
    res["doors_rev6"] = [dict(tag=t, hinge_XY=[hx, hy], closes_towards=list(c), opens_towards=list(o), width=w, note=n)
                         for t, hx, hy, c, o, w, n in DOORS]
    json.dump(res, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(res, open(OUT_JSON_ARCH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(dict(K=K, dims=dim_check, totals=totals, counts=counts), ensure_ascii=False, indent=1))
    if "--dxf-only" in sys.argv:
        return
    scr = os.path.join(tmp, "save.scr")
    with open(scr, "w", encoding="utf-8") as f:
        f.write(f'_.FILEDIA 0\n_.ZOOM _E\n_.SAVEAS 2018 "{OUT_DWG}"\n')
    if os.path.exists(OUT_DWG):
        os.remove(OUT_DWG)
    r = subprocess.run([ACCORE, "/i", dxf, "/s", scr, "/l", "en-US"], capture_output=True, timeout=300)
    if not os.path.exists(OUT_DWG):
        print(r.stdout.decode("utf-16-le", errors="ignore")[-2000:])
        raise SystemExit("DWG not written")
    print("DWG:", OUT_DWG, os.path.getsize(OUT_DWG))


main()
