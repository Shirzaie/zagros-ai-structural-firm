# -*- coding: utf-8 -*-
"""Merage3 Rev.5: rebuild added mass (fixed point-load mass), check definitions, Run Analysis + Concrete design (51 A22),
extract everything BEFORE saving (ETABS 19 clears results on Save), post-process, then save the model without results
and close ETABS.  python r5_run.py
Outputs in Merage3\\ETABS\\: Merage3_Rev5_results.xlsx (raw ETABS tables), Merage3_Rev5_analysis.xlsx,
Merage3_Rev5_summary.json, Merage3_Rev5_joint_reactions_SAFE*.csv, Merage3_Rev5_cantilever_demand.csv, *_design_forces.csv
"""
import sys, os, json, math, traceback
import pandas as pd
from r5_common import *
from r5_build import rebuild_mass

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
PFX = os.path.join(HERE, "Merage3_Rev5_")
REF = os.path.join(HERE, "ref_run3")
CD, IE, LIMIT, LIMIT_OLD = 5.5, 1.0, 0.025, 0.020
CAP = 2 * 113.1 / 80
GB = json.load(open(os.path.join(HERE, "geom_before.json"), encoding="utf-8"))


def combo_defs():
    D = ["Dead", "Dead part", "SuperDead"]
    out = {"A22-1": [(d, 1.4) for d in D], "A22-2": [(d, 1.2) for d in D] + [("Live", 1.6), ("Lr", 0.5)],
           "A22-3": [(d, 1.2) for d in D] + [("Live", 1.0), ("Lr", 1.6)]}
    for k, fd, live in (("6", 1.35, True), ("7", 0.75, False)):
        base = [(d, fd) for d in D] + ([("Live", 1.0)] if live else [])
        for e_ in ("EXP", "EXN", "EYP", "EYN"):
            for s in (1, -1):
                out[f"A22-{k}{'+' if s > 0 else '-'}{e_}"] = base + [(e_, s)]
        for a, b in (("EXP", "EYP"), ("EXN", "EYN"), ("EYP", "EXP"), ("EYN", "EXN")):
            for sa in (1, -1):
                for sb in (1, -1):
                    out[f"A22-{k}_{a}{'+' if sa > 0 else '-'}_{b}{'+' if sb > 0 else '-'}"] = base + [(a, sa), (b, 0.3 * sb)]
    return out


def check_defs(m):
    S = {}
    defs = combo_defs()
    bad = []
    for nm, items in defs.items():
        r = m.RespCombo.GetCaseList(nm)
        if sorted((n, round(float(s), 4)) for n, s in zip(r[2], r[3])) != sorted((n, round(float(s), 4)) for n, s in items):
            bad.append(nm)
    dc = table(m, "Concrete Frame Design Load Combination Data")
    names = list(dc["ComboName"]) if not dc.empty else []
    S["A22_mismatch"] = bad
    S["design_combos_n"] = len(names)
    S["design_combos_ok"] = len(names) == 51 and set(names) == set(defs)
    pr = table(m, "Concrete Frame Design Preferences - ACI 318-19")
    S["prefs"] = pr.iloc[0].to_dict() if not pr.empty else {}
    S["code"] = m.DesignConcrete.GetCode()[0]
    S["load_patterns"] = {pt: m.LoadPatterns.GetLoadType(pt)[0] for pt in m.LoadPatterns.GetNameList()[1]}
    return S


def story_heights(m):
    r = m.Story.GetStories()
    z = dict(zip(list(r[1]), list(r[2])))
    order = sorted(z, key=lambda s: z[s])
    return {order[i]: z[order[i]] - z[order[i - 1]] for i in range(1, len(order))}


def oldlab(df, col_label, col_un="UniqueName", kind="frames"):
    """add project label (Run 1-3 / architect) next to the ETABS label, by unique name"""
    if df.empty or col_un not in df:
        return df
    d = GB[kind]
    df.insert(df.columns.get_loc(col_label) + 1, "Label_project", [d.get(str(u), {}).get("label", "") for u in df[col_un].astype(str)])
    return df


