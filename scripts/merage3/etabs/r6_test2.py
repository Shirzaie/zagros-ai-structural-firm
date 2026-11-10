# -*- coding: utf-8 -*-
"""Diagnostic 2 (task 42): SetHeight + save + reopen; and Story Definitions table edit. Copies in C:\ZagrosTemp\r6test."""
import sys, os, shutil
from r5_common import *
from r6_test_heights import run, TD, SRC, HEIGHTS
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

def short(m, tag):
    m.Analyze.SetRunCaseFlag("", True, True)
    p(tag, "RunAnalysis", m.Analyze.RunAnalysis())
    m.DatabaseTables.SetLoadCasesSelectedForDisplay(list(m.LoadCases.GetNameList()[1]))
    mod = table(m, "Modal Participating Mass Ratios"); p(tag, "T", list(mod["Period"].head(3)))
    ss = table(m, "Story Stiffness"); p(tag, ss[ss["Output Case"] == "EXP"][["Story", "StiffX"]].to_string())
    ej = table(m, "Objects and Elements - Joints"); p(tag, "elem joints", len(ej)); p(ej.head(60).to_string())
    ef = table(m, "Objects and Elements - Frames"); p(tag, "elem frames", len(ef)); p(ef.head(30).to_string())

e = None
try:
    a = os.path.join(TD, "T_h2.EDB"); b = os.path.join(TD, "T_tab.EDB")
    shutil.copy2(SRC, a); shutil.copy2(SRC, b)
    e, m = connect(a); m.SetModelIsLocked(False)
    for st, h in HEIGHTS.items():
        m.Story.SetHeight(st, h)
    p("save", m.File.Save(a)); p("reopen", m.File.OpenFile(a)); m.SetPresentUnits(6)
    short(m, "H+SAVE")
    p("open b", m.File.OpenFile(b)); m.SetPresentUnits(6); m.SetModelIsLocked(False)
    db = m.DatabaseTables; key = "Story Definitions"
    r = db.GetTableForEditingArray(key, ""); ver, fields, n, data = r[0], list(r[1]), r[2], list(r[3]); nf = len(fields)
    p(fields, data)
    rows = [list(data[i*nf:(i+1)*nf]) for i in range(n)]
    ist, ih = fields.index("Story"), fields.index("Height")
    for row in rows:
        row[ih] = str(HEIGHTS[row[ist]]).replace(".", "/")
    fl = list(db.GetAllFieldsInTable(key, 0, 0, [], [], [], [], [])[3])
    p("set", db.SetTableForEditingArray(key, ver, fl, n, [v if v is not None else "" for row in rows for v in row])[-1])
    res = db.ApplyEditedTables(True); p("apply", res[0], res[1], res[2], res[3], str(res[4])[:500])
    p("stories", m.Story.GetStories())
    short(m, "TABLE")
except Exception:
    import traceback; p(traceback.format_exc())
finish("r6_test2")
try: e.ApplicationExit(False)
except Exception: pass
os._exit(0)
