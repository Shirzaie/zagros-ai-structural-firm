# -*- coding: utf-8 -*-
"""Merage3 Rev6e run (task 52): r6d_run.py on Merage3_Rev6e.EDB in its own ETABS instance, compared with Rev6d."""

import sys, os, json, math, traceback
import pandas as pd
import comtypes.client
import r5_run as R5
import r6_run as R6
from r5_common import *

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
EDB6A = os.path.join(HERE, "Merage3_Rev6e.EDB")
PFX = os.path.join(HERE, "Merage3_Rev6e_")
R6.EDB6 = EDB6A; R6.PFX = PFX; R6.REV5 = os.path.join(HERE, "Merage3_Rev6d_")
R5.PFX = PFX; R5.EDB = EDB6A
NEW = json.load(open(os.path.join(HERE, "geom_Rev6d.json"), encoding="utf-8"))["new_objects_project_labels"]
for k in ("frames", "areas", "points"):
    for u, v in NEW[k].items():
        R5.GB[k][u] = v


def rename(df):
    return df.rename(columns={c: c.replace("Rev5", "Rev6d").replace("Rev6b", "Rev6d").replace("Rev6a", "Rev6d").replace("Rev6c", "Rev6d") for c in df.columns})


def extra(S, out, T):
    E = {}
    dc = out["Design Forces - Columns"].copy()
    dc["Combo"] = dc["Combo"].astype(str).str.replace(r"-\d+$", "", regex=True)
    c6 = pd.read_csv(R6.REV5 + "columns_design_forces.csv", encoding="utf-8-sig")
    rows = []
    for lab in ("C16", "C17", "C18", "C19", "C2", "C6"):
        for st in ("Story1", "Story2", "Story3", "Story4", "Story5"):
            g = dc[(dc.Label_project == lab) & (dc.Story == st)]
            g6 = c6[(c6.Label_project == lab) & (c6.Story == st)]
            if g.empty:
                continue
            rows.append({"Column": lab, "Story": st, "Pu_max_kN": round(-g["P"].min(), 1), "Pu_max_Rev6d": round(-g6["P"].min(), 1) if len(g6) else None,
                         "M2_max": round(g["M2"].abs().max(), 1), "M3_max": round(g["M3"].abs().max(), 1), "V_max": round(max(g["V2"].abs().max(), g["V3"].abs().max()), 1)})
    E["Penthouse columns forces"] = pd.DataFrame(rows)
    # Story5 cantilevers (40x40) - same hand torsion check as r6_run.post6 with h = 400
    b = out["Beam Design Summary"].copy()
    for k in ("VRebar", "TTrnRebar"):
        b[k] = b[k] * 1000
    for k in ("AsTop", "AsBot", "TLngRebar"):
        b[k] = b[k] * 1e6
    b["Dem"] = b["VRebar"] + 2 * b["TTrnRebar"]
    bb = T["Beams shear+torsion"]
    fc, cv = 25.0, 41.5
    can = []
    for (st, lab), gg in b[b["Label_project"].isin(["B3", "B5", "B2", "B31", "B33", "B38", "B36", "B30", "B32", "B12", "BH"]) & (b["Story"] == "Story5")].groupby(["Story", "Label_project"]):
        r = gg.loc[gg["Dem"].idxmax()]
        t = bb[(bb.Story == st) & (bb.Label_project == lab)].iloc[0]
        bw, h = (250.0 if lab == "BH" else 400.0), 400.0
        Acp, pcp = bw * h, 2 * (bw + h)
        x1, y1 = bw - 2 * cv, h - 2 * cv
        Aoh, ph = x1 * y1, 2 * (x1 + y1)
        phTth = 0.75 * 0.083 * math.sqrt(fc) * Acp ** 2 / pcp / 1e6
        xs = math.hypot(t.Vu_kN * 1e3 / (bw * 340), t.Tu_kNm * 1e6 * ph / (1.7 * Aoh ** 2)) / (0.75 * 0.83 * math.sqrt(fc))
        can.append({"Story": st, "Label_project": lab, "Label_ETABS": r["Label"], "Sect": r["DesignSect"], "Tu_kNm": round(t.Tu_kNm, 2), "phiTth": round(phTth, 2),
                    "phiTcr": round(4 * phTth, 2), "Vu_kN": round(t.Vu_kN, 1), "Av/s+2At/s": round(r["Dem"], 3), "Al mm2": round(gg["TLngRebar"].max()),
                    "As top": round(gg["AsTop"].max()), "As bot": round(gg["AsBot"].max()), "xsect 22.7.7.1": round(xs, 3),
                    "msg": "; ".join(sorted(set(str(x) for x in gg["ErrMsg"].tolist() + gg["WarnMsg"].tolist() if str(x) not in ("No Message", "nan", ""))))})
    E["Story5 beams"] = pd.DataFrame(can)
    # cantilever Tu vs phiTcr (ACI 22.7.3.2 cap) for B3/B5/B6 Story1-4
    c = T["Cantilevers"].copy()
    c["phiTcr=4phiTth"] = (4 * c["phiTth"]).round(2)
    c["Tu<=phiTcr"] = c["Tu_kNm"] <= c["phiTcr=4phiTth"]
    T["Cantilevers"] = c
    # cantilever tip deflections (D + SD + L, elastic, cracked modifiers of the model) relative to the support joint
    jd = out["Joint Displacements"]
    pairs = {"Story5 B3 (new)": ("92", "90"), "Story5 B5 (new)": ("93", "91"), "Story4 B3": ("67", "18"), "Story4 B5": ("73", "40")}
    dfl = []
    for k, (tip, sup) in pairs.items():
        row = {"Cantilever": k}
        for case in ("Dead", "SuperDead", "Live", "Lr"):
            u = lambda q: float(jd[(jd["UniqueName"].astype(str) == q) & (jd["Output Case"] == case)]["Uz"].iloc[0]) if len(jd[(jd["UniqueName"].astype(str) == q) & (jd["Output Case"] == case)]) else float("nan")
            row[case + "_mm"] = round((u(tip) - u(sup)) * 1000, 2)
        row["D+SD+L_mm"] = round(row["Dead_mm"] + row["SuperDead_mm"] + row["Live_mm"] + row["Lr_mm"], 2)
        dfl.append(row)
    E["Cantilever tip deflection"] = pd.DataFrame(dfl)
    # hook beam connectivity check: its end joints must move with B31 / B33 (Dead, Uz) and eccentricity check of the seismic cases
    hk = []
    for q in [u for u, v in NEW["points"].items() if v["label"].startswith("BH")]:
        g_ = jd[(jd["UniqueName"].astype(str) == q) & (jd["Output Case"].isin(["Dead", "SuperDead"]))]
        hk.append({"joint": q, **{f"Uz_{c}_mm": round(float(g_[g_["Output Case"] == c]["Uz"].iloc[0]) * 1000, 3) for c in ("Dead", "SuperDead") if len(g_[g_["Output Case"] == c])}})
    E["Hook beam joints"] = pd.DataFrame(hk)
    br = out["Base reactions"]; br = br[br["Output Case"].isin(["EXP", "EXN", "EYP", "EYN"])][["Output Case", "FX", "FY", "MZ"]]
    E["Seismic base reactions"] = br
    pd.concat([E["Penthouse columns forces"].assign(table="columns"), E["Story5 beams"].assign(table="Story5 beams")]).to_csv(PFX + "penthouse.csv", index=False, encoding="utf-8-sig")
    return E