def extract(m):
    out, S = {}, {"model": EDB}
    db = m.DatabaseTables
    db.SetLoadCasesSelectedForDisplay(list(m.LoadCases.GetNameList()[1]))
    db.SetLoadCombinationsSelectedForDisplay(list(m.RespCombo.GetNameList()[1]))
    seismic = ["EXP", "EXN", "EYP", "EYN"]
    aus = table(m, "Load Pattern Definitions - Auto Seismic - User Coefficient"); out["Auto seismic"] = aus
    S["W_kN"] = float(aus["WeightUsed"].max()); S["V_kN"] = float(aus["BaseShear"].max()); S["C"] = float(aus["C"].max()); S["K"] = float(aus["K"].max())
    mass = table(m, "Mass Summary by Story"); out["Mass by story"] = mass
    S["mass_by_story_kN"] = {r.Story: round(float(r.UX) * G, 1) for r in mass.itertuples()}
    base = table(m, "Base Reactions"); out["Base reactions"] = base
    b = base[base["Output Case"].isin(seismic)]
    S["VX_kN"] = float(b["FX"].abs().max()); S["VY_kN"] = float(b["FY"].abs().max())
    g = base[base["Output Case"].isin(["Dead", "Dead part", "SuperDead", "Live", "Lr"])]
    S["base_FZ_by_case_kN"] = {r["Output Case"]: round(float(r["FZ"]), 1) for _, r in g.iterrows()}
    mod = table(m, "Modal Participating Mass Ratios"); out["Modal"] = mod
    S["T1_T2_T3_s"] = [float(x) for x in mod["Period"].head(3)]
    S["mode_dirs"] = [("UX" if r.UX > max(r.UY, r.RZ) else "UY" if r.UY > r.RZ else "RZ") for r in mod.head(3).itertuples()]
    S["SumUX"] = float(mod["SumUX"].max()); S["SumUY"] = float(mod["SumUY"].max())
    dr = table(m, "Story Drifts"); out["Story drifts (all)"] = dr
    hts = story_heights(m)
    d = dr[dr["Output Case"].isin(seismic)].copy(); d["Drift"] = d["Drift"].abs()
    g = d.groupby(["Story", "Direction"], sort=False)["Drift"].max().reset_index()
    g["h_m"] = g["Story"].map(hts); g["Delta=Cd*de/Ie"] = g["Drift"] * CD / IE
    g["Ratio /0.025"] = g["Delta=Cd*de/Ie"] / LIMIT; g["Ratio /0.020"] = g["Delta=Cd*de/Ie"] / LIMIT_OLD
    g["Design story drift mm"] = g["Delta=Cd*de/Ie"] * g["h_m"] * 1000
    out["Drift max per story"] = g
    S["drift_elastic_max"] = float(g["Drift"].max()); S["drift_ratio_vs_0.025"] = float(g["Ratio /0.025"].max())
    S["drift_ratio_vs_0.020"] = float(g["Ratio /0.020"].max()); S["design_story_drift_mm_max"] = float(g["Design story drift mm"].max())
    S["drift_table"] = g.round(5).to_dict("records")
    sd = table(m, "Story Max Over Avg Drifts"); out["Story max-avg drift"] = sd
    if not sd.empty:
        S["torsion_ratio_max"] = float(sd[sd["Output Case"].isin(seismic)]["Ratio"].max())
    for k in [k for k in list(db.GetAvailableTables(0, [], [], [])[1]) if "ACI 318-19" in k and "Concrete" in k]:
        df = table(m, k)
        if not df.empty:
            out[k.replace("Concrete ", "").replace(" - ACI 318-19", "")[:31]] = oldlab(df, "Label") if "Label" in df else df
    for k in ("Concrete Frame Design Load Combination Data", "Design Forces - Beams", "Design Forces - Columns", "Joint Reactions",
              "Element Forces - Columns", "Joint Displacements", "Load Combination Definitions", "Mass Source Definition",
              "Grid Definitions - Grid Lines", "Point Object Connectivity", "Beam Object Connectivity", "Column Object Connectivity"):
        df = table(m, k)
        if "Beam" in df.columns and k.startswith("Design"):
            df = oldlab(df, "Beam")
        if "Column" in df.columns and k.startswith(("Design", "Element")):
            df = oldlab(df, "Column")
        if k == "Joint Reactions":
            df = oldlab(df, "Label", kind="points")
        out[k[:31]] = df
        p(f"  table {k}: {len(df)} rows")
    jr = out["Joint Reactions"]
    jr.to_csv(PFX + "joint_reactions_SAFE.csv", index=False, encoding="utf-8-sig")
    jr[jr["Output Case"].isin(["Dead", "Dead part", "SuperDead", "Live", "Lr", "EXP", "EXN", "EYP", "EYN"]) |
       jr["Output Case"].astype(str).str.startswith("A22-")].to_csv(PFX + "joint_reactions_SAFE_A22.csv", index=False, encoding="utf-8-sig")
    S["joint_reactions"] = f"{jr['UniqueName'].nunique()} supports x {jr['Output Case'].nunique()} cases/combos"
    out["Design Forces - Beams"].to_csv(PFX + "beams_design_forces.csv", index=False, encoding="utf-8-sig")
    out["Design Forces - Columns"].to_csv(PFX + "columns_design_forces.csv", index=False, encoding="utf-8-sig")
    # cantilever single-case forces (B2/B3/B5/B6) for task 13 records
    rs = m.Results.Setup; rs.DeselectAllCasesAndCombosForOutput()
    for c in ["Dead", "Dead part", "SuperDead", "Live", "EXP", "EXN", "EYP", "EYN"]:
        rs.SetCaseSelectedForOutput(c, True)
    fr = []
    for u, v in GB["frames"].items():
        if v["label"] in ("B2", "B3", "B5", "B6") and v["story"] in ("Story1", "Story2", "Story3", "Story4"):
            r = m.Results.FrameForce(u, 0)
            for k in range(r[0]):
                fr.append({"Story": v["story"], "Beam": v["label"], "UniqueName": u, "Station_m": r[2][k], "Case": r[5][k],
                           "P": r[8][k], "V2": r[9][k], "V3": r[10][k], "T": r[11][k], "M2": r[12][k], "M3": r[13][k]})
    out["Cantilever single cases"] = pd.DataFrame(fr)
    return S, out


