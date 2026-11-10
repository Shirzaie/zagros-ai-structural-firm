# -*- coding: utf-8 -*-
"""Plot the model space of a DWG/DXF to PDF with AutoCAD 2026 accoreconsole (DWG To PDF.pc3).

    python plot_pdf.py <drawing.dwg> [out.pdf] [--scale 1:100 | --fit] [--paper "ISO full bleed A1 (841.00 x 594.00 MM)"]
                       [--window x0,y0,x1,y1]

Writes the script next to the PDF, runs accoreconsole, prints the console log tail and
returns exit code 0 only if the PDF was written. Unicode (Persian) paths are passed as is.
"""
import argparse
import os
import subprocess
import sys

ACCORE = r"C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe"
A1 = "ISO full bleed A1 (841.00 x 594.00 MM)"


def plot(dwg, pdf=None, scale="1:100", paper=A1, window=None, ctb="monochrome.ctb", timeout=180):
    dwg = os.path.abspath(dwg)
    pdf = os.path.abspath(pdf or os.path.splitext(dwg)[0] + ".pdf")
    scr = os.path.splitext(pdf)[0] + "_plot.scr"
    if window:
        x0, y0, x1, y1 = window
        area = f"_W\n{x0},{y0}\n{x1},{y1}"
    else:
        area = "_E"
    sc = "_F" if scale in (None, "fit") else scale.replace(":", "=")
    lines = [
        "_.FILEDIA 0", "_.CMDDIA 0", "_.BACKGROUNDPLOT 0", "_.ZOOM _E",
        "_.-PLOT", "_Y", "Model", "DWG To PDF.pc3", paper, "_M", "_L", "_N",
        area, sc, "_C", "_Y", ctb, "_Y", "_A", f'"{pdf}"', "_N", "_Y",
    ]
    with open(scr, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(lines) + "\n")
    if os.path.exists(pdf):
        os.remove(pdf)
    log, rc = run_accore(dwg, scr, timeout)
    ok = os.path.exists(pdf) and os.path.getsize(pdf) > 0
    return ok, pdf, log, rc


def run_accore(dwg, scr, timeout=600):
    """Run accoreconsole; on timeout kill it and still return the console output."""
    p = subprocess.Popen([ACCORE, "/i", dwg, "/s", scr, "/l", "en-US"], stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        out, _ = p.communicate(timeout=timeout)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        p.kill()
        out, _ = p.communicate()
        rc = "TIMEOUT"
    return (out or b"").decode("utf-16-le", errors="ignore").replace("\x00", ""), rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dwg")
    ap.add_argument("pdf", nargs="?")
    ap.add_argument("--scale", default="1:100")
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("--paper", default=A1)
    ap.add_argument("--window")
    a = ap.parse_args()
    win = [float(v) for v in a.window.split(",")] if a.window else None
    ok, pdf, log, rc = plot(a.dwg, a.pdf, "fit" if a.fit else a.scale, a.paper, win)
    sys.stdout.reconfigure(encoding="utf-8")
    print(log[-3000:])
    print("RETURN CODE:", rc)
    print("PDF OK:" if ok else "PDF MISSING:", pdf, os.path.getsize(pdf) if ok else "")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
