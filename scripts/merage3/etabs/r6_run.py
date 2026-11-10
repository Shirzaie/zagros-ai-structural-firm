# -*- coding: utf-8 -*-
"""Merage3 Rev6 (task 42): check definitions, Run Analysis + ACI 318-19 design (51 A22), extract BEFORE saving,
post-process with comparison to Rev5 (after T32-33), save the model without results, close ETABS.   python r6_run.py
Mass is NOT rebuilt here (r6_build.py builds the half / half wall mass).
Outputs: Merage3_Rev6_results.xlsx, _analysis.xlsx, _summary.json, _joint_reactions_SAFE*.csv, _cantilever_demand.csv,
         _beams/_columns_design_forces.csv, _stair_columns.csv
"""
import sys, os, json, math, traceback
import pandas as pd
import r5_run as R5
from r5_common import *

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
EDB6 = os.path.join(HERE, "Merage3_Rev6.EDB")
PFX = os.path.join(HERE, "Merage3_Rev6_")
REV5 = os.path.join(HERE, "Merage3_Rev5_")
R5.PFX = PFX
R5.EDB = EDB6
CAP = 2 * 113.1 / 80


def extract6(m):
    S, out = R5.extract(m)
    ej = table(m, "Objects and Elements - Joints")
    zst = [round(z, 3) for z in m.Story.GetStories()[2]]
    zsh = sorted(set(ej[ej["ObjType"] == "Shell"]["GlobalZ"].round(3))) if "ObjType" in ej else []
    zall = sorted(set(ej["GlobalZ"].round(3)))
    S["mesh_check"] = {"story_z": zst, "shell_node_z": zsh, "all_node_z": zall, "ok": set(zsh) <= set(zst)}
    p("  MESH CHECK", S["mesh_check"])
    out["Analysis joints"] = ej
    for k in ("Story Stiffness", "Story Forces", "Diaphragm Center Of Mass Displacements", "Centers Of Mass And Rigidity",
              "Story Max Over Avg Displacements", "Mass Summary by Story", "Story Definitions", "Tower and Base Story Definitions",
              "Frame Section Property Definitions - Concrete Rectangular", "Frame Assignments - Section Properties"):
        df = R5.table(m, k) if hasattr(R5, "table") else table(m, k)
        out[k[:31]] = df
        p(f"  table {k}: {len(df)} rows")
    return S, out


