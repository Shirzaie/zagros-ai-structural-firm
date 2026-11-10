# -*- coding: utf-8 -*-
"""Task 59: export Merage3 Rev6h from ETABS for the ABZ program (automatic ETABS -> ABZ test).
Works on a COPY of ETABS/Merage3_Rev6h.EDB in this folder, in its own ETABS instance (never attaches to a running ETABS).
Writes: Merage3_Rev6h_abz.e2k (the model text written by ETABS on save) and one CSV per table, as ETABS exports them."""
import os, sys, shutil, json, traceback
import comtypes.client

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "..", "..", "ETABS", "Merage3_Rev6h.EDB"))
EDB = os.path.join(HERE, "Merage3_Rev6h_abz.EDB")
OUT = os.path.join(HERE, "export")
EXE = r"C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"
TABLES = ["Element Forces - Beams", "Element Forces - Columns", "Joint Reactions", "Story Drifts",
          "Concrete Beam Design Summary - ACI 318-19", "Concrete Column Design Summary - ACI 318-19"]
LOG = []


def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)


def main():
    os.makedirs(OUT, exist_ok=True)
    shutil.copy2(SRC, EDB)
    p("copied", SRC, "->", EDB)
    h = comtypes.client.CreateObject("ETABSv1.Helper").QueryInterface(comtypes.gen.ETABSv1.cHelper)
    e = h.CreateObject(EXE)          # a new ETABS of its own
    p("ApplicationStart", e.ApplicationStart())
    m = e.SapModel
    try:
        r = m.File.OpenFile(EDB); p("OpenFile", r); assert r == 0
        assert os.path.normcase(m.GetModelFilename()) == os.path.normcase(EDB)
        m.SetPresentUnits(6)  # kN, m, C
        m.SetModelIsLocked(False)
        m.Analyze.SetRunCaseFlag("", True, True)
        p("RunAnalysis", m.Analyze.RunAnalysis())
        p("StartDesign", m.DesignConcrete.StartDesign())
        db = m.DatabaseTables
        combos = list(m.RespCombo.GetNameList()[1]); cases = list(m.LoadCases.GetNameList()[1])
        db.SetLoadCasesSelectedForDisplay(cases); db.SetLoadCombinationsSelectedForDisplay(combos)
        p("cases", len(cases), "combos", len(combos))
        avail = list(db.GetAvailableTables(0, [], [], [])[1])
        info = {}
        for k in TABLES:
            if k not in avail:
                p("  ! not available:", k); info[k] = "not available"; continue
            f = os.path.join(OUT, k.replace(" - ", "_").replace(" ", "_") + ".csv")
            r = db.GetTableForDisplayCSVFile(k, [], "All", 0, f)
            ok = os.path.exists(f)
            p("  table", k, "->", r, os.path.getsize(f) if ok else "missing"); info[k] = os.path.basename(f) if ok else f"error {r}"
        # the model text: ETABS writes <name>.$et on save; kept as .e2k
        m.SetModelIsLocked(False)
        p("Save", m.File.Save(EDB))
        et = os.path.splitext(EDB)[0] + ".$et"
        if os.path.exists(et):
            shutil.copy2(et, os.path.join(OUT, "Merage3_Rev6h_abz.e2k")); info["e2k"] = "Merage3_Rev6h_abz.e2k"
        p("e2k", info.get("e2k", "missing"))
        json.dump(info, open(os.path.join(OUT, "export_info.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        p(traceback.format_exc())
    try:
        p("ApplicationExit", e.ApplicationExit(False))
    except Exception as ex:
        p("exit err", ex)
    open(os.path.join(HERE, "log_export.txt"), "w", encoding="utf-8").write("\n".join(LOG))


if __name__ == "__main__":
    main()
    os._exit(0)