def post(S, out):
    T = {}
    r3 = pd.ExcelFile(os.path.join(REF, "Merage3_run3_20261022_analysis.xlsx"))
    S3 = json.load(open(os.path.join(REF, "Merage3_run3_20261022_summary.json"), encoding="utf-8"))
    c = out["Column Design Summary"]
    g = c.loc[c.groupby(["Story", "Label_project"])["PMMRatio"].idxmax(), ["Story", "Label_project", "Label", "DesignSect", "PMMRatio", "PMMCombo", "VMajRebar", "VMinRebar", "WarnMsg"]]
    p3 = r3.parse("Columns PMM (per column)")[["Story", "Label", "PMMRatio"]].rename(columns={"Label": "Label_project", "PMMRatio": "PMM_Run3"})
    g = g.merge(p3, on=["Story", "Label_project"], how="left")
    g["VMajRebar"] *= 1000; g["VMinRebar"] *= 1000
    g["Result"] = g["PMMRatio"].map(lambda v: "رد" if v > 1 else "OK")
    g = g.sort_values("PMMRatio", ascending=False); T["Columns PMM"] = g
    j = out["Joint Design Summary"].copy()
    j["BCmax"] = j[["BCMajRatio", "BCMinRatio"]].max(axis=1); j["JSmax"] = j[["JSMajRatio", "JSMinRatio"]].max(axis=1)
    j3 = r3.parse("Joints BC + shear")[["Story", "Label", "BCmax", "JSmax"]].rename(columns={"Label": "Label_project", "BCmax": "BC_Run3", "JSmax": "JS_Run3"})
    j = j[["Story", "Label_project", "Label", "BCMajRatio", "BCMajCombo", "BCMinRatio", "BCMinCombo", "BCmax", "JSmax", "WarnMsg"]].merge(j3, on=["Story", "Label_project"], how="left").sort_values("BCmax", ascending=False)
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
    b3 = r3.parse("Beams shear+torsion")[["Story", "Label", "Dem_max", "Tu_kNm"]].rename(columns={"Label": "Label_project", "Dem_max": "Dem_Run3", "Tu_kNm": "Tu_Run3"})
    bb = bb.merge(b3, on=["Story", "Label_project"], how="left").sort_values("Dem", ascending=False)
    T["Beams shear+torsion"] = bb
    fc, fyt, fy, cv = 25.0, 340.0, 400.0, 41.5
    can = []
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
        r3c = pd.read_csv(os.path.join(REF, "Merage3_run3_20261022_cantilever_demand.csv"), encoding="utf-8-sig")
        prev = r3c[(r3c.Story == st) & (r3c.Label == lab)]["Av/s+2At/s"]
        can.append({"Story": st, "Label_project": lab, "Label_ETABS": r["Label"], "Sect": r["DesignSect"], "Tu_kNm": round(t.Tu_kNm, 1), "Tu_combo": t.Tu_combo,
                    "Vu_kN": round(t.Vu_kN, 1), "phiTth": round(phTth, 2), "Av/s": round(r["VRebar"], 3), "At/s ETABS": round(r["TTrnRebar"], 3),
                    "At/s hand": round(ats, 3), "Av/s+2At/s": round(r["Dem"], 3), "cap phi12@80": round(CAP, 3), "ratio": round(r["Dem"] / CAP, 3),
                    "Stirrups": "OK" if r["Dem"] <= CAP else "رد", "Al mm2": round(Al), "As top": round(AsT), "As bot": round(AsB),
                    "Long (3phi25+2phi16/side)": "OK" if ok_l else "رد", "xsect 22.7.7.1": round(xs, 3),
                    "Run3 Av/s+2At/s": float(prev.iloc[0]) if len(prev) else None})
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
    rp = dc[(dc.Story == "Story4") & dc.Label_project.isin(["C5", "C10", "C19", "C20", "C21"])]
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
        "Run3": {k: S3.get(k) for k in ("W_kN", "V_kN", "T1_T2_T3_s", "drift_ratio_vs_0.025", "design_story_drift_mm_max", "PMM_max", "PMM_max_at",
                                         "BC_max", "cantilever_demand_max", "cantilever_demand_max_at", "beam_Av/s+2At/s_max", "beam_Av/s+2At/s_max_at", "base_FZ_by_case_kN")},
    })
    return fin, T


