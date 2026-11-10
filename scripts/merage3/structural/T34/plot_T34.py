# -*- coding: utf-8 -*-
"""Plot the T34 sheets (A3 1:100, Zagros_ARCH_Rev7.ctb) -> one PDF per sheet + merged PDF, PNGs for checking,
and the list of plotted line widths."""
import collections
import json
import os
import sys

import pymupdf

import os; sys.path.insert(0, os.environ.get("ZAGROS_AUTOCAD_TOOLS") or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'autocad'))  # shared AutoCAD helpers in scripts/autocad
from plot_pdf import plot  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))
DWG = os.path.join(OUT, "Merage3_struct_T34_draft.dwg")
A3 = "ISO full bleed A3 (420.00 x 297.00 MM)"
PNG = "C:/ZagrosTemp/t34"
NAMES = {"S-101": "grid_columns", "S-102": "typical_framing_F1-F3", "S-103": "roof_framing", "S-104": "beam_schedule_F1-F3",
         "S-105": "beam_schedule_roof_details"}


def main():
    sheets = json.load(open(os.path.join(HERE, "t34_sheets.json")))
    pdfs = []
    for name, win in sheets.items():
        pdf = os.path.join(HERE, "pdf", f"Merage3_struct_T34_{name}_{NAMES[name]}.pdf")
        os.makedirs(os.path.dirname(pdf), exist_ok=True)
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
    merged = os.path.join(OUT, "Merage3_struct_T34_draft.pdf")
    out.save(merged)
    for i, page in enumerate(pymupdf.open(merged)):
        page.get_pixmap(dpi=110).save(f"{PNG}/s{i + 1}.png")
        w = collections.Counter(round((d["width"] or 0) * 25.4 / 72, 3) for d in page.get_drawings())
        print(f"page {i + 1}: plotted widths mm -> count", sorted(w.items()))
    print("merged:", merged)


if __name__ == "__main__":
    main()
