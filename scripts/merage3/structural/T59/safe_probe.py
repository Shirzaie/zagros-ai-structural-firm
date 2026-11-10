# -*- coding: utf-8 -*-
"""Task 59c: probe the SAFE 23 API (own instance, new blank model; nothing on disk is opened). Lists tables that can be edited."""
import os, sys, json, traceback
import comtypes.client
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"C:\Program Files\Computers and Structures\SAFE 23\SAFE.exe"
h = comtypes.client.CreateObject("CSiAPIv1.Helper")
h = h.QueryInterface(comtypes.gen.CSiAPIv1.cHelper)
e = h.CreateObjectProgID("CSI.SAFE.API.ETABSObject")
print("start", e.ApplicationStart())
m = e.SapModel
out = {}
try:
    print("init", m.InitializeNewModel(6))
    print("blank", m.File.NewBlank())
    r = m.DatabaseTables.GetAllTables(0, [], [], [], [])
    keys, names, imp, isEmpty = list(r[1]), list(r[2]), list(r[3]), list(r[4]) if len(r) > 4 else []
    out["tables"] = [[k, imp[i]] for i, k in enumerate(keys)]
    print(len(keys), "tables")
    for k in keys:
        if any(w in k for w in ("Strip", "Area Object", "Point Object", "Spring", "Soil", "Slab", "Punching", "Design", "Material", "Load Pattern", "Point Load")):
            print(" ", k)
    out["sapmodel"] = [a for a in dir(m) if not a.startswith("_")]
    print("SapModel:", out["sapmodel"])
except Exception:
    print(traceback.format_exc())
json.dump(out, open(os.path.join(HERE, "safe_probe.json"), "w", encoding="utf-8"), indent=1)
try:
    print("exit", e.ApplicationExit(False))
except Exception as ex:
    print("exit err", ex)
os._exit(0)
