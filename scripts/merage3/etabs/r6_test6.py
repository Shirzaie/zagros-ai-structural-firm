# -*- coding: utf-8 -*-
"""Diagnostic 6 (task 42): SetHeight + recreate_areas on a copy; check shell z, T, loads."""
import sys, os, shutil
from r5_common import *
from r6_test_heights import TD, SRC, HEIGHTS
from r6_areafix import recreate_areas
from r6_test5 import chk
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
e = None
try:
    a = os.path.join(TD, "T_h6.EDB"); shutil.copy2(SRC, a)
    e, m = connect(a); m.SetModelIsLocked(False)
    for st, h in HEIGHTS.items():
        m.Story.SetHeight(st, h)
    recreate_areas(m)
    chk(m, "FIX", run=True)
    ss = table(m, "Story Stiffness"); p(ss[ss["Output Case"] == "EXP"][["Story", "StiffX"]].to_string())
    b = table(m, "Base Reactions"); p(b[b["Output Case"].isin(["Dead", "SuperDead", "Live", "Lr"])][["Output Case", "FZ"]].to_string())
    ms = table(m, "Mass Summary by Story"); p(ms.to_string())
    dr = table(m, "Story Drifts"); d = dr[dr["Output Case"].isin(["EXP", "EYP"])]; p(d.groupby(["Story", "Direction"])["Drift"].max().to_string())
except Exception:
    import traceback; p(traceback.format_exc())
finish("r6_test6")
try: e.ApplicationExit(False)
except Exception: pass
os._exit(0)
