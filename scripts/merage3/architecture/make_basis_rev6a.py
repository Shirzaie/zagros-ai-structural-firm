# -*- coding: utf-8 -*-
"""Merage3 architectural BASIS plan Rev.6a (task 37, boss decision 2026-10-23).

Rev.6a = Rev.6 FINAL + grid B' (X = 2.500) + column C19 centre moved from X = 2.507 to 2.500 (coordination 55,
ETABS Rev5 T33). Nothing else changes; Rev.6 drawing style (layers A-*, monochrome.ctb) is kept.
The Rev.6 files in arch/ are NOT touched: the Rev.6 geometry is regenerated in a temp folder from the unchanged
copy of its generator (rev6_source.py) and written to NEW files:

    arch/Merage3_arch_plan_BASIS_Rev6a.dwg / .pdf / _geometry.json

    python make_basis_rev6a.py
"""
import json
import os
import re
import subprocess
import sys

import ezdxf
import pymupdf
from ezdxf import bbox
from ezdxf.enums import TextEntityAlignment as TA

from rev6_source import build_rev6, TMP

import os; sys.path.insert(0, os.environ.get("ZAGROS_AUTOCAD_TOOLS") or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'autocad'))  # shared AutoCAD helpers in scripts/autocad
from plot_pdf import plot  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.abspath(os.path.join(HERE, "..", "..", "arch"))
OUT = os.path.join(ARCH, "Merage3_arch_plan_BASIS_Rev6a")
ACCORE = r"C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe"
A3 = "ISO full bleed A3 (420.00 x 297.00 MM)"
REV = "Rev.6a"
C19_X, C19_OLD = 2.500, 2.507030485295048
B_X = 2.3485772717135847


def fa(text):
    text = text.replace("\u200c", " ")
    return re.sub("ی(?=[ؠ-يپ-ۓ])", "ي", text).replace("ی", "ى")


def text(msp, s, u, v, h, style="LATIN", align=TA.MIDDLE_CENTER, width=0.9):
    t = msp.add_text(s, height=h, dxfattribs={"layer": "A-TEXT", "style": style, "width": width})
    t.set_placement((u, v), align=align)
    return t


