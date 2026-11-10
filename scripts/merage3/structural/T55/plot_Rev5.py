# -*- coding: utf-8 -*-
"""Plot Merage3_struct_Rev5.dwg: A0 sheets at 1:20 (50 mm per metre), Zagros_ARCH_Rev7.ctb -> struct/pdf_Rev5/*.pdf + merged PDF;
AutoCAD lock Merage3/work/_autocad.lock around each accoreconsole run."""
import json, os, sys
import pymupdf
import os; sys.path.insert(0, os.environ.get("ZAGROS_AUTOCAD_TOOLS") or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'autocad'))  # shared AutoCAD helpers in scripts/autocad
from plot_pdf import plot  # noqa: E402
from make_struct_Rev5 import acquire, release, OUT_DWG, OUT_DIR, HERE  # noqa: E402
A0 = "ISO full bleed A0 (841.00 x 1189.00 MM)"
PNG = "C:/ZagrosTemp/rev3"
sheets = json.load(open(os.path.join(HERE, "rev3_sheets.json")))
pdfs = []
for name, win in sheets.items():
    pdf = os.path.join(OUT_DIR, "pdf_Rev5", f"Merage3_struct_Rev5_{name}.pdf")
    os.makedirs(os.path.dirname(pdf), exist_ok=True)
    acquire()
    try:
        ok, pdf, log, rc = plot(OUT_DWG, pdf, scale="50:1", paper=A0, window=win, ctb="Zagros_ARCH_Rev7.ctb", timeout=300)
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
merged = os.path.join(OUT_DIR, "Merage3_struct_Rev5.pdf")
out.save(merged)
for i, page in enumerate(pymupdf.open(merged)):
    page.get_pixmap(dpi=40).save(f"{PNG}/r{i + 1}.png")
print("merged:", merged, len(pdfs))