def post6(S, out):
    T = {}
    x5 = pd.ExcelFile(REV5 + "analysis.xlsx")
    S5 = json.load(open(REV5 + "summary.json", encoding="utf-8"))
    c = out["Column Design Summary"]
    g = c.loc[c.groupby(["Story", "Label_project"])["PMMRatio"].idxmax(), ["Story", "Label_project", "Label", "DesignSect", "PMMRatio", "PMMCombo", "VMajRebar", "VMinRebar", "WarnMsg"]]
    p5 = x5.parse("Columns PMM")[["Story", "Label_project", "PMMRatio", "VMajRebar", "VMinRebar"]].rename(columns={"PMMRatio": "PMM_Rev5", "VMajRebar": "VMaj_Rev5", "VMinRebar": "VMin_Rev5"})
    g = g.merge(p5, on=["Story", "Label_project"], how="left")
    g["VMajRebar"] *= 1000; g["VMinRebar"] *= 1000
    g["Result"] = g["PMMRatio"].map(lambda v: "رد" if v > 1 else "OK")
    g = g.sort_values("PMMRatio", ascending=False); T["Columns PMM"] = g
    j = out["Joint Design Summary"].copy()
    j["BCmax"] = j[["BCMajRatio", "BCMinRatio"]].max(axis=1); j["JSmax"] = j[["JSMajRatio", "JSMinRatio"]].max(axis=1)
    j5 = x5.parse("Joints BC + shear")[["Story", "Label_project", "BCmax", "JSmax"]].rename(columns={"BCmax": "BC_Rev5", "JSmax": "JS_Rev5"})
    j = j[["Story", "Label_project", "Label", "BCMajRatio", "BCMajCombo", "BCMinRatio", "BCMinCombo", "BCmax", "JSmax", "WarnMsg"]].merge(j5, on=["Story", "Label_project"], how="left").sort_values("BCmax", ascending=False)
    T["Joints BC + shear"] = j
    b = out["Beam Design Summary"].copy()
    for k in ("VRebar", "TTrnRebar"):
        b[k] = b[k] * 1000
    for k in ("AsTop", "AsBot", "TLngRebar"):
        b[k] = b[k] * 1e6
    b["Dem"] = b["VRebar"] + 2 * b["TTrnRebar"]
    df = out["Design Forces - Beams"].copy()
    df["Combo"] = df["Combo"].astype(str).str.replace(r"-\d+$", "", regex=True)
    df["absT"] = df["T"].abs(); df["absV2"] = df["V2"].abs()
    tu = df.loc[df.groupby(["Story", "Label_project"])["absT"].idxmax(), ["Story", "Label_project", "absT", "Combo"]].rename(columns={"absT": "Tu_kNm", "Combo": "Tu_combo"})
    vu = df.loc[df.groupby(["Story", "Label_project"])["absV2"].idxmax(), ["Story", "Label_project", "absV2", "Combo"]].rename(columns={"absV2": "Vu_kN", "Combo": "Vu_combo"})
    bb = b.groupby(["Story", "Label_project", "Label", "DesignSect"]).agg(VRebar=("VRebar", "max"), TTrn=("TTrnRebar", "max"), TLng=("TLngRebar", "max"),
                                                                         Dem=("Dem", "max"), AsTop=("AsTop", "max"), AsBot=("AsBot", "max")).reset_index()
    bb = bb.merge(tu, on=["Story", "Label_project"], how="left").merge(vu, on=["Story", "Label_project"], how="left")
    b5 = x5.parse("Beams shear+torsion")[["Story", "Label_project", "Dem", "Tu_kNm", "AsTop", "AsBot", "Vu_kN"]].rename(
        columns={"Dem": "Dem_Rev5", "Tu_kNm": "Tu_Rev5", "AsTop": "AsTop_Rev5", "AsBot": "AsBot_Rev5", "Vu_kN": "Vu_Rev5"})
    bb = bb.merge(b5, on=["Story", "Label_project"], how="left").sort_values("Dem", ascending=False)
    T["Beams shear+torsion"] = bb
    fc, fyt, cv = 25.0, 340.0, 41.5
    can = []
    c5 = pd.read_csv(REV5 + "cantilever_demand.csv", encoding="utf-8-sig")
    for (st, lab), gg in b[b["Label_project"].isin(["B3", "B5", "B6"]) & b["Story"].isin(["Story1", "Story2", "Story3", "Story4"])].groupby(["Story", "Label_project"]):
        r = gg.loc[gg["Dem"].idxmax()]
        t = bb[(bb.Story == st) & (bb.Label_project == lab)].iloc[0]
        bw = int(r["DesignSect"].split("BW")[1].split("x")[0]) * 10
        Acp, pcp = bw * 500.0, 2 * (bw + 500.0)
        x1, y1 = bw - 2 * cv, 500 - 2 * cv
        Aoh, ph = x1 * y1, 2 * (x1 + y1)
        phTth = 0.75 * 0.083 * math.sqrt(fc) * Acp ** 2 / pcp / 1e6
        ats = t.Tu_kNm * 1e6 / (0.75 * 2 * 0.85 * Aoh * fyt) if t.Tu_kNm > phTth else 0.0
        xs = math.hypot(t.Vu_kN * 1e3 / (bw * 440), t.Tu_kNm * 1e6 * ph / (1.7 * Aoh ** 2)) / (0.75 * 0.83 * math.sqrt(fc))
        Al, AsT, AsB = gg["TLngRebar"].max(), gg["AsTop"].max(), gg["AsBot"].max()
        ok_l = AsT + Al / 4 <= 1473 and AsB + Al / 4 <= 1473 and Al / 4 <= 402
        prev = c5[(c5.Story == st) & (c5.Label_project == lab)]["Av/s+2At/s"]
        can.append({"Story": st, "Label_project": lab, "Label_ETABS": r["Label"], "Sect": r["DesignSect"], "Tu_kNm": round(t.Tu_kNm, 1), "Tu_combo": t.Tu_combo,
                    "Vu_kN": round(t.Vu_kN, 1), "phiTth": round(phTth, 2), "Av/s": round(r["VRebar"], 3), "At/s ETABS": round(r["TTrnRebar"], 3),
                    "At/s hand": round(ats, 3), "Av/s+2At/s": round(r["Dem"], 3), "cap phi12@80": round(CAP, 3), "ratio": round(r["Dem"] / CAP, 3),
                    "Stirrups": "OK" if r["Dem"] <= CAP else "رد", "Al mm2": round(Al), "As top": round(AsT), "As bot": round(AsB),
                    "Long (3phi25+2phi16/side)": "OK" if ok_l else "رد", "xsect 22.7.7.1": round(xs, 3),
                    "Rev5 Av/s+2At/s": float(prev.iloc[0]) if len(prev) else None})
    can = pd.DataFrame(can); T["Cantilevers"] = can
    can.to_csv(PFX + "cantilever_demand.csv", index=False, encoding="utf-8-sig")
    dc = out["Design Forces - Columns"].copy()
    dc["Combo"] = dc["Combo"].astype(str).str.replace(r"-\d+$", "", regex=True)
    corner = []
    for lab in ("C1", "C17", "C5", "C16", "C19", "C21"):
        gg = dc[(dc.Label_project == lab) & (dc.Story == "Story1")]
        g0 = gg[gg.Station == gg.Station.min()]
        i = g0["P"].idxmax()
        corner.append({"Column": lab, "Label_ETABS": g0.loc[i, "Column"], "Pmax_tension_kN": round(g0.loc[i, "P"], 1), "combo": g0.loc[i, "Combo"],
                       "M2": round(g0.loc[i, "M2"], 1), "M3": round(g0.loc[i, "M3"], 1), "Pmax_comp_kN": round(-g0["P"].min(), 1)})
    T["Corner columns Story1"] = pd.DataFrame(corner)
    # stair columns C2 / C6 (short-column check input): Pu range, Vu, per storey (all A22 combos)
    sc = []
    for lab in ("C2", "C6", "C16", "C18"):
        for st in ("Story1", "Story2", "Story3", "Story4"):
            gg = dc[(dc.Label_project == lab) & (dc.Story == st)]
            if gg.empty:
                continue
            sc.append({"Column": lab, "Story": st, "Label_ETABS": gg["Column"].iloc[0], "Pu_max_comp_kN": round(-gg["P"].min(), 1), "Pu_min_comp_kN": round(-gg["P"].max(), 1),
                       "V2_max": round(gg["V2"].abs().max(), 1), "V3_max": round(gg["V3"].abs().max(), 1),
                       "M2_max": round(gg["M2"].abs().max(), 1), "M3_max": round(gg["M3"].abs().max(), 1)})
    T["Stair columns"] = pd.DataFrame(sc)
    T["Stair columns"].to_csv(PFX + "stair_columns.csv", index=False, encoding="utf-8-sig")
    rp = dc[(dc.Story == "Story4") & dc.Label_project.isin(["C5", "C10", "C19", "C20", "C21", "C1", "C9", "C17"])]
    roof = rp.groupby("Label_project").apply(lambda g_: pd.Series({"Pu_max_comp_kN": round(-g_["P"].min(), 1)})).reset_index()
    roof["Ag_fc_10"] = 506.25; roof["Exempt_18.7.3.1"] = roof["Pu_max_comp_kN"] <= 506.25
    T["Roof columns Pu"] = roof
    cw = out["Column Design Summary"]
    cw = cw[cw["Status"] != "No Message"][["Story", "Label_project", "Label", "PMMRatio", "WarnMsg", "ErrMsg"]].drop_duplicates(["Story", "Label_project"])
    T["Column warnings"] = cw
    bmsg = out["Beam Design Summary"]
    bmsg = bmsg[bmsg["Status"] != "No Message"][["Story", "Label_project", "Label", "WarnMsg", "ErrMsg"]].drop_duplicates()
    T["Beam messages"] = bmsg
    T["Drift"] = pd.DataFrame(S["drift_table"])
    ss = out.get("Story Stiffness", pd.DataFrame())
    if not ss.empty:
        s2 = ss[ss["Output Case"].isin(["EXP", "EXN", "EYP", "EYN"])].copy()
        T["Story stiffness"] = s2
        soft = []
        order = ["Story1", "Story2", "Story3", "Story4", "Story5"]
        for case in ("EXP", "EYP"):
            d = s2[s2["Output Case"] == case].set_index("Story")
            col = "StiffX" if case == "EXP" else "StiffY"
            for k, st in enumerate(order[:-1]):
                if st not in d.index:
                    continue
                kx = float(d.loc[st, col]) if not isinstance(d.loc[st, col], pd.Series) else float(d.loc[st, col].iloc[0])
                ab = [float(d.loc[s, col]) if not isinstance(d.loc[s, col], pd.Series) else float(d.loc[s, col].iloc[0]) for s in order[k + 1:k + 4] if s in d.index and s != "Story5"]
                if not ab:
                    continue
                soft.append({"case": case, "Story": st, "K": round(kx), "K_above": round(ab[0]), "ratio_above": round(kx / ab[0], 3),
                             "ratio_avg3": round(kx / (sum(ab) / len(ab)), 3), "soft_2800 (<0.7 / <0.8)": (kx / ab[0] < 0.7) or (kx / (sum(ab) / len(ab)) < 0.8)})
        T["Soft storey 2800"] = pd.DataFrame(soft)
    fin = {k: v for k, v in S.items() if k != "drift_table"}
    fin.update({
        "PMM_max": float(g.iloc[0]["PMMRatio"]), "PMM_max_at": f"{g.iloc[0]['Story']} {g.iloc[0]['Label_project']} (ETABS {g.iloc[0]['Label']}, {g.iloc[0]['PMMCombo']})",
        "columns_over_1": g[g.PMMRatio > 1][["Story", "Label_project"]].values.tolist(),
        "BC_max": float(j.iloc[0]["BCmax"]), "BC_over_1": {f"{r.Story} {r.Label_project}": round(float(r.BCmax), 3) for r in j[j.BCmax > 1].itertuples()},
        "joint_shear_max": float(j["JSmax"].max()), "column_warnings": [f"{r.Story} {r.Label_project}: {r.WarnMsg}" for r in cw.itertuples()],
        "beam_messages": [f"{r.Story} {r.Label_project}: {r.WarnMsg} {r.ErrMsg}" for r in bmsg.itertuples()],
        "beam_dem_max": float(bb.iloc[0]["Dem"]), "beam_dem_max_at": f"{bb.iloc[0]['Story']} {bb.iloc[0]['Label_project']}",
        "cantilever_dem_max": float(can["Av/s+2At/s"].max()), "cantilever_dem_max_at": " ".join(can.loc[can["Av/s+2At/s"].idxmax(), ["Story", "Label_project"]]),
        "cantilever_rejected": can[(can.Stirrups != "OK") | (can["Long (3phi25+2phi16/side)"] != "OK")][["Story", "Label_project"]].values.tolist(),
        "roof_Pu": roof.to_dict("records"), "corner": corner,
        "soft_storey": T["Soft storey 2800"].to_dict("records") if "Soft storey 2800" in T else None,
        "Rev5": {k: S5.get(k) for k in ("W_kN", "V_kN", "T1_T2_T3_s", "mode_dirs", "drift_elastic_max", "drift_ratio_vs_0.025", "design_story_drift_mm_max", "torsion_ratio_max",
                                         "PMM_max", "PMM_max_at", "BC_max", "joint_shear_max", "beam_dem_max", "beam_dem_max_at", "cantilever_dem_max", "cantilever_dem_max_at",
                                         "base_FZ_by_case_kN", "mass_by_story_kN")},
    })
    return fin, T