def write(fin, out, T):
    with pd.ExcelWriter(PFX + "results.xlsx", engine="openpyxl") as xw:
        for name, df in out.items():
            if df is not None and not df.empty:
                df.to_excel(xw, sheet_name="".join(ch for ch in name if ch not in "[]:*?/\\")[:31], index=False)
    with pd.ExcelWriter(PFX + "analysis.xlsx", engine="openpyxl") as xw:
        pd.DataFrame([{"Key": k, "Value": json.dumps(v, ensure_ascii=False, default=str)} for k, v in fin.items()]).to_excel(xw, sheet_name="SUMMARY", index=False)
        for k, v in T.items():
            v.to_excel(xw, sheet_name=k[:31], index=False)
    json.dump(fin, open(PFX + "summary.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)


if __name__ == "__main__":
    e = None
    try:
        e, m = connect()
        m.SetModelIsLocked(False)
        tot, by = rebuild_mass(m, {"Dead": 1.0, "Dead part": 1.0, "SuperDead": 1.0, "Live": 0.2})
        p("save model with fixed mass:", m.File.Save(EDB))
        D = check_defs(m)
        p("DEFS", json.dumps(D, ensure_ascii=False, default=str))
        assert D["design_combos_ok"] and not D["A22_mismatch"], "design combos not the 51 A22 -> STOP"
        m.SetModelIsLocked(False)
        m.Analyze.SetRunCaseFlag("", True, True)
        p("RunAnalysis", m.Analyze.RunAnalysis())
        st = m.Analyze.GetCaseStatus(); p("case status", dict(zip(st[1], st[2])))
        p("StartDesign", m.DesignConcrete.StartDesign())
        S, out = extract(m)
        S["defs"] = {k: D[k] for k in ("design_combos_n", "design_combos_ok", "code")}
        S["Omega0"] = D["prefs"].get("Omega0")
        S["added_weight_kN"] = round(tot, 1); S["added_by_kN"] = {k: round(v, 1) for k, v in by.items()}
        S["overwrites_frame_type"] = out["Beam Overwrites"][["Story", "Label_project", "FrameType"]].query("FrameType != 'Sway Special'").values.tolist() if "Beam Overwrites" in out else None
        fin, T = post(S, out)
        write(fin, out, T)
        p(json.dumps({k: v for k, v in fin.items() if k not in ("corner", "roof_Pu")}, ensure_ascii=False, default=str, indent=1))
        for k in ("Columns PMM", "Joints BC + shear", "Cantilevers", "Corner columns Story1", "Roof columns Pu", "Beams shear+torsion"):
            p("==", k); p(T[k].head(14).to_string())
        m.SetModelIsLocked(False)
        p("final save WITHOUT results (unlocked):", m.File.Save(EDB))
    except Exception:
        p(traceback.format_exc())
    finish("run")
    try:
        if e is not None:
            p("ApplicationExit", e.ApplicationExit(False))
    except Exception as ex:
        p("exit err", ex)
    finish("run")
    os._exit(0)
