# -*- coding: utf-8 -*-
"""Plot the five Rev.13 sheets (T41) from their named paper-space LAYOUTS (A1, 1:1 paper = 1:50 drawing,
Zagros_ARCH_Rev7.ctb) to one PDF per sheet, merge them, render PNGs for visual checking and list the plotted
line widths (pt -> mm).

    python plot_rev13.py
"""
import collections
import json
import os
import sys

import pymupdf

import os; sys.path.insert(0, os.environ.get("ZAGROS_AUTOCAD_TOOLS") or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'autocad'))  # shared AutoCAD helpers in scripts/autocad
from plot_pdf import run_accore  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.abspath(os.path.join(HERE, "..", "..", "arch"))
DWG = os.path.join(ARCH, "Merage3_arch_Rev13.dwg")
A3 = "ISO full bleed A0 (1189.00 x 841.00 MM)"   # T51: 1:20, 4 A0 tiles per sheet
CTB = "Zagros_ARCH_Rev7.ctb"
SHEETS = [("A-101", "A-101_PARKING", "parking_ground"), ("A-102", "A-102_FLOOR-1", "floor1"),
          ("A-103", "A-103_FLOOR-2", "floor2"), ("A-104", "A-104_FLOOR-3", "floor3"), ("A-105", "A-105_ROOF", "roof"),
          ("A-106", "A-106_STAIR-HOUSE-ROOF", "stair_house_roof"),
          ("A-201", "A-201_SECTION-LONG", "section_long"), ("A-202", "A-202_SECTION-TRANS", "section_trans")]
PNG = "C:/ZagrosTemp/arch13"


def main():
    os.makedirs(PNG, exist_ok=True)
    pdfs = []
    lines = ["_.FILEDIA 0", "_.CMDDIA 0", "_.BACKGROUNDPLOT 0"]
    tiles = {}
    for no, layout, tag in SHEETS:
        tiles[no] = []
        for k in (1, 2, 3, 4):
            pdf = os.path.join(PNG, f"Merage3_arch_Rev13_{no}_{k}.pdf")
            if os.path.exists(pdf):
                os.remove(pdf)
            tiles[no].append(pdf)
            pdfs.append(pdf)
            lines += ["_.-PLOT", "_Y", f"{layout}-{k}", "DWG To PDF.pc3", A3, "_M", "_L", "_N", "_L", "1:1", "0,0",
                      "_Y", CTB, "_Y", "_N", "_N", "_N", f'"{pdf}"', "_N", "_Y"]
    scr = os.path.join(PNG, "plot13.scr")
    with open(scr, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(lines) + "\n")
    log, rc = run_accore(DWG, scr, 1800)
    open(os.path.join(HERE, "plot_rev13.log"), "w", encoding="utf-8").write(log)
    ok = [p for p in pdfs if os.path.exists(p) and os.path.getsize(p) > 0]
    print("plotted", len(ok), "of", len(pdfs), "rc", rc)
    if len(ok) != len(pdfs):
        print(log[-3000:])
        raise SystemExit(1)
    for no, layout, tag in SHEETS:                       # one PDF per sheet (4 A0 tiles)
        one = pymupdf.open()
        for p in tiles[no]:
            one.insert_pdf(pymupdf.open(p))
        one.save(os.path.join(ARCH, f"Merage3_arch_Rev13_{no}_{tag}.pdf"))
    out = pymupdf.open()
    for p in pdfs:
        out.insert_pdf(pymupdf.open(p))
    merged = os.path.join(ARCH, "Merage3_arch_Rev13.pdf")
    out.save(merged)
    print("sheets: 8 x 4 A0 tiles =", len(pdfs), "pages")
    return
    res = {}
    for i, page in enumerate(pymupdf.open(merged)):
        no = SHEETS[i][0]
        page.get_pixmap(dpi=55).save(f"{PNG}/rev13_{no}.png")
        w = collections.Counter(round((d["width"] or 0) * 25.4 / 72, 3) for d in page.get_drawings())
        res[no] = dict(size_mm=[round(page.rect.width * 25.4 / 72), round(page.rect.height * 25.4 / 72)],
                       widths=sorted(w.items()))
        print(no, res[no])
    doc = pymupdf.open(merged)
    zooms = {}   # T49: A1 sheets; visual checks done separately
    for nm, (pg, r) in zooms.items():
        doc[pg].get_pixmap(dpi=300, clip=pymupdf.Rect(*r)).save(f"{PNG}/rev13_{nm}.png")
    print("merged:", merged)


if __name__ == "__main__":
    main()