if __name__ == "__main__":
    e = None
    try:
        e, m = connect(EDB6)
        m.SetModelIsLocked(False)
        D = R5.check_defs(m)
        p("DEFS", json.dumps(D, ensure_ascii=False, default=str))
        assert D["design_combos_ok"] and not D["A22_mismatch"], "design combos not the 51 A22 -> STOP"
        m.Analyze.SetRunCaseFlag("", True, True)
        p("RunAnalysis", m.Analyze.RunAnalysis())
        st = m.Analyze.GetCaseStatus(); p("case status", dict(zip(st[1], st[2])))
        p("StartDesign", m.DesignConcrete.StartDesign())
        S, out = extract6(m)
        S["defs"] = {k: D[k] for k in ("design_combos_n", "design_combos_ok", "code")}
        S["prefs"] = D["prefs"]
        S["Omega0"] = D["prefs"].get("Omega0")
        S["overwrites_frame_type"] = out["Beam Overwrites"][["Story", "Label_project", "FrameType"]].query("FrameType != 'Sway Special'").values.tolist() if "Beam Overwrites" in out else None
        fin, T = post6(S, out)
        R5.write(fin, out, T)
        p(json.dumps({k: v for k, v in fin.items() if k not in ("corner", "roof_Pu")}, ensure_ascii=False, default=str, indent=1))
        for k in ("Columns PMM", "Joints BC + shear", "Cantilevers", "Corner columns Story1", "Roof columns Pu", "Beams shear+torsion", "Stair columns", "Soft storey 2800", "Drift"):
            if k in T:
                p("==", k); p(T[k].head(16).to_string())
        m.SetModelIsLocked(False)
        p("final save WITHOUT results (unlocked):", m.File.Save(EDB6))
    except Exception:
        p(traceback.format_exc())
    finish("r6_run")
    try:
        if e is not None:
            p("ApplicationExit", e.ApplicationExit(False))
    except Exception as ex:
        p("exit err", ex)
    finish("r6_run")
    os._exit(0)
