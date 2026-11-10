# -*- coding: utf-8 -*-
"""Plot the two Rev.7 sheets (model-space windows, A3 1:100, Zagros_ARCH_Rev7.ctb) to PDF, merge them,
render PNGs for visual checking and list the plotted line widths (pt -> mm).

    python plot_rev7.py
"""
import collections
import os
import sys

import pymupdf

import os; sys.path.insert(0, os.environ.get("ZAGROS_AUTOCAD_TOOLS") or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'autocad'))  # shared AutoCAD helpers in scripts/autocad
from plot_pdf import plot  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.abspath(os.path.join(HERE, "..", "..", "arch"))
DWG = os.path.join(ARCH, "Merage3_arch_Rev7.dwg")
A3 = "ISO full bleed A3 (420.00 x 297.00 MM)"
SHEETS = {"A-101_ground_parking": (-74.5, -15.2, -32.5, 14.5), "A-102_typical_F1-F3": (-29.5, -15.2, 12.5, 14.5)}
PNG = "C:/ZagrosTemp/arch7"


def main():
    pdfs = []
    for name, win in SHEETS.items():
        pdf = os.path.join(ARCH, f"Merage3_arch_Rev7_{name}.pdf")
        ok, pdf, log, rc = plot(DWG, pdf, scale="10:1", paper=A3, window=win, ctb="Zagros_ARCH_Rev7.ctb")
        print(name, "OK" if ok else "FAILED", rc)
        if not ok:
            print(log[-2000:])
            continue
        pdfs.append(pdf)
        scr = os.path.splitext(pdf)[0] + "_plot.scr"
        if os.path.exists(scr):
            os.replace(scr, os.path.join(PNG, os.path.basename(scr)))
    out = pymupdf.open()
    for p in pdfs:
        out.insert_pdf(pymupdf.open(p))
    merged = os.path.join(ARCH, "Merage3_arch_Rev7.pdf")
    out.save(merged)
    for i, page in enumerate(pymupdf.open(merged)):
        page.get_pixmap(dpi=110).save(f"{PNG}/rev7_p{i + 1}.png")
        page.get_pixmap(dpi=300, clip=pymupdf.Rect(250, 180, 760, 450)).save(f"{PNG}/rev7_p{i + 1}_zoom.png")
        w = collections.Counter(round((d["width"] or 0) * 25.4 / 72, 3) for d in page.get_drawings())
        print(f"page {i + 1}: plotted widths mm -> count", sorted(w.items()))
    print("merged:", merged)


if __name__ == "__main__":
    main()
