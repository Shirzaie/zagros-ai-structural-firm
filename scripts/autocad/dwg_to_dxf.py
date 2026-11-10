# -*- coding: utf-8 -*-
"""Convert a DWG to DXF (R2018) with accoreconsole:  python dwg_to_dxf.py in.dwg out.dxf
Work on a COPY of any reference drawing; the source is only opened, never saved."""
import os, subprocess, sys
ACCORE = r"C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe"
def main():
    src, out = map(os.path.abspath, sys.argv[1:3])
    scr = os.path.splitext(out)[0] + "_todxf.scr"
    with open(scr, "w", encoding="utf-8-sig") as f:
        f.write(f'_.FILEDIA 0\n_.SAVEAS _DXF _V 2018 16 "{out}"\n')
    if os.path.exists(out): os.remove(out)
    p = subprocess.run([ACCORE, "/i", src, "/s", scr, "/l", "en-US"], stdin=subprocess.DEVNULL, capture_output=True, timeout=300)
    print("OK" if os.path.exists(out) else (p.stdout or b"").decode("utf-16-le", "ignore")[-2000:], out)
main()
