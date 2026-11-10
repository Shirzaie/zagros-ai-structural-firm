# -*- coding: utf-8 -*-
"""Task 46: test on a TEMP copy how the accidental eccentricity 0.05 -> 0.0585 can be set in ETABS 19 (Rev6a untouched).
Lists tables with 'Eccentric'/'Seismic' in the name, then tries the Auto Seismic table edit (EccRatio only) and reads
the direction flags back."""
import sys, os, shutil
from r5_common import *
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
TD = r"C:\ZagrosTemp\r6b_test"; os.makedirs(TD, exist_ok=True)
TMP = os.path.join(TD, "ecc_test.EDB")
shutil.copy2(os.path.join(HERE, "Merage3_Rev6a.EDB"), TMP)
e = None
try:
    e, m = connect(TMP); m.SetModelIsLocked(False)
    db = m.DatabaseTables
    av = list(db.GetAvailableTables(0, [], [], [])[1])
    p("tables:", [t for t in av if "ccentric" in t or "Seismic" in t or "Diaphragm" in t])
    al = list(db.GetAllTables(0, [], [], [], [])[1]) if hasattr(db, "GetAllTables") else []
    p("all tables:", [t for t in al if "ccentric" in t or "Seismic" in t])
    key = "Load Pattern Definitions - Auto Seismic - User Coefficient"
    rr = db.GetTableForEditingArray(key, "")
    ver, fields, n, data = rr[0], list(rr[1]), rr[2], list(rr[3])
    nf = len(fields); rows = [list(data[i * nf:(i + 1) * nf]) for i in range(n)]
    p("fields", fields); [p(" ", r_) for r_ in rows]
    fi = db.GetAllFieldsInTable(key, 0, 0, [], [], [], [], [])
    p("field info", [x if not isinstance(x,(list,tuple)) else list(x) for x in fi])
    ie = fields.index("EccRatio")
    for r_ in rows:
        r_[ie] = "0/0585"
    fl = list(fi[3])
    flat = [v if v is not None else "" for r_ in rows for v in r_]
    p("Set", db.SetTableForEditingArray(key, ver, fl, n, flat)[-1])
    res = db.ApplyEditedTables(True)
    p("Apply", res[0], res[1], res[2], res[3], str(res[4])[:800])
    p("after", table(m, key).to_string())
    for pt in ("EXP", "EXN", "EYP", "EYN"):
        try:
            p(pt, m.LoadPatterns.AutoSeismic.GetAutoSeismicCode(pt))
        except Exception as ex:
            p(pt, "err", ex)
except Exception:
    import traceback; p(traceback.format_exc())
finish("r6b_ecc_test")
try:
    e.ApplicationExit(False)
except Exception:
    pass
os._exit(0)
