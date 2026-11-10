# -*- coding: utf-8 -*-
"""Task 59: the API CSV export has no title and units rows; the ETABS window export has both.
abz_export.py exported in kN, m, C (SetPresentUnits 6), so this writes those units, as ETABS does, into a copy of each table (export_gui/)."""
import os, csv
HERE = os.path.dirname(os.path.abspath(__file__))
SRC, DST = os.path.join(HERE, "export"), os.path.join(HERE, "export_gui")
U = {"Station": "m", "Elem Station": "m", "P": "kN", "V2": "kN", "V3": "kN", "T": "kN-m", "M2": "kN-m", "M3": "kN-m",
     "FX": "kN", "FY": "kN", "FZ": "kN", "MX": "kN-m", "MY": "kN-m", "MZ": "kN-m", "X": "m", "Y": "m", "Z": "m",
     "AsMinTop": "m²", "AsTop": "m²", "AsMinBot": "m²", "AsBot": "m²", "VRebar": "m²/m", "TLngRebar": "m²", "TTrnRebar": "m²/m",
     "AsMin": "m²", "As": "m²", "Mid Bar As": "m²", "CornerBarAs": "m²", "VMajRebar": "m²/m", "VMinRebar": "m²/m"}
os.makedirs(DST, exist_ok=True)
for f in os.listdir(SRC):
    if not f.endswith(".csv"):
        continue
    rows = list(csv.reader(open(os.path.join(SRC, f), encoding="utf-8-sig")))
    title = "TABLE: " + f[:-4].replace("_ACI_318-19", " - ACI 318-19").replace("_", " ").replace("Element Forces ", "Element Forces - ")
    out = [[title], rows[0], [U.get(h, "") for h in rows[0]]] + rows[1:]
    csv.writer(open(os.path.join(DST, f), "w", encoding="utf-8", newline="")).writerows(out)
    print(f, len(rows) - 1, "rows")
for f in os.listdir(SRC):
    if not f.endswith(".csv"):
        import shutil; shutil.copy2(os.path.join(SRC, f), os.path.join(DST, f))
