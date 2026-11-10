# -*- coding: utf-8 -*-
"""Plot Merage3_struct_Rev1.dwg (A3 1:100, Zagros_ARCH_Rev7.ctb) -> one PDF per sheet + merged struct/Merage3_struct_Rev1.pdf;
AutoCAD lock Merage3/work/_autocad.lock around each accoreconsole run."""
import json, os, sys, time
import pymupdf
import os; sys.path.insert(0, os.environ.get("ZAGROS_AUTOCAD_TOOLS") or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'autocad'))  # shared AutoCAD helpers in scripts/autocad
from plot_pdf import plot  # noqa: E402
from make_struct_Rev1 import acquire, release, OUT_DWG, OUT_DIR, HERE  # noqa: E402
A3 = "ISO full bleed A3 (420.00 x 297.00 MM)"
PNG = "C:/ZagrosTemp/rev1"
NAMES = {"S-101": "grid_columns", "S-102": "typical_framing_F1-F3", "S-103": "roof_stairhouse_framing", "S-104": "beam_schedule_F1-F3",
         "S-105": "beam_schedule_roof_typical_details", "S-106": "cantilevers_hook_beam", "S-107": "stair_details"}
sheets = json.load(open(os.path.join(HERE, "rev1_sheets.json")))
pdfs = []
for name, win in sheets.items():
    pdf = os.path.join(OUT_DIR, "pdf", f"Merage3_struct_Rev1_{name}_{NAMES[name]}.pdf")
    os.makedirs(os.path.dirname(pdf), exist_ok=True)
    acquire()
    try:
        ok, pdf, log, rc = plot(OUT_DWG, pdf, scale="10:1", paper=A3, window=win, ctb="Zagros_ARCH_Rev7.ctb")
    finally:
        release()
    print(name, "OK" if ok else "FAILED", rc)
    if not ok:
        print(log[-1500:]); continue
    pdfs.append(pdf)
    scr = os.path.splitext(pdf)[0] + "_plot.scr"
    if os.path.exists(scr):
        os.replace(scr, os.path.join(PNG, os.path.basename(scr)))
out = pymupdf.open()
for p_ in pdfs:
    out.insert_pdf(pymupdf.open(p_))
merged = os.path.join(OUT_DIR, "Merage3_struct_Rev1.pdf")
out.save(merged)
for i, page in enumerate(pymupdf.open(merged)):
    page.get_pixmap(dpi=100).save(f"{PNG}/r{i + 1}.png")
print("merged:", merged, len(pdfs))