def main():
    dxf6, geom6 = build_rev6()
    doc = ezdxf.readfile(dxf6)
    msp = doc.modelspace()

    # 1. C19: 2.507 -> 2.500 (outline + fill), as in Rev.7 A-102 / ETABS Rev5
    moved = 0
    for e in list(msp.query('*[layer=="A-COLUMN"]')):
        b = bbox.extents([e])
        if b.has_data and b.extmin.x > -19.10 and b.extmax.x < -18.50 and b.extmin.y > 2.20 and b.extmax.y < 2.80:
            e.translate(0, C19_X - C19_OLD, 0)
            moved += 1
    assert moved >= 2, moved

    # 2. grid B' (X = 2.50) from axis 3 to the rear, bubble at the rear end (B is only 0.15 away)
    u_min, R = -20.254, 0.40
    u3 = -13.503237097792388
    ax = next(e for e in msp.query('LINE[layer=="A-AXIS"]'))          # same linetype / colour as the other grid lines
    msp.add_line((u3 + 0.8, C19_X), (u_min - 1.0, C19_X),
                 dxfattribs={"layer": "A-AXIS", **{k: ax.dxf.get(k) for k in ("linetype", "color", "ltscale") if ax.dxf.hasattr(k)}})
    msp.add_circle((u_min - 1.0 - R, C19_X), R, dxfattribs={"layer": "A-AXIS", "linetype": "CONTINUOUS"})
    t = msp.add_text("B'", height=0.30, dxfattribs={"layer": "A-AXIS", "style": "LATIN"})
    t.set_placement((u_min - 1.0 - R, C19_X), align=TA.MIDDLE_CENTER)
    d = msp.add_linear_dim(base=(u_min - 0.5, B_X), p1=(u_min - 0.5, B_X), p2=(u_min - 0.5, C19_X), angle=90,
                           dimstyle="A100", text="0.15", dxfattribs={"layer": "A-DIM"})
    d.render()
    t = msp.add_text("B' = 2.50 (C19)", height=0.10, dxfattribs={"layer": "A-AXIS", "style": "LATIN"})
    t.set_placement((u_min - 1.0 - R, C19_X - 0.75), align=TA.MIDDLE_CENTER)

    # 3. texts: revision, date, notes 2 and 11
    kill = []
    for e in msp.query("TEXT"):
        s = e.dxf.text
        if s == fa("مدل ETABS باید با این هماهنگ شود"):
            kill.append(e)
        elif s.startswith("2. Axis 4 at 18.81 and column C19"):
            e.dxf.text = ("2. Axis 4 at 18.81; column C19 at X=2.500 on grid B' = 2.50 (Rev.6a, boss 2026-10-23; "
                          "was 2.507) = ETABS Rev5.")
        elif s.startswith("11. Rev.6 FINAL"):
            e.dxf.text = "11. Rev.6a FINAL - architectural basis plan = Rev.6 + grid B' 2.50 + C19 at 2.500 (coordination 55)."
        elif s.startswith("1. Redrawn from the vector PDF"):
            pass                                     # history note "Rev.1 to Rev.6" stays
        elif s.startswith("SOURCE: arch/"):
            e.dxf.text = s.replace("Rev.6: BOSS DECISIONS 2026-10-22/23", "Rev.6a: BOSS DECISIONS 2026-10-22/23 + C19/B' 2026-10-23")
        elif "1405/07/30" in s:
            e.dxf.text = s.replace("1405/07/30", "1405/08/01")
        elif re.search(r"Rev\.6\b", s):
            e.dxf.text = re.sub(r"Rev\.6\b", REV, s)
    for e in kill:
        msp.delete_entity(e)

    # sheet window = outer A-SHEET frame (largest polyline)
    frames = [e for e in msp.query('LWPOLYLINE[layer=="A-SHEET"]')]
    ext = max((bbox.extents([e]) for e in frames), key=lambda b: b.size.x)
    win = (round(ext.extmin.x, 3), round(ext.extmin.y, 3), round(ext.extmax.x, 3), round(ext.extmax.y, 3))

    dxf = os.path.join(TMP, "Merage3_arch_plan_BASIS_Rev6a.dxf")
    doc.saveas(dxf)
    dwg = OUT + ".dwg"
    scr = os.path.join(TMP, "save6a.scr")
    with open(scr, "w", encoding="utf-8") as f:
        f.write(f'_.FILEDIA 0\n_.ZOOM _E\n_.SAVEAS 2018 "{dwg}"\n')
    if os.path.exists(dwg):
        os.replace(dwg, OUT + "_prev.dwg")
    subprocess.run([ACCORE, "/i", dxf, "/s", scr, "/l", "en-US"], capture_output=True, timeout=300)
    assert os.path.exists(dwg), "DWG not written"
    ok, pdf, log, rc = plot(dwg, OUT + ".pdf", scale="10:1", paper=A3, window=win, ctb="monochrome.ctb")
    print("PDF", ok, rc, pdf)
    s2 = os.path.splitext(pdf)[0] + "_plot.scr"
    if os.path.exists(s2):
        os.replace(s2, os.path.join(TMP, os.path.basename(s2)))
    pymupdf.open(pdf)[0].get_pixmap(dpi=110).save(f"{TMP}/rev6a.png")
    pymupdf.open(pdf)[0].get_pixmap(dpi=250, clip=pymupdf.Rect(0, 600, 640, 842)).save(f"{TMP}/rev6a_notes.png")
    pymupdf.open(pdf)[0].get_pixmap(dpi=250, clip=pymupdf.Rect(180, 260, 420, 470)).save(f"{TMP}/rev6a_c19.png")

    # geometry json: Rev.6 + C19 / grid B'
    g = json.load(open(geom6, encoding="utf-8"))
    g["rev"] = REV
    g["columns_etabs"] = [[C19_X, y] if abs(x - C19_OLD) < 0.01 else [x, y] for x, y in g["columns_etabs"]]
    g["axes_X"]["B'"] = C19_X
    g["dxf"] = dxf
    g["rev6a_change"] = ("Rev.6a (task 37, boss 2026-10-23): grid B' = 2.500 added and C19 moved 7 mm from 2.507 to 2.500 "
                         "(= ETABS Rev5). Wall table / areas unchanged from Rev.6 (7 mm effect on W5a/W5c/W18 neglected).")
    json.dump(g, open(OUT + "_geometry.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("window", win, "C19 entities moved", moved)


if __name__ == "__main__":
    main()