if __name__ == "__main__":
    e = None
    try:
        h = comtypes.client.CreateObject("ETABSv1.Helper").QueryInterface(comtypes.gen.ETABSv1.cHelper)
        e = h.CreateObject(EXE); p("ApplicationStart (own instance)", e.ApplicationStart()); m = e.SapModel
        assert m.File.OpenFile(EDB6A) == 0 and os.path.normcase(m.GetModelFilename()) == os.path.normcase(EDB6A)
        m.SetPresentUnits(6)
        m.SetModelIsLocked(False)
        D = R5.check_defs(m)
        p("DEFS", json.dumps(D, ensure_ascii=False, default=str))
        assert D["design_combos_ok"] and not D["A22_mismatch"], "design combos not the 51 A22 -> STOP"
        m.Analyze.SetRunCaseFlag("", True, True)
        p("RunAnalysis", m.Analyze.RunAnalysis())
        st = m.Analyze.GetCaseStatus(); p("case status", dict(zip(st[1], st[2])))
        p("StartDesign", m.DesignConcrete.StartDesign())
        S, out = R6.extract6(m)
        S["model"] = EDB6A
        S["defs"] = {k: D[k] for k in ("design_combos_n", "design_combos_ok", "code")}
        S["prefs"] = D["prefs"]; S["Omega0"] = D["prefs"].get("Omega0")
        S["overwrites_frame_type"] = out["Beam Overwrites"][["Story", "Label_project", "FrameType"]].query("FrameType != 'Sway Special'").values.tolist() if "Beam Overwrites" in out else None
        fin, T = R6.post6(S, out)
        E = extra(S, out, T)
        T.update(E)
        T = {k: rename(v) for k, v in T.items()}
        fin["Rev6d"] = fin.pop("Rev5")
        fin["cantilever_tip_deflection"] = E["Cantilever tip deflection"].to_dict("records")
        R5.write(fin, out, T)
        p(json.dumps({k: v for k, v in fin.items() if k not in ("corner", "roof_Pu")}, ensure_ascii=False, default=str, indent=1))
        for k in ("Columns PMM", "Joints BC + shear", "Cantilevers", "Story5 beams", "Penthouse columns forces", "Cantilever tip deflection",
                  "Corner columns Story1", "Roof columns Pu", "Beams shear+torsion", "Stair columns", "Soft storey 2800", "Drift", "Column warnings", "Beam messages"):
            if k in T:
                p("==", k); p(T[k].head(40).to_string())
        m.SetModelIsLocked(False)
        p("final save WITHOUT results (unlocked):", m.File.Save(EDB6A))
    except Exception:
        p(traceback.format_exc())
    finish("r6e_run")
    try:
        if e is not None:
            p("ApplicationExit", e.ApplicationExit(False))
    except Exception as ex:
        p("exit err", ex)
    finish("r6e_run")
    os._exit(0)
