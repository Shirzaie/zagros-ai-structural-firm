# -*- coding: utf-8 -*-
"""Column drawing (DRAFT) in the style of the boss's sample "شیرزایی (3).dwg":
column layout plan 1:100 + column schedule + column type elevations 1:50 / sections 1:20,
one A1 landscape sheet, model units cm, plotted 1 mm = 10 cm (1:100 sheet basis).

    python make_columns_dwg.py <geometry.json> <out.dwg> [rebar.json]

geometry.json: export of the ETABS model (etabs_export_geometry.py). Rebar is NOT taken from
section names (e.g. "C50X50/16T16" is a model assumption). Without a reviewed rebar.json every
rebar cell reads "منتظر طراحی".
rebar.json (optional, from the structural engineer): {"CT1": {"C50X50": {"long": "..", "tie_end": "..",
"tie_mid": ".."}, ...}, ...}
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import OrderedDict, defaultdict

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

ACCORE = r"C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe"
MM = 10.0                       # 1 mm on paper = 10 cm in the model (sheet basis 1:100)
SHEET_W, SHEET_H = 841, 594     # A1 landscape, paper mm
WAIT = "منتظر طراحی"

LAYERS = {   # name: (ACI colour, linetype, lineweight 1/100 mm)
    "S-AXIS": (1, "CENTER", 13),
    "S-COLUMN": (7, "CONTINUOUS", 35),
    "S-CONC": (7, "CONTINUOUS", 35),
    "S-BEAM": (8, "CONTINUOUS", 25),
    "S-FOUND": (8, "DASHED", 25),
    "S-DIM": (3, "CONTINUOUS", 13),
    "S-TEXT": (7, "CONTINUOUS", 18),
    "S-TITLE": (7, "CONTINUOUS", 35),
    "S-TABLE": (7, "CONTINUOUS", 25),
    "S-SHEET": (7, "CONTINUOUS", 50),
    "S-FRAME": (4, "CONTINUOUS", 0),
}


def fa(text):
    """Logical-order Persian for AutoCAD 2026: yeh fix + ZWNJ -> space (see Merage3/CLAUDE.md)."""
    text = text.replace("\u200c", " ")
    return re.sub("ی(?=[ؠ-يپ-ۓ])", "ي", text).replace("ی", "ى")


class Sheet:
    def __init__(self):
        self.doc = ezdxf.new("R2018", setup=True)
        d = self.doc
        d.units = ezdxf.units.CM
        d.header["$INSUNITS"] = 5
        d.header["$MEASUREMENT"] = 1
        d.header["$LTSCALE"] = 5.0
        d.header["$LWDISPLAY"] = 1
        for name, (color, lt, lw) in LAYERS.items():
            d.layers.add(name, color=color, linetype=lt, lineweight=lw)
        d.styles.add("LATIN", font="arial.ttf")
        d.styles.add("FARSI", font="tahoma.ttf")
        d.styles.add("ITAL", font="ariali.ttf")
        ds = d.dimstyles.new("S-DIM")
        ds.dxf.dimtxsty = "LATIN"
        ds.dxf.dimtxt = 1.8
        ds.dxf.dimasz = 1.2
        ds.dxf.dimtsz = 0.9          # oblique ticks, like the sample
        ds.dxf.dimexo = 1.0
        ds.dxf.dimexe = 1.0
        ds.dxf.dimgap = 0.6
        ds.dxf.dimscale = MM
        ds.dxf.dimtad = 1
        ds.dxf.dimtih = 0
        ds.dxf.dimtoh = 0
        ds.dxf.dimclrd = 3
        ds.dxf.dimclre = 3
        self.msp = d.modelspace()

    # paper-mm helpers --------------------------------------------------------------------------
    def text(self, s, x, y, h, layer="S-TEXT", align=TA.MIDDLE_CENTER, style="LATIN", rot=0.0, width=0.9):
        if style == "FARSI":
            s, width = fa(s), 1.0
        t = self.msp.add_text(s, height=h * MM, rotation=rot,
                              dxfattribs={"layer": layer, "style": style, "width": width})
        t.set_placement((x * MM, y * MM), align=align)
        return t

    def rect(self, x0, y0, x1, y1, layer, model=False):
        k = 1 if model else MM
        pts = [(x0 * k, y0 * k), (x1 * k, y0 * k), (x1 * k, y1 * k), (x0 * k, y1 * k)]
        return self.msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})

    def line(self, a, b, layer, model=False, **kw):
        k = 1 if model else MM
        return self.msp.add_line((a[0] * k, a[1] * k), (b[0] * k, b[1] * k), dxfattribs={"layer": layer, **kw})

    def solid(self, pts_model, layer, color=7):
        h = self.msp.add_hatch(color=color, dxfattribs={"layer": layer})
        h.paths.add_polyline_path(pts_model, is_closed=True)
        return h

    def dim(self, p1, p2, base, angle=0, lfac=0.01, dec=2):
        """Linear dimension, points in MODEL units; lfac converts model cm to the shown unit."""
        d = self.msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=angle, dimstyle="S-DIM",
                                    dxfattribs={"layer": "S-DIM"},
                                    override={"dimlfac": lfac, "dimdec": dec, "dimzin": 0 if dec else 8})
        d.render()

    def title(self, s_fa, scale_txt, cx, y, w=70):
        """Sample-style view title: Persian title, double underline, 'SC:1/100' under it."""
        self.text(s_fa, cx, y + 3.5, 4.0, style="FARSI", layer="S-TITLE")
        self.line((cx - w / 2, y), (cx + w / 2, y), "S-TITLE")
        self.line((cx - w / 2 - 3, y - 0.8), (cx + w / 2 - 3, y - 0.8), "S-TITLE")
        self.text(scale_txt, cx + w / 2 - 12, y - 3.5, 2.5, style="LATIN")


# ---------------------------------------------------------------------------------------------
def column_data(m):
    """Columns grouped into types by their section sequence over the stories."""
    stories = [s for s, _ in m["stories"]]
    elev = {s: z for s, z in m["stories"]}
    cols = defaultdict(dict)
    for f in m["frames"]:
        if f["kind"] == "Column":
            key = (f["label"], round(f["i"][0]), round(f["i"][1]))
            cols[key][f["story"]] = f["section"]
    types = OrderedDict()
    for key in sorted(cols, key=lambda k: (-len(cols[k]), int(k[0][1:]))):
        seq = tuple((s, cols[key][s].split("/")[0]) for s in stories if s in cols[key])
        types.setdefault(seq, []).append(key)
    named = OrderedDict()
    for n, (seq, members) in enumerate(types.items(), 1):
        named[f"CT{n}"] = {"seq": seq, "cols": sorted(members, key=lambda k: int(k[0][1:]))}
    return named, stories, elev


def dims_of(m, sec_short):
    for name, s in m["sections"].items():
        if name.split("/")[0] == sec_short:
            return s["width"] / 10.0, s["depth"] / 10.0   # cm
    raise KeyError(sec_short)


def story_groups(seq):
    """[(section, [stories])] for consecutive stories with the same section."""
    out = []
    for s, sec in seq:
        if out and out[-1][0] == sec:
            out[-1][1].append(s)
        else:
            out.append((sec, [s]))
    return out


# ---------------------------------------------------------------------------------------------
def draw_frame(S):
    """Sample-style frame: outer thin line, cyan band, inner double line."""
    S.rect(0, 0, SHEET_W, SHEET_H, "S-SHEET")
    S.rect(5, 5, SHEET_W - 5, SHEET_H - 5, "S-SHEET")
    outer = [(7 * MM, 7 * MM), ((SHEET_W - 7) * MM, 7 * MM), ((SHEET_W - 7) * MM, (SHEET_H - 7) * MM),
             (7 * MM, (SHEET_H - 7) * MM)]
    inner = [(11 * MM, 11 * MM), ((SHEET_W - 11) * MM, 11 * MM), ((SHEET_W - 11) * MM, (SHEET_H - 11) * MM),
             (11 * MM, (SHEET_H - 11) * MM)]
    h = S.msp.add_hatch(color=4, dxfattribs={"layer": "S-FRAME"})
    h.paths.add_polyline_path(outer, is_closed=True, flags=1)
    h.paths.add_polyline_path(inner, is_closed=True, flags=0)
    S.rect(13, 13, SHEET_W - 13, SHEET_H - 13, "S-SHEET")
    S.rect(15, 15, SHEET_W - 15, SHEET_H - 15, "S-SHEET")


def draw_plan(S, m, types, ox, oy):
    """Column layout plan 1:100; grid origin at paper (ox, oy)."""
    O = (ox * MM, oy * MM)
    gx = [g for g in m["grids"] if g["dir"] == "X"]
    gy = [g for g in m["grids"] if g["dir"] == "Y"]
    xs = [g["coord"] / 10 for g in gx]
    ys = [g["coord"] / 10 for g in gy]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    ext, R = 12 * MM, 3.2 * MM
    P = lambda x, y: (O[0] + x, O[1] + y)  # noqa: E731
    for g in gx:
        c = g["coord"] / 10
        a, b = P(c, y0 - ext / 2), P(c, y1 + ext)
        S.line(a, b, "S-AXIS", model=True)
        cen = (b[0], b[1] + R)
        S.msp.add_circle(cen, R, dxfattribs={"layer": "S-AXIS", "linetype": "CONTINUOUS"})
        S.msp.add_circle(cen, R * 0.82, dxfattribs={"layer": "S-AXIS", "linetype": "CONTINUOUS"})
        S.text(g["label"], cen[0] / MM, cen[1] / MM, 2.8, style="ITAL")
    for g in gy:
        c = g["coord"] / 10
        a, b = P(x0 - ext, c), P(x1 + ext / 2, c)
        S.line(a, b, "S-AXIS", model=True)
        cen = (a[0] - R, a[1])
        S.msp.add_circle(cen, R, dxfattribs={"layer": "S-AXIS", "linetype": "CONTINUOUS"})
        S.msp.add_circle(cen, R * 0.82, dxfattribs={"layer": "S-AXIS", "linetype": "CONTINUOUS"})
        S.text(g["label"], cen[0] / MM, cen[1] / MM, 2.8, style="ITAL")
    # dimension chains (m, 2 decimals) like the sample
    sx, sy = sorted(xs), sorted(ys)
    top1, top2 = y1 + ext * 0.45, y1 + ext * 0.8
    for a, b in zip(sx, sx[1:]):
        S.dim(P(a, y1), P(b, y1), (0, P(0, top1)[1]))
    S.dim(P(sx[0], y1), P(sx[-1], y1), (0, P(0, top2)[1]))
    l1, l2 = x0 - ext * 0.45, x0 - ext * 0.8
    for a, b in zip(sy, sy[1:]):
        S.dim(P(x0, a), P(x0, b), (P(l1, 0)[0], 0), angle=90)
    S.dim(P(x0, sy[0]), P(x0, sy[-1]), (P(l2, 0)[0], 0), angle=90)
    # columns at their lowest-story size (true size, solid), name + type on the text layer
    for tname, t in types.items():
        sec = t["seq"][0][1]
        w, d = dims_of(m, sec)
        for label, x, y in t["cols"]:
            cx, cy = x / 10, y / 10
            pts = [P(cx - d / 2, cy - w / 2), P(cx + d / 2, cy - w / 2), P(cx + d / 2, cy + w / 2),
                   P(cx - d / 2, cy + w / 2)]
            S.msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "S-COLUMN"})
            S.solid(pts, "S-COLUMN")
            tx, ty = P(cx + d / 2 + 25, cy + w / 2 + 25)
            S.text(label, tx / MM, ty / MM, 2.0, align=TA.BOTTOM_LEFT)
            S.text(f"({tname})", tx / MM, ty / MM - 0.6, 1.6, align=TA.TOP_LEFT)
    cx = ox + (x0 + x1) / 2 / MM
    S.title("پلان ستون گذاری", "SC:1/100", cx, oy + y0 / MM - 30)


def draw_schedule(S, m, types, x, ytop, rebar):
    """Column schedule (جدول ستون‌ها). Paper mm; table drawn right-to-left like a Persian table."""
    cols = [("نوع ستون", 18), ("ستون ها", 46), ("طبقه", 34), ("ابعاد (cm)", 20),
            ("آرماتور طولى", 30), ("خاموت ناحيه ويژه", 32), ("خاموت ميانى", 28)]
    W = sum(w for _, w in cols)
    rows = []
    for tname, t in types.items():
        for sec, sts in story_groups(t["seq"]):
            w, d = dims_of(m, sec)
            r = (rebar or {}).get(tname, {}).get(sec, {})
            rows.append([tname, ", ".join(c[0] for c in t["cols"]),
                         f"{sts[0]} - {sts[-1]}" if len(sts) > 1 else sts[0],
                         f"{w:.0f} x {d:.0f}", r.get("long", WAIT), r.get("tie_end", WAIT), r.get("tie_mid", WAIT)])
    hh, rh = 9, 8
    H = hh + rh * len(rows)
    S.text("جدول ستون ها", x + W / 2, ytop + 6, 4.0, style="FARSI", layer="S-TITLE")
    S.rect(x, ytop - H, x + W, ytop, "S-TABLE")
    S.line((x, ytop - hh), (x + W, ytop - hh), "S-TABLE")
    xr = x + W
    for k, (head, w) in enumerate(cols):
        xl = xr - w
        if k:
            S.line((xr, ytop), (xr, ytop - H), "S-TABLE")
        S.text(head, (xl + xr) / 2, ytop - hh / 2, 2.2, style="FARSI")
        for j, row in enumerate(rows):
            yy = ytop - hh - (j + 0.5) * rh
            v = row[k]
            if v == WAIT:
                S.text(v, (xl + xr) / 2, yy, 2.0, style="FARSI")
            else:
                hgt = 2.0 if len(v) * 1.1 < w else max(1.3, (w - 2) / len(v) / 0.55)
                S.text(v, (xl + xr) / 2, yy, hgt)
        xr = xl
    for j in range(1, len(rows)):
        S.line((x, ytop - hh - j * rh), (x + W, ytop - hh - j * rh), "S-TABLE")
    return ytop - H


def draw_type(S, m, tname, t, stories, elev, ex, ybase, sx):
    """Column type: elevation 1:50 centred at paper x=ex; sections 1:20 centred at paper x=sx."""
    k50, k20 = 2.0, 5.0                         # real cm -> model cm
    z0 = elev[stories[0]] / 10                  # base level (cm)
    Y = lambda z: ybase * MM + (z - z0) * k50   # noqa: E731
    X = ex * MM
    seq = t["seq"]
    beam_d = 50.0
    stub = 60.0                                  # beam stub length each side (real cm)
    prev_top = z0
    # foundation (schematic, size not designed yet)
    fw, fh = 160.0, 80.0
    S.rect(X - fw / 2 * k50, Y(z0 - fh), X + fw / 2 * k50, Y(z0), "S-FOUND", model=True)
    S.text("پی - منتظر طراحی", (X + fw / 2 * k50) / MM + 2, Y(z0 - fh / 2) / MM, 1.8,
           style="FARSI", align=TA.MIDDLE_LEFT)
    sections = []
    for n, (sec, sts) in enumerate(story_groups(seq), 1):
        w, d = dims_of(m, sec)
        zb = elev[stories[stories.index(sts[0]) - 1]] / 10
        zt = elev[sts[-1]] / 10
        S.rect(X - w / 2 * k50, Y(zb), X + w / 2 * k50, Y(zt - beam_d), "S-CONC", model=True)
        for s in sts:
            zs = elev[s] / 10
            # beam / slab stub with break lines
            for side in (-1, 1):
                xa, xb = X + side * w / 2 * k50, X + side * (w / 2 + stub) * k50
                S.rect(min(xa, xb), Y(zs - beam_d), max(xa, xb), Y(zs), "S-BEAM", model=True)
            S.rect(X - w / 2 * k50, Y(zs - beam_d), X + w / 2 * k50, Y(zs), "S-BEAM", model=True)
            # level mark on the right
            lx = X + (w / 2 + stub) * k50 + 4 * MM
            S.line((lx - 2 * MM, Y(zs)), (lx + 14 * MM, Y(zs)), "S-TEXT", model=True)
            S.msp.add_solid([(lx, Y(zs)), (lx - 1.2 * MM, Y(zs) + 1.6 * MM), (lx + 1.2 * MM, Y(zs) + 1.6 * MM)],
                            dxfattribs={"layer": "S-TEXT"})
            S.text(f"+{zs / 100:.2f}", lx / MM + 2, Y(zs) / MM + 0.8, 1.8, align=TA.BOTTOM_LEFT)
            S.text(s, lx / MM + 2, Y(zs) / MM - 0.8, 1.6, align=TA.TOP_LEFT)
        # clear-height dimension of the first story of the group (cm)
        # section cut mark at mid-height of the lowest story of the group
        zc = (zb + elev[sts[0]] / 10 - beam_d) / 2
        tag = f"{n}-{n}"
        for side in (-1, 1):
            xx = X + side * (w / 2 * k50 + 3 * MM)
            S.text(str(n), xx / MM, Y(zc) / MM + 2.2, 2.0)
            S.msp.add_solid([(xx - 1 * MM, Y(zc)), (xx + 1 * MM, Y(zc)), (xx, Y(zc) + 1.4 * MM)],
                            dxfattribs={"layer": "S-TEXT"})
        sections.append((tag, sec, w, d, Y(zc) / MM, sts))
        prev_top = zt
    # sections 1:20, sample style: dims on top and right, title "برش n-n" + scale under
    for tag, sec, w, d, ycen, sts in sections:
        hx, hy = d / 2 * k20 / MM, w / 2 * k20 / MM
        S.rect(sx - hx, ycen - hy, sx + hx, ycen + hy, "S-CONC")
        S.text(WAIT, sx, ycen + 1.5, 1.8, style="FARSI")
        S.text("آرماتور و خاموت", sx, ycen - 1.8, 1.5, style="FARSI")
        x0m, x1m = (sx - hx) * MM, (sx + hx) * MM
        y0m, y1m = (ycen - hy) * MM, (ycen + hy) * MM
        S.dim((x0m, y1m), (x1m, y1m), (0, y1m + 5 * MM), lfac=1 / k20, dec=0)
        S.dim((x1m, y0m), (x1m, y1m), (x1m + 5 * MM, 0), angle=90, lfac=1 / k20, dec=0)
        S.text(fa("برش ") + tag, sx, ycen - hy - 6, 2.8, style="FARSI")
        S.line((sx - 16, ycen - hy - 8.5), (sx + 16, ycen - hy - 8.5), "S-TITLE")
        S.text("SC:1/20", sx - 10, ycen - hy - 11, 1.8)
    # type title under the elevation (sample: big "C1" with underline) + member list
    ty = ybase - fh * k50 / MM - 14
    S.text(tname, ex, ty, 6.5, layer="S-TITLE")
    S.line((ex - 22, ty - 5), (ex + 22, ty - 5), "S-TITLE")
    S.line((ex - 22, ty - 6), (ex + 22, ty - 6), "S-TITLE")
    S.text("SC:1/50", ex + 14, ty - 8.5, 1.8)
    S.text(", ".join(c[0] for c in t["cols"]), ex, ty - 12, 2.0)


def title_block(S, x1, y0, w, h):
    x0 = x1 - w
    S.rect(x0, y0, x1, y0 + h, "S-SHEET")
    rows = [
        ("مهندس محاسب: رحمت الله شیرزایی", 4.0, "FARSI"),
        ("شرکت آهن بتن زاگرس - سهامی خاص", 3.2, "FARSI"),
        ("پروژه: مرآژ 3 - مینودشت، گلستان", 3.2, "FARSI"),
        ("عنوان نقشه: پلان ستون گذاری، جدول و جزئیات ستون ها", 3.2, "FARSI"),
        ("تاریخ: 1405/07/27", 2.6, "FARSI"),
        ("وضعیت: پیش نویس - برای اجرا نیست", 3.2, "FARSI"),
        ("SC: PLAN 1/100 - ELEV. 1/50 - SECT. 1/20 | ACI 318-19 | C25 | ETABS run 2026-10-19 | DRAFT", 2.2, "LATIN"),
    ]
    rh = h / len(rows)
    for k, (s, hp, st) in enumerate(rows):
        if k:
            S.line((x0, y0 + h - k * rh), (x1, y0 + h - k * rh), "S-SHEET")
        S.text(s, x0 + w / 2, y0 + h - (k + 0.5) * rh, hp, style=st)


def notes(S, x_right, ytop):
    lines = [
        "یادداشت ها - پیش نویس",
        "الف - ابعاد و جانمایی ستون ها از مدل ای تبس پروژه، اجرای 1405/07/27",
        "ب - آرماتور طولی و خاموت ها هنوز طراحی و تأیید نشده اند",
        "پ - عدد آرماتور در نام مقطع های مدل فقط فرض مدل است، نه آرماتور طراحی",
        "ت - طول ناحیه ویژه و فاصله خاموت ها بعد از طراحی تعیین می شود",
        "ث - ابعاد پی بعد از طراحی پی اضافه می شود",
        "ج - اندازه ها در پلان به متر و در برش ها به سانتی متر است",
    ]
    for k, s in enumerate(lines):
        S.text(s, x_right, ytop - k * 5.2, 2.6 if k == 0 else 2.2, style="FARSI", align=TA.MIDDLE_RIGHT)


def build(m, path, rebar=None):
    S = Sheet()
    types, stories, elev = column_data(m)
    draw_frame(S)
    draw_plan(S, m, types, ox=55, oy=330)
    yb = draw_schedule(S, m, types, x=155, ytop=560, rebar=rebar)
    notes(S, x_right=820, ytop=140)
    # column types: elevation + sections; spread across the right part of the sheet
    slots = [(330, 270), (540, 480)]
    for (tname, t), (ex, sx) in zip(types.items(), slots):
        draw_type(S, m, tname, t, stories, elev, ex, ybase=150, sx=sx)
    title_block(S, SHEET_W - 18, 18, 190, 70)
    S.doc.set_modelspace_vport(height=SHEET_H * MM * 1.05, center=(SHEET_W * MM / 2, SHEET_H * MM / 2))
    S.doc.saveas(path)
    return S.doc, types


def convert_to_dwg(dxf_path, dwg_path):
    scr = os.path.splitext(dxf_path)[0] + "_save.scr"
    with open(scr, "w", encoding="utf-8-sig") as f:
        f.write(f'_.FILEDIA 0\n_.ZOOM _E\n_.SAVEAS 2018 "{dwg_path}"\n')
    if os.path.exists(dwg_path):
        os.remove(dwg_path)
    p = subprocess.run([ACCORE, "/i", dxf_path, "/s", scr, "/l", "en-US"], stdin=subprocess.DEVNULL,
                       capture_output=True, timeout=300)
    if not os.path.exists(dwg_path):
        raise RuntimeError("DWG not written:\n" + (p.stdout or b"").decode("utf-16-le", "ignore")[-2000:])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    src, out = sys.argv[1], os.path.abspath(sys.argv[2])
    rebar = None
    if len(sys.argv) > 3:
        with open(sys.argv[3], encoding="utf-8") as f:
            rebar = json.load(f)
    with open(src, encoding="utf-8") as f:
        m = json.load(f)
    dxf = os.path.join(tempfile.mkdtemp(prefix="cols_"), "columns.dxf")
    doc, types = build(m, dxf, rebar)
    for k, t in types.items():
        print(k, [c[0] for c in t["cols"]], t["seq"])
    convert_to_dwg(dxf, out)
    print("DWG:", out, os.path.getsize(out))


if __name__ == "__main__":
    main()
