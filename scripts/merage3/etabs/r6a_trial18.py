# -*- coding: utf-8 -*-
"""Task 45 (boss 2026-10-31): trial of the 12 parking columns C50X50/16T20 -> C50X50/16T18 on a TEMPORARY copy of
Merage3_Rev6a.EDB (Rev6a untouched). Run + ACI 318-19 design (51 A22). Writes r6a_trial18.json / .csv. Nothing else changed."""
import sys, os, json, shutil
import pandas as pd
from r5_common import *
import r5_run as R5
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
TD = r"C:\ZagrosTemp\r6a18"; os.makedirs(TD, exist_ok=True)
SRC = os.path.join(HERE, "Merage3_Rev6a.EDB")
TMP = os.path.join(TD, "Merage3_Rev6a_trial18.EDB")
NEW = json.load(open(os.path.join(HERE, "geom_Rev6a.json"), encoding="utf-8"))["new_objects_project_labels"]
for k in ("frames", "areas", "points"):
    for u, v in NEW[k].items():
        R5.GB[k][u] = v
CAP_SH = 3 * 113.1 / 85            # 3-leg phi12@85 (T44 column hoops), mm2/mm
S = {}
e = None
try:
    shutil.copy2(SRC, TMP)
    e, m = connect(TMP); m.SetModelIsLocked(False)
    base, new = "C50X50/16T20", "C50X50/16T18"
    rect = m.PropFrame.GetRectangle(base); rb = m.PropFrame.GetRebarColumn(base)
    p("SetRectangle", m.PropFrame.SetRectangle(new, rect[1], rect[2], rect[3]))
    args = list(rb[:-1]); args[8] = "18"
    p("SetRebarColumn", m.PropFrame.SetRebarColumn(new, *args), m.PropFrame.GetRebarColumn(new))
    m.PropFrame.SetModifiers(new, list(m.PropFrame.GetModifiers(base)[0]))
    pts, frs, ars = geometry(m)
    s1 = [f for f, v in frs.items() if v["kind"] == "column" and v["sec"] == base]
    assert len(s1) == 12 and all(frs[f]["story"] == "Story1" for f in s1), s1
    for f in s1:
        assert m.FrameObj.SetSection(f, new, 0) == 0
    m.Analyze.SetRunCaseFlag("", True, True)
    p("run", m.Analyze.RunAnalysis()); p("design", m.DesignConcrete.StartDesign())
    db = m.DatabaseTables
    db.SetLoadCasesSelectedForDisplay(list(m.LoadCases.GetNameList()[1])); db.SetLoadCombinationsSelectedForDisplay(list(m.RespCombo.GetNameList()[1]))
    cs = R5.oldlab(table(m, "Concrete Column Design Summary - ACI 318-19"), "Label")
    rows = []
    for (st, lab), g in cs.groupby(["Story", "Label_project"]):
        i = g["PMMRatio"].idxmax()
        v = max(g["VMajRebar"].max(), g["VMinRebar"].max()) * 1000
        rows.append({"Story": st, "Column": lab, "Sect": g.loc[i, "DesignSect"], "PMM": float(g.loc[i, "PMMRatio"]), "Combo": g.loc[i, "PMMCombo"],
                     "Av/s_req": round(v, 3), "shear_ratio_phi12@85x3": round(v / CAP_SH, 3),
                     "msg": "; ".join(sorted(set(str(x) for x in list(g["WarnMsg"]) + list(g["ErrMsg"]) if str(x) != "No Message")))})
    T = pd.DataFrame(rows).sort_values("PMM", ascending=False)
    p(T.to_string())
    dc = R5.oldlab(table(m, "Design Forces - Columns"), "Column")
    dc["Combo"] = dc["Combo"].astype(str).str.replace(r"-\d+$", "", regex=True)
    g = dc[(dc.Label_project == "C17") & (dc.Story == "Story1")]
    g0 = g[g.Station == g.Station.min()]; i = g0["P"].idxmax()
    S["C17_bottom_max_tension"] = {"P": float(g0.loc[i, "P"]), "M2": float(g0.loc[i, "M2"]), "M3": float(g0.loc[i, "M3"]), "combo": g0.loc[i, "Combo"]}
    mod = table(m, "Modal Participating Mass Ratios"); S["T"] = [float(x) for x in mod["Period"].head(3)]
    dr = table(m, "Story Drifts"); S["drift_max"] = float(dr[dr["Output Case"].isin(["EXP", "EXN", "EYP", "EYN"])]["Drift"].abs().max())
    jt = R5.oldlab(table(m, "Concrete Joint Design Summary - ACI 318-19"), "Label")
    jt["BC"] = jt[["BCMajRatio", "BCMinRatio"]].max(axis=1); jt["JS"] = jt[["JSMajRatio", "JSMinRatio"]].max(axis=1)
    S["joint_S1"] = jt[jt.Story == "Story1"][["Label_project", "BC", "JS"]].round(3).values.tolist()
    S["beam_msgs"] = R5.oldlab(table(m, "Concrete Beam Design Summary - ACI 318-19"), "Label").query("Status != 'No Message'")[["Story", "Label_project", "ErrMsg"]].drop_duplicates().values.tolist()
    S["columns"] = T.to_dict("records")
    T.to_csv(os.path.join(HERE, "r6a_trial18.csv"), index=False, encoding="utf-8-sig")
    p(json.dumps({k: v for k, v in S.items() if k != "columns"}, default=str))
except Exception:
    import traceback; p(traceback.format_exc())
json.dump(S, open(os.path.join(HERE, "r6a_trial18.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
finish("r6a_trial18")
try:
    e.ApplicationExit(False)
except Exception:
    pass
os._exit(0)
